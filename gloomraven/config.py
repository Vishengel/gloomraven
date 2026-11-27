import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT_PATH = Path(__file__).parents[1]


class BaseConfig(BaseSettings):
    log_level: int = logging.DEBUG

    model_config = SettingsConfigDict(env_file=PROJECT_ROOT_PATH / ".env", env_file_encoding="utf-8", extra="ignore")


BASECONFIG = BaseConfig()
