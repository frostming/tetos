import os
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_openai_speaker(tmp_path: Path):
    from tetos.openai import OpenAISpeaker

    speaker = OpenAISpeaker(
        api_base=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    duration = await speaker.synthesize("Hello, world!", tmp_path / "hello.mp3")
    assert 0.5 < duration < 4
    assert (tmp_path / "hello.mp3").stat().st_size > 0


@pytest.mark.asyncio
async def test_edge_speaker(tmp_path: Path):
    from tetos.edge import EdgeSpeaker

    speaker = EdgeSpeaker()
    duration = await speaker.synthesize("Hello, world!", tmp_path / "hello.mp3")
    assert 0.5 < duration < 4
    assert (tmp_path / "hello.mp3").stat().st_size > 0


@pytest.mark.asyncio
async def test_azure_speaker(tmp_path: Path):
    from tetos.azure import AzureSpeaker

    speaker = AzureSpeaker(
        speech_key=os.getenv("AZURE_SPEECH_KEY"),
        speech_region=os.getenv("AZURE_SPEECH_REGION"),
    )
    duration = await speaker.synthesize("Hello, world!", tmp_path / "hello.mp3")
    assert 0.5 < duration < 4
    assert (tmp_path / "hello.mp3").stat().st_size > 0


@pytest.mark.asyncio
async def test_volc_speaker(tmp_path: Path):
    from tetos.volc import VolcSpeaker

    speaker = VolcSpeaker(
        access_key=os.getenv("VOLC_ACCESS_KEY"),
        secret_key=os.getenv("VOLC_SECRET_KEY"),
        app_key=os.getenv("VOLC_APP_KEY"),
    )
    duration = await speaker.synthesize("Hello, world!", tmp_path / "hello.mp3")
    assert 0.5 < duration < 4
    assert (tmp_path / "hello.mp3").stat().st_size > 0


@pytest.mark.asyncio
async def test_google_speaker(tmp_path: Path):
    from tetos.google import GoogleSpeaker

    speaker = GoogleSpeaker()
    duration = await speaker.synthesize("Hello, world!", tmp_path / "hello.mp3")
    assert 0.5 < duration < 4
    assert (tmp_path / "hello.mp3").stat().st_size > 0


@pytest.mark.asyncio
async def test_xunfei_speaker(tmp_path: Path):
    from tetos.xunfei import XunfeiSpeaker

    speaker = XunfeiSpeaker(
        app_id=os.getenv("XF_APP_ID"),
        api_key=os.getenv("XF_API_KEY"),
        api_secret=os.getenv("XF_API_SECRET"),
    )
    duration = await speaker.synthesize("Hello, world!", tmp_path / "hello.mp3")
    assert 0.5 < duration < 4
    assert (tmp_path / "hello.mp3").stat().st_size > 0
