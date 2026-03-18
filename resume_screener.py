import re
import nltk
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PyPDF2 import PdfReader

# Download stopwords (first time only)
nltk.download('stopwords')
from nltk.corpus import stopwords

stop_words = set(stopwords.words('english'))

# ----------------------------------------------------------------------
# 📄 Extract text from PDF
# ----------------------------------------------------------------------
def extract_text_from_pdf(file_stream):
    try:
        reader = PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

# ----------------------------------------------------------------------
# 🧹 Clean Text
# ----------------------------------------------------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)

# ----------------------------------------------------------------------
# 🔍 Extract Keywords
# ----------------------------------------------------------------------
def extract_keywords(text, top_n=20):
    words = text.split()
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]

# ----------------------------------------------------------------------
# 🎯 Status Label
# ----------------------------------------------------------------------
def get_status(score):
    if score < 40:
        return "Fail"
    elif score < 60:
        return "Pass"
    elif score < 75:
        return "Good"
    else:
        return "Excellent"

# ----------------------------------------------------------------------
# 🤖 Compute Similarity (UPDATED)
# ----------------------------------------------------------------------
def compute_similarity(jd_text, resume_texts, filenames=None):
    try:
        jd_clean = clean_text(jd_text)
        resumes_clean = [clean_text(r) for r in resume_texts]
        corpus = [jd_clean] + resumes_clean

        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform(corpus)
        similarity_matrix = cosine_similarity(vectors[0:1], vectors[1:]).flatten()

        results = []
        jd_keywords = set(extract_keywords(jd_clean, top_n=30))

        for i, score in enumerate(similarity_matrix):
            percentage = round(score * 100, 2)
            resume_words = set(resumes_clean[i].split())
            missing = list(jd_keywords - resume_words)

            item = {
                "score": percentage,             # Changed to 0-100 to match HTML logic
                "status": get_status(percentage),
                "missing_skills": missing[:15]   # Renamed to match HTML variable
            }
            
            # Attach filename BEFORE sorting to prevent mismatch bug
            if filenames:
                item["filename"] = filenames[i]  

            results.append(item)

        # Sort by score (descending)
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Add ranks after sorting
        for idx, r in enumerate(results):
            r['rank'] = idx + 1

        return results

    except Exception as e:
        raise Exception(f"Similarity computation failed: {str(e)}")