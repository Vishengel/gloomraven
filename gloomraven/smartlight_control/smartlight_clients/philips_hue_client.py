import logging

from phue import Bridge

from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)

logger = logging.getLogger(__name__)


class PhilipsHueClient(SmartlightClient):
    def __init__(self, bridge_ip: str):
        super().__init__(bridge_ip)
        self.bridge_ip = bridge_ip
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
        """Get all available light IDs from the Philips Hue bridge."""
        try:
            lights = self.bridge.get_light_objects("id")
            return list(lights.keys())
        except Exception as exc:
            logger.error("Failed to get light IDs from Philips Hue bridge: %s", exc)
            return []

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
