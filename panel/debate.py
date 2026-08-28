"""Stage 3: the debate step.

Unlike Stage 2, this is sequential and cumulative: each agent, in turn,
sees every agent's independent (Stage 2) opinion PLUS every debate turn
that has happened so far this round. This lets later agents genuinely
react to earlier reactions, not just the original 4 opinions.

Every DebateTurn is logged, including `changed_opinion`, which is the
proof-of-real-debate artifact called for in the assignment rules.
"""
from __future__ import annotations
from panel.llm_client import LLMClient
from panel.prompts import DEBATE_PROMPT_TEMPLATE
from panel.schemas import AGENT_NAMES, AgentOpinion, DebateTurn


def _format_opinions(opinions: dict[str, AgentOpinion]) -> str:
    blocks = []
    for name, op in opinions.items():
        findings_text = "\n".join(
            f'    - {f.point} (evidence: "{f.evidence_quote}" [{f.evidence_source}])'
            for f in op.findings
        )
        gaps_text = "; ".join(op.unresolved_gaps) if op.unresolved_gaps else "none"
        blocks.append(
            f"{name} — verdict: {op.verdict}, confidence: {op.confidence}\n"
            f"  findings:\n{findings_text}\n"
            f"  unresolved_gaps: {gaps_text}"
        )
    return "\n\n".join(blocks)


def _format_debate_so_far(turns: list[DebateTurn]) -> str:
    if not turns:
        return "(no debate turns yet this round)"
    blocks = []
    for t in turns:
        blocks.append(
            f"{t.agent} responded to {t.responding_to} on \"{t.referenced_finding}\": "
            f"stance={t.stance}, changed_opinion={t.changed_opinion}. "
            f"\"{t.response_text}\""
        )
    return "\n".join(blocks)


def run_debate_round(
    client: LLMClient,
    independent_opinions: dict[str, AgentOpinion],
    call_key_prefix: str | None = None,
) -> list[DebateTurn]:
    """Run one sequential debate pass across all 4 agents.

    Order: Technical -> HR_Culture -> HiringManager -> Skeptic. Each agent
    sees the full set of independent opinions plus all debate turns
    produced earlier in this same pass, so a chain of real cross-reference
    can form naturally.
    """
    debate_log: list[DebateTurn] = []
    opinions_text = _format_opinions(independent_opinions)

    for agent_name in AGENT_NAMES:
        system_prompt = DEBATE_PROMPT_TEMPLATE.format(agent_name=agent_name)
        user_prompt = f"""ALL AGENTS' INDEPENDENT OPINIONS:
{opinions_text}

DEBATE SO FAR THIS ROUND:
{_format_debate_so_far(debate_log)}

Your own independent opinion was:
verdict={independent_opinions[agent_name].verdict}, confidence={independent_opinions[agent_name].confidence}
"""
        call_key = f"{call_key_prefix}:debate:{agent_name}" if call_key_prefix else None
        turn = client.call_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=DebateTurn,
            call_key=call_key,
        )
        debate_log.append(turn)

    return debate_log


def apply_debate_revisions(
    independent_opinions: dict[str, AgentOpinion], debate_log: list[DebateTurn]
) -> dict[str, AgentOpinion]:
    """Produce post-debate opinions: same findings/evidence, but verdict and
    confidence updated to each agent's final (revised) stance."""
    revised = {}
    # last debate turn per agent wins (in case of multiple rounds in future)
    last_turn_by_agent = {t.agent: t for t in debate_log}

    for name, opinion in independent_opinions.items():
        turn = last_turn_by_agent.get(name)
        if turn is None:
            revised[name] = opinion
            continue
        revised[name] = opinion.model_copy(
            update={"verdict": turn.revised_verdict, "confidence": turn.revised_confidence}
        )
    return revised
