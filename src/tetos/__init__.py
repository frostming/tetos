from __future__ import annotations

from typing import Sequence

from tetos.fish import FishSpeaker

from .azure import AzureSpeaker
from .baidu import BaiduSpeaker
from .base import Speaker
from .edge import EdgeSpeaker
from .google import GoogleSpeaker
from .minimax import MinimaxSpeaker
from .openai import OpenAISpeaker
from .volc import VolcSpeaker
from .xunfei import XunfeiSpeaker

ALL_SPEAKERS: Sequence[type[Speaker]] = [
    AzureSpeaker,
    BaiduSpeaker,
    EdgeSpeaker,
    GoogleSpeaker,
    MinimaxSpeaker,
    OpenAISpeaker,
    VolcSpeaker,
    XunfeiSpeaker,
    FishSpeaker,
]


def get_speaker(name: str) -> type[Speaker]:
    """Get a speaker by name.

    Args:
        name (str): The lowercase name of the speaker.

    Raises:
        ValueError: If the speaker is not found.

    Returns:
        type[Speaker]: The speaker class.
    """
    allowed_names: list[str] = []
    for speaker in ALL_SPEAKERS:
        if (n := speaker.__name__[:-7].lower()) == name.lower():
            return speaker
        allowed_names.append(n)
    raise ValueError(
        f"Speaker {name} not found. Allowed speakers: {', '.join(allowed_names)}"
    )
