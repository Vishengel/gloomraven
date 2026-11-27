import logging
import socket
from _socket import gaierror

from pydantic import BaseModel, Field

from gloomraven.data_model.game_state import GameState
from gloomraven.gloomhaven_app_clients.x_haven_client.config import CONFIG

logger = logging.getLogger(__name__)


class StateMessage(BaseModel):
    # Envelope X-Haven uses for state updates since app v1.14 (protocol version 1)
    index: int = Field(alias="i")
    description: str = Field(alias="d")
    game_state: str = Field(alias="s")  # The game state as a JSON string


class XHavenClient:
    MESSAGE_START = "S3nD:"
    MESSAGE_END = "[EOM]"

    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        self._unprocessed_data = ""

    def connect(self) -> socket.socket:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.server_ip, self.server_port))
            logger.info("Connected to server at %s:%s.", self.server_ip, self.server_port)
            return s
        except gaierror as exc:
            logger.error("%s. Is the server ip %s correct?", exc, self.server_ip)
            raise
        except ConnectionRefusedError as exc:
            logger.error("%s. Is the server port %s correct?", exc, self.server_port)
            raise

    def receive_data(self, s: socket.socket) -> GameState | None:
        data = self._unprocessed_data + s.recv(CONFIG.socket_buffer_size).decode()

        while self.MESSAGE_END not in data:
            # If the EOM marker is not in the data, we haven't received the full message yet
            data += s.recv(CONFIG.socket_buffer_size).decode()

        # Anything after the last end marker is the start of the next message
        complete_data, _, self._unprocessed_data = data.rpartition(self.MESSAGE_END)
        return self.process_server_message(complete_data)

    def process_server_message(self, message: str) -> GameState | None:
        # One read can hold several messages
        contents = [frame.strip().removeprefix(self.MESSAGE_START) for frame in message.split(self.MESSAGE_END)]
        # Other messages, like "ping", are not JSON
        state_messages = [content for content in contents if content.startswith("{")]
        if not state_messages:
            return None

        logger.info("Received game state message from server")
        try:
            return self._process_game_state(state_messages[-1])
        except ValueError as exc:
            logger.error("Could not process game state: %s", exc)
        return None

    def _process_game_state(self, message: str) -> GameState:
        state_message = StateMessage.model_validate_json(message)
        game_state = GameState.model_validate_json(state_message.game_state)
        logger.debug("Full game state: %s", game_state)
        return game_state
