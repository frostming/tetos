from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import anyio
import click

from .base import Speaker, SynthesizeError, common_options
from .consts import AZURE_SUPPORTED_VOICES


@dataclass
class EdgeSpeaker(Speaker):
    """Edge TTS speaker.

    Args:
        voice (str): The voice to use.
        rate (str): The rate of speech.
        pitch (str): The pitch of speech.
        volume (str): The volume of speech.
    """

    voice: str | None = None
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"

    async def synthesize(
        self, text: str, out_file: str | Path, lang: str = "en-US"
    ) -> float:
        import edge_tts

        communicate = edge_tts.Communicate(
            text,
            voice=self.get_voice(lang),
            rate=self.rate,
            pitch=self.pitch,
            volume=self.volume,
        )
        duration = 0
        file = anyio.Path(out_file)
        async with await file.open("wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    duration = (chunk["offset"] + chunk["duration"]) / 1e7
            if duration == 0:
                raise SynthesizeError("Failed to get tts from edge")
        return duration

    def get_voice(self, lang: str) -> str:
        if self.voice:
            return self.voice
        else:
            return next(
                (v for v in self.list_voices() if v.startswith(lang)),
                "en-US-AriaNeural",
            )

    @classmethod
    def list_voices(cls) -> list[str]:
        return AZURE_SUPPORTED_VOICES

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option("--rate", default="+0%", help="The rate of speech.")
        @click.option("--pitch", default="+0Hz", help="The pitch of speech.")
        @click.option("--volume", default="+0%", help="The volume of speech.")
        @common_options(cls)
        def edge(
            voice: str | None,
            rate: str,
            pitch: str,
            volume: str,
            text: str,
            lang: str,
            output: str,
        ) -> None:
            speaker = cls(voice=voice, rate=rate, pitch=pitch, volume=volume)
            speaker.say(text, output, lang=lang)

        return edge
