"""Canned responses for LLMClient(mode="mock").

This lets you run `python main.py --mock` and see the full pipeline
(profile building -> 4 independent agents -> debate with a real opinion
change -> non-averaged final decision -> report) end to end with zero API
calls. It's meant for demoing/testing orchestration logic, not for
judging actual candidates -- swap to --mode live with real PDFs for that.

The story baked into candidate A's mock data is deliberately a case where
the Skeptic catches an inflated claim that the Technical agent initially
missed, and the Technical agent revises its confidence downward during
debate -- so you can see `changed_opinion: true` appear in the log.
"""

MOCK_RESPONSES = {
    # -------------------------------------------------------------- Candidate A
    "profile:A": {
        "candidate_name": "Jordan Lee",
        "role_applied_for": "Senior Backend Engineer",
        "job_requirements": {
            "required_skills": ["distributed systems", "Python", "API design"],
            "nice_to_have_skills": ["Kubernetes", "mentoring experience"],
            "seniority_level": "Senior",
            "culture_signals": ["collaborative", "gives/receives feedback well"],
        },
        "resume_claims": [
            {
                "claim": "Led a team that rebuilt the payments microservice, reducing latency by 40%",
                "source_snippet": "Led a 5-engineer team to rebuild the payments microservice, cutting p99 latency by 40%.",
            },
            {
                "claim": "5 years of distributed systems experience",
                "source_snippet": "5+ years designing and operating distributed systems at scale.",
            },
        ],
        "transcript_turns": [
            {"turn_id": 1, "speaker": "Interviewer", "text": "Tell me about the payments microservice rebuild."},
            {
                "turn_id": 2,
                "speaker": "Candidate",
                "text": "Sure, so the team decided to move to an event-driven architecture, and that's what got us the latency win.",
            },
            {"turn_id": 3, "speaker": "Interviewer", "text": "What was your specific role in that decision?"},
            {
                "turn_id": 4,
                "speaker": "Candidate",
                "text": "I mean, it was a team effort, we all contributed. I was involved in a lot of the discussions.",
            },
            {"turn_id": 5, "speaker": "Interviewer", "text": "Can you walk me through a specific technical tradeoff you personally made?"},
            {
                "turn_id": 6,
                "speaker": "Candidate",
                "text": "Honestly a lot of that was handled by our staff engineer, I was more focused on coordinating the team's timeline.",
            },
        ],
    },
    "independent:A:Technical": {
        "agent": "Technical",
        "verdict": "Lean Hire",
        "confidence": 0.7,
        "findings": [
            {
                "point": "Resume claims a significant latency improvement from a microservice rebuild",
                "evidence_quote": "Led a 5-engineer team to rebuild the payments microservice, cutting p99 latency by 40%.",
                "evidence_source": "resume_claim_0",
            },
            {
                "point": "Candidate confirmed the architectural approach (event-driven) that drove the win",
                "evidence_quote": "the team decided to move to an event-driven architecture, and that's what got us the latency win",
                "evidence_source": "transcript_turn_2",
            },
        ],
        "unresolved_gaps": ["Candidate's personal hands-on technical contribution to key decisions is unclear"],
    },
    "independent:A:HR_Culture": {
        "agent": "HR_Culture",
        "verdict": "Lean Hire",
        "confidence": 0.6,
        "findings": [
            {
                "point": "Candidate frames the work as a team effort rather than claiming individual credit",
                "evidence_quote": "it was a team effort, we all contributed",
                "evidence_source": "transcript_turn_4",
            }
        ],
        "unresolved_gaps": ["No direct examples of handling conflict or giving/receiving feedback were discussed"],
    },
    "independent:A:HiringManager": {
        "agent": "HiringManager",
        "verdict": "Lean Hire",
        "confidence": 0.65,
        "findings": [
            {
                "point": "Candidate has direct experience on a project matching a required skill area",
                "evidence_quote": "5+ years designing and operating distributed systems at scale.",
                "evidence_source": "resume_claim_1",
            }
        ],
        "unresolved_gaps": ["Not enough evidence yet on mentoring experience, a nice-to-have for this role"],
    },
    "independent:A:Skeptic": {
        "agent": "Skeptic",
        "verdict": "Lean No Hire",
        "confidence": 0.55,
        "findings": [
            {
                "point": "Contradicted: resume implies the candidate personally led key technical decisions, but under direct questioning the candidate deflects credit to a staff engineer",
                "evidence_quote": "Honestly a lot of that was handled by our staff engineer, I was more focused on coordinating the team's timeline.",
                "evidence_source": "transcript_turn_6",
            },
            {
                "point": "Candidate gave a vague, non-specific answer when asked for a concrete personal technical tradeoff",
                "evidence_quote": "I was involved in a lot of the discussions.",
                "evidence_source": "transcript_turn_4",
            },
        ],
        "unresolved_gaps": [],
    },
    "A:debate:Technical": {
        "agent": "Technical",
        "responding_to": "Skeptic",
        "referenced_finding": "Under direct questioning the candidate deflects credit to a staff engineer for the key technical decision",
        "stance": "agree",
        "response_text": "That's a fair catch. I weighted the resume's latency claim without noticing the transcript shows the candidate wasn't the one making the core technical tradeoffs. My verdict was too generous to the resume framing.",
        "changed_opinion": True,
        "revised_verdict": "Lean No Hire",
        "revised_confidence": 0.5,
    },
    "A:debate:HR_Culture": {
        "agent": "HR_Culture",
        "responding_to": "Technical",
        "referenced_finding": "Candidate confirmed the architectural approach that drove the latency win",
        "stance": "partially_agree",
        "response_text": "I read the same deflection differently -- coordinating a team's timeline while deferring technical credit to a staff engineer can be a legitimate, healthy team dynamic, not necessarily evasiveness. I don't think this alone is a culture red flag.",
        "changed_opinion": False,
        "revised_verdict": "Lean Hire",
        "revised_confidence": 0.6,
    },
    "A:debate:HiringManager": {
        "agent": "HiringManager",
        "responding_to": "Skeptic",
        "referenced_finding": "Candidate deflects credit to a staff engineer under direct questioning",
        "stance": "partially_agree",
        "response_text": "This does raise the risk that the candidate is more of a coordinator than a hands-on senior IC, which matters for a Senior Backend Engineer role expected to make technical tradeoffs directly. I'm lowering my confidence but not flipping my verdict yet, since coordination skill has value too.",
        "changed_opinion": True,
        "revised_verdict": "Lean Hire",
        "revised_confidence": 0.5,
    },
    "A:debate:Skeptic": {
        "agent": "Skeptic",
        "responding_to": "HR_Culture",
        "referenced_finding": "Deferring technical credit to a staff engineer can be a healthy team dynamic, not evasiveness",
        "stance": "disagree",
        "response_text": "The concern isn't that they deferred credit -- it's that the resume specifically claims they 'led' the rebuild that produced the technical win, and the transcript shows someone else made the core decisions. That's a gap between the resume framing and the transcript, not just modesty.",
        "changed_opinion": False,
        "revised_verdict": "Lean No Hire",
        "revised_confidence": 0.55,
    },
    "decision:A": {
        "final_recommendation": "Lean No Hire",
        "confidence": 0.55,
        "reasoning_steps": [
            "The Technical agent's initial 'Lean Hire' rested heavily on the resume's latency-improvement claim, but revised downward in debate after acknowledging the transcript shows a staff engineer, not the candidate, made the core technical tradeoffs.",
            "The Skeptic's finding is evidence-backed with a direct quote and identifies a real gap between resume framing ('Led...cutting p99 latency by 40%') and transcript testimony ('a lot of that was handled by our staff engineer') -- this is treated as a higher-weight signal per the panel's evidence-quality rule.",
            "HR_Culture's alternative read (deference as healthy team dynamic) is plausible but does not resolve the specific resume-vs-transcript discrepancy the Skeptic raised; this remains a genuine unresolved disagreement.",
            "For a Senior Backend Engineer role, the job requires the candidate to personally drive distributed-systems tradeoffs, which is exactly the area the transcript leaves unverified.",
        ],
        "weighting_rationale": "Skeptic and Technical (post-revision) were weighted most heavily since this is a senior IC role where personal technical ownership is a required skill; HR_Culture's read was given real but secondary weight since it addresses tone/interpretation rather than the underlying factual gap.",
        "strengths": [
            {
                "point": "Candidate has confirmed exposure to the architectural approach behind a real production win",
                "evidence_quote": "the team decided to move to an event-driven architecture, and that's what got us the latency win",
                "source_agent": "Technical",
            }
        ],
        "concerns": [
            {
                "point": "Resume claims individual leadership of a technical rebuild; transcript suggests the candidate coordinated rather than personally drove technical decisions",
                "evidence_quote": "Honestly a lot of that was handled by our staff engineer, I was more focused on coordinating the team's timeline.",
                "source_agent": "Skeptic",
            }
        ],
        "unresolved_disagreements": [
            {
                "topic": "Whether deferring technical credit reflects a resume/reality gap or healthy team modesty",
                "agents_involved": ["Skeptic", "HR_Culture"],
                "positions": "Skeptic sees a factual discrepancy between the resume's 'led' framing and the transcript; HR_Culture sees plausible team-oriented modesty. Debate did not resolve which read is correct.",
            }
        ],
    },
    # -------------------------------------------------------------- Candidate B
    "profile:B": {
        "candidate_name": "Priya Shah",
        "role_applied_for": "Senior Backend Engineer",
        "job_requirements": {
            "required_skills": ["distributed systems", "Python", "API design"],
            "nice_to_have_skills": ["Kubernetes", "mentoring experience"],
            "seniority_level": "Senior",
            "culture_signals": ["collaborative", "gives/receives feedback well"],
        },
        "resume_claims": [
            {
                "claim": "Designed and implemented a rate-limiting service handling 50k req/s",
                "source_snippet": "Designed and implemented a token-bucket based rate-limiting service handling 50k req/s in production.",
            }
        ],
        "transcript_turns": [
            {"turn_id": 1, "speaker": "Interviewer", "text": "Walk me through the rate-limiting service you built."},
            {
                "turn_id": 2,
                "speaker": "Candidate",
                "text": "I chose a token-bucket algorithm over a sliding window because we needed to allow short bursts without penalizing steady clients. I implemented it with Redis for shared state across nodes, using Lua scripts to keep the check-and-decrement atomic.",
            },
            {"turn_id": 3, "speaker": "Interviewer", "text": "What was the hardest part?"},
            {
                "turn_id": 4,
                "speaker": "Candidate",
                "text": "Getting the Redis Lua script right under concurrent load -- we had a race condition in an early version that let a few clients slightly exceed their limit. I fixed it by making the whole check atomic in a single script instead of two round trips.",
            },
        ],
    },
    "independent:B:Technical": {
        "agent": "Technical",
        "verdict": "Hire",
        "confidence": 0.85,
        "findings": [
            {
                "point": "Candidate gave a specific, technically sound justification for the algorithm choice",
                "evidence_quote": "I chose a token-bucket algorithm over a sliding window because we needed to allow short bursts without penalizing steady clients.",
                "evidence_source": "transcript_turn_2",
            },
            {
                "point": "Candidate demonstrated hands-on debugging of a real concurrency bug",
                "evidence_quote": "we had a race condition in an early version that let a few clients slightly exceed their limit. I fixed it by making the whole check atomic in a single script",
                "evidence_source": "transcript_turn_4",
            },
        ],
        "unresolved_gaps": [],
    },
    "independent:B:HR_Culture": {
        "agent": "HR_Culture",
        "verdict": "Insufficient Info",
        "confidence": 0.3,
        "findings": [],
        "unresolved_gaps": ["Transcript contains no discussion of teamwork, conflict, or feedback -- purely technical Q&A"],
    },
    "independent:B:HiringManager": {
        "agent": "HiringManager",
        "verdict": "Hire",
        "confidence": 0.75,
        "findings": [
            {
                "point": "Candidate shows deep, verified ownership of a production system matching the required distributed-systems skill",
                "evidence_quote": "Designed and implemented a token-bucket based rate-limiting service handling 50k req/s in production.",
                "evidence_source": "resume_claim_0",
            }
        ],
        "unresolved_gaps": ["No evidence available yet on mentoring or team collaboration"],
    },
    "independent:B:Skeptic": {
        "agent": "Skeptic",
        "verdict": "Hire",
        "confidence": 0.7,
        "findings": [
            {
                "point": "No contradiction found between resume claim and transcript detail -- the candidate's account is specific and consistent, including admitting a real bug rather than presenting a flawless narrative",
                "evidence_quote": "we had a race condition in an early version that let a few clients slightly exceed their limit",
                "evidence_source": "transcript_turn_4",
            }
        ],
        "unresolved_gaps": [],
    },
    "B:debate:Technical": {
        "agent": "Technical",
        "responding_to": "HR_Culture",
        "referenced_finding": "Transcript contains no discussion of teamwork or collaboration",
        "stance": "agree",
        "response_text": "Agreed that's outside what I can evaluate, but it doesn't change my technical read -- the depth on the Redis/Lua atomicity fix is a strong, specific signal on its own.",
        "changed_opinion": False,
        "revised_verdict": "Hire",
        "revised_confidence": 0.85,
    },
    "B:debate:HR_Culture": {
        "agent": "HR_Culture",
        "responding_to": "Skeptic",
        "referenced_finding": "Candidate's account is specific and consistent, including admitting a real bug",
        "stance": "partially_agree",
        "response_text": "Willingly admitting a production bug and how it was fixed is a mild positive signal for honesty, which is at least adjacent to my area. I'll move off pure 'Insufficient Info' but I still don't have enough to assess teamwork specifically.",
        "changed_opinion": True,
        "revised_verdict": "Lean Hire",
        "revised_confidence": 0.4,
    },
    "B:debate:HiringManager": {
        "agent": "HiringManager",
        "responding_to": "Technical",
        "referenced_finding": "Candidate demonstrated hands-on debugging of a real concurrency bug",
        "stance": "agree",
        "response_text": "This reinforces my read -- exactly the kind of hands-on ownership this role needs. No change to my verdict, just higher conviction.",
        "changed_opinion": False,
        "revised_verdict": "Hire",
        "revised_confidence": 0.8,
    },
    "B:debate:Skeptic": {
        "agent": "Skeptic",
        "responding_to": "HiringManager",
        "referenced_finding": "Candidate shows deep, verified ownership of a production system",
        "stance": "agree",
        "response_text": "Agreed, and I'll add that the willingness to describe a real bug rather than a polished success-only story is itself evidence against exaggeration, which is specifically what I screen for.",
        "changed_opinion": False,
        "revised_verdict": "Hire",
        "revised_confidence": 0.75,
    },
    "decision:B": {
        "final_recommendation": "Hire",
        "confidence": 0.8,
        "reasoning_steps": [
            "Technical and Skeptic both independently converged on strong, evidence-backed positive findings anchored in specific, verifiable transcript detail (the Lua/Redis atomicity fix), which is weighted heavily under the evidence-quality rule.",
            "The Skeptic explicitly found no resume-vs-transcript contradiction, and treated the candidate volunteering a real bug as a positive honesty signal rather than a flaw -- this lowers the risk of an inflated resume claim.",
            "HR_Culture had insufficient transcript material to assess collaboration and appropriately said so rather than guessing; this is a real gap but not one that overrides the strong technical and integrity signals for this role.",
            "For a Senior Backend Engineer role where required skills are distributed systems, Python, and API design, the Technical and HiringManager findings are most directly relevant and both are strongly positive.",
        ],
        "weighting_rationale": "Technical and Skeptic given the highest weight given specific, verifiable evidence directly tied to required skills; HiringManager weighted for overall role fit; HR_Culture given lower weight here only because it had insufficient material to work with, not because its input was distrusted.",
        "strengths": [
            {
                "point": "Specific, technically sound justification for a core design decision",
                "evidence_quote": "I chose a token-bucket algorithm over a sliding window because we needed to allow short bursts without penalizing steady clients.",
                "source_agent": "Technical",
            },
            {
                "point": "Demonstrated real hands-on debugging under production conditions",
                "evidence_quote": "we had a race condition in an early version that let a few clients slightly exceed their limit. I fixed it by making the whole check atomic in a single script",
                "source_agent": "Skeptic",
            },
        ],
        "concerns": [
            {
                "point": "No transcript evidence available on teamwork, mentoring, or collaboration style",
                "evidence_quote": "Transcript contains no discussion of teamwork, conflict, or feedback -- purely technical Q&A",
                "source_agent": "HR_Culture",
            }
        ],
        "unresolved_disagreements": [],
    },
}
