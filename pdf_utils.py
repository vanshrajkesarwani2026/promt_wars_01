"""PDF text extraction utilities."""
from __future__ import annotations
from pathlib import Path

import pdfplumber


def extract_pdf_text(path: str | Path) -> str:
    """Extract plain text from a PDF, preserving page breaks."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n\n".join(pages).strip()
