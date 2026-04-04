import json
import subprocess


def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file using pdftotext (poppler).

    Falls back to reading as plain text if pdftotext is not available.
    """
    try:
        result = subprocess.run(
            ["pdftotext", file_path, "-"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass

    # Fallback: try reading as text (for .txt resumes)
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    except Exception:
        return ""


def parse_resume(file_path: str) -> dict:
    """Parse a resume file into structured sections.

    Returns a dict with raw text and basic section detection.
    Full LLM-powered parsing can be added later.
    """
    text = extract_text_from_pdf(file_path)

    return {
        "raw_text": text,
        "sections": detect_sections(text),
    }


def detect_sections(text: str) -> dict:
    """Basic keyword-based section detection.

    Looks for common resume headings and splits text accordingly.
    """
    section_keywords = {
        "education": ["education", "academic"],
        "experience": ["experience", "work history", "employment"],
        "skills": ["skills", "technical skills", "technologies"],
        "projects": ["projects", "project experience"],
    }

    lines = text.split("\n")
    current_section = "header"
    sections = {"header": []}

    for line in lines:
        line_lower = line.strip().lower()
        matched = False
        for section_name, keywords in section_keywords.items():
            if any(kw in line_lower for kw in keywords) and len(line.strip()) < 50:
                current_section = section_name
                sections[current_section] = []
                matched = True
                break
        if not matched:
            sections.setdefault(current_section, []).append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}
