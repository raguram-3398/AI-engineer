from __future__ import annotations

import asyncio
import os

from io import BytesIO
from openai import AsyncOpenAI

from src.models.schemas import TranscriptionResult, ConfidenceResult
from src.utils.logger import get_logger

logger = get_logger(__name__)

def _get_client(api_key: str | None) -> AsyncOpenAI:
    """Returns AsyncAnthropic fron user key or env fallback"""
    return AsyncOpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])

async def transcribe_audio(audio_bytes: bytes, filename: str, request_id: str, openai_api_key: str | None = None, timeout: float = 60.0) -> TranscriptionResult:
    """Transcribe audio via Whisper using verbose_json to capture duration for cost tracking."""
    client = _get_client(openai_api_key)
    file_obj = BytesIO(audio_bytes)
    file_obj.name = filename
    try:
        response = await asyncio.wait_for(
            client.audio.transcriptions.create(
                model="whisper-1",
                file=file_obj,
                response_format="verbose_json",
            ),
            timeout=timeout
        )
    except asyncio.TimeoutError as e:
        raise TimeoutError(f"whisper timed out after {timeout:.1f}s") from e
    duration = getattr(response, "duration", None)
    result = TranscriptionResult(transcript=response.text, duration_seconds=duration)
    logger.info(
        "transcription_complete",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "transcript_chars": len(result.transcript),
                "duration_seconds": duration,
            }
        },
    )
    return result

def check_confidence(transcript: str, request_id: str = "", wer_threshold: float = 0.3) -> ConfidenceResult:
    """Flag transcript as low-confidence if consecutive repeated words exceed the WER threshold."""
    words = transcript.split()
    repeated = 0
    for current, nxt in zip(words, words[1:]):
        if current==nxt:
            repeated += 1
    limit = wer_threshold * len(words)
    if repeated > limit:
        msg = f"Transcript contains {repeated} consecutive repeated words"
        logger.warning("low_confidence_transcript", extra={"extra_fields": {"request_id": request_id, "repeated_words": repeated}},)
        return ConfidenceResult(is_low_confidence=True, flag_message=msg,)
    return ConfidenceResult(is_low_confidence=False, flag_message=None,)