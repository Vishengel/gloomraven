import logging
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, Field, ValidationError

from gloomraven.smartlight_control.smartlight_clients.config import CONFIG
from gloomraven.smartlight_control.smartlight_clients.smartlight_types import SupportedBrands
from gloomraven.util import write_text_atomically

logger = logging.getLogger(__name__)


class LightSelection(BaseModel):
    # Per brand, because the keys differ: MAC addresses for WiZ, light names for Hue
    lights_by_brand: dict[SupportedBrands, list[str]] = Field(default_factory=dict)
    # Names typed in the web UI, keyed by light key, "room:<room id>" or "group:<group id>"
    names_by_brand: dict[SupportedBrands, dict[str, str]] = Field(default_factory=dict)


class LightSelectionStore:
    """
    The lights picked to control and their names, saved in a JSON file.

    Falls back to LIGHTS in .env for a brand without a saved selection.
    """

    def __init__(self, path: Path = CONFIG.light_selection_path):
        self.path = path
        self._lock = Lock()  # The web UI can save from several threads at once

    def load(self, brand: SupportedBrands) -> list[str]:
        selection = self._read()
        if selection is None or brand not in selection.lights_by_brand:
            return CONFIG.lights
        return selection.lights_by_brand[brand]

    def save(self, brand: SupportedBrands, light_keys: list[str]) -> None:
        with self._lock:
            selection = self._read() or LightSelection()
            selection.lights_by_brand[brand] = light_keys
            self._write(selection)
        logger.info("Saved a selection of %s %s lights to %s", len(light_keys), brand, self.path)

    def load_names(self, brand: SupportedBrands) -> dict[str, str]:
        selection = self._read()
        return selection.names_by_brand.get(brand, {}) if selection else {}

    def save_names(self, brand: SupportedBrands, names: dict[str, str]) -> None:
        """Replace the names for this brand. An empty name removes it."""
        with self._lock:
            selection = self._read() or LightSelection()
            selection.names_by_brand[brand] = {key: name.strip() for key, name in names.items() if name.strip()}
            self._write(selection)

    def _write(self, selection: LightSelection) -> None:
        write_text_atomically(self.path, selection.model_dump_json(indent=2))

    def _read(self) -> LightSelection | None:
        if not self.path.exists():
            return None
        try:
            return LightSelection.model_validate_json(self.path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            logger.error("Ignoring the light selection in %s, it is invalid: %s", self.path, exc)
            return None
