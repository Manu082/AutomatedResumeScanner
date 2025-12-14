# ats_score.py
def calculate_ats_score(resume_text, jd_keywords):
    """
    ATS Score = (Matched Keywords / Total JD Keywords) * 100
    """
    resume_text_lower = resume_text.lower()
    matched = [kw for kw in jd_keywords if kw.lower() in resume_text_lower]
    if not jd_keywords:
        return 0
    return round((len(matched) / len(jd_keywords)) * 100, 2)

if __name__ == "__main__":
    jd_keywords = ["python", "flask", "sql", "docker", "cloud"]
    resume_text = "I am a Python Developer skilled in Flask, SQL, and Docker."
    print("ATS Score:", calculate_ats_score(resume_text, jd_keywords))
