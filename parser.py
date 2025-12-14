# parser.py
import os
import re
import docx
import spacy
import subprocess
import sys
from pdfminer.high_level import extract_text
from datetime import datetime


# -------- SAFE SPACY LOADER (LOCAL + STREAMLIT CLOUD) --------
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        print("[parser] spaCy model not found. Downloading en_core_web_sm...")
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            check=True
        )
        return spacy.load("en_core_web_sm")


nlp = load_spacy_model()
# ------------------------------------------------------------


def extract_text_from_pdf(filepath: str) -> str:
    try:
        return extract_text(filepath)
    except Exception as e:
        print(f"[parser] PDF extraction failed: {e}")
        return ""


def extract_text_from_docx(filepath: str) -> str:
    try:
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"[parser] DOCX extraction failed: {e}")
        return ""


def extract_email(text: str):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text
    )
    return match.group(0) if match else None


def extract_phone(text: str):
    match = re.search(
        r"(\+?\d{1,3}[-.\s]?)?\d{10}", text
    )
    return match.group(0) if match else None


def extract_name(text: str):
    doc = nlp(text[:500])  # First 500 chars usually contain name
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


def extract_education(text: str):
    edu_keywords = [
        "bachelor", "master", "phd", "b.tech", "m.tech",
        "bsc", "msc", "mba", "degree", "diploma"
    ]
    lines = text.split("\n")
    return [
        l.strip() for l in lines
        if any(k in l.lower() for k in edu_keywords)
    ]


def extract_experience_years(text: str):
    matches = re.findall(r"(\d{1,2})\+?\s*year", text.lower())
    return max([int(m) for m in matches], default=0) if matches else 0


def extract_skills(text: str, skills_list=None):
    """
    Hybrid skill extraction:
    - Keyword-based matching
    - spaCy NLP fallback
    """
    skills_found = set()
    text_lower = text.lower()

    if skills_list:
        for skill in skills_list:
            if skill.lower() in text_lower:
                skills_found.add(skill)
    else:
        tokens = re.findall(r"[A-Za-z\+\#]{2,}", text_lower)
        common_skills = {
            "python", "java", "c++", "sql", "html", "css", "javascript",
            "react", "node", "docker", "aws", "ml", "ai",
            "tensorflow", "pytorch", "flask", "django", "fastapi"
        }

        skills_found.update({t for t in tokens if t in common_skills})

        # NLP-based enrichment
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"]:
                ent_text = ent.text.lower()
                if ent_text in common_skills:
                    skills_found.add(ent_text)

    return sorted(skills_found)


def parse_resume(filepath: str, skills_list=None):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(filepath)
    elif ext in [".docx", ".doc"]:
        text = extract_text_from_docx(filepath)
    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return {
        "file_path": filepath,
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "education": extract_education(text),
        "experience_years": extract_experience_years(text),
        "skills": extract_skills(text, skills_list=skills_list),
        "raw_text": text,
        "parsed_at": datetime.now().isoformat()
    }
