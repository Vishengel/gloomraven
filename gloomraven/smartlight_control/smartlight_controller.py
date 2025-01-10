import logging
from typing import Dict, List

from gloomraven.data_model.element_state import Element, ElementLevel
from gloomraven.data_model.game_state import GameState
from gloomraven.smartlight_control.smartlight_clients.config import ELEMENT_COLOR_MAP
from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)

logger = logging.getLogger(__name__)


class SmartlightController:
    def __init__(self, smartlight_client: SmartlightClient):
        self.smartlight_client = smartlight_client
        self.current_active_elements: Dict[Element, ElementLevel] = {}
        self.light_ids = [8, 9, 12]  # Hard coded during testing phase
        self.color_updates: List[Dict[str, int]] = []
        logger.info(
            "SmartlightController initialized with bridge ip %s",
            smartlight_client.bridge_ip,
        )

    def update(self, game_state: GameState):
        self._process_game_state(game_state)
        self._update_lights()

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

            self.color_updates.append(hsv_for_element)

    def _update_lights(self):
        # This is temporary, as this just cycles through the element-based colors and immediately
        #  updates the lights for each of them.
        for color in self.color_updates:
            self.smartlight_client.change_color_by_light_ids(self.light_ids, color)
