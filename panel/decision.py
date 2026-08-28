"""Stage 4: the Decision Agent.

Takes the post-debate opinions + full debate log and produces a single
reasoned recommendation. This step explicitly does NOT average the 4
confidence scores — the prompt requires step-by-step reasoning about
evidence quality, role-relevance weighting, and unresolved disagreement.
"""
from __future__ import annotations
from panel.debate import _format_debate_so_far, _format_opinions
from panel.llm_client import LLMClient
from panel.prompts import DECISION_PROMPT
from panel.schemas import AgentOpinion, CandidateProfile, DebateTurn, FinalDecision


def make_final_decision(
    client: LLMClient,
    profile: CandidateProfile,
    post_debate_opinions: dict[str, AgentOpinion],
    debate_log: list[DebateTurn],
    call_key: str | None = None,
) -> FinalDecision:
    user_prompt = f"""ROLE: {profile.role_applied_for}
JOB REQUIREMENTS:
  Required skills: {', '.join(profile.job_requirements.required_skills) or 'none listed'}
  Nice-to-have skills: {', '.join(profile.job_requirements.nice_to_have_skills) or 'none listed'}
  Seniority level: {profile.job_requirements.seniority_level or 'not specified'}
  Culture signals: {', '.join(profile.job_requirements.culture_signals) or 'none listed'}

POST-DEBATE AGENT POSITIONS:
{_format_opinions(post_debate_opinions)}

FULL DEBATE LOG:
{_format_debate_so_far(debate_log)}
"""
    return client.call_structured(
        system_prompt=DECISION_PROMPT,
        user_prompt=user_prompt,
        response_model=FinalDecision,
        call_key=call_key,
    )
