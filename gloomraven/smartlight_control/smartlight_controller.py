import logging
from collections.abc import Callable
from threading import Event, Lock, Thread
from types import TracebackType
from typing import Self

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
    """
    Show the active elements on the smartlights, cycling through them when more than one is active.

    Use it as a context manager: the lights' state is saved on entry and restored on exit, also when the program
    exits through an exception or Ctrl+C.
    """

    def __init__(self, smartlight_client: SmartlightClient):
        self.smartlight_client = smartlight_client
        self.light_ids = self.smartlight_client.get_all_light_ids()
        self.current_active_elements: dict[Element, ElementLevel] = {}

        # Replaced as a whole on every change, so the update thread never sees a half-built list
        self.active_colors: list[tuple[Element, dict[str, int]]] = []
        self.color_index = 0  # Position of the next color to show
        self.shown_element: Element | None = None
        self.transition_speed = CONFIG.light_transition_speed
        self.transition_interval = CONFIG.light_transition_interval

        self._force_transition_event = Event()
        # Held while talking to the lights, so a change of lights from the web UI never interleaves with a color change
        self._lights_lock = Lock()
        self._stop_event = Event()
        self._thread = Thread(target=self._light_update_loop, daemon=True)

    def __enter__(self) -> Self:
        self.smartlight_client.save_states()
        self._thread.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.stop()

    def update(self, game_state: GameState):
        self._process_element_state(game_state.element_state)

    def select_lights(self, light_keys: list[str]) -> None:
        """Control other lights from now on. The lights that are dropped get their own state back."""
        self._reconfigure_lights(lambda: self.smartlight_client.select_lights(light_keys))

    def rediscover_lights(self) -> None:
        self._reconfigure_lights(self.smartlight_client.rediscover_lights)

    def _reconfigure_lights(self, reconfigure: Callable[[], None]) -> None:
        with self._lights_lock:
            self.smartlight_client.restore_states(transition_speed=self.transition_speed)
            reconfigure()
            self.light_ids = self.smartlight_client.get_all_light_ids()
            self.smartlight_client.save_states()
            if self.active_colors:
                self._show_next_color(self.active_colors)
        logger.info("Now controlling %s lights", len(self.light_ids))

    def _process_element_state(self, element_state: dict[Element, ElementLevel]):
        new_active_elements = {
            element: element_level
            for element, element_level in element_state.items()
            if element_level != ElementLevel.INERT
        }
        if new_active_elements == self.current_active_elements:
            return

        logger.debug("Change in elements detected. Currently active elements: %s", new_active_elements)
        added_elements = new_active_elements.keys() - self.current_active_elements.keys()
        shown_element_removed = self.shown_element is not None and self.shown_element not in new_active_elements

        self.current_active_elements = new_active_elements
        self.active_colors = self._get_colors_for_elements(new_active_elements)
        self.color_index = 0

        if added_elements or shown_element_removed:
            self._force_transition_event.set()

    @staticmethod
    def _get_colors_for_elements(
        active_elements: dict[Element, ElementLevel],
    ) -> list[tuple[Element, dict[str, int]]]:
        colors = []
        for element, element_level in active_elements.items():
            if element not in ELEMENT_COLOR_MAP:
                logger.error("No mapping to a HSV color is present in the element color map for element %s", element)
                continue
            hsv_for_element = ELEMENT_COLOR_MAP[element].copy()  # Make a copy to avoid modifying original
            if element_level == ElementLevel.HALF:
                hsv_for_element["bri"] = hsv_for_element["bri"] // 2
            colors.append((element, hsv_for_element))
        return colors

    def _light_update_loop(self):
        shown_colors = self.active_colors

        while not self._stop_event.is_set():
            active_colors = self.active_colors
            # Only send something when there is a cycle to show, or the set of colors has changed
            if len(active_colors) > 1 or active_colors != shown_colors:
                with self._lights_lock:
                    self._show_next_color(active_colors)
                shown_colors = active_colors

            self._force_transition_event.wait(timeout=self.transition_interval)
            self._force_transition_event.clear()

    def _show_next_color(self, active_colors: list[tuple[Element, dict[str, int]]]):
        if not active_colors:
            self.shown_element = None
            self.smartlight_client.restore_states(transition_speed=self.transition_speed)
            return

        element, color = active_colors[self.color_index % len(active_colors)]
        self.color_index = (self.color_index + 1) % len(active_colors)
        self.shown_element = element
        logger.debug("Changing color to %s for element %s", color, element)
        self.smartlight_client.change_color_by_light_ids(self.light_ids, color, self.transition_speed)

    def stop(self):
        self._stop_event.set()
        self._force_transition_event.set()  # Wake the update thread so it stops right away
        if self._thread.is_alive():
            self._thread.join()
        with self._lights_lock:
            self.smartlight_client.restore_states(transition_speed=self.transition_speed)
