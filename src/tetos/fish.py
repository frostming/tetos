from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal, cast

import anyio
import click
import httpx
import mutagen.mp3
import ormsgpack
from click.core import Command as Command

from .base import Speaker, common_options

# https://fish.audio/zh-CN/m/59cb5986671546eaa6ca8ae6f29f6d22/
DEFAULT_VOICE = "59cb5986671546eaa6ca8ae6f29f6d22"


@dataclass
class FishSpeaker(Speaker):
    API_URL: ClassVar[str] = "https://api.fish.audio/v1/tts"

    api_key: str
    chunk_length: int = 200
    bitrate: Literal[64, 128, 192] = 128
    # Reference id
    # For example, if you want use https://fish.audio/zh-CN/m/7f92f8afb8ec43bf81429cc1c9199cb1/
    # Just pass 7f92f8afb8ec43bf81429cc1c9199cb1
    voice: str = DEFAULT_VOICE
    # Normalize text for en & zh, this increase stability for numbers
    normalize: bool = True

    async def synthesize(
        self, text: str, out_file: str | Path, lang: str = "en-US"
    ) -> float:
        request = {
            "text": text,
            "chunk_length": self.chunk_length,
            "format": "mp3",
            "mp3_bitrate": self.bitrate,
            "reference_id": self.voice,
            "normalize": self.normalize,
        }
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.API_URL,
                content=ormsgpack.packb(request),
                headers={
                    "content-type": "application/msgpack",
                    "api-key": self.api_key,
                },
                timeout=None,
            ) as response:
                f = anyio.Path(out_file)
                async with await f.open("wb") as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
        audio = mutagen.mp3.MP3(out_file)
        return cast(float, audio.info.length)

    @classmethod
    def list_voices(cls) -> list[str]:
        return []

    @classmethod
    def get_command(cls) -> Command:
        @click.command()
        @click.option(
            "--api-key",
            required=True,
            envvar="FISH_API_KEY",
            show_envvar=True,
            help="The Fish audio API key.",
        )
        @click.option("--voice", help="The voice to use.")
        @click.option(
            "--bitrate",
            default="128",
            help="The bitrate of mp3.",
            type=click.Choice(["64", "128", "192"]),
        )
        @click.option(
            "--chunk-length", default=200, help="The chunk length.", type=click.INT
        )
        @click.option(
            "--normalize",
            default=True,
            help="Normalize text for en & zh, this increase stability for numbers",
            is_flag=True,
        )
        @common_options(cls)
        def fish(
            api_key: str,
            voice: str,
            bitrate: str,
            chunk_length: int,
            normalize: bool,
            lang: str,
            text: str,
            output: str,
        ):
            speaker = cls(
                api_key,
                chunk_length=chunk_length,
                bitrate=int(bitrate),
                voice=voice or DEFAULT_VOICE,
                normalize=normalize,
            )
            speaker.say(text, output, lang=lang)

        return fish
