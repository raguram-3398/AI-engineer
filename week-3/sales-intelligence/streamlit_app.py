from __future__ import annotations

import json
import os

import requests
import streamlit as st

from partial_json_parser import loads as partial_loads, Allow

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Sales Call Intelligence", layout="wide",)
st.title("Sales Call Intelligence")
with st.sidebar:
    st.header("API Keys")
    anthropic_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.caption("keys are sent as request headers and are not logged or persisted")
if "metadata" not in st.session_state:
    st.session_state.metadata = None
uploaded_file = st.file_uploader("Upload a sales call recording", type=["mp3", "mp4", "wav", "m4a"])

def _auth_headers() -> dict[str, str]:
    """Build X-Anthropic-Key / X-OpenAI-Key headers from sidebar inputs; omits keys if blank."""
    headers: dict[str,str] = {}
    if anthropic_key:
        headers["X-Anthropic-Key"] = anthropic_key
    if openai_key:
        headers["X-OpenAI-Key"] = openai_key
    return headers

def _render_analysis(placeholders: dict, analysis: dict, low_confidence: bool, confidence_message: str | None,) -> None:
    """Write current analysis fields into st.empty() placeholders; safe to call repeatedly as fields arrive.
    
    # Design note: called progressively during streaming with partial data, then once more
    # from __META__ with the final validated SalesCallAnalysis. _clear_placeholders() is called
    # before the final render so any partial or invalid content from attempt 1 is replaced cleanly.
    """
    if low_confidence and confidence_message:
        placeholders["confidence"].warning(f"Low confidence: {confidence_message}")
    summary = analysis.get("summary", "")
    if summary:
        placeholders["summary"].markdown(f"**Summary**\n\n{summary}")
    objections = analysis.get("objections", [])
    if objections:
        placeholders["objections"].markdown("**Objections**\n\n" + "\n".join(f"• {o}" for o in objections))
    action_items = analysis.get("action_items", [])
    if action_items:
        placeholders["action_items"].markdown("**Action_Items**\n\n" + "\n".join(f"• {a}" for a in action_items))
    sentiment = analysis.get("sentiment", "")
    if sentiment:
        placeholders["sentiment"].markdown(f"**Sentiment**\n\n{sentiment}")

def _clear_placeholders(placeholders: dict) -> None:
    """Clear all five st.empty() placeholders; called before re-rendering the validated retry result."""
    for ph in placeholders.values():
        ph.empty()

def _stream_and_render(file) -> dict:
    """POST audio, consume SSE stream, progressively render fields via partial_json_parser, return metadata.
    
    # Design note: partial_json_parser.loads(buffer, Allow.ALL) parses incomplete JSON on every
    # chunk — the same pattern used by Claude.ai, ChatGPT, and Gemini to render structured UI
    # fields progressively as tokens arrive. last_rendered guards against redundant re-renders.
    # On __META__ arrival the placeholders are cleared and re-rendered from the authoritative
    # validated result, handling the retry-replace case transparently.
    """
    file.seek(0)
    files = {"audio_file": (file.name, file, file.type)}
    placeholders = {
        "confidence":   st.empty(),
        "summary":      st.empty(),
        "objections":   st.empty(),
        "action_items": st.empty(),
        "sentiment":    st.empty(),
    }
    buffer = ""
    metadata: dict = {}
    last_rendered: dict = {}
    with requests.post(
        f"{API_BASE_URL}/analyse",
        files=files,
        headers=_auth_headers(),
        stream=True,
        timeout=300,
    ) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if not chunk:
                continue
            if chunk.startswith("__META__:"):
                metadata = json.loads(chunk[len("__META__:"):].strip())
                analysis = metadata.get("analysis", {})
                _clear_placeholders(placeholders)
                _render_analysis(placeholders, analysis, metadata.get("low_confidence", False), metadata.get("confidence_message", ""),)
                continue
            buffer += chunk
            try:
                partial = partial_loads(buffer, Allow.ALL)
                if not isinstance(partial, dict):
                    continue
                analysis = partial.get("analysis", partial)
                if analysis != last_rendered:
                    _render_analysis(placeholders, analysis, False, None)
                    last_rendered = dict(analysis)
            except Exception:
                pass
    return metadata

if st.button("Analyse"):
    if uploaded_file is None:
        st.warning("Please upload an audio file.")
        st.stop()
    uploaded_file.seek(0)
    st.subheader("Analysis")
    with st.spinner("Transcribing audio..."):
        pass
    try:
        metadata = _stream_and_render(uploaded_file)
        st.session_state.metadata = metadata
    except RuntimeError as e:
        st.error(f"Analysis failed: {e}")
    except requests.HTTPError as e:
        st.error(f"Request failed: {e.response.status_code}: {e.response.text}")
metadata = st.session_state.metadata

if metadata:
    st.subheader("Cost Breakdown")
    col1, col2, col3 = st.columns(3)
    col1.metric("Whisper Cost", f"${metadata['whisper_cost']:.6f}")
    col2.metric("Claude Cost", f"${metadata['claude_cost']:.6f}")
    col3.metric("Total Cost", f"${metadata['total_cost']:.6f}")