"""Stage 5: assemble a readable per-candidate report.

Pure templating — no LLM call needed, since all the reasoning already
happened in the Decision Agent step. Keeping this deterministic makes the
final report faithful to what the agents actually said.
"""
from panel.schemas import CandidateResult


def render_report(result: CandidateResult) -> str:
    p = result.profile
    d = result.final_decision
    lines = []

    lines.append(f"# Interview Panel Report — {p.candidate_name}")
    lines.append(f"**Role:** {p.role_applied_for}\n")

    lines.append("## Final Recommendation")
    lines.append(f"**{d.final_recommendation}** (confidence: {d.confidence:.0%})\n")

    lines.append("### Reasoning")
    for step in d.reasoning_steps:
        lines.append(f"- {step}")
    lines.append(f"\n**Weighting rationale:** {d.weighting_rationale}\n")

    lines.append("### Strengths")
    if d.strengths:
        for s in d.strengths:
            lines.append(f'- {s.point} — _"{s.evidence_quote}"_ (via {s.source_agent})')
    else:
        lines.append("- None identified.")

    lines.append("\n### Concerns")
    if d.concerns:
        for c in d.concerns:
            lines.append(f'- {c.point} — _"{c.evidence_quote}"_ (via {c.source_agent})')
    else:
        lines.append("- None identified.")

    lines.append("\n### Unresolved Disagreements")
    if d.unresolved_disagreements:
        for u in d.unresolved_disagreements:
            lines.append(f"- **{u.topic}** ({', '.join(u.agents_involved)}): {u.positions}")
    else:
        lines.append("- None — the panel reached consensus in debate.")

    lines.append("\n---\n## Independent Agent Opinions (pre-debate)")
    for opinion in result.independent_opinions:
        lines.append(f"\n**{opinion.agent}** — {opinion.verdict} (confidence: {opinion.confidence:.0%})")
        for f in opinion.findings:
            lines.append(f'  - {f.point} — _"{f.evidence_quote}"_ [{f.evidence_source}]')
        if opinion.unresolved_gaps:
            lines.append(f"  - Gaps: {'; '.join(opinion.unresolved_gaps)}")

    lines.append("\n---\n## Debate Log")
    for turn in result.debate_log:
        changed = "✅ CHANGED OPINION" if turn.changed_opinion else "held position"
        lines.append(
            f"\n**{turn.agent} → {turn.responding_to}** ({turn.stance}, {changed})\n"
            f'  Re: "{turn.referenced_finding}"\n'
            f"  \"{turn.response_text}\"\n"
            f"  Revised: {turn.revised_verdict} (confidence: {turn.revised_confidence:.0%})"
        )

    return "\n".join(lines)


def render_comparison(results: list[CandidateResult]) -> str:
    """Bonus: side-by-side comparison across candidates."""
    lines = ["# Candidate Comparison\n"]
    lines.append("| Candidate | Recommendation | Confidence |")
    lines.append("|---|---|---|")
    for r in results:
        d = r.final_decision
        lines.append(f"| {r.profile.candidate_name} | {d.final_recommendation} | {d.confidence:.0%} |")
    return "\n".join(lines)
