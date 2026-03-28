import re
from datetime import datetime
import math
from urllib.parse import urlparse

# -----------------------------
# Configuration & Weights
# -----------------------------
# Weights are balanced for academic/professional focus
WEIGHTS = {
    "author": 0.25,
    "domain": 0.25,
    "recency": 0.20,
    "citation": 0.20,
    "disclaimer": 0.10
}

# Trusted Domain Database (High Reputation)
TRUSTED_DOMAINS = {
    "ncbi.nlm.nih.gov", "nature.com", "science.org", 
    "mayoclinic.org", "webmd.com", "cdc.gov", 
    "who.int", "mit.edu", "stanford.edu", "harvard.edu",
    "machinelearningmastery.com", "kdnuggets.com"
}

AUTHOR_EXPERTISE_KEYWORDS = {"phd", "md", "professor", "doctor", "researcher", "scientist", "expert", "editor"}


# -----------------------------
# 1. Author Credibility (Smarter Validation)
# -----------------------------
def calc_author_score(data):
    source_type = data.get("source_type", "blog")
    author = str(data.get("author", "")).lower()
    
    if not author or author == "unknown":
        return 0.3 # Base for anonymous
        
    score = 0.5 # Default for identified author
    
    # 1. Expertise check
    if any(kw in author for kw in AUTHOR_EXPERTISE_KEYWORDS):
        score += 0.3
        
    # 2. Source-specific reputation
    if source_type == "pubmed":
        score += 0.2 # Academic peer-reviewed baseline
    elif source_type == "youtube":
        # Check sub/view ratio (Engagement Quality)
        views = int(data.get("view_count", 1))
        subs = int(data.get("subscriber_count", 0))
        if subs > 0:
            ratio = subs / views
            if ratio > 0.1: # High loyalty/sub count
                score += 0.2
    
    return min(score, 1.0)


# -----------------------------
# 2. Citation Score (Quality-weighted)
# -----------------------------
def calc_citation_score(data):
    source_type = data.get("source_type", "blog")
    links = data.get("outbound_links", [])
    
    if source_type == "pubmed":
        return 0.9 # Hard-coded high for PubMed as it's the gold standard
        
    if not links:
        return 0.4 if source_type == "blog" else 0.5
        
    trusted_count = 0
    for link in links:
        ext_domain = urlparse(link).netloc.lower()
        if any(td in ext_domain for td in TRUSTED_DOMAINS):
            trusted_count += 1
            
    # Score = (2 * Trusted + Neutral) / total
    # This rewards quality over quantity
    total = len(links)
    score = (2.0 * trusted_count + (total - trusted_count)) / (total * 1.5)
    
    return min(max(score, 0.4), 1.0)


# -----------------------------
# 3. Domain Authority (Safe Extraction)
# -----------------------------
def calc_domain_score(url):
    if not url:
        return 0.3
        
    try:
        domain = urlparse(url).netloc.lower()
        if not domain:
            return 0.3
            
        # Exact or suffix match
        if any(domain == td or domain.endswith("." + td) for td in TRUSTED_DOMAINS):
            return 1.0
            
        # TLD Hierarchy
        if domain.endswith((".gov", ".edu")):
            return 1.0
        if domain.endswith(".org"):
            return 0.8
        if domain.endswith((".com", ".net")):
            return 0.6
    except:
        pass
        
    return 0.4


# -----------------------------
# 4. Recency (Exponential Decay)
# -----------------------------
def calc_recency_score(pub_date_str):
    if not pub_date_str or pub_date_str == "unknown":
        return 0.5
        
    try:
        if len(pub_date_str) == 4 and pub_date_str.isdigit():
            pub_date = datetime(int(pub_date_str), 1, 1)
        else:
            pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00")).replace(tzinfo=None)
            
        years_old = (datetime.now() - pub_date).days / 365.25
        
        # Exponential Decay: exp(-k * t)
        # k=0.4: 1yr ~ 0.67, 5yr ~ 0.13
        score = math.exp(-0.4 * years_old)
        return max(score, 0.05)
    except:
        return 0.5


# -----------------------------
# 5. Context-Aware Disclaimer
# -----------------------------
def calc_disclaimer_score(data, full_text):
    # Detect if content is medical/health related
    medical_keywords = {"health", "medical", "disease", "treatment", "cure", "doctor", "clinical", "surgery"}
    text_words = set(full_text.lower().split())
    
    is_medical = any(kw in text_words for kw in medical_keywords)
    
    # regex for common disclaimer patterns
    patterns = [r"not medical advice", r"consult (a|your) doctor", r"for educational purposes", r"disclaimer"]
    has_disclaimer = any(re.search(p, full_text.lower()) for p in patterns)
    
    if is_medical:
        return 1.0 if has_disclaimer else 0.2 # Heavy penalty for medical lack of disclaimer
    
    return 1.0 # Optional for non-medical


# -----------------------------
# 6. Abuse Prevention & Quality Metrics
# -----------------------------
def calc_quality_metrics(full_text, data):
    if not full_text or len(full_text.split()) < 50:
        return 1.0
        
    words = full_text.lower().split()
    unique_words = set(words)
    total_words = len(words)
    
    # 1. Lexical Diversity (Anti-Spam)
    diversity = len(unique_words) / total_words
    diversity_penalty = 0.0
    if diversity < 0.3: # Too repetitive, possibly keyword stuffed
        diversity_penalty = 0.3
        
    # 2. Link Density (Anti-Link Farm)
    links = data.get("outbound_links", [])
    link_density = len(links) / (total_words / 100) # Links per 100 words
    density_penalty = 0.0
    if link_density > 5.0: # More than 5 links per 100 words is suspicious
        density_penalty = 0.2
        
    return 1.0 - (diversity_penalty + density_penalty)


# -----------------------------
# MAIN CALCULATION FUNCTION
# -----------------------------
def calculate_trust_score(data):
    """
    Academic-refactored trust score.
    Refines rules, handles uncertainty, and prevents manipulation.
    """
    # Build full text for analysis
    full_text = " ".join([
        str(data.get("title", "")),
        str(data.get("description", "")),
        str(data.get("abstract", "")),
        str(data.get("content", "")),
        str(data.get("transcript", ""))
    ])
    
    # Component Scores
    s_author = calc_author_score(data)
    s_citation = calc_citation_score(data)
    s_domain = calc_domain_score(data.get("source_url", ""))
    s_recency = calc_recency_score(data.get("published_date", ""))
    s_disclaimer = calc_disclaimer_score(data, full_text)
    
    # Weighted Sum
    raw_score = (
        (s_author * WEIGHTS["author"]) +
        (s_domain * WEIGHTS["domain"]) +
        (s_recency * WEIGHTS["recency"]) +
        (s_citation * WEIGHTS["citation"]) +
        (s_disclaimer * WEIGHTS["disclaimer"])
    )
    
    # Apply Quality Multiplier (Abuse prevention)
    quality_mult = calc_quality_metrics(full_text, data)
    final_score = raw_score * quality_mult
    
    # Uncertainty Penalty (Internal transparency check)
    # If key data is missing, we trust it less
    if data.get("author") == "unknown" or data.get("published_date") == "unknown":
        final_score *= 0.7
        
    return round(min(max(final_score, 0.0), 1.0), 2)


