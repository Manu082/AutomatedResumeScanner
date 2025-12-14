# parser.py
import os
import re
import docx
import spacy
from spacy.cli import download
from pdfminer.high_level import extract_text
from datetime import datetime


# ---------------- SAFE SPACY LOADER ----------------
def load_spacy_model():
    """
    Loads spaCy model safely for:
    - Local machine
    - Streamlit Cloud
    """
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        print("[parser] spaCy model not found. Downloading...")
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")


nlp = load_spacy_model()
# --------------------------------------------------


def extract_text_from_pdf(filepath: str) -> str:
    try:
        return extract_text(filepath)
    except Exception as e:
        print(f"[parser] PDF extraction failed: {e}")
        return ""


def extract_text_from_docx(filepath: str) -> str:
    try:
        doc = docx.Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        print(f"[parser] DOCX extraction failed: {e}")
        return ""


def extract_email(text: str):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )
    return match.group(0) if match else None


def extract_phone(text: str):
    match = re.search(
        r"(\+?\d{1,3}[-.\s]?)?\d{10}",
        text
    )
    return match.group(0) if match else None


def extract_name(text: str):
    """
    Uses spaCy NER to extract candidate name
    """
    doc = nlp(text[:500])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


def extract_education(text: str):
    edu_keywords = [
        "bachelor", "master", "phd",
        "b.tech", "m.tech", "bsc", "msc",
        "mba", "degree", "diploma"
    ]
    lines = text.split("\n")
    return [
        line.strip()
        for line in lines
        if any(k in line.lower() for k in edu_keywords)
    ]


def extract_experience_years(text: str):
    matches = re.findall(r"(\d{1,2})\+?\s*year", text.lower())
    return max(map(int, matches), default=0)


def extract_skills(text: str, skills_list=None):
    """
    Hybrid Skill Extraction:
    - Keyword matching
    - NLP enrichment
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

        skills_found.update(t for t in tokens if t in common_skills)

        # NLP enrichment
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"]:
                if ent.text.lower() in common_skills:
                    skills_found.add(ent.text.lower())

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
        "skills": extract_skills(text, skills_list),
        "raw_text": text,
        "parsed_at": datetime.now().isoformat()
    }
