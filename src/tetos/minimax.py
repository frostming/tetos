from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import AsyncGenerator, TypedDict

import click

from .base import Speaker, SynthesizeError, common_options, filter_none
from .consts import MINIMAX_SUPPORTED_VOICES

logger = logging.getLogger(__name__)


class TimberWeight(TypedDict):
    voice_id: str
    """系统音色"""
    weight: int
    """取值[1,100]。最多支持4种音色混合，取值为整数，单一音色取值占比越高，合成音色越像。"""


@dataclass
class MinimaxSpeaker(Speaker):
    """MiniMax TTS speaker.

    Args:
        api_key (str): The MiniMax API key.
        group_id (str): The MiniMax group ID.
        model (str): The model to use. Defaults to "speech-01".
        voice (str): The voice to use.
        timber_weights (list[TimberWeight]): The timber weights.
        speed (float): The speed of speech. Range [0.5, 2.0]. Defaults to 1.0.
        vol (float | int): The volume of speech. Range (0, 10]. Defaults to 1.
        pitch (int): The pitch of speech. Range [-12, 12]. Defaults to 0.
    """

    api_key: str
    group_id: str
    model: str = "speech-01"
    voice: str | None = None
    timber_weights: list[TimberWeight] | None = None
    speed: float | None = None
    vol: float | int | None = None
    pitch: int | None = None

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        import httpx

        data = filter_none(
            {
                "model": self.model,
                "voice_id": self.voice or self.list_voices()[0],
                "timber_weights": self.timber_weights,
                "speed": self.speed,
                "vol": self.vol,
                "pitch": self.pitch,
                "text": text,
            }
        )

        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"},
            params={"GroupId": self.group_id},
        ) as client:
            async with client.stream(
                "POST", "https://api.minimax.chat/v1/text_to_speech", json=data
            ) as resp:
                if resp.is_error:
                    await resp.aread()
                    logger.error("Failed to get tts: %s", resp.text)
                    raise SynthesizeError("Failed to get tts")
                if "application/json" in resp.headers["Content-Type"]:
                    logger.error("Failed to get tts: %s", await resp.aread())
                    err = resp.json()
                    raise SynthesizeError(
                        "Failed to get tts: "
                        f"{err.get('base_resp', {}).get('status_msg', '')}"
                    )

                async for chunk in resp.aiter_bytes():
                    yield chunk

    @classmethod
    def list_voices(cls) -> list[str]:
        return MINIMAX_SUPPORTED_VOICES

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option(
            "--api-key",
            required=True,
            envvar="MINIMAX_API_KEY",
            help="The Minimax API key.",
            show_envvar=True,
        )
        @click.option(
            "--group-id",
            required=True,
            help="The Minimax group ID.",
            show_envvar=True,
            envvar="MINIMAX_GROUP_ID",
        )
        @click.option(
            "--speed", default=1.0, help="The speed of speech.", type=click.FLOAT
        )
        @click.option(
            "--vol", default=1, help="The volume of speech.", type=click.FLOAT
        )
        @click.option("--pitch", default=0, help="The pitch of speech.", type=click.INT)
        @common_options(cls)
        def minimax(
            api_key: str,
            group_id: str,
            voice: str | None,
            speed: float,
            vol: float,
            pitch: int,
            text: str,
            lang: str,
            output: str,
        ):
            speaker = MinimaxSpeaker(
                api_key, group_id, voice=voice, speed=speed, vol=vol, pitch=pitch
            )
            speaker.say(text, output, lang=lang)

        return minimax
