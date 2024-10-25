from __future__ import annotations

from typing import AsyncGenerator

import click

from .base import Speaker, common_options


class OpenAISpeaker(Speaker):
    """OpenAI TTS speaker.

    Args:
        model (str): The model to use. Defaults to "tts-1".
        voice (str): The voice to use. Defaults to "alloy".
        speed (float, optional): The speed of the speech.
        api_key (str, optional): The OpenAI API key.
        api_base (str, optional): The OpenAI API base URL.
    """

    def __init__(
        self,
        *,
        model: str = "tts-1",
        voice: str | None = None,
        speed: float | None = None,
        api_key: str | None,
        api_base: str | None,
    ) -> None:
        import openai

        self.voice = voice or "alloy"
        self.speed = speed
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=api_base)

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        extra_args = {"speed": self.speed} if self.speed is not None else {}
        async with self.client.with_streaming_response.audio.speech.create(
            model=self.model,
            input=text,
            voice=self.voice,
            **extra_args,
        ) as resp:
            async for chunk in resp.iter_bytes():
                yield chunk

    @classmethod
    def list_voices(cls) -> list[str]:
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option(
            "--api-key",
            required=True,
            envvar="OPENAI_API_KEY",
            help="The OpenAI API key.",
            show_envvar=True,
        )
        @click.option(
            "--api-base",
            envvar="OPENAI_API_BASE",
            help="The OpenAI API base URL.",
            show_envvar=True,
        )
        @click.option("--model", default="tts-1", help="The model to use.")
        @click.option("--speed", type=float, help="The speed of the speech.")
        @common_options(cls)
        def openai(
            api_key: str | None,
            api_base: str | None,
            model: str,
            speed: float | None,
            voice: str,
            text: str,
            lang: str,
            output: str,
        ) -> None:
            speaker = cls(
                model=model,
                voice=voice,
                speed=speed,
                api_key=api_key,
                api_base=api_base,
            )
            speaker.say(text, output, lang=lang)

        return openai
