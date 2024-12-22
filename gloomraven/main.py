import argparse

from gloomraven.gloomraven_manager import GloomravenManager


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
    gloomraven_manager = GloomravenManager(args.ip, args.port)
    gloomraven_manager.run()
