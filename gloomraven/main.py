import argparse

from gloomraven.x_haven_client.x_haven_client import XHavenClient


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ip",
        help="IP address of the X-Haven Assistant server",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--port", help="Port of the X-Haven Assistant server", type=int, default=4567
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    x_haven_client = XHavenClient(args.ip, args.port)
    x_haven_client.poll_game_server()
