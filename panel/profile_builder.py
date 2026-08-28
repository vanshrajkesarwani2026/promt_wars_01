"""Stage 1: build a shared, factual candidate profile from raw documents.

This is deliberately NOT an opinion agent. It only extracts facts so that
every downstream agent judges the exact same shared context.
"""
from __future__ import annotations
from panel.llm_client import LLMClient
from panel.prompts import PROFILE_BUILDER_PROMPT
from panel.schemas import CandidateProfile


def build_candidate_profile(
    client: LLMClient,
    job_description_text: str,
    resume_text: str,
    transcript_text: str,
    call_key: str | None = None,
) -> CandidateProfile:
    user_prompt = f"""JOB DESCRIPTION:
{job_description_text}

RESUME:
{resume_text}

INTERVIEW TRANSCRIPT:
{transcript_text}
"""
    return client.call_structured(
        system_prompt=PROFILE_BUILDER_PROMPT,
        user_prompt=user_prompt,
        response_model=CandidateProfile,
        call_key=call_key,
    )
