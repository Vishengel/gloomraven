import asyncio
import logging
import threading

from pywizlight import PilotBuilder, discovery, wizlight

from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)

logger = logging.getLogger(__name__)
logging.getLogger("pywizlight").setLevel(logging.INFO)


class PhilipsWizClient(SmartlightClient):
    id_to_light_mapping: dict[int, wizlight]

    def __init__(self):
        super().__init__()
        self._loop = None
        self._loop_thread = None
        self._start_event_loop_thread()
        self._run_async_threadsafe(self._discover_lights_on_network())
        logger.info("Smartlight client of type %s initialized", self.__class__.__name__)

    def _start_event_loop_thread(self):
        """Start a dedicated thread with an event loop for async operations."""
        self._loop_ready = threading.Event()

        def run_loop():
            self._loop = asyncio.new_event_loop()
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
        lights = await discovery.discover_lights()
        self.id_to_light_mapping = dict(enumerate(lights))

    def get_all_light_ids(self) -> list[int]:
        return list(self.id_to_light_mapping.keys())

    def change_color_by_light_ids(
        self, light_ids: list[int], color: dict[str, int], transition_speed: int | None = None
    ) -> None:
        async def run_tasks():
            tasks = [self._change_color_async(ip, color) for ip in light_ids]
            await asyncio.gather(*tasks)

        self._run_async_threadsafe(run_tasks())

    async def _change_color_async(self, light_id: id, color: dict[str, int], transition_speed: int | None = None):
        """Async method to change light color."""
        try:
            light = self.id_to_light_mapping[light_id]
            await light.turn_on(
                PilotBuilder(hucolor=(color["hue"], color["sat"]), brightness=color["bri"], speed=transition_speed)
            )
        except Exception as exc:
            logger.error("Failed to change color for WiZ light at %s: %s", light_id, exc)

    def add_light(self, name: str, ip: str):
        """Add a WiZ light to the known lights dictionary."""
        self.lights[name] = ip
        logger.info("Added WiZ light '%s' at IP %s", name, ip)

    async def turn_on_light(self, light_ip: str):
        """Turn on a WiZ light."""
        try:
            light = wizlight(light_ip)
            await light.turn_on()
        except Exception as exc:
            logger.error("Failed to turn on WiZ light at %s: %s", light_ip, exc)

    async def turn_off_light(self, light_ip: str):
        """Turn off a WiZ light."""
        try:
            light = wizlight(light_ip)
            await light.turn_off()
        except Exception as exc:
            logger.error("Failed to turn off WiZ light at %s: %s", light_ip, exc)
