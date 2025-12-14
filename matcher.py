# matcher.py
import re
import os
from collections import Counter
from typing import List, Dict
import numpy as np

def normalize_term(t: str):
    return re.sub(r"[^a-z0-9\s\+]", "", t.lower()).strip()

def compute_keyword_match_score(resume_text: str, jd_keywords: List[str], weights: Dict[str, float] = None):
    """
    Compute ATS score:
    - Weighted score if weights provided, else simple % match.
    """
    resume_text_low = resume_text.lower()
    total_keywords = len(jd_keywords)
    if total_keywords == 0:
        return {"score": 0.0, "matched": [], "total": 0}

    matched = []
    weighted_numer = 0.0
    total_weight = 0.0

    for kw in jd_keywords:
        kw_norm = normalize_term(kw)
        weight = 1.0 if not weights else float(weights.get(kw, 1.0))
        total_weight += weight
        if kw_norm and kw_norm in resume_text_low:
            matched.append(kw)
            weighted_numer += weight

    score = (weighted_numer / total_weight * 100) if total_weight else (len(matched)/total_keywords*100)
    return {"score": round(score,2), "matched": matched, "total": total_keywords}

def aggregate_scores_for_jd(resumes: List[dict], jd_keywords: List[str], weights: Dict[str,float] = None):
    """
    Aggregate ATS scores for multiple resumes and sort.
    """
    results = []
    for prof in resumes:
        res_text = prof.get("raw_text", "")
        result = compute_keyword_match_score(res_text, jd_keywords, weights)
        entry = {
            "name": os.path.splitext(prof.get("orig_filename", "Unknown File"))[0],
            "email": prof.get("email"),
            "phone": prof.get("phone"),
            "education": prof.get("education"),
            "experience_years": prof.get("experience_years"),
            "skills": prof.get("skills"),
            "score": result["score"],
            "matched_keywords": result["matched"],
            "file_path": prof.get("file_path")
        }
        results.append(entry)

    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    return results_sorted

def compute_dashboard_stats(results: List[dict]):
    """
    Compute summary stats for a JD:
    - Avg matching %, most common skills, avg experience
    """
    if not results:
        return {"avg_score":0, "common_skills":[], "avg_experience":0}

    avg_score = round(np.mean([r["score"] for r in results]),2)
    all_skills = [skill for r in results if r.get("skills") for skill in r["skills"]]
    
    # Get the top 10 skills and their counts for the chart
    common_skills_counts = Counter(all_skills).most_common(10)
    
    avg_experience = round(np.mean([r["experience_years"] or 0 for r in results]),2)

    return {
        "avg_score": avg_score,
        "common_skills": common_skills_counts, # Return skills with counts
        "avg_experience": avg_experience
    }