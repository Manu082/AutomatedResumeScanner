import json
from typing import List, Dict

def load_job_profiles(filepath: str = 'job_profiles.json') -> Dict:
    """Loads the job profiles from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def recommend_job(resume_skills: List[str]) -> Dict:
    """
    Recommends a job title based on the skills extracted from a resume.
    """
    job_profiles = load_job_profiles()
    if not job_profiles:
        return {"best_match": "No job profiles found.", "score": 0}

    best_match_job = None
    highest_score = -1

    resume_skills_set = set(s.lower() for s in resume_skills)

    for job_title, required_skills in job_profiles.items():
        required_skills_set = set(s.lower() for s in required_skills)
        
        # Calculate the number of matching skills
        matching_skills = resume_skills_set.intersection(required_skills_set)
        
        # Calculate a match score (percentage of required skills met)
        if required_skills_set:
            score = (len(matching_skills) / len(required_skills_set)) * 100
        else:
            score = 0

        if score > highest_score:
            highest_score = score
            best_match_job = job_title
            
    return {"best_match": best_match_job, "score": round(highest_score, 2)}