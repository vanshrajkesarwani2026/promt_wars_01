# Multi-Agent AI Interview Panel Simulator

Reads a job description, resume, and interview transcript for a candidate,
runs 4 independent AI agent personas over it, has them debate, and reaches
a reasoned (not averaged) hire/no-hire recommendation with a full evidence
trail.

See `interview_panel_design.md` (in the parent deliverable) for the full
architecture writeup and prompt rationale. This is the implementation.

## Pipeline

```
PDFs → Profile Builder → 4 Independent Agents → Debate → Decision Agent → Report
```

- **Profile Builder**: pure extraction (no judgment) into a shared JSON profile
  every agent reads from.
- **4 Independent Agents** (Technical, HR_Culture, HiringManager, Skeptic):
  run as 4 *separate* LLM calls in parallel. None sees another's output —
  this is enforced structurally in `panel/agents.py`, not just by prompt wording.
- **Debate**: a second, sequential pass where each agent sees everyone's
  independent opinion (and the debate so far) and must directly respond to
  a specific point from another agent. Every `changed_opinion: true/false`
  is logged.
- **Decision Agent**: one more LLM call that reasons step-by-step over the
  post-debate positions — explicitly not an average of the 4 confidence
  scores. Surfaces any disagreement debate didn't resolve.
- **Report**: deterministic templating (no LLM call) over the final decision
  + full opinion/debate history.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # only needed for --live
```

## Usage

### Try it instantly, no API key or PDFs needed

```bash
python main.py --mock
```

This runs the full pipeline with deterministic canned LLM responses (see
`panel/mock_data.py`) so you can see the whole orchestration — including a
real debate-driven opinion change — end to end. Reports are written to
`reports/`.

### Real run against your documents

```bash
python main.py --live \
  --job-desc 02_Job_Description.pdf \
  --resume-a 03_Resume_A.pdf --transcript-a 05_Transcript_A.pdf \
  --resume-b 04_Resume_B.pdf --transcript-b 06_Transcript_B.pdf \
  --out-dir reports/
```

Requires `ANTHROPIC_API_KEY` in your environment. Outputs
`candidate_A_report.md`, `candidate_B_report.md`, and `comparison.md`.

## Project layout

```
main.py                    CLI entry point
panel/
  schemas.py                Pydantic models for every pipeline boundary
  prompts.py                All system prompts (profile builder, 4 agents, debate, decision)
  llm_client.py              Anthropic API wrapper w/ JSON validation + 1 retry; also mock mode
  pdf_utils.py                PDF text extraction
  profile_builder.py          Stage 1
  agents.py                   Stage 2 (parallel, isolated)
  debate.py                    Stage 3 (sequential, cumulative)
  decision.py                   Stage 4 (reasoning, not averaging)
  report.py                      Stage 5 (templating)
  pipeline.py                     Orchestrates stages 1-4 for one candidate
  mock_data.py                    Canned responses for --mock
```

## Extending

- **Voice debate (bonus)**: wire `debate.py`'s output through a TTS API,
  one voice per agent persona, to narrate the debate log.
- **More debate rounds**: `run_debate_round` can be called again with the
  post-debate opinions as the new "independent" input if you want deeper
  back-and-forth before the Decision Agent runs.
- **Different role weighting**: `prompts.py`'s `DECISION_PROMPT` is where
  to adjust how agent relevance is weighted per role type.
