import logging
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from gloomraven.smartlight_control.smartlight_clients.config import CONFIG
from gloomraven.smartlight_control.smartlight_clients.smartlight_types import SupportedBrands

logger = logging.getLogger(__name__)


class LightSelection(BaseModel):
    # Per brand, because the keys differ: MAC addresses for WiZ, light names for Hue
    lights_by_brand: dict[SupportedBrands, list[str]] = Field(default_factory=dict)


class LightSelectionStore:
    """The lights picked to control, saved in a JSON file. Falls back to LIGHTS in .env for a brand without one."""

    def __init__(self, path: Path = CONFIG.light_selection_path):
        self.path = path

    def load(self, brand: SupportedBrands) -> list[str]:
        selection = self._read()
        if selection is None or brand not in selection.lights_by_brand:
            return CONFIG.lights
        return selection.lights_by_brand[brand]

    def save(self, brand: SupportedBrands, light_keys: list[str]) -> None:
        selection = self._read() or LightSelection()
        selection.lights_by_brand[brand] = light_keys
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Write to a temporary file first, so a crash halfway never leaves a corrupt selection behind
        temporary_path = self.path.with_suffix(".tmp")
        temporary_path.write_text(selection.model_dump_json(indent=2), encoding="utf-8")
        temporary_path.replace(self.path)
        logger.info("Saved a selection of %s %s lights to %s", len(light_keys), brand, self.path)

    def _read(self) -> LightSelection | None:
        if not self.path.exists():
            return None
        try:
            return LightSelection.model_validate_json(self.path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            logger.error("Ignoring the light selection in %s, it is invalid: %s", self.path, exc)
            return None
