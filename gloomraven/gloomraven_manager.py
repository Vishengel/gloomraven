import logging
import sys
from typing import Optional

from gloomraven.config import BASECONFIG
from gloomraven.data_model.game_state import GameState
from gloomraven.gloomhaven_app_clients.x_haven_client.x_haven_client import XHavenClient
from gloomraven.smartlight_control.smartlight_clients.smartlight_client import (
    SmartlightClient,
)
from gloomraven.smartlight_control.smartlight_controller import SmartlightController

logging.basicConfig(stream=sys.stdout, level=BASECONFIG.log_level)
logger = logging.getLogger(__name__)


class GloomravenManager:
    def __init__(
        self,
        gloomhaven_client: XHavenClient,
        smartlight_client: Optional[SmartlightClient],
    ):
        self.gloomhaven_client = gloomhaven_client
        self.smartlight_controller = (
            SmartlightController(smartlight_client) if smartlight_client else None
        )
        self.running = False

    def run(self) -> None:
        self.running = True
        with self.gloomhaven_client.connect() as connection:
            while self.running:
                self._await_and_process_data(connection)

    def _await_and_process_data(self, connection):
        try:
            game_state = self.gloomhaven_client.receive_data(connection)
            if game_state:
                self.update(game_state)
        except KeyboardInterrupt:
            logger.info("Terminating due to KeyboardInterrupt")
            self.running = False

    def update(self, game_state: GameState):
        if self.smartlight_controller:
            self.smartlight_controller.update(game_state)
