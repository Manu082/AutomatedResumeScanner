# jd_parser.py
import re, string
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from keybert import KeyBERT
    keybert_model = KeyBERT()
except:
    keybert_model = None

def clean_text(text):
    text = text.lower()
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_keywords(jd_text, method="tfidf", top_n=15):
    cleaned = clean_text(jd_text)
    if method=="keybert" and keybert_model:
        keywords = keybert_model.extract_keywords(cleaned, keyphrase_ngram_range=(1,2), stop_words="english", top_n=top_n)
        return [kw[0] for kw in keywords]
    else:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([cleaned])
        scores = zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0])
        sorted_keywords = sorted(scores, key=lambda x:x[1], reverse=True)
        return [word for word, score in sorted_keywords[:top_n]]
