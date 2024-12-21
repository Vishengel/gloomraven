from pydantic_settings import BaseSettings


class Config(BaseSettings):
    socket_buffer_size: int = 8192


CONFIG = Config()
