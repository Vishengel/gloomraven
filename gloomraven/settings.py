import logging
from pathlib import Path
from threading import Lock

from pydantic import BaseModel, Field, ValidationError

from gloomraven.config import PROJECT_ROOT_PATH, BaseConfig
from gloomraven.util import write_text_atomically

logger = logging.getLogger(__name__)


class Config(BaseConfig):
    settings_path: Path = PROJECT_ROOT_PATH / "resources" / "settings.json"


CONFIG = Config()


# Settings changed from the web UI. The UI builds its form from this model's JSON schema, so a new setting only
# needs a field here (with a title, and for a slider ge/le) and a place where it is applied
class Settings(BaseModel):
    element_cycle_interval: int = Field(
        default=30,
        ge=5,
        le=120,
        title="Time per element",
        description="How long each element's colour is shown when several elements are active",
        json_schema_extra={"unit": "s"},
    )


class SettingsStore:
    def __init__(self, path: Path = CONFIG.settings_path):
        self.path = path
        self._lock = Lock()  # The web UI can save from several threads at once

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        try:
            return Settings.model_validate_json(self.path.read_text(encoding="utf-8"))
        except ValidationError as exc:
            logger.error("Using the default settings, the ones in %s are invalid: %s", self.path, exc)
            return Settings()

    def save(self, settings: Settings) -> None:
        with self._lock:
            write_text_atomically(self.path, settings.model_dump_json(indent=2))
        logger.info("Saved settings to %s: %s", self.path, settings)
