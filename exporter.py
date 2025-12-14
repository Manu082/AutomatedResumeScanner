import pandas as pd

def results_to_dataframe(results):
    """Converts the list of result dictionaries into a pandas DataFrame."""
    df = pd.DataFrame(results)
    
    # Reorder columns for a more readable display in Streamlit
    column_order = [
        "name", 
        "score", 
        "experience_years",
        "matched_keywords", 
        "skills", 
        "email", 
        "phone",
        "education"
    ]
    
    # Filter for columns that actually exist to avoid errors
    existing_columns = [col for col in column_order if col in df.columns]
    
    return df[existing_columns]


class CSVExporter:
    def export_to_csv(self, results, filename):
        df = pd.DataFrame(results)
        df = df.sort_values(by='Score', ascending=False)
        df.to_csv(filename, index=False)