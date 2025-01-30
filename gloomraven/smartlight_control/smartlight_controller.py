import atexit
import logging
import signal
import time
from queue import Queue
from threading import Event, Thread
from typing import Dict

from gloomraven.data_model.element_state import Element, ElementLevel
from gloomraven.data_model.game_state import GameState
from gloomraven.smartlight_control.smartlight_clients.config import (
    CONFIG,
    ELEMENT_COLOR_MAP,
)
from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)

logger = logging.getLogger(__name__)


class SmartlightController:
    def __init__(self, smartlight_client: SmartlightClient):
        self.smartlight_client = smartlight_client
        self.current_active_elements: Dict[Element, ElementLevel] = {}
        # self.light_ids = [8, 9, 12]  # Hard coded during testing phase
        self.group_id = 1  # Hard coded for Geke's woonkamer

        self.color_update_queue: Queue = Queue()

        # Store initial light colors here, return to this state when no elements are active or program is shutdown
        reference_light_id = 16
        reference_light = self.smartlight_client.bridge.get_light(reference_light_id)
        # self.original_light_state = {"hue": reference_light["state"]["hue"], "sat": reference_light["state"]["sat"],
        #                              "bri": reference_light["state"]["bri"]}
        self.original_light_state = {"hue": 4453, "sat": 205,
                                     "bri": 248}
        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self._stop_event = Event()
        self._thread = Thread(target=self._light_update_loop, daemon=True)
        self._thread.start()

        logger.info(
            "SmartlightController initialized with bridge ip %s",
            smartlight_client.bridge_ip,
        )

    def update(self, game_state: GameState):
        self._process_game_state(game_state)

    def _process_game_state(self, game_state: GameState):
        self._process_element_state(game_state.element_state)

    def _process_element_state(self, element_state: Dict[Element, ElementLevel]):
        new_active_elements = {
            element: element_level
            for element, element_level in element_state.items()
            if element_level != ElementLevel.INERT
        }
        if new_active_elements == {}:
            # Clear the queue
            while not self.color_update_queue.empty():
                self.color_update_queue.get()
            self.smartlight_client.change_all_colors_in_group(self.group_id, self.original_light_state)
        #     while not self.color_update_queue.empty():
        #         self.color_update_queue.get()
            return

        if new_active_elements == self.current_active_elements:
            return

        # Clear the queue
        while not self.color_update_queue.empty():
            self.color_update_queue.get()

        for element, element_level in new_active_elements.items():
            if element not in ELEMENT_COLOR_MAP:
                logger.error(
                    "No mapping to a HSV color is present in the element color map for element %s",
                    element,
                )
                continue
            hsv_for_element = ELEMENT_COLOR_MAP[element].copy()

            if element_level == ElementLevel.HALF:
                hsv_for_element["bri"] = (
                    int(0.85*hsv_for_element["bri"])
                )  # Half brightness if element is at half capacity

            self.color_update_queue.put(hsv_for_element)

    def _light_update_loop(self):
        while not self._stop_event.is_set():
            if not self.color_update_queue.empty():
                color = self.color_update_queue.get()
                self.smartlight_client.change_all_colors_in_group(self.group_id, color)
                self.color_update_queue.put(color)
                time.sleep(CONFIG.light_transition_interval)
            else:
                self.smartlight_client.change_all_colors_in_group(self.group_id, self.original_light_state)
                time.sleep(CONFIG.light_transition_interval)

    def restore_original_light_states(self):
        logger.info("Restoring original light states: %s", self.original_light_state)
        self.smartlight_client.change_all_colors_in_group(
            1, self.original_light_state
        )

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self.restore_original_light_states()

    def _handle_signal(self, signum: int, _):
        logger.info("Received signal %s, stopping SmartlightController...", signum)
        self.stop()
