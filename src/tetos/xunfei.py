from __future__ import annotations

import base64
import datetime
from dataclasses import dataclass
from typing import AsyncGenerator
from urllib.parse import urlencode

import click

from .base import Speaker, SynthesizeError, common_options, hmac_sha256


@dataclass
class XunfeiSpeaker(Speaker):
    """Xuefei Cloud TTS speaker.

    Args:
        app_id (str): The APP ID.
        api_key (str): The API key.
        api_secret (str): The API secret.
        voice (str): The voice to use. Defaults to "xiaoyan".
            Check available voices at the console.
        rate (int): The rate of the speech(8K or 16K). Defaults to 8000.
        speed (int): The speed of the speech [0-100]. Defaults to 50.
        volume (int): The volume of the speech [0-100]. Defaults to 50.
        pitch (int): The pitch of the speech [0-100]. Defaults to 50.
    """

    app_id: str
    api_key: str
    api_secret: str
    voice: str = "xiaoyan"
    rate: int = 8000
    speed: int = 50
    volume: int = 50
    pitch: int = 50

    def _get_url(self) -> str:
        base_url = "wss://tts-api.xfyun.cn/v2/tts"
        host = "tts-api.xfyun.cn"
        date = datetime.datetime.now(tz=datetime.timezone.utc).strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )
        string_to_sign = f"host: {host}\ndate: {date}\nGET /v2/tts HTTP/1.1"
        signature = base64.b64encode(
            hmac_sha256(string_to_sign, self.api_secret.encode())
        ).decode("latin1")
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )

        query = {
            "host": host,
            "date": date,
            "authorization": base64.b64encode(
                authorization_origin.encode("utf-8")
            ).decode(),
        }
        return f"{base_url}?{urlencode(query)}"

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        from httpx_ws import aconnect_ws

        async with aconnect_ws(self._get_url()) as ws:
            request = {
                "common": {"app_id": self.app_id},
                "business": {
                    "aue": "lame",
                    "sfl": 1,
                    "auf": f"audio/L16;rate={self.rate}",
                    "vcn": self.voice,
                    "pitch": self.pitch,
                    "speed": self.speed,
                    "volume": self.volume,
                    "tte": "utf8",
                },
                "data": {
                    "status": 2,
                    "text": base64.b64encode(text.encode("utf8")).decode(),
                },
            }

            await ws.send_json(request)

            while True:
                try:
                    data = await ws.receive_json()
                except Exception as e:
                    raise SynthesizeError(
                        f"Failed to parse response from xunfei: {e}"
                    ) from e
                if data.get("code", 0) != 0:
                    raise SynthesizeError(
                        "Failed to synthesize speech: "
                        f"{data.get('message', 'Unknown error')}"
                    )
                if not data.get("data"):
                    raise SynthesizeError("No data received from xunfei")
                chunk = base64.b64decode(data["data"]["audio"].encode())
                yield chunk
                if data["data"]["status"] == 2:
                    break

    @classmethod
    def list_voices(cls) -> list[str]:
        """This only lists the basic voices, add more voices at the console."""
        return ["xiaoyan", "aisjiuxu", "aisxping", "aisxyan", "aisjinger", "aisbabyxu"]

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option(
            "--app-id",
            required=True,
            help="The APP ID.",
            envvar="XF_APP_ID",
            show_envvar=True,
        )
        @click.option(
            "--api-key",
            required=True,
            help="The API key.",
            envvar="XF_API_KEY",
            show_envvar=True,
        )
        @click.option(
            "--api-secret",
            required=True,
            help="The API secret.",
            envvar="XF_API_SECRET",
            show_envvar=True,
        )
        @click.option("--speed", type=int, default=50, help="The speed of the speech.")
        @click.option(
            "--volume", type=int, default=50, help="The volume of the speech."
        )
        @click.option("--pitch", type=int, default=50, help="The pitch of the speech.")
        @common_options(cls)
        def xunfei(
            app_id: str,
            api_key: str,
            api_secret: str,
            voice: str | None,
            speed: int,
            volume: int,
            pitch: int,
            text: str,
            lang: str,
            output: str,
        ) -> None:
            speaker = cls(
                app_id=app_id,
                api_key=api_key,
                api_secret=api_secret,
                voice=voice or "xiaoyan",
                speed=speed,
                volume=volume,
                pitch=pitch,
            )
            speaker.say(text, output, lang=lang)

        return xunfei
