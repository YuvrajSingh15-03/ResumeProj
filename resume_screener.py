import nltk
nltk.download('stopwords')
import re
import string
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords

def get_status_class(status: str) -> str:
    """Return CSS class based on status."""
    status_classes = {
        'Fail': 'bg-score-fail',
        'Pass': 'bg-score-pass',
        'Good': 'bg-score-good',
        'Excellent': 'bg-score-excellent'
    }
    return status_classes.get(status, 'bg-score-pass')
# ----------------------------------------------------------------------
# 1️⃣ Text Cleaning
# ----------------------------------------------------------------------
def clean_text(txt: str) -> str:
    """Lowercase, remove punctuation, numbers, and extra whitespace."""
    txt = txt.lower()
    # remove numbers
    txt = re.sub(r'\d+', '', txt)
    # remove punctuation
    txt = txt.translate(str.maketrans('', '', string.punctuation))
    # collapse multiple spaces
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt


def remove_stopwords(txt: str) -> str:
    stop_words = set(stopwords.words('english'))
    words = txt.split()
    filtered = [w for w in words if w not in stop_words]
    return ' '.join(filtered)


def preprocess(txt: str) -> str:
    txt = clean_text(txt)
    txt = remove_stopwords(txt)
    return txt


# ----------------------------------------------------------------------
# 2️⃣ Resume Parsing (PDF)
# ----------------------------------------------------------------------
def extract_text_from_pdf(file_stream) -> str:
    """Extract all text from a PDF file using PyPDF2."""
    import PyPDF2
    reader = PyPDF2.PdfReader(file_stream)
    text = ''
    for page in reader.pages:
        text += page.extract_text() or ''
    return text


# ----------------------------------------------------------------------
# 3️⃣ Scoring & Feedback
# ----------------------------------------------------------------------
def compute_similarity(job_desc: str, resume_texts: list) -> list:
    """
    Returns a list of dicts:
        {
            'resume_name': str,
            'score': float (0‑1),
            'percentage': str,
            'status': str,
            'missing_keywords': list[str]
        }
    """
    # Pre‑process
    jd_clean = preprocess(job_desc)
    resumes_clean = [preprocess(txt) for txt in resume_texts]

    # Edge case: empty JD
    if not jd_clean.strip():
        raise ValueError("Job description is empty.")

    # Build TF‑IDF matrix (fit on JD + all resumes)
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([jd_clean] + resumes_clean)

    # Cosine similarity between JD (row 0) and each resume
    similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Extract vocabulary for missing‑keyword feedback
    jd_vocab = set(vectorizer.transform([jd_clean]).toarray()[0].nonzero()[1])
    # map feature index → word
    feature_names = vectorizer.get_feature_names_out()
    jd_words = set(feature_names[i] for i in jd_vocab)

    results = []
    for idx, sim in enumerate(similarities):
        pct = round(sim * 100, 1)
        # Simple status thresholds (customizable)
        if pct < 30:
            status = "Fail"
        elif pct < 60:
            status = "Pass"
        elif pct < 80:
            status = "Good"
        else:
            status = "Excellent"

        # Compute missing keywords
        resume_vocab = set(tfidf_matrix[idx + 1].toarray()[0].nonzero()[1])
        resume_words = set(feature_names[i] for i in resume_vocab)
        missing = sorted(jd_words - resume_words)[:10]  # top 10 missing

    results.append({
        'resume_name':  f"Resume {idx + 1}",
        'score': sim,
        'percentage': f"{pct}%",
        'percentage_num': round(pct, 1),
        'status': status,
        'status_class': get_status_class(status),
     'missing_keywords': missing
    })

    # Sort by score descending (recruiter view)
    results.sort(key=lambda x: x['score'], reverse=True)

    return results