import socket
import json
from enum import Enum

from gloomraven.data_model.game_state import GameState

ELEMENT_COLOR_MAP = {
    "Fire": {"hue": 0, "sat": 254, "bri": 254},  # Red
    "Ice": {"hue": 46920, "sat": 254, "bri": 254},  # Blue
    "Earth": {"hue": 25500, "sat": 254, "bri": 254},  # Green
    "Air": {"hue": 40000, "sat": 254, "bri": 254},  # Light blue
    "Light": {},
    "Dark": {},
}


def poll_game_server(server_ip, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((server_ip, server_port))
        while True:
            data = s.recv(8192).decode()  # Adjust buffer size as needed
            if data:
                process_game_state(data)


# Parse and process the game state
def process_game_state(message):
    if message.startswith("S3nD:") and message.endswith("[EOM]"):
        message = message.replace("S3nD:", "").replace("[EOM]", "")
        if "GameState:" in message:
            message_split = message.split("GameState:")
            assert len(message_split) == 2
            gamestate_string = message_split[1]
            gamestate_json = json.loads(gamestate_string)
            print(gamestate_json)
            game_state = GameState.model_validate_json(gamestate_string)
            print(game_state)


if __name__ == "__main__":
    GAME_SERVER_IP = "192.168.2.47"  # Replace with your server's IP
    GAME_SERVER_PORT = 4567  # Replace with your server's port
    poll_game_server(GAME_SERVER_IP, GAME_SERVER_PORT)
