from dataclasses import dataclass
from pathlib import Path

import anyio
import click

from .base import Speaker, SynthesizeError, common_options
from .consts import AZURE_SUPPORTED_VOICES


@dataclass
class EdgeSpeaker(Speaker):
    voice: str = "en-US-AriaNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"

    async def synthesize(self, text: str, out_file: Path) -> float:
        import edge_tts

        communicate = edge_tts.Communicate(
            text, voice=self.voice, rate=self.rate, pitch=self.pitch, volume=self.volume
        )
        duration = 0
        with open(out_file, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    duration = (chunk["offset"] + chunk["duration"]) / 1e7
            if duration == 0:
                raise SynthesizeError("Failed to get tts from edge")
        return duration

    @classmethod
    def list_voices(cls) -> list[str]:
        return AZURE_SUPPORTED_VOICES

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option("--voice", default="en-US-AriaNeural", help="The voice to use.")
        @click.option("--rate", default="+0%", help="The rate of speech.")
        @click.option("--pitch", default="+0Hz", help="The pitch of speech.")
        @click.option("--volume", default="+0%", help="The volume of speech.")
        @common_options(cls)
        def edge(
            voice: str, rate: str, pitch: str, volume: str, text: str, output: str
        ) -> None:
            speaker = cls(voice=voice, rate=rate, pitch=pitch, volume=volume)
            anyio.run(speaker.synthesize, text, Path(output))
            click.echo(f"Speech generated successfully at {output}")

        return edge
