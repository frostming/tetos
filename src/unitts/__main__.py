import click

from .azure import AzureSpeaker
from .edge import EdgeSpeaker
from .openai import OpenAISpeaker


@click.group()
def tts() -> None:
    pass


for speaker in (OpenAISpeaker, EdgeSpeaker, AzureSpeaker):
    tts.add_command(speaker.get_command())


if __name__ == "__main__":
    tts()
