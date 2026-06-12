from __future__ import annotations

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Sales Call Intelligence", layout="wide",)
st.title("Sales Call Intelligence")
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "Streamed_text" not in st.session_state:
    st.session_state.Streamed_text = None
uploaded_file = st.file_uploader("Upload a sales call recording", type=["mp3", "mp4", "wav", "m4a"],)

def stream_tokens(transcript: str):
    response = requests.get(
        f"{API_BASE_URL}/analyse/stream",
        params={"transcript": transcript},
        stream=True,
        timeout=300,
    )
    response.raise_for_status()
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if chunk:
            yield chunk

if st.button("Analyse"):
    if uploaded_file is None:
        st.warning("Please upload an audio file.")
        st.stop()
    files = {"audio_file": (uploaded_file.name, uploaded_file, uploaded_file.type,)}
    with st.spinner("Transcribing and analysing call..."):
        response = requests.post(
            f"{API_BASE_URL}/analyse",
            files=files,
            timeout=300,
        )
        response.raise_for_status()
        result = response.json()
        transcript = result["transcript"]
        st.subheader("claude analysis")
        streamed_text = st.write_stream(stream_tokens(transcript))
        st.session_state.streamed_text = streamed_text
        st.session_state.analysis_result = result
analysis_result = st.session_state.analysis_result

if analysis_result:
    if analysis_result["low_confidence"]:
        st.warning(analysis_result["confidence_message"])
    st.subheader("Cost Breakdown.")
    st.write(f"{analysis_result['whisper_cost']:.6f}")
    st.write(f"{analysis_result['claude_cost']:.6f}")
    st.write(f"{analysis_result['total_cost']:.6f}")
    analysis = analysis_result["analysis"]
    with st.expander("Summary", expanded=True):
        st.write(analysis["summary"])
    with st.expander("Objections"):
        for objection in analysis["objections"]:
            st.write(f"• {objection}")
    with st.expander("Action items"):
        for item in analysis["action_items"]:
            st.write(f"• {item}")
    with st.expander("Sentiment"):
        st.write(analysis["sentiment"])