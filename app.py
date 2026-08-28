"""Streamlit Web UI for the Multi-Agent AI Interview Panel Simulator."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
import streamlit as st

from panel.llm_client import LLMClient
from panel.mock_data import MOCK_RESPONSES
from panel.pdf_utils import extract_pdf_text
from panel.pipeline import run_pipeline_for_candidate
from panel.report import render_comparison, render_report

# Page configuration
st.set_page_config(
    page_title="Multi-Agent AI Interview Panel",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚖️ Multi-Agent AI Interview Panel Simulator")
st.caption(
    "A multi-agent committee that debates candidate evaluations, checks claims against transcripts, "
    "and produces evidence-backed hiring decisions."
)

# -----------------------------------------------------------------------------
# Sidebar: Configuration & API Key
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")
    mode = st.radio(
        "Execution Mode",
        options=["Mock Mode (Demo)", "Live Mode (Gemini API)"],
        index=0,
        help="Mock mode uses deterministic canned responses. Live mode processes uploaded PDFs with Gemini.",
    )

    api_key_input = ""
    if mode == "Live Mode (Gemini API)":
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="Enter your AI Studio API key.",
        )
        if api_key_input:
            os.environ["GEMINI_API_KEY"] = api_key_input

    st.markdown("---")
    st.markdown("### 📋 Required Documents")
    st.markdown(
        """
        - **1 Job Description** (PDF)
        - **2 Candidate Resumes** (A & B PDFs)
        - **2 Interview Transcripts** (A & B PDFs)
        """
    )


# -----------------------------------------------------------------------------
# Document Uploaders
# -----------------------------------------------------------------------------
def save_uploaded_file(uploaded_file) -> str:
    """Save an uploaded file to a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        return tmp.name


if mode == "Live Mode (Gemini API)":
    st.subheader("📄 Upload Input Documents")
    col_job, _ = st.columns([2, 1])
    with col_job:
        job_file = st.file_uploader("Job Description (PDF)", type=["pdf"], key="job_desc")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Candidate A")
        resume_a_file = st.file_uploader("Candidate A Resume (PDF)", type=["pdf"], key="res_a")
        transcript_a_file = st.file_uploader("Candidate A Transcript (PDF)", type=["pdf"], key="trn_a")

    with col_b:
        st.markdown("#### Candidate B")
        resume_b_file = st.file_uploader("Candidate B Resume (PDF)", type=["pdf"], key="res_b")
        transcript_b_file = st.file_uploader("Candidate B Transcript (PDF)", type=["pdf"], key="trn_b")
else:
    st.info("ℹ️ **Mock Mode Selected:** Default canned interview data for Jordan Lee and Priya Shah will be loaded. No PDFs required!")
    job_file = resume_a_file = transcript_a_file = resume_b_file = transcript_b_file = None

# -----------------------------------------------------------------------------
# Run Pipeline Trigger
# -----------------------------------------------------------------------------
run_button = st.button("🚀 Run Multi-Agent Evaluation Panel", type="primary", use_container_width=True)

if run_button:
    # 1. Validation Block (Properly indented so it only triggers in Live Mode)
    if mode == "Live Mode (Gemini API)":
        if not api_key_input:
            st.error("Please provide a Gemini API Key in the sidebar.")
            st.stop()
            
        if not all([job_file, resume_a_file, transcript_a_file, resume_b_file, transcript_b_file]):
            st.error("Please upload all 5 required PDF documents.")
            st.stop()
            
    # 2. Execution Block
    with st.spinner("Initializing Agents & Extracting Text..."):
        try:
            if mode == "Mock Mode (Demo)":
                client = LLMClient(mode="mock", mock_responses=MOCK_RESPONSES)
                job_text = resume_a = transcript_a = resume_b = transcript_b = "(mock mode: unused)"
            else:
                client = LLMClient(mode="live")
                job_text = extract_pdf_text(save_uploaded_file(job_file))
                resume_a = extract_pdf_text(save_uploaded_file(resume_a_file))
                transcript_a = extract_pdf_text(save_uploaded_file(transcript_a_file))
                resume_b = extract_pdf_text(save_uploaded_file(resume_b_file))
                transcript_b = extract_pdf_text(save_uploaded_file(transcript_b_file))

            results = []
            reports = {}

            # Process candidates
            for key, res_text, trn_text in [("A", resume_a, transcript_a), ("B", resume_b, transcript_b)]:
                st.write(f"🔄 **Running Committee Evaluation for Candidate {key}...**")
                result = run_pipeline_for_candidate(
                    client, job_text, res_text, trn_text, candidate_key=key
                )
                results.append(result)
                reports[key] = render_report(result)

            comparison_text = render_comparison(results)

            st.session_state["results"] = results
            st.session_state["reports"] = reports
            st.session_state["comparison"] = comparison_text
            st.success("✅ Multi-Agent Evaluation and Debate Completed!")

        except Exception as e:
            st.error(f"Error running pipeline: {e}")
            st.stop()

# -----------------------------------------------------------------------------
# Display Reports and Results
# -----------------------------------------------------------------------------
if "results" in st.session_state:
    results = st.session_state["results"]
    reports = st.session_state["reports"]
    comparison_text = st.session_state["comparison"]

    st.markdown("---")
    tab_comp, tab_a, tab_b = st.tabs(["📊 Candidate Comparison", "👤 Candidate A Report", "👤 Candidate B Report"])

    # --- TAB 1: Comparison ---
    with tab_comp:
        st.markdown(comparison_text)
        
        col_m1, col_m2 = st.columns(2)
        if len(results) >= 2:
            with col_m1:
                st.metric(
                    label=f"Candidate A ({results[0].profile.candidate_name})",
                    value=results[0].final_decision.final_recommendation,
                    delta=f"{int(results[0].final_decision.confidence * 100)}% confidence",
                )
            with col_m2:
                st.metric(
                    label=f"Candidate B ({results[1].profile.candidate_name})",
                    value=results[1].final_decision.final_recommendation,
                    delta=f"{int(results[1].final_decision.confidence * 100)}% confidence",
                )

        st.download_button(
            label="📥 Download Comparison Markdown",
            data=comparison_text,
            file_name="comparison.md",
            mime="text/markdown",
        )

    # --- TAB 2: Candidate A ---
    with tab_a:
        st.markdown(reports["A"])
        st.download_button(
            label="📥 Download Candidate A Report",
            data=reports["A"],
            file_name="candidate_A_report.md",
            mime="text/markdown",
            key="dl_a",
        )

    # --- TAB 3: Candidate B ---
    with tab_b:
        st.markdown(reports["B"])
        st.download_button(
            label="📥 Download Candidate B Report",
            data=reports["B"],
            file_name="candidate_B_report.md",
            mime="text/markdown",
            key="dl_b",
        )