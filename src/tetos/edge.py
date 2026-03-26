from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncGenerator

import click

from .base import Duration, Speaker, SynthesizeError, common_options
from .consts import EDGE_SUPPORTED_VOICES


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

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        import edge_tts
        from edge_tts.exceptions import EdgeTTSException

        communicate = edge_tts.Communicate(
            text,
            voice=self.get_voice(lang),
            rate=self.rate,
            pitch=self.pitch,
            volume=self.volume,
            boundary="WordBoundary",
        )
        duration = 0
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
                elif chunk["type"] in {"WordBoundary", "SentenceBoundary"}:
                    duration = (chunk["offset"] + chunk["duration"]) / 1e7
        except EdgeTTSException as exc:
            raise SynthesizeError(f"Failed to get tts from edge: {exc}") from exc
        if duration == 0:
            raise SynthesizeError("Failed to get tts from edge")
        raise Duration(duration)

    def get_voice(self, lang: str) -> str:
        if self.voice:
            return self.voice

        multilingual_voice = next(
            (
                voice
                for voice in self.list_voices()
                if voice.startswith(lang) and "MultilingualNeural" in voice
            ),
            None,
        )
        if multilingual_voice:
            return multilingual_voice

        locale_voice = next((v for v in self.list_voices() if v.startswith(lang)), None)
        if locale_voice:
            return locale_voice

        return "en-US-EmmaMultilingualNeural"

    @classmethod
    def list_voices(cls) -> list[str]:
        return EDGE_SUPPORTED_VOICES

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
