import atexit
import logging
import signal
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

        self.active_colors: list[dict[str, int]] = []  # Store colors for cycling
        self.color_index = 0  # Track current position in cycle
        self.transition_speed = CONFIG.light_transition_speed
        self.transition_interval = CONFIG.light_transition_interval

        atexit.register(self.stop)
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self._force_transition_event = Event()
        self._stop_event = Event()
        self._thread = Thread(target=self._light_update_loop, daemon=True)
        self._thread.start()

    def update(self, game_state: GameState):
        self._process_game_state(game_state)

    def _process_game_state(self, game_state: GameState):
        self._process_element_state(game_state.element_state)

    def _process_element_state(self, element_state: dict[Element, ElementLevel]):
        """Process changes in element states and update active colors accordingly.

        Args:
            element_state: Dictionary mapping Elements to their current ElementLevel
        """
        new_active_elements = {
            element: element_level
            for element, element_level in element_state.items()
            if element_level != ElementLevel.INERT
        }
        if new_active_elements == self.current_active_elements:
            return

        logger.debug("Change in elements detected. Currently active elements: %s", new_active_elements)

        added_elements = set(new_active_elements.keys()) - set(self.current_active_elements.keys())
        removed_elements = set(self.current_active_elements.keys()) - set(new_active_elements.keys())

        self.current_active_elements = new_active_elements
        force_transition = added_elements or self._currently_active_color_has_been_removed(removed_elements)

        self._reset_color_queue()
        self._set_color_queue(new_active_elements)

        if force_transition:
            self._force_transition_event.set()

    def _set_color_queue(self, active_elements: dict[Element, ElementLevel]):
        for element, element_level in active_elements.items():
            if element not in ELEMENT_COLOR_MAP:
                logger.error(
                    "No mapping to a HSV color is present in the element color map for element %s",
                    element,
                )
                continue
            hsv_for_element = ELEMENT_COLOR_MAP[element].copy()  # Make a copy to avoid modifying original

            if element_level == ElementLevel.HALF:
                hsv_for_element["bri"] = hsv_for_element["bri"] // 2

            self.active_colors.append(hsv_for_element)

    def _reset_color_queue(self):
        self.active_colors = []
        self.color_index = 0

    def _currently_active_color_has_been_removed(self, removed_color_set: list | set):
        current_active_color = self.active_colors[self.color_index]
        return current_active_color in removed_color_set

    def _light_update_loop(self):
        previous_colors = []

        while not self._stop_event.is_set():
            if len(self.active_colors) < 2 and previous_colors == self.active_colors:
                # We only cycle if there are multiple elements active or the set of elements has changed
                continue

            if self.active_colors:
                color = self.active_colors[self.color_index]
                self.color_index = (self.color_index + 1) % len(self.active_colors)

                logger.debug("Changing color to %s (index %s)", color, self.color_index)
                self.smartlight_client.change_color_by_light_ids(self.light_ids, color, self.transition_speed)
            else:
                self.restore_original_light_states()

            previous_colors = self.active_colors.copy()
            self._force_transition_event.wait(timeout=self.transition_interval)
            self._force_transition_event.clear()

    def restore_original_light_states(self):
        logger.info("Restoring original light state")
        try:
            self.smartlight_client.reset_to_initial_state(transition_speed=self.transition_speed)
        except NotImplementedError as exc:
            logger.error("Restoring original light state not supported by client: %s", exc)

    def stop(self):
        self._stop_event.set()
        self._thread.join()
        self.restore_original_light_states()

    def _handle_signal(self, signum: int, _):
        logger.info("Received signal %s, stopping SmartlightController...", signum)
        self.stop()
