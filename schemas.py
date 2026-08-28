"""Structured data contracts used at every pipeline boundary.

Keeping these explicit (rather than passing around loose dicts) is what
makes each stage independently testable and gives us free validation:
if an LLM call doesn't return something that fits, we catch it immediately
instead of silently propagating a malformed opinion down the pipeline.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Verdict = Literal["Hire", "Lean Hire", "Lean No Hire", "No Hire", "Insufficient Info"]
Stance = Literal["agree", "disagree", "partially_agree"]

AGENT_NAMES = ["Technical", "HR_Culture", "HiringManager", "Skeptic"]


# ---------------------------------------------------------------------------
# Stage 1: Candidate Profile Builder
# ---------------------------------------------------------------------------

class JobRequirements(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    seniority_level: Optional[str] = None
    culture_signals: list[str] = Field(default_factory=list)


class ResumeClaim(BaseModel):
    claim: str
    source_snippet: str


class TranscriptTurn(BaseModel):
    turn_id: int
    speaker: Literal["Interviewer", "Candidate"]
    text: str


class CandidateProfile(BaseModel):
    candidate_name: str
    role_applied_for: str
    job_requirements: JobRequirements
    resume_claims: list[ResumeClaim] = Field(default_factory=list)
    transcript_turns: list[TranscriptTurn] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage 2: Independent agent opinions
# ---------------------------------------------------------------------------

class Finding(BaseModel):
    point: str
    evidence_quote: str
    evidence_source: str  # e.g. "transcript_turn_5" or "resume_claim_2"


class AgentOpinion(BaseModel):
    agent: str
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[Finding] = Field(default_factory=list)
    unresolved_gaps: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Stage 3: Debate
# ---------------------------------------------------------------------------

class DebateTurn(BaseModel):
    agent: str
    responding_to: str
    referenced_finding: str
    stance: Stance
    response_text: str
    changed_opinion: bool
    revised_verdict: Verdict
    revised_confidence: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Stage 4: Final decision
# ---------------------------------------------------------------------------

class EvidencedPoint(BaseModel):
    point: str
    evidence_quote: str
    source_agent: str


class Disagreement(BaseModel):
    topic: str
    agents_involved: list[str]
    positions: str


class FinalDecision(BaseModel):
    final_recommendation: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_steps: list[str]
    weighting_rationale: str
    strengths: list[EvidencedPoint] = Field(default_factory=list)
    concerns: list[EvidencedPoint] = Field(default_factory=list)
    unresolved_disagreements: list[Disagreement] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Full result bundle for one candidate (used by the report generator)
# ---------------------------------------------------------------------------

class CandidateResult(BaseModel):
    profile: CandidateProfile
    independent_opinions: list[AgentOpinion]
    debate_log: list[DebateTurn]
    final_decision: FinalDecision
