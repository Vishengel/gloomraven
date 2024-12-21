from typing import Dict

from phue import Bridge

from gloomraven.smartlight_client.smartlight_controller import SmartlightClient


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
        except KeyError:
            print(f"Light '{light_name}' not found on the bridge.")