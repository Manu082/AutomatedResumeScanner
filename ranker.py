# ranker.py
import pandas as pd
from ats_score import calculate_ats_score
from jd_parser import extract_jd_keywords

def rank_resumes_against_jds(resume_profiles, jd_list):
    """
    resume_profiles: List of dicts from parser.py
    jd_list: List of job description strings
    Returns: Pandas DataFrame with ranking per JD
    """
    results = []
    for jd_index, jd_text in enumerate(jd_list):
        jd_keywords = extract_jd_keywords(jd_text)
        for profile in resume_profiles:
            ats = calculate_ats_score(profile["raw_text"], jd_keywords)
            results.append({
                "JD #": jd_index + 1,
                "Candidate": profile.get("name", "Unknown"),
                "Email": profile.get("email", ""),
                "Experience": profile.get("experience_years", 0),
                "Skills": ", ".join(profile.get("skills", [])),
                "ATS Score (%)": ats
            })
    return pd.DataFrame(results)

if __name__ == "__main__":
    jd_list = [
        "Looking for Data Scientist with Python, ML, and SQL expertise.",
        "Hiring Web Developer with React, Node.js, and Docker experience."
    ]
    resume_profiles = [
        {"name": "Alice", "email": "alice@test.com", "experience_years": 2,
         "skills": ["Python", "ML", "SQL"], "raw_text": "Python ML SQL projects"},
        {"name": "Bob", "email": "bob@test.com", "experience_years": 3,
         "skills": ["React", "Node.js"], "raw_text": "React Node.js developer"}
    ]
    df = rank_resumes_against_jds(resume_profiles, jd_list)
    print(df)
