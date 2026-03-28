import re
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import nltk

def download_nltk_resources():
    try:
        from nltk.corpus import stopwords
        stopwords.words('english')
    except (ImportError, LookupError):
        nltk.download('stopwords', quiet=True)

# Call once
download_nltk_resources()


# -----------------------------
# Preprocess Text
# -----------------------------
def preprocess_text(text):
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove special characters, numbers
    text = re.sub(r"[^a-zA-Z\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


# -----------------------------
# Generate Tags (Frequency-based for single documents)
# -----------------------------
def generate_tags(text, top_n=5):
    if not text:
        return []

    text = preprocess_text(text)
    if not text:
        return []

    # Get stopwords
    try:
        from nltk.corpus import stopwords
        stop_words = set(stopwords.words('english'))
    except:
        stop_words = set()

    # Split into words and filter
    words = [w for w in text.split() if w not in stop_words and len(w) > 2]
    
    if not words:
        return []

    # Count frequencies
    from collections import Counter
    word_counts = Counter(words)

    # Return top N most common words
    return [word for word, count in word_counts.most_common(top_n)]


# -----------------------------
# Universal Tag Extractor
# -----------------------------
def extract_tags(data, top_n=5):
    """
    Works for:
    - YouTube (transcript + description)
    - Blogs (content + description)
    - PubMed (abstract + title)
    """

    text_parts = []

    # Priority: transcript > content > description
    if data.get("transcript"):
        text_parts.append(data["transcript"])

    if data.get("content"):
        text_parts.append(data["content"])

    if data.get("description"):
        text_parts.append(data["description"])

    # Combine all available text
    combined_text = " ".join(text_parts)

    return generate_tags(combined_text, top_n)