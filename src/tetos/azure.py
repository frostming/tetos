from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncGenerator

import anyio.to_thread
import azure.cognitiveservices.speech as speechsdk
import click

from .base import Duration, Speaker, SynthesizeError, common_options
from .consts import AZURE_SUPPORTED_VOICES


class OutputStream(speechsdk.audio.PushAudioOutputStreamCallback):
    def __init__(self, queue: asyncio.Queue[bytes]):
        self.queue = queue

    def write(self, data: bytes) -> int:
        self.queue.put_nowait(bytes(data))
        return len(data)


@dataclass
class AzureSpeaker(Speaker):
    """Azure TTS speaker.

    Args:
        speech_key (str): The Azure Speech key.
        speech_region (str): The Azure Speech region.
        voice (str, optional): The voice to use.
    """

    speech_key: str
    speech_region: str
    voice: str | None = None

    def _set_proxy(self, speech_config: speechsdk.SpeechConfig) -> None:
        from urllib.parse import urlparse

        for env in ("http_proxy", "https_proxy", "all_proxy"):
            # Try both lowercase and uppercase versions of the environment variable
            url = os.getenv(env, os.getenv(env.upper(), ""))
            if not url:
                continue
            parsed_url = urlparse(url)
            speech_config.set_proxy(
                parsed_url.hostname,
                parsed_url.port,
                parsed_url.username,
                parsed_url.password,
            )
            break

    def get_speech_config(self, lang: str) -> str:
        config = speechsdk.SpeechConfig(
            subscription=self.speech_key, region=self.speech_region
        )
        self._set_proxy(config)
        config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        if self.voice:
            voice = self.voice
        else:
            voice = next(
                (v for v in self.list_voices() if v.startswith(lang)),
                "en-US-AriaNeural",
            )
        config.speech_synthesis_voice_name = voice
        return config

    async def synthesize(
        self, text: str, out_file: str | Path, lang: str = "en-US"
    ) -> float:
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(out_file))
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.get_speech_config(lang), audio_config=audio_config
        )
        result = await anyio.to_thread.run_sync(speech_synthesizer.speak_text, text)
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_duration.total_seconds()
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                errmsg = f"Error details: {cancellation_details.error_details}"
                raise SynthesizeError(errmsg)
        raise SynthesizeError("Failed to get tts from azure")

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        queue = asyncio.Queue[bytes]()
        stop_event = asyncio.Event()
        output_stream = speechsdk.audio.PushAudioOutputStream(OutputStream(queue))
        audio_config = speechsdk.audio.AudioOutputConfig(stream=output_stream)
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.get_speech_config(lang), audio_config=audio_config
        )

        async def worker():
            return await anyio.to_thread.run_sync(speech_synthesizer.speak_text, text)

        task = asyncio.create_task(worker())
        task.add_done_callback(lambda _: stop_event.set())

        while True:
            done, pending = await asyncio.wait(
                [
                    asyncio.ensure_future(queue.get()),
                    asyncio.ensure_future(stop_event.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for t in pending:
                t.cancel()
            chunk = done.pop().result()
            if chunk is True:
                break
            yield chunk

        result = task.result()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            raise Duration(result.audio_duration.total_seconds())
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                errmsg = f"Error details: {cancellation_details.error_details}"
                raise SynthesizeError(errmsg)
        raise SynthesizeError("Failed to get tts from azure")

    @classmethod
    def list_voices(cls) -> list[str]:
        return AZURE_SUPPORTED_VOICES

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option(
            "--speech-key",
            required=True,
            envvar="AZURE_SPEECH_KEY",
            show_envvar=True,
            help="The Azure Speech key.",
        )
        @click.option(
            "--speech-region",
            envvar="AZURE_SPEECH_REGION",
            show_envvar=True,
            required=True,
            help="The Azure Speech region.",
        )
        @common_options(cls)
        def azure(
            speech_key: str,
            speech_region: str,
            voice: str | None,
            text: str,
            lang: str,
            output: str,
        ) -> None:
            speaker = cls(speech_key, speech_region, voice=voice)
            speaker.say(text, output, lang=lang)

        return azure
