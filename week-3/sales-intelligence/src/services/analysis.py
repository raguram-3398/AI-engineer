from __future__ import annotations
from collections.abc import AsyncGenerator

import asyncio
import json
import re

from pydantic import ValidationError
from anthropic import AsyncAnthropic

from src.models.schemas import SalesCallAnalysis
from src.utils.exceptions import AnalysisError
from src.services.cost_tracker import calculate_claude_cost, record_spend

client = AsyncAnthropic()

PROMPT_REGISTRY: dict[str, dict[str, str]] = {
    "v1": {
        "system": (
            "You are an expert sales analyst.\n"
            "Analyse the provided sales call transcript and return:\n"
            "1. Executive summary\n"
            "2. Key objections raised by the customer\n"
            "3. Action items for the sales team\n"
            "4. Overall sentiment (Positive, Neutral or Negative)\n\n"
            "Be concise, accurate and fact-based."
        ),
        "user": (
            "Analyse the following sales call transcript:\n\n"
            "{transcript}"
        ),
    }
}

def get_prompt(version: str) -> dict[str, str]:
    """Retrives a prompt version from the PROMPT_REGISTRY"""
    try:
        return PROMPT_REGISTRY[version]
    except KeyError as e:
        raise KeyError(f"Prompt version {version} does not exist.") from e
    
async def call_claude(prompt_version: str, transcript: str, timeout: float = 30.0) -> str:
    """Send a transcript to claude and returns the raw response text"""
    prompt = get_prompt(prompt_version)
    user_content = prompt["user"].format(transcript = transcript)
    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model="claude-sonnet-4",
                max_tokens=2048,
                system=prompt["system"],
                messages=[
                    {
                        "role": "user",
                        "content" : user_content,
                    }
                ],
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError as e:
        raise TimeoutError(f"Claude timed out for prompt '{prompt_version}'.") from e
    return response.content[0].text

async def call_claude_raw(system: str, user_content: str, timeout: float = 30.0) -> str:
    """Send a retry transcript to claude and returns the raw response text"""
    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model="claude-sonnet-4",
                max_tokens=2048,
                system=system,
                messages=[
                    {
                         "role": "user",
                          "content": user_content,
                    }
                ],
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError as e:
        raise TimeoutError("Claude timed out for retry.") from e
    return response.content[0].text

def extract_json(raw: str) -> str:
    """Removes markdown fences from claude output"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return raw.strip()

async def analyse_with_retry(transcript: str, prompt_version: str = "v1", max_attempts: int = 3) -> SalesCallAnalysis:
    """Returns sales call analysis with retry for errors"""
    original_transcript = transcript
    last_error = ""
    prompt = get_prompt(prompt_version)
    raw = ""
    for attempt in range(1, max_attempts + 1):
        if attempt == 1:
            raw = await call_claude(prompt_version, original_transcript)
        else:
            correction_prompt = f"""
You are correcting a structured analysis output.

TASK:
Return valid JSON matching the required schema.

ORIGINAL TRANSCRIPT:
{original_transcript}

YOUR PREVIOUS RESPONSE:
{raw}

ERROR:
{last_error}

RULES:
- Output ONLY valid JSON
- Must match schema exactly
- sentiment must be: Positive | Neutral | Negative
- No markdown, no code fences
"""
            raw = await call_claude_raw(system=prompt["system"], user_content=correction_prompt)
        cleaned = extract_json(raw)
        try:
            data = json.loads(cleaned)
            return SalesCallAnalysis.model_validate(data)
        except(json.JSONDecodeError, ValidationError) as e:
            last_error = str(e)
            if attempt == max_attempts:
                raise AnalysisError(message=f"failed after {max_attempts} attempts", attempts=max_attempts, last_error=last_error,)


async def stream_analysis(transcript: str, prompt_version: str = "v1", timeout: float = 30.0,) -> AsyncGenerator[str, None]:
    prompt = get_prompt(prompt_version)
    message = None
    try:
        async with asyncio.timeout(timeout):
            async with client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=4096,
                system=prompt["system"],
                messages=[
                    {
                        "role": "user",
                        "content": prompt["user"].format(transcript=transcript),
                    }   
                ],
            ) as stream:
                async for chunk in stream.text_stream:
                    yield chunk
            message = await stream.get_final_message()
    finally:
            if message is not None:
                input_cost, output_cost = calculate_claude_cost(
                    input_tokens=message.usage.input_tokens,
                    output_tokens=message.usage.output_tokens,
                )
                record_spend(input_cost + output_cost)