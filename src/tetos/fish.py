from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncGenerator, AsyncIterable, ClassVar, Literal

import click
import httpx
import ormsgpack
from click.core import Command as Command

from .base import Speaker, SynthesizeError, common_options

# https://fish.audio/zh-CN/m/59cb5986671546eaa6ca8ae6f29f6d22/
DEFAULT_VOICE = "59cb5986671546eaa6ca8ae6f29f6d22"


@dataclass
class FishSpeaker(Speaker):
    API_URL: ClassVar[str] = "https://api.fish.audio"

    api_key: str
    chunk_length: int = 200
    bitrate: Literal[64, 128, 192] = 128
    # Reference id
    # For example, if you want use https://fish.audio/zh-CN/m/7f92f8afb8ec43bf81429cc1c9199cb1/
    # Just pass 7f92f8afb8ec43bf81429cc1c9199cb1
    voice: str = DEFAULT_VOICE
    # Normalize text for en & zh, this increase stability for numbers
    normalize: bool = True

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        request = {
            "text": text,
            "chunk_length": self.chunk_length,
            "format": "mp3",
            "mp3_bitrate": self.bitrate,
            "reference_id": self.voice,
            "normalize": self.normalize,
        }
        async with httpx.AsyncClient(
            base_url=self.API_URL, headers={"Authorization": f"Bearer {self.api_key}"}
        ) as client:
            async with client.stream(
                "POST",
                "/v1/tts",
                content=ormsgpack.packb(request),
                headers={
                    "content-type": "application/msgpack",
                },
                timeout=None,
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk

    async def live(
        self, text_stream: AsyncIterable[str], lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        from httpx_ws import WebSocketDisconnect, aconnect_ws

        async with httpx.AsyncClient(
            base_url=self.API_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
        ) as client:
            async with aconnect_ws("/v1/tts/live", client=client) as ws:

                async def sender():
                    request = {
                        "text": "",
                        "chunk_length": self.chunk_length,
                        "format": "mp3",
                        "mp3_bitrate": self.bitrate,
                        "reference_id": self.voice,
                        "normalize": self.normalize,
                    }
                    await ws.send_bytes(
                        ormsgpack.packb({"event": "start", "request": request})
                    )
                    async for text in text_stream:
                        await ws.send_bytes(
                            ormsgpack.packb({"event": "text", "text": text})
                        )
                    await ws.send_bytes(ormsgpack.packb({"event": "stop"}))

                sender_future = asyncio.create_task(sender())

                while True:
                    try:
                        message = await ws.receive_bytes()
                        data = ormsgpack.unpackb(message)
                        match data["event"]:
                            case "audio":
                                yield data["audio"]
                            case "finish" if data["reason"] == "error":
                                raise SynthesizeError("websocket finish with error")
                            case "finish" if data["reason"] == "stop":
                                break
                    except WebSocketDisconnect:
                        raise SynthesizeError("websocket disconnect") from None

                await sender_future

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
