import logging
import socket
from typing import Optional

from _socket import gaierror

from gloomraven.data_model.game_state import GameState
from gloomraven.gloomhaven_app_clients.x_haven_client.config import CONFIG

logger = logging.getLogger(__name__)


class XHavenClient:
    MESSAGE_START = "S3nD:"
    MESSAGE_END = "[EOM]"
    GAME_STATE_START = "GameState:"

    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port

    def connect(self) -> socket.socket:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.server_ip, self.server_port))
            logger.info(
                "Connected to server at %s:%s.", self.server_ip, self.server_port
            )
            return s
        except gaierror as exc:
            logger.error("%s. Is the server ip %s correct?", exc, self.server_ip)
            raise
        except ConnectionRefusedError as exc:
            logger.error("%s. Is the server port %s correct?", exc, self.server_port)
            raise

    def receive_data(self, s: socket.socket) -> Optional[GameState]:
        data = s.recv(CONFIG.socket_buffer_size).decode()

        while self.MESSAGE_END not in data:
            # If the EOM marker is not in the data, we haven't received the full message yet
            data += s.recv(CONFIG.socket_buffer_size).decode()

        if data:
            return self.process_server_message(data)
        return None

    def process_server_message(self, message: str) -> Optional[GameState]:
        message = message.replace(self.MESSAGE_START, "").replace(self.MESSAGE_END, "")
        if self.GAME_STATE_START in message:
            logger.info("Received game state message from server")
            try:
                return self._process_game_state(message)
            except ValueError as exc:
                logger.error("Could not process game state: %s", exc)

        return None

    def _process_game_state(self, message: str) -> GameState:
        message_split = message.split(self.GAME_STATE_START)

        if len(message_split) < 2:
            raise ValueError(
                f"'{self.GAME_STATE_START} should be part of the game state message. "
                f"Message: {message}"
            )

        game_state_string = message_split[1]
        game_state = GameState.model_validate_json(game_state_string)
        logger.debug("Full game state: %s", game_state)
        return game_state
