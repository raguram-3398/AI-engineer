from __future__ import annotations

import asyncio
import logging
import math


from anthropic import AsyncAnthropic
from src.models.schemas import CostRecord

client = AsyncAnthropic()

whisper_cost_per_minute: float = 0.006
claude_input_cost_per_token: float = 3.0 / 1_000_000
claude_output_cost_per_token: float = 15.0 / 1_000_000
daily_spend_alert_threshold: float = 1.0
_daily_spend: float = 0.0

logger = logging.getLogger(__name__)

async def count_tokens(messages: list[dict[str, str]], system: str, model: str = "claude-sonnet-4") -> int:
    try:
        response = await asyncio.wait_for(
            client.messages.count_tokens(
                model=model,
                messages=messages,
                system=system,
            ),
            timeout = 10.0,
        )
        return response.input_tokens
    except asyncio.TimeoutError:
        raise TimeoutError("Token counting request timed out")

def trim_transcript(transcript: str, max_tokens: int = 150000, char_per_token: float = 4.0) -> tuple[str, bool]:
    estimated_tokens = len(transcript) / char_per_token
    if estimated_tokens <= max_tokens:
        return transcript, False
    max_char = int(max_tokens * char_per_token)
    trimmed = transcript[:max_char].rstrip()
    trimmed += "\n\n [Transcript Trimmed - original exceeded context budget]"
    return trimmed, True

def calculate_claude_cost(input_tokens: int, output_tokens: int) -> tuple[float, float]:
    input_cost = input_tokens * claude_input_cost_per_token
    output_cost = output_tokens * claude_output_cost_per_token
    return input_cost, output_cost

def calculate_whisper_cost(duration_seconds: float) -> float:
    billed_minutes = math.ceil(duration_seconds / 60)
    return billed_minutes * whisper_cost_per_minute

def check_daily_spend(current_spend: float, threshold: float = daily_spend_alert_threshold) -> bool:
    return current_spend >= threshold

def record_spend(amount: float) -> float:
    global _daily_spend
    _daily_spend += amount
    if check_daily_spend(_daily_spend):
        logger.warning("Daily threshold exceeded",)
    return _daily_spend