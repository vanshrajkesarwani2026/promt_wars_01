"""CLI entry point.

Usage:
  # Demo/test the orchestration with zero API calls and no PDFs needed:
  python main.py --mock

  # Real run against your documents (requires ANTHROPIC_API_KEY env var):
  python main.py --live \\
      --job-desc 02_Job_Description.pdf \\
      --resume-a 03_Resume_A.pdf --transcript-a 05_Transcript_A.pdf \\
      --resume-b 04_Resume_B.pdf --transcript-b 06_Transcript_B.pdf \\
      --out-dir reports/
"""
from __future__ import annotations

import argparse
from pathlib import Path

from panel.llm_client import LLMClient
from panel.mock_data import MOCK_RESPONSES
from panel.pdf_utils import extract_pdf_text
from panel.pipeline import run_pipeline_for_candidate
from panel.report import render_comparison, render_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Agent AI Interview Panel Simulator")
    parser.add_argument("--mock", action="store_true", help="Run with canned responses, no API key or PDFs needed")
    parser.add_argument("--live", action="store_true", help="Run against the real Anthropic API")
    parser.add_argument("--job-desc", type=str, help="Path to job description PDF")
    parser.add_argument("--resume-a", type=str, help="Path to candidate A's resume PDF")
    parser.add_argument("--transcript-a", type=str, help="Path to candidate A's transcript PDF")
    parser.add_argument("--resume-b", type=str, help="Path to candidate B's resume PDF")
    parser.add_argument("--transcript-b", type=str, help="Path to candidate B's transcript PDF")
    parser.add_argument("--out-dir", type=str, default="reports", help="Directory to write reports to")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mock:
        client = LLMClient(mode="mock", mock_responses=MOCK_RESPONSES)
        # In mock mode the document text is irrelevant -- canned responses
        # are keyed by candidate id, not by content -- but we pass
        # placeholders through so the pipeline code path is identical to live.
        job_text = resume_a = transcript_a = resume_b = transcript_b = "(mock mode: unused)"
    elif args.live:
        if not all([args.job_desc, args.resume_a, args.transcript_a, args.resume_b, args.transcript_b]):
            parser.error("--live requires --job-desc, --resume-a, --transcript-a, --resume-b, --transcript-b")
        client = LLMClient(mode="live")
        job_text = extract_pdf_text(args.job_desc)
        resume_a = extract_pdf_text(args.resume_a)
        transcript_a = extract_pdf_text(args.transcript_a)
        resume_b = extract_pdf_text(args.resume_b)
        transcript_b = extract_pdf_text(args.transcript_b)
    else:
        parser.error("Pass either --mock or --live")
        return

    results = []
    for key, resume_text, transcript_text in [
        ("A", resume_a, transcript_a),
        ("B", resume_b, transcript_b),
    ]:
        print(f"Running pipeline for candidate {key}...")
        result = run_pipeline_for_candidate(
            client, job_text, resume_text, transcript_text, candidate_key=key
        )
        results.append(result)

        report_text = render_report(result)
        out_path = out_dir / f"candidate_{key}_report.md"
        out_path.write_text(report_text)
        print(f"  -> wrote {out_path}")

    comparison_text = render_comparison(results)
    comparison_path = out_dir / "comparison.md"
    comparison_path.write_text(comparison_text)
    print(f"  -> wrote {comparison_path}")


if __name__ == "__main__":
    main()
