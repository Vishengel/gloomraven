from gloomraven.config import BaseConfig


class Config(BaseConfig):
    web_host: str = "0.0.0.0"  # Reachable from the whole LAN
    web_port: int = 4568  # Next to the X-Haven server's 4567


CONFIG = Config()
