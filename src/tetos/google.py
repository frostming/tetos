"""Synthesizes speech from the input string of text."""

from pathlib import Path
from typing import cast

import anyio
import click
import mutagen.mp3
from google.cloud import texttospeech

from .base import Speaker, common_options


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
        voice: str = "en-US-Studio-M",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
        volume_gain_db: float = 0.0,
    ) -> None:
        self.speaking_rate = speaking_rate
        self.pitch = pitch
        self.voice = voice
        self.volume_gain_db = volume_gain_db

    async def synthesize(self, text: str, out_file: Path) -> float:
        input_text = texttospeech.SynthesisInput(text=text)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=self.speaking_rate,
            pitch=self.pitch,
            volume_gain_db=self.volume_gain_db,
        )
        voice = texttospeech.VoiceSelectionParams(
            language_code="-".join(self.voice.split("-")[:2]),
            name=self.voice,
        )
        async with texttospeech.TextToSpeechAsyncClient() as client:
            resp = await client.synthesize_speech(
                request={
                    "input": input_text,
                    "voice": voice,
                    "audio_config": audio_config,
                }
            )
        file = anyio.Path(out_file)
        async with await file.open("wb") as f:
            await f.write(resp.audio_content)

        audio = mutagen.mp3.MP3(out_file)
        return cast(float, audio.info.length)

    @classmethod
    def list_voices(cls) -> list[str]:
        with texttospeech.TextToSpeechClient() as client:
            resp = client.list_voices()
        return [v.name for v in resp.voices]

    @classmethod
    def get_command(cls) -> click.Command:
        @click.command()
        @click.option("--voice", default="en-US-Studio-M", help="The voice to use.")
        @click.option(
            "--speaking-rate", default=1.0, help="The speaking rate.", type=click.FLOAT
        )
        @click.option("--pitch", default=0.0, help="The pitch.", type=click.FLOAT)
        @click.option(
            "--volume-gain-db", default=0.0, help="The volume gain.", type=click.FLOAT
        )
        @common_options(cls)
        def google(
            voice: str,
            speaking_rate: float,
            pitch: float,
            volume_gain_db: float,
            text: str,
            output: str,
        ) -> None:
            speaker = cls(
                voice=voice,
                speaking_rate=speaking_rate,
                pitch=pitch,
                volume_gain_db=volume_gain_db,
            )
            speaker.say(text, Path(output))

        return google
