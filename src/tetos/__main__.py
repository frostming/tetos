import logging

import click

from .azure import AzureSpeaker
from .baidu import BaiduSpeaker
from .edge import EdgeSpeaker
from .google import GoogleSpeaker
from .minimax import MinimaxSpeaker
from .openai import OpenAISpeaker
from .volc import VolcSpeaker


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


for speaker in (
    OpenAISpeaker,
    EdgeSpeaker,
    AzureSpeaker,
    VolcSpeaker,
    GoogleSpeaker,
    BaiduSpeaker,
    MinimaxSpeaker,
):
    tts.add_command(speaker.get_command())


if __name__ == "__main__":
    tts()
