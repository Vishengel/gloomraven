import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AvailableLight:
    key: str  # What identifies the light in the light selection: the MAC address for WiZ, the name for Hue
    description: str
    selected: bool  # Whether the light is controlled


class SmartlightClient(ABC):
    """
    Base class for a smartlight brand.

    Subclasses only read and write the state of their own lights; saving and restoring that state is shared, so
    every brand gets its lights back to how they were before the game.
    """

    def __init__(self):
        self._saved_states: dict[int, Any] = {}

    def save_states(self) -> None:
        self._saved_states = self._get_light_states(self.get_all_light_ids())
        logger.info("Saved the state of %s lights", len(self._saved_states))

    def restore_states(self, transition_speed: int | None = None) -> None:
        if not self._saved_states:
            return
        logger.info("Restoring the state of %s lights", len(self._saved_states))
        self._set_light_states(self._saved_states, transition_speed)

    @abstractmethod
    def _get_light_states(self, light_ids: list[int]) -> dict[int, Any]:
        """Return the brand-specific state of each light, in a form `_set_light_states` can apply again."""
        ...

    @abstractmethod
    def _set_light_states(self, light_states: dict[int, Any], transition_speed: int | None = None) -> None: ...

    @abstractmethod
    def get_all_light_ids(self) -> list[int]:
        """Return a list of all available light IDs for this client type."""
        ...

    @abstractmethod
    def list_available_lights(self) -> list[AvailableLight]:
        """Return every light found, also the ones that aren't selected."""
        ...

    @abstractmethod
    def select_lights(self, light_keys: list[str]) -> None:
        """Control only the lights with these keys (see `AvailableLight.key`), or all lights when empty."""
        ...

    @abstractmethod
    def rediscover_lights(self) -> None:
        """Search for lights again, e.g. for one that was off at startup. Keeps the selection."""
        ...

    @abstractmethod
    def change_color_by_light_ids(
        self, light_ids: list[int], color: dict[str, int], transition_speed: int | None = None
    ) -> None: ...
