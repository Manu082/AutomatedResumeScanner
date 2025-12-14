from parser import ResumeParser
from matcher import KeywordMatcher
from exporter import CSVExporter
import os

def load_job_description(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    resumes_folder = "resumes/"
    job_desc_file = "job_description.txt"
    output_csv = "ranked_candidates.csv"

    jd_text = load_job_description(job_desc_file)
    matcher = KeywordMatcher(jd_text)
    parser = ResumeParser()
    results = []

    for filename in os.listdir(resumes_folder):
        if filename.lower().endswith(('.pdf', '.docx')):
            filepath = os.path.join(resumes_folder, filename)
            print(f"Parsing: {filename}")
            text = parser.parse_resume(filepath)
            score = matcher.match_score(text)
            results.append({'FileName': filename, 'Score': score})

    exporter = CSVExporter()
    exporter.export_to_csv(results, output_csv)
    print(f"\nRanking complete. Results saved to {output_csv}")

if __name__ == "__main__":
    main()

