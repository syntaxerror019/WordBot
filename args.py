import argparse


def create_parser():
    parser = argparse.ArgumentParser(
        description="JKLM.FUN's Favorite BombParty bot is back!"
    )
    parser.add_argument(
        "--code",
        type=str,
        default=None,
        help="The JKLM game code to join"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="en",
        help="The language of the game to be played"
    )
    parser.add_argument(
        "--public",
        type=bool,
        default=True,
        help="Whether the created room should be public or not"
    )

    args = parser.parse_args()
    if args.code:
        args.code = args.code.upper()
    return args
