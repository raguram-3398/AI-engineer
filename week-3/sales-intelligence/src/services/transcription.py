import asyncio

from openai import AsyncOpenAI
from io import BytesIO

from src.models.schemas import TranscriptionResult
from src.models.schemas import ConfidenceResult

client = AsyncOpenAI()

async def transcribe_audio(audio_bytes: bytes, filename: str, timeout: float = 60.0) -> TranscriptionResult:
    """Returns the Transcription result for the input audio bytes"""
    try:
        file_obj = BytesIO(audio_bytes)
        file_obj.name = filename
        response = await asyncio.wait_for(
            client.audio.transcriptions.create(
                model="whisper-1",
                file=file_obj,
            ),
            timeout=timeout
        )
    except asyncio.TimeoutError as e:
        raise TimeoutError(f"whisper timed out after {timeout:.1f}s") from e
    transcript = response.text
    return TranscriptionResult(transcript=transcript, duration_seconds=None)

def check_confidence(transcript: str, wer_threshold: float = 0.3) -> ConfidenceResult:
    words = transcript.split()
    repeated = 0
    for current, nxt in zip(words, words[1:]):
        if current==nxt:
            repeated += 1
    limit = wer_threshold * len(words)
    if repeated > limit:
        return ConfidenceResult(is_low_confidence=True, flag_message=(f"transcript contains {repeated} repeated consecutive words"),)
    return ConfidenceResult(is_low_confidence=False, flag_message=None,)
