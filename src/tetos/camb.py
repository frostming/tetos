from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import AsyncGenerator, ClassVar

import click
import httpx
from click.core import Command as Command

from .base import Speaker, SynthesizeError, common_options

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "147320"


@dataclass
class CambSpeaker(Speaker):
    API_URL: ClassVar[str] = "https://client.camb.ai/apis"

    api_key: str
    model: str = "mars-flash"
    voice: str = DEFAULT_VOICE

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        payload: dict = {
            "text": text,
            "voice_id": int(self.voice),
            "language": lang.lower(),
            "speech_model": self.model,
            "output_configuration": {"format": "mp3"},
        }
        async with httpx.AsyncClient(
            base_url=self.API_URL,
            headers={"x-api-key": self.api_key},
        ) as client:
            async with client.stream(
                "POST",
                "/tts-stream",
                json=payload,
                timeout=None,
            ) as response:
                if response.is_error:
                    await response.aread()
                    logger.error("Failed to get tts: %s", response.text)
                    raise SynthesizeError("Failed to get tts")
                async for chunk in response.aiter_bytes():
                    yield chunk

    @classmethod
    def list_voices(cls) -> list[str]:
        return []

    @classmethod
    def get_command(cls) -> Command:
        @click.command()
        @click.option(
            "--api-key",
            required=True,
            envvar="CAMB_API_KEY",
            show_envvar=True,
            help="The CAMB AI API key.",
        )
        @click.option(
            "--model",
            default="mars-flash",
            type=click.Choice(
                ["mars-flash", "mars-pro", "mars-instruct", "mars-nano"]
            ),
            help="The speech model to use.",
        )
        @common_options(cls)
        def camb(
            api_key: str,
            model: str,
            voice: str,
            lang: str,
            text: str,
            output: str,
        ):
            speaker = cls(
                api_key=api_key,
                model=model,
                voice=voice or DEFAULT_VOICE,
            )
            speaker.say(text, output, lang=lang)

        return camb
