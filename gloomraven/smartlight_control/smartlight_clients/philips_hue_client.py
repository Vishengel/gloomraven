import logging

from phue import Bridge, PhueException

from gloomraven.smartlight_control.smartlight_clients.config import CONFIG
from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)

logger = logging.getLogger(__name__)


class PhilipsHueClient(SmartlightClient):
    def __init__(self, bridge_ip: str, light_names: list[str] | None = None):
        super().__init__()
        self.bridge_ip = bridge_ip
        self.light_names = CONFIG.lights if light_names is None else light_names
        self.bridge = Bridge(self.bridge_ip)
        self.bridge.connect()

        logger.info(
            "Smartlight client of type %s initialized with bridge ip %s",
            self.__class__.__name__,
            self.bridge_ip,
        )

    def reset_to_initial_state(self) -> None:
        super().reset_to_initial_state()

    def get_all_light_ids(self) -> list[int]:
        """Get the IDs of the configured lights, or of all lights if none are configured."""
        try:
            name_to_light = self.bridge.get_light_objects("name")
        except (PhueException, OSError) as exc:
            logger.error("Failed to get lights from Philips Hue bridge: %s", exc)
            return []

        if not self.light_names:
            return [light.light_id for light in name_to_light.values()]

        if missing_names := set(self.light_names) - set(name_to_light):
            logger.warning("Configured Hue lights not found on the bridge: %s", sorted(missing_names))
        return [name_to_light[name].light_id for name in self.light_names if name in name_to_light]

    def list_available_lights(self) -> list[str]:
        return [f"{name} (id {light.light_id})" for name, light in self.bridge.get_light_objects("name").items()]

    def _set_light(self, light_ids: list[int], color: dict[str, int]):
        if "hue" in color:
            color["hue"] = int(color["hue"] / 360) * 65535
        self.bridge.set_light(light_ids, color)

    def change_color_by_light_ids(
        self, light_ids: list[int], color: dict[str, int], transition_speed: int | None = None
    ) -> None:
        self.bridge.set_light(light_ids, color)

    def change_color_by_light_name(self, light_name: str, color: dict[str, int]) -> None:
        try:
            light = self.bridge.get_light_objects("name")[light_name]
            self.bridge.set_light(light.light_id, color)
        except KeyError as exc:
            logger.error("Light '%s' not found on the Philips Hue bridge", exc)
