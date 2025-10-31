import atexit
import logging
import signal
import time
from queue import Queue
from threading import Event, Thread

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
        self.light_ids = self.smartlight_client.get_all_light_ids()
        self.current_active_elements: dict[Element, ElementLevel] = {}

        self.color_update_queue: Queue = Queue()

        # Store initial light colors here, return to this state when no elements are active or program is shutdown
        self.original_light_state = None
        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self._stop_event = Event()
        self._thread = Thread(target=self._light_update_loop, daemon=True)
        self._thread.start()

    def update(self, game_state: GameState):
        self._process_game_state(game_state)

    def _process_game_state(self, game_state: GameState):
        self._process_element_state(game_state.element_state)

    def _process_element_state(self, element_state: dict[Element, ElementLevel]):
        new_active_elements = {
            element: element_level
            for element, element_level in element_state.items()
            if element_level != ElementLevel.INERT
        }
        logger.debug("Queue: %s", self.color_update_queue.qsize())
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
            hsv_for_element = ELEMENT_COLOR_MAP[element]

            if element_level == ElementLevel.HALF:
                hsv_for_element["bri"] = hsv_for_element["bri"] // 2  # Half brightness if element is at half capacity

            self.color_update_queue.put(hsv_for_element)

    def _light_update_loop(self):
        while not self._stop_event.is_set():
            if not self.color_update_queue.empty():
                color = self.color_update_queue.get()
                logger.debug("Changing color to %s", color)
                self.smartlight_client.change_color_by_light_ids(self.light_ids, color)
                time.sleep(CONFIG.light_transition_interval)
            else:
                self.restore_original_light_states()

    def restore_original_light_states(self):
        logger.info("Restoring original light states: %s", self.original_light_state)
        self.smartlight_client.change_color_by_light_ids(self.light_ids, self.original_light_state)

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self.restore_original_light_states()

    def _handle_signal(self, signum: int, _):
        logger.info("Received signal %s, stopping SmartlightController...", signum)
        self.stop()
