import logging

from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    log_level: int = logging.DEBUG


BASECONFIG = BaseConfig
