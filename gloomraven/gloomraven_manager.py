import logging
import sys
from typing import Dict, List

from gloomraven.config import BASECONFIG
from gloomraven.data_model.element_state import Element, ElementLevel
from gloomraven.data_model.game_state import GameState
from gloomraven.gloomhaven_app_clients.x_haven_client.x_haven_client import XHavenClient
from gloomraven.smartlight_control.smartlight_clients.config import ELEMENT_COLOR_MAP
from gloomraven.smartlight_control.smartlight_clients.philips_hue_client import (
    PhilipsHueClient,
)

logging.basicConfig(stream=sys.stdout, level=BASECONFIG.log_level)
logger = logging.getLogger(__name__)


class GloomravenManager:
    def __init__(self, ip: str, port: int):
        self.x_haven_client = XHavenClient(ip, port)
        self.running = False
        self.philips_hue_client = PhilipsHueClient(
            "192.168.1.153"
        )  # Hard coded during testing phase
        self.light_ids = [8, 9, 12]  # Hard coded during testing phase
        self.current_active_elements: Dict[Element, ElementLevel] = {}
        self.color_updates: List[Dict[str, int]] = []

    def run(self) -> None:
        self.running = True
        with self.x_haven_client.connect() as connection:
            while self.running:
                self._await_and_process_data(connection)

    def _await_and_process_data(self, connection):
        try:
            data = self.x_haven_client.receive_data(connection)
            if data:
                game_state = self.x_haven_client.process_server_message(data)
                self._process_game_state(game_state)
                self._update()
        except KeyboardInterrupt:
            logger.info("Terminating due to KeyboardInterrupt")
            self.running = False

    def _process_game_state(self, game_state: GameState):
        self._process_element_state(game_state.element_state)

    def _process_element_state(self, element_state: Dict[Element, ElementLevel]):
        new_active_elements = {
            element: element_level
            for element, element_level in element_state.items()
            if element_level != ElementLevel.INERT
        }
        if new_active_elements == self.current_active_elements:
            return

        for element, element_level in new_active_elements.items():
            if element not in ELEMENT_COLOR_MAP:
                logger.error(
                    "No mapping to a HSV color is present in the element color map for element %s",
                    element,
                )
                continue
            hsv_for_element = ELEMENT_COLOR_MAP[element]

            if element_level == ElementLevel.HALF:
                hsv_for_element["bri"] = (
                    hsv_for_element["bri"] // 2
                )  # Half brightness if element is at half capacity

    def _update(self):
        # This is temporary, as this just cycles through the element-based colors and immediately
        #  updates the lights for each.
        for color in self.color_updates:
            self.philips_hue_client.bridge.set_light(self.light_ids, color)
