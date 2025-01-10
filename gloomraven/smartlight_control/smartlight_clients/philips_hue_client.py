import logging
from typing import Dict

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

    def change_color(self, color: Dict[str, int], light_name: str) -> None:
        try:
            light = self.bridge.get_light_objects("name")[light_name]
            self.bridge.set_light(light.light_id, color)
        except KeyError as exc:
            logger.error("Light '%s' not found on the Philips Hue bridge", exc)
