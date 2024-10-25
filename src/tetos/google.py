"""Synthesizes speech from the input string of text."""

from __future__ import annotations

import json
import os
from typing import AsyncGenerator

import click
from google.cloud import texttospeech

from .base import Speaker, common_options
from .consts import GOOGLE_SUPPORTED_VOICES


class GoogleSpeaker(Speaker):
    """Google TTS speaker.

    Args:
        voice (str): The voice to use. Defaults to "en-US-Studio-M".
        speaking_rate (float):
            Optional. Input only. Speaking rate/speed, in the range
            [0.25, 4.0]. 1.0 is the normal native speed supported by the
            specific voice. 2.0 is twice as fast, and 0.5 is half as
            fast. If unset(0.0), defaults to the native 1.0 speed. Any
            other values < 0.25 or > 4.0 will return an error.
        pitch (float):
            Optional. Input only. Speaking pitch, in the range [-20.0,
            20.0]. 20 means increase 20 semitones from the original
            pitch. -20 means decrease 20 semitones from the original
            pitch.
        volume_gain_db (float):
            Optional. Input only. Volume gain (in dB) of the normal
            native volume supported by the specific voice, in the range
            [-96.0, 16.0]. If unset, or set to a value of 0.0 (dB), will
            play at normal native signal amplitude. A value of -6.0 (dB)
            will play at approximately half the amplitude of the normal
            native signal amplitude. A value of +6.0 (dB) will play at
            approximately twice the amplitude of the normal native
            signal amplitude. Strongly recommend not to exceed +10 (dB)
            as there's usually no effective increase in loudness for any
            value greater than that.
    """

    def __init__(
        self,
        *,
        voice: str | None = None,
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0,
    ) -> None:
        self.voice = voice
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speaking_rate,
            pitch=pitch,
            volume_gain_db=volume_gain_db,
        )

    def get_voice(self, lang: str) -> str:
        if self.voice:
            return self.voice
        else:
            if lang.startswith("zh-"):
                lang = "cmn-" + lang[3:]
            return next(
                (v for v in self.list_voices() if v.startswith(lang)),
                "en-US-Studio-M",
            )

    async def stream(
        self, text: str, lang: str = "en-US"
    ) -> AsyncGenerator[bytes, None]:
        input_text = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            name=(voice := self.get_voice(lang)),
            language_code="-".join(voice.split("-")[:2]),
        )
        if "GOOGLE_CREDENTIALS_JSON" in os.environ:
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_info(
                json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
            )
        else:
            credentials = None  # Use default credentials
        async with texttospeech.TextToSpeechAsyncClient(
            credentials=credentials
        ) as client:
            resp = await client.synthesize_speech(
                request={
                    "input": input_text,
                    "voice": voice,
                    "audio_config": self.audio_config,
                }
            )
            yield resp.audio_content

    @classmethod
    def list_voices(cls) -> list[str]:
        return GOOGLE_SUPPORTED_VOICES

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option(
            "--speaking-rate", default=1.0, help="The speaking rate.", type=click.FLOAT
        )
        @click.option("--pitch", default=0.0, help="The pitch.", type=click.FLOAT)
        @click.option(
            "--volume-gain-db", default=0.0, help="The volume gain.", type=click.FLOAT
        )
        @common_options(cls)
        def google(
            voice: str | None,
            speaking_rate: float,
            pitch: float,
            volume_gain_db: float,
            text: str,
            lang: str,
            output: str,
        ) -> None:
            speaker = cls(
                voice=voice,
                speaking_rate=speaking_rate,
                pitch=pitch,
                volume_gain_db=volume_gain_db,
            )
            speaker.say(text, output, lang=lang)

        return google
