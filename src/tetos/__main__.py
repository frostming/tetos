import logging

import click

from . import ALL_SPEAKERS


def setup_logger(debug: bool = False):
    logger = logging.getLogger("tetos")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)


@click.group(context_settings={"show_default": True})
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def tts(verbose: bool) -> None:
    setup_logger(verbose)


for speaker in ALL_SPEAKERS:
    tts.add_command(speaker.get_command())


if __name__ == "__main__":
    tts()
