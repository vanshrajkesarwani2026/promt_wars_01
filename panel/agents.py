"""Stage 2: four independent agent opinions.

CRITICAL DESIGN RULE: each agent call below receives ONLY the shared
candidate profile. None of them receive any other agent's output. They
are run as separate LLM calls (in a thread pool, since they don't depend
on each other) so independence is structural, not just a prompt
instruction that could be ignored.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor

from panel.llm_client import LLMClient
from panel.prompts import AGENT_SYSTEM_PROMPTS
from panel.schemas import AGENT_NAMES, AgentOpinion, CandidateProfile


def _profile_to_prompt_text(profile: CandidateProfile) -> str:
    lines = [
        f"Candidate: {profile.candidate_name}",
        f"Role applied for: {profile.role_applied_for}",
        "",
        "JOB REQUIREMENTS:",
        f"  Required skills: {', '.join(profile.job_requirements.required_skills) or 'none listed'}",
        f"  Nice-to-have skills: {', '.join(profile.job_requirements.nice_to_have_skills) or 'none listed'}",
        f"  Seniority level: {profile.job_requirements.seniority_level or 'not specified'}",
        f"  Culture signals: {', '.join(profile.job_requirements.culture_signals) or 'none listed'}",
        "",
        "RESUME CLAIMS:",
    ]
    for i, claim in enumerate(profile.resume_claims):
        lines.append(f"  resume_claim_{i}: {claim.claim} (source: \"{claim.source_snippet}\")")

    lines.append("")
    lines.append("INTERVIEW TRANSCRIPT:")
    for turn in profile.transcript_turns:
        lines.append(f"  transcript_turn_{turn.turn_id} [{turn.speaker}]: {turn.text}")

    return "\n".join(lines)


def _run_single_agent(
    client: LLMClient, agent_name: str, profile: CandidateProfile, call_key_prefix: str | None
) -> AgentOpinion:
    system_prompt = AGENT_SYSTEM_PROMPTS[agent_name]
    user_prompt = _profile_to_prompt_text(profile)
    call_key = f"{call_key_prefix}:{agent_name}" if call_key_prefix else None
    return client.call_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=AgentOpinion,
        call_key=call_key,
    )


def run_independent_agents(
    client: LLMClient, profile: CandidateProfile, call_key_prefix: str | None = None
) -> dict[str, AgentOpinion]:
    """Run all 4 agents independently (parallel, isolated). Returns a dict
    keyed by agent name for easy lookup in later stages."""
    opinions: dict[str, AgentOpinion] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(_run_single_agent, client, name, profile, call_key_prefix): name
            for name in AGENT_NAMES
        }
        for future in futures:
            name = futures[future]
            opinions[name] = future.result()
    return opinions
