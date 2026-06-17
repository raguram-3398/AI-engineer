from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.transcription import check_confidence, transcribe_audio
from services.cost_tracker import calculate_whisper_cost


def test_calculate_whisper_cost():
    """None → 0.0; partial minute billed as full; two minutes correct."""
    assert calculate_whisper_cost(None) == 0.0
    assert abs(calculate_whisper_cost(45) - 0.006) < 1e-9  # ceil(45/60)=1 min
    assert abs(calculate_whisper_cost(90) - 0.012) < 1e-9  # ceil(90/60)=2 min


def test_check_confidence_clean():
    result = check_confidence(
        "The customer was interested in our pricing.", request_id="r1"
    )
    assert result.is_low_confidence is False


def test_check_confidence_flagged():
    """More than 30% consecutive repeated words triggers low-confidence flag."""
    result = check_confidence(
        "the the the the customer customer was interested", request_id="r1"
    )
    assert result.is_low_confidence is True
    assert result.flag_message is not None


async def test_transcribe_audio_happy_path():
    mock_response = MagicMock()
    mock_response.text = "Hello this is a test transcript."
    mock_response.duration = 30.0

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_response)

    with patch("services.transcription._get_client", return_value=mock_client):
        result = await transcribe_audio(
            audio_bytes=b"fake_audio", filename="test.mp3", request_id="req-1"
        )

    assert result.transcript == "Hello this is a test transcript."
    assert result.duration_seconds == 30.0


async def test_transcribe_audio_timeout():
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create = AsyncMock(
        side_effect=asyncio.TimeoutError()
    )

    with patch("services.transcription._get_client", return_value=mock_client):
        with pytest.raises(TimeoutError, match="Whisper timed out"):
            await transcribe_audio(
                audio_bytes=b"fake_audio",
                filename="test.mp3",
                request_id="req-1",
                timeout=0.001,
            )
