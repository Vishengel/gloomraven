from gloomraven.config import BaseConfig


class Config(BaseConfig):
    socket_buffer_size: int = 8192


CONFIG = Config()
