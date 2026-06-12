import uuid

from pathlib import Path
from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from src.models.schemas import AnalysisResponse
from src.utils.exceptions import AnalysisError
from src.services.transcription import transcribe_audio, check_confidence
from src.services.pii_scrubber import scrub_pii, check_injection
from src.services.analysis import analyse_with_retry, stream_analysis
from src.services.cost_tracker import trim_transcript


router = APIRouter()
max_size = 25 * 1024 * 1024
allowed_extensions = {".mp3", ".mp4", ".wav", ".m4a",}
allowed_mime_types = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/mp4", "audio/x-m4a", "audio/m4a",}

@router.post("/analyse")
async def analyze_call(audio_file: UploadFile) -> AnalysisResponse:
    request_id = str(uuid.uuid4())
    suffix = Path(audio_file.filename or "").suffix.lower()
    if suffix not in allowed_extensions:
        raise HTTPException(status_code=422, detail="Unsupported audio format. Allowed: mp3, mp4, wav, m4a",)
    if audio_file.content_type not in allowed_mime_types:
        raise HTTPException(status_code=422, detail="unsupported MIME type.",)
    audio_bytes = await audio_file.read()
    if len(audio_bytes) > max_size:
        raise HTTPException(status_code=413, detail="File exceeds 25MB limit",)
    try:
        transcription = await transcribe_audio(audio_bytes=audio_bytes, filename=audio_file.filename,)
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e)) from e
    confidence = check_confidence(transcription.transcript,)
    guard = check_injection(transcription.transcript,)
    if not guard.is_safe:
        raise HTTPException(status_code=400, detail=guard.reason)
    scrubbed = scrub_pii(transcription.transcript,)
    trimmed, was_trimmed = trim_transcript(scrubbed)
    if was_trimmed:
        print(f"[WARN] {request_id}: Transcript trimmed due to excess length")
    try:
        analysis = await analyse_with_retry(trimmed,)
    except AnalysisError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return AnalysisResponse(
        request_id=request_id,
        transcript=trimmed,
        analysis=analysis,
        low_confidence=confidence.is_low_confidence,
        confidence_message=confidence.flag_message,
        whisper_cost=0.0,
        claude_cost=0.0,
        total_cost=0.0,
    )

@router.get("/analyse/stream")
async def stream_analysis_endpoint(transcript: str,) -> StreamingResponse:
    return StreamingResponse(stream_analysis(transcript), media_type="text/event-stream",)