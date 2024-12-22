import logging
import sys

from gloomraven.config import BASECONFIG
from gloomraven.x_haven_client.x_haven_client import XHavenClient

logging.basicConfig(stream=sys.stdout, level=BASECONFIG.log_level)
logger = logging.getLogger(__name__)


class GloomravenManager:
    def __init__(self, ip: str, port: int):
        self.x_haven_client = XHavenClient(ip, port)
        self.running = False

    def run(self) -> None:
        self.running = True
        with self.x_haven_client.connect() as connection:
            while self.running:
                try:
                    data = self.x_haven_client.receive_message(connection)
                    if data:
                        self.x_haven_client.process_server_message(data)
                except KeyboardInterrupt:
                    logger.info("Terminating due to KeyboardInterrupt")
                    self.running = False
