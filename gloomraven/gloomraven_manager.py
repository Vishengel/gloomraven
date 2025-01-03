import logging
import sys

from gloomraven.config import BASECONFIG
from gloomraven.data_model.element_state import Element, ElementLevel
from gloomraven.smartlight_client.philips_hue_client import PhilipsHueClient
from gloomraven.x_haven_client.x_haven_client import XHavenClient

logging.basicConfig(stream=sys.stdout, level=BASECONFIG.log_level)
logger = logging.getLogger(__name__)


class GloomravenManager:
    def __init__(self, ip: str, port: int):
        self.x_haven_client = XHavenClient(ip, port)
        self.running = False
        self.philips_hue_client = PhilipsHueClient("192.168.1.153")

    def run(self) -> None:
        self.running = True
        with self.x_haven_client.connect() as connection:
            while self.running:
                try:
                    data = self.x_haven_client.receive_data(connection)
                    if data:
                        game_state = self.x_haven_client.process_server_message(data)
                        element_state = game_state.element_state
                        if element_state[Element.FIRE] == ElementLevel.FULL:
                            self.philips_hue_client.bridge.set_light([8,9,12], {"hue": 0, "sat": 254, "bri": 254})
                        elif element_state[Element.FIRE] == ElementLevel.HALF:
                            self.philips_hue_client.bridge.set_light([8, 9, 12], {"hue": 0, "sat": 254, "bri": 254})
                        else:
                            self.philips_hue_client.bridge.set_light([8,9,12], {"hue": 0, "sat": 100, "bri": 254})

                except KeyboardInterrupt:
                    logger.info("Terminating due to KeyboardInterrupt")
                    self.running = False
