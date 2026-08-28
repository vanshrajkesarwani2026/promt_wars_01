"""Orchestrates the full pipeline for one candidate:
Profile Builder -> 4 Independent Agents -> Debate -> Decision -> Report.
"""
from panel.agents import run_independent_agents
from panel.debate import apply_debate_revisions, run_debate_round
from panel.decision import make_final_decision
from panel.llm_client import LLMClient
from panel.profile_builder import build_candidate_profile
from panel.schemas import CandidateResult


def run_pipeline_for_candidate(
    client: LLMClient,
    job_description_text: str,
    resume_text: str,
    transcript_text: str,
    candidate_key: str,
) -> CandidateResult:
    """candidate_key is a short id like 'A' or 'B', used to namespace mock
    call keys and keep logs readable — has no effect in live mode."""

    profile = build_candidate_profile(
        client,
        job_description_text,
        resume_text,
        transcript_text,
        call_key=f"profile:{candidate_key}",
    )

    independent_opinions = run_independent_agents(
        client, profile, call_key_prefix=f"independent:{candidate_key}"
    )

    debate_log = run_debate_round(
        client, independent_opinions, call_key_prefix=candidate_key
    )

    post_debate_opinions = apply_debate_revisions(independent_opinions, debate_log)

    final_decision = make_final_decision(
        client,
        profile,
        post_debate_opinions,
        debate_log,
        call_key=f"decision:{candidate_key}",
    )

    return CandidateResult(
        profile=profile,
        independent_opinions=list(independent_opinions.values()),
        debate_log=debate_log,
        final_decision=final_decision,
    )
