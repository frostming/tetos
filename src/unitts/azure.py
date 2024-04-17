import os
from pathlib import Path

import anyio.to_thread
import azure.cognitiveservices.speech as speechsdk
import click

from .base import Speaker, SynthesizeError, common_options
from .consts import AZURE_SUPPORTED_VOICES


class AzureSpeaker(Speaker):
    """Azure TTS speaker.

    Args:
        speech_key (str): The Azure Speech key.
        speech_region (str): The Azure Speech region.
        voice (str): The voice to use.
    """

    def __init__(
        self, speech_key: str, speech_region: str, *, voice: str = "en-US-AriaNeural"
    ) -> None:
        self.speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=speech_region
        )
        self.speech_config.speech_synthesis_voice_name = voice
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        self._set_proxy()

    def _set_proxy(self) -> None:
        from urllib.parse import urlparse

        for env in ("http_proxy", "https_proxy", "all_proxy"):
            # Try both lowercase and uppercase versions of the environment variable
            url = os.getenv(env, os.getenv(env.upper(), ""))
            if not url:
                continue
            parsed_url = urlparse(url)
            self.speech_config.set_proxy(
                parsed_url.hostname,
                parsed_url.port,
                parsed_url.username,
                parsed_url.password,
            )
            break

    async def synthesize(self, text: str, out_file: Path) -> float:
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(out_file))
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
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
        @click.option("--voice", default="en-US-AriaNeural", help="The voice to use.")
        @common_options(cls)
        def azure(
            speech_key: str, speech_region: str, voice: str, text: str, output: str
        ) -> None:
            speaker = cls(speech_key, speech_region, voice=voice)
            anyio.run(speaker.synthesize, text, Path(output))
            click.echo(f"Speech generated successfully at {output}")

        return azure
