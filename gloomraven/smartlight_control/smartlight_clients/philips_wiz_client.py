import asyncio
import logging
import threading
from typing import Any

from pywizlight import PilotBuilder, discovery, wizlight
from pywizlight.exceptions import WizLightError

from gloomraven.smartlight_control.smartlight_clients.config import CONFIG
from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    AvailableLight,
    SmartlightClient,
)

logger = logging.getLogger(__name__)
logging.getLogger("pywizlight").setLevel(logging.INFO)


# Pilot fields that describe what a bulb shows and can be sent back as is. A bulb only reports the fields of its current
# mode: sceneId (+ speed) for a scene, temp for white, r/g/b/c/w for a colour
RESTORABLE_PILOT_FIELDS = ("dimming", "sceneId", "speed", "temp", "r", "g", "b", "c", "w")


def _normalise_mac(mac: str) -> str:
    """WiZ bulbs report their MAC as lowercase hex without separators, e.g. a8bb50aabbcc."""
    return mac.lower().replace(":", "").replace("-", "")


def _get_pilot_params_to_restore(pilot: dict[str, Any]) -> dict[str, Any]:
    if not pilot.get("state"):
        return {"state": False}
    restorable_fields = {field: pilot[field] for field in RESTORABLE_PILOT_FIELDS if field in pilot}
    if restorable_fields.get("sceneId") == 0:
        # sceneId 0 means the bulb isn't showing a scene, and isn't a valid scene to set
        del restorable_fields["sceneId"]
    return {"state": True} | restorable_fields


class PhilipsWizClient(SmartlightClient):
    id_to_light_mapping: dict[int, wizlight]

    def __init__(self):
        super().__init__()
        self.light_macs: list[str] = []
        self._loop = None
        self._loop_thread = None
        self._start_event_loop_thread()
        self._run_async_threadsafe(self._discover_lights_on_network())
        logger.info("Smartlight client of type %s initialized", self.__class__.__name__)

    def _start_event_loop_thread(self):
        """Start a dedicated thread with an event loop for async operations."""
        self._loop_ready = threading.Event()

        def run_loop():
            # The default Proactor loop on Windows sometimes never closes pywizlight's discovery socket, which hangs
            # discovery forever. The selector loop doesn't have this problem and is the default on other platforms
            self._loop = asyncio.SelectorEventLoop()
            asyncio.set_event_loop(self._loop)
            self._loop_ready.set()
            try:
                self._loop.run_forever()
            finally:
                self._loop.close()

        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        self._loop_ready.wait()  # Wait until loop is ready

    def _run_async_threadsafe(self, coro):
        """Run async coroutine from any thread safely."""
        if self._loop is None:
            raise RuntimeError("Event loop not initialized")

        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    async def _discover_lights_on_network(self):
        self.discovered_lights = await discovery.discover_lights(broadcast_space=CONFIG.wiz_broadcast_address)
        self.id_to_light_mapping = dict(enumerate(self._select_configured_lights(self.discovered_lights)))

    def select_lights(self, light_keys: list[str]) -> None:
        self.light_macs = [_normalise_mac(mac) for mac in light_keys]
        self.id_to_light_mapping = dict(enumerate(self._select_configured_lights(self.discovered_lights)))

    def _get_light_states(self, light_ids: list[int]) -> dict[int, dict[str, Any]]:
        async def get_states():
            return await asyncio.gather(*(self._get_light_state_async(light_id) for light_id in light_ids))

        states = self._run_async_threadsafe(get_states())
        return {light_id: state for light_id, state in zip(light_ids, states, strict=True) if state is not None}

    async def _get_light_state_async(self, light_id: int) -> dict[str, Any] | None:
        light = self.id_to_light_mapping[light_id]
        try:
            # Newer pywizlight versions return one state per bulb head; regular bulbs only have one
            states = await light.updateState()
        except WizLightError as exc:
            logger.warning("Could not read the state of WiZ light at %s, it won't be restored: %s", light.ip, exc)
            return None
        if not states or states[0] is None:
            logger.warning("WiZ light at %s returned no state, it won't be restored", light.ip)
            return None
        return dict(states[0].pilotResult)

    def _set_light_states(self, light_states: dict[int, dict[str, Any]], transition_speed: int | None = None) -> None:
        async def set_states():
            await asyncio.gather(
                *(self._set_light_state_async(light_id, pilot) for light_id, pilot in light_states.items())
            )

        self._run_async_threadsafe(set_states())

    async def _set_light_state_async(self, light_id: int, pilot: dict[str, Any]) -> None:
        light = self.id_to_light_mapping[light_id]
        try:
            await light.send({"method": "setPilot", "params": _get_pilot_params_to_restore(pilot)})
        except WizLightError as exc:
            logger.error("Failed to restore the state of WiZ light at %s: %s", light.ip, exc)

    def _select_configured_lights(self, lights: list[wizlight]) -> list[wizlight]:
        if not self.light_macs:
            return lights

        mac_to_light = {_normalise_mac(light.mac): light for light in lights if light.mac}
        if missing_macs := set(self.light_macs) - set(mac_to_light):
            logger.warning("Configured WiZ lights not found on the network: %s", sorted(missing_macs))
        return [mac_to_light[mac] for mac in self.light_macs if mac in mac_to_light]

    def get_all_light_ids(self) -> list[int]:
        return list(self.id_to_light_mapping.keys())

    def rediscover_lights(self) -> None:
        self._run_async_threadsafe(self._discover_lights_on_network())

    def list_available_lights(self) -> list[AvailableLight]:
        selected_macs = {light.mac for light in self.id_to_light_mapping.values()}
        return [
            AvailableLight(key=light.mac, description=f"ip {light.ip}", selected=light.mac in selected_macs)
            for light in self.discovered_lights
        ]

    def change_color_by_light_ids(
        self, light_ids: list[int], color: dict[str, int], transition_speed: int | None = None
    ) -> None:
        async def run_tasks():
            tasks = [self._change_color_async(ip, color) for ip in light_ids]
            await asyncio.gather(*tasks)

        self._run_async_threadsafe(run_tasks())

    async def _change_color_async(self, light_id: int, color: dict[str, int], transition_speed: int | None = None):
        """Lil' hacky, but works for now. Will be refactored when HSV and RGB have proper data classes."""
        if "hue" in color.keys() and color["hue"] is not None:
            pilot_builder = PilotBuilder(
                hucolor=(color["hue"], color["sat"]), brightness=color["bri"], speed=transition_speed
            )
        elif "r" in color.keys() and color["r"] is not None:
            pilot_builder = PilotBuilder(
                rgb=(color["r"], color["g"], color["b"]), brightness=color["bri"], speed=transition_speed
            )
        elif "bri" in color.keys() and color["bri"] is not None:
            pilot_builder = PilotBuilder(brightness=color["bri"], speed=transition_speed)
        else:
            raise ValueError("A HSV dict OR RGB dict OR brightness value must be provided")

        light = self.id_to_light_mapping[light_id]
        try:
            await light.turn_on(pilot_builder)
        except WizLightError as exc:
            logger.error("Failed to change color for WiZ light at %s: %s", light.ip, exc)
