import asyncio
import logging
import threading
from typing import Any

from pywizlight import PilotBuilder, discovery, wizlight
from pywizlight.exceptions import WizLightError

from gloomraven.smartlight_control.smartlight_clients.config import CONFIG
from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)

logger = logging.getLogger(__name__)
logging.getLogger("pywizlight").setLevel(logging.INFO)


def _normalise_mac(mac: str) -> str:
    """WiZ bulbs report their MAC as lowercase hex without separators, e.g. a8bb50aabbcc."""
    return mac.lower().replace(":", "").replace("-", "")


class PhilipsWizClient(SmartlightClient):
    id_to_light_mapping: dict[int, wizlight]
    initial_states = dict[int, Any]

    def __init__(self, light_macs: list[str] | None = None):
        super().__init__()
        self.light_macs = [_normalise_mac(mac) for mac in (CONFIG.lights if light_macs is None else light_macs)]
        self._loop = None
        self._loop_thread = None
        self._start_event_loop_thread()
        self._run_async_threadsafe(self._discover_lights_on_network())
        logger.info("Smartlight client of type %s initialized", self.__class__.__name__)

    def reset_to_initial_state(self, transition_speed: int | None = None) -> None:
        assert self.id_to_light_mapping.keys() == self.initial_states.keys()
        for idx, state in self.initial_states.items():
            self.change_color_by_light_ids(light_ids=[idx], color=state, transition_speed=transition_speed)

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
        self.initial_states = {}

        for idx, light in self.id_to_light_mapping.items():
            # Newer pywizlight versions return one state per bulb head; regular bulbs only have one
            state = (await light.updateState())[0]
            self.initial_states[idx] = {
                "r": state.get_rgb()[0],
                "g": state.get_rgb()[1],
                "b": state.get_rgb()[2],
                "bri": state.get_brightness(),
            }

    def _select_configured_lights(self, lights: list[wizlight]) -> list[wizlight]:
        if not self.light_macs:
            return lights

        mac_to_light = {_normalise_mac(light.mac): light for light in lights if light.mac}
        if missing_macs := set(self.light_macs) - set(mac_to_light):
            logger.warning("Configured WiZ lights not found on the network: %s", sorted(missing_macs))
        return [mac_to_light[mac] for mac in self.light_macs if mac in mac_to_light]

    def get_all_light_ids(self) -> list[int]:
        return list(self.id_to_light_mapping.keys())

    def list_available_lights(self) -> list[str]:
        return [f"{light.mac} (ip {light.ip})" for light in self.discovered_lights]

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
