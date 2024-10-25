from __future__ import annotations

import base64
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Generator

import click
from click.core import Command as Command
from httpx import AsyncClient, Auth, Request
from httpx._models import Response

from .base import Duration, Speaker, SynthesizeError, common_options, hmac_sha256
from .consts import VOLC_SUPPORTED_VOICES

logger = logging.getLogger(__name__)


class VolcSignAuth(Auth):
    ALGORITHM = "HMAC-SHA256"

    requires_request_body = True

    def __init__(
        self, access_key: str, secret_key: str, service: str, region: str
    ) -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.service = service
        self.region = region

    def auth_flow(self, request: Request) -> Generator[Request, Response, None]:
        x_content_sha256 = hashlib.sha256(request.content).hexdigest()
        x_date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        signed_headers = "content-type;host;x-content-sha256;x-date"
        canonical_request = "\n".join(
            [
                request.method.upper(),
                request.url.path,
                request.url.query.decode(),
                f"content-type:{request.headers['content-type']}",
                f"host:{request.headers['host']}",
                f"x-content-sha256:{x_content_sha256}",
                f"x-date:{x_date}",
                "",
                signed_headers,
                x_content_sha256,
            ]
        )

        canonical_request_hash = hashlib.sha256(canonical_request.encode()).hexdigest()
        credential_scope = f"{x_date[:8]}/{self.region}/{self.service}/request"
        string_to_sign = "\n".join(
            [
                self.ALGORITHM,
                x_date,
                credential_scope,
                canonical_request_hash,
            ]
        )
        sign_key = self.secret_key.encode()
        for scope in credential_scope.split("/"):
            sign_key = hmac_sha256(scope, sign_key)
        signature = hmac_sha256(string_to_sign, sign_key).hex()
        authorization = (
            f"{self.ALGORITHM} Credential={self.access_key}/{credential_scope}"
            f", SignedHeaders={signed_headers}, Signature={signature}"
        )
        request.headers.update(
            {
                "Authorization": authorization,
                "X-Content-Sha256": x_content_sha256,
                "X-Date": x_date,
            }
        )
        yield request


class VolcSpeaker(Speaker):
    """Volcengine TTS speaker.

    Args:
        access_key (str): The access key ID.
        secret_key (str): The access secret key.
        app_key (str): The app key.
        voice (str, optional): The voice to use.
        sample_rate (int, optional): The sample rate.
            Available values: [8000,16000,22050,24000,32000,44100,48000],
            Defaults to 24000.
        speech_rate (int, optional): The speech rate. It should be in range [-50,100].
            100 means 2x speed and -50 means half speed. Defaults to 0.
        pitch_rate (int, optional): The pitch rate. It should be in range [-12,12].
            Defaults to 0.
    """

    SERVICE_NAME = "sami"
    REGION = "cn-north-1"
    AUTH_VERSION = "volc-auth-v1"
    API_HOST = "open.volcengineapi.com"
    VERSION = "2021-07-27"
    TOKEN_FILE = Path.home() / ".tetos" / "volc_token.json"
    SAMI_API_URL = "https://sami.bytedance.com/api/v1/invoke"

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        app_key: str,
        *,
        voice: str | None = None,
        sample_rate: int = 24000,
        speech_rate: int = 0,
        pitch_rate: int = 0,
    ) -> None:
        self.access_key = access_key
        self.secret_key = secret_key
        self.app_key = app_key
        self.voice = voice or "zh_female_qingxin"
        self.sample_rate = sample_rate
        self.speech_rate = speech_rate
        self.pitch_rate = pitch_rate
        self._token: dict[str, Any] = {}
        self.client = AsyncClient()
        if self.TOKEN_FILE.exists():
            with self.TOKEN_FILE.open() as f:
                self._token = json.load(f)

    async def _ensure_token(self) -> str:
        if not self._token or time.time() > self._token["expires_at"]:
            self._token = await self._request_token()
            # self._token = self._request_token_sync()
        return self._token["token"]

    async def _request_token(self) -> dict[str, Any]:
        logger.info("Requesting token")
        data = {
            "appkey": self.app_key,
            "token_version": self.AUTH_VERSION,
            "expiration": 3600 * 24,  # expire in 1 day
        }
        resp = await self.client.post(
            f"https://{self.API_HOST}/",
            params={"Action": "GetToken", "Version": self.VERSION},
            json=data,
            headers={"Host": self.API_HOST},
            auth=VolcSignAuth(
                self.access_key, self.secret_key, self.SERVICE_NAME, self.REGION
            ),
        )
        if resp.is_error:
            logger.error("Failed to get token: %s", resp.text)
            raise SynthesizeError("Failed to get token")
        token = resp.json()
        self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with self.TOKEN_FILE.open("w") as f:
            json.dump(token, f)
        return token

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        tts_payload = json.dumps(
            {
                "text": text,
                "speaker": self.voice,
                "audio_config": {
                    "format": "mp3",
                    "sample_rate": self.sample_rate,
                    "speech_rate": self.speech_rate,
                    "pitch_rate": self.pitch_rate,
                },
            }
        )
        req = {
            "appkey": self.app_key,
            "token": await self._ensure_token(),
            "namespace": "TTS",
            "payload": tts_payload,
        }

        resp = await self.client.post(self.SAMI_API_URL, json=req)
        if resp.is_error:
            raise self._get_error(resp)
        data = resp.json()
        if data["status_code"] == 20000000 and len(data["data"]) > 0:
            yield base64.b64decode(data["data"])
            payload = json.loads(data["payload"])
            raise Duration(payload["duration"])
        raise SynthesizeError("Failed to get tts from volcengine")

    def _get_error(self, resp: Response) -> SynthesizeError:
        logger.error("Failed to get tts from volcengine: %s", resp.text)
        try:
            data = resp.json()
            return SynthesizeError(data["status_text"])
        except Exception:
            return SynthesizeError("Failed to get tts from volcengine")

    @classmethod
    def list_voices(cls) -> list[str]:
        return VOLC_SUPPORTED_VOICES

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option(
            "--access-key",
            required=True,
            help="The access key.",
            envvar="VOLC_ACCESS_KEY",
            show_envvar=True,
        )
        @click.option(
            "--secret-key",
            required=True,
            help="The secret key.",
            envvar="VOLC_SECRET_KEY",
            show_envvar=True,
        )
        @click.option(
            "--app-key",
            required=True,
            help="The app key.",
            envvar="VOLC_APP_KEY",
            show_envvar=True,
        )
        @click.option("--voice", default="zh_female_qingxin", help="The voice to use.")
        @click.option(
            "--sample-rate", default=24000, help="The sample rate.", type=click.INT
        )
        @click.option(
            "--speech-rate", default=0, help="The speech rate.", type=click.INT
        )
        @click.option("--pitch-rate", default=0, help="The pitch rate.", type=click.INT)
        @common_options(cls)
        def volc(
            access_key: str,
            secret_key: str,
            app_key: str,
            voice: str,
            sample_rate: int,
            speech_rate: int,
            pitch_rate: int,
            lang: str,
            text: str,
            output: str,
        ) -> None:
            speaker = cls(
                access_key,
                secret_key,
                app_key,
                voice=voice,
                sample_rate=sample_rate,
                speech_rate=speech_rate,
                pitch_rate=pitch_rate,
            )
            speaker.say(text, output, lang=lang)

        return volc
