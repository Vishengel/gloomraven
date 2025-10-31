from abc import ABC, abstractmethod


class SmartlightClient(ABC):
    @abstractmethod
    def reset_to_initial_state(self, transition_speed: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all_light_ids(self) -> list[int]:
        """Return a list of all available light IDs for this client type."""
        raise NotImplementedError

    @abstractmethod
    def change_color_by_light_ids(
        self, light_ids: list[int], color: dict[str, int], transition_speed: int | None = None
    ) -> None:
        raise NotImplementedError
