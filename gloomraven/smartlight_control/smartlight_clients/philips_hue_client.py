import logging
from typing import Dict, List

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

    def change_color_by_light_name(
        self, light_name: str, color: Dict[str, int]
    ) -> None:
        try:
            light = self.bridge.get_light_objects("name")[light_name]
            self.bridge.set_light(light.light_id, color)
        except KeyError as exc:
            logger.error("Light '%s' not found on the Philips Hue bridge", exc)

    def change_color_by_light_ids(
        self, light_ids: List[int], color: Dict[str, int]
    ) -> None:
        self.bridge.set_light(light_ids, color)

    def change_all_colors_in_group(self, group_id: int, color: Dict[str, int]):
        group_dict = self.bridge.get_group(group_id)
        self.change_color_by_light_ids([int(light_id) for light_id in group_dict["lights"] if int(light_id) != 10], color)
