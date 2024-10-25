from __future__ import annotations

import json
import logging
import platform
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncGenerator, ClassVar
from urllib.parse import quote_plus

import click
import httpx

from .base import Speaker, SynthesizeError, common_options
from .consts import BAIDU_SUPPORTED_VOICES

logger = logging.getLogger(__name__)

TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
TTS_URL = "https://tsn.baidu.com/text2audio"
SCOPE = "audio_tts_post"
CUID = f"tetos/{platform.python_implementation()}-{platform.python_version()}"


@dataclass
class BaiduSpeaker(Speaker):
    """Baidu TTS speaker.

    Args:
        api_key (str): The Baidu API key.
        secret_key (str): The Baidu secret key.
        voice (str): The voice to use.
        speed (int): The speed of speech, from 0 to 15. Defaults to 5.
        pitch (int): The pitch of speech, from 0 to 15. Defaults to 5.
        volume (int): The volume of speech,
            from 0 to 9(basic) and 0 to 15(high quality). Defaults to 5.
    """

    api_key: str
    secret_key: str
    voice: str | None = None
    speed: int = 5
    pitch: int = 5
    volume: int = 5
    _token: dict[str, Any] = field(default_factory=dict, init=False)

    TOKEN_FILE: ClassVar[Path] = Path.home() / ".tetos" / "baidu_token.json"

    def __post_init__(self) -> None:
        if self.TOKEN_FILE.exists():
            with self.TOKEN_FILE.open() as f:
                self._token = json.load(f)

    @property
    def per(self) -> int:
        return BAIDU_SUPPORTED_VOICES[self.voice] if self.voice else 1

    async def _ensure_token(self) -> str:
        if not self._token or time.time() > self._token["expires_at"]:
            self._token = await self._request_token()
        return self._token["access_token"]

    async def _request_token(self) -> dict[str, Any]:
        logger.info("Requesting token")
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(TOKEN_URL, data=data)
            if resp.is_error:
                logger.error("Failed to get token: %s", resp.text)
                raise SynthesizeError("Failed to get token")
            token = resp.json()
            if SCOPE not in token["scope"].split():
                raise SynthesizeError("scope is not correct")
            token["expires_at"] = time.time() + token["expires_in"]
            with self.TOKEN_FILE.open("w") as f:
                json.dump(token, f)
            return token

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        params = {
            "tok": await self._ensure_token(),
            "tex": quote_plus(text),  # one more encode here
            "per": self.per,
            "spd": self.speed,
            "pit": self.pitch,
            "vol": self.volume,
            "aue": 3,  # mp3
            "cuid": CUID,
            "lan": "zh",  # Fixed value
            "ctp": 1,  # Fixed value
        }
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", TTS_URL, data=params) as resp:
                if resp.is_error:
                    await resp.aread()
                    logger.error("Failed to get tts: %s", resp.text)
                    raise SynthesizeError("Failed to get tts")
                async for chunk in resp.aiter_bytes(8192):
                    yield chunk

    @classmethod
    def list_voices(cls) -> list[str]:
        return list(BAIDU_SUPPORTED_VOICES)

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option(
            "--api-key",
            required=True,
            envvar="BAIDU_API_KEY",
            show_envvar=True,
            help="The Baidu API key.",
        )
        @click.option(
            "--secret-key",
            required=True,
            envvar="BAIDU_SECRET_KEY",
            show_envvar=True,
            help="The Baidu secret key.",
        )
        @click.option("--voice", help="The voice to use.")
        @click.option("--speed", default=5, help="The speed of speech.", type=click.INT)
        @click.option("--pitch", default=5, help="The pitch of speech.", type=click.INT)
        @click.option(
            "--volume", default=5, help="The volume of speech.", type=click.INT
        )
        @common_options(cls)
        def baidu(
            api_key: str,
            secret_key: str,
            voice: str,
            speed: int,
            pitch: int,
            volume: int,
            lang: str,
            text: str,
            output: str,
        ):
            speaker = cls(api_key, secret_key, voice, speed, pitch, volume)
            speaker.say(text, output, lang=lang)

        return baidu
