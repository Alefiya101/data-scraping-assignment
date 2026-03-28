import requests
import re
import json
from bs4 import BeautifulSoup
from langdetect import detect


# -----------------------------
# Extract PMID from URL
# -----------------------------
def extract_pmid(url):
    """
    Extract the PubMed ID (PMID) from a PubMed URL.
    Examples:
    - https://pubmed.ncbi.nlm.nih.gov/35921606/ -> 35921606
    - https://pubmed.ncbi.nlm.nih.gov/35921606 -> 35921606
    """
    if "pubmed.ncbi.nlm.nih.gov/" in url:
        parts = url.split("pubmed.ncbi.nlm.nih.gov/")[1].split("/")
        pmid = parts[0]
        if pmid.isdigit():
            return pmid
    
    # Fallback: find any digit sequence longer than 4 chars
    match = re.search(r"(\d{5,10})", url)
    if match:
        return match.group(1)
        
    return None


# -----------------------------
# Fetch PubMed Data (XML)
# -----------------------------
def fetch_pubmed_data(pmid):
    """
    Fetch article metadata and abstract from NCBI E-utilities (EFetch).
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": pmid,
        "retmode": "xml"
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error fetching PubMed data for PMID {pmid}: {e}")
        return None


# -----------------------------
# Parse PubMed XML
# -----------------------------
def parse_pubmed_xml(xml_content):
    """
    Extract Title, Authors, Journal, Abstract, and PubDate from XML.
    """
    if not xml_content:
        return None
        
    soup = BeautifulSoup(xml_content, "xml")
    
    # Title
    article = soup.find("Article")
    title_text = "Title not available"
    if article:
        title = article.find("ArticleTitle")
        if title:
            title_text = title.get_text()
    
    # Authors
    authors = []
    author_list = soup.find_all("Author")
    for author in author_list:
        last_name = author.find("LastName")
        fore_name = author.find("ForeName")
        initials = author.find("Initials")
        
        if last_name:
            ln = last_name.get_text()
            fn = fore_name.get_text() if fore_name else (initials.get_text() if initials else "")
            authors.append(f"{ln} {fn}".strip())
            
    author_str = ", ".join(authors) if authors else "Author unknown"
    
    # Journal
    journal = soup.find("Journal")
    journal_text = "Journal unknown"
    if journal:
        j_title = journal.find("Title")
        if j_title:
            journal_text = j_title.get_text()
    
    # Publication Year
    pub_date = soup.find("PubDate")
    year = "unknown"
    if pub_date:
        year_tag = pub_date.find("Year")
        if year_tag:
            year = year_tag.get_text()
        else:
            # Fallback for MedlineDate format
            medline_date = pub_date.find("MedlineDate")
            if medline_date:
                match = re.search(r"(\d{4})", medline_date.get_text())
                if match:
                    year = match.group(1)
    
    # Abstract
    abstract_sections = soup.find_all("AbstractText")
    abstract_parts = []
    
    for section in abstract_sections:
        label = section.get("Label")
        text = section.get_text(strip=True)
        if label:
            abstract_parts.append(f"{label}: {text}")
        else:
            abstract_parts.append(text)
            
    if abstract_parts:
        abstract_text = "\n".join(abstract_parts)
    else:
        # Fallback for plain Abstract tag
        abstract_tag = soup.find("Abstract")
        abstract_text = abstract_tag.get_text(strip=True) if abstract_tag else "Abstract not available"
        
    return {
        "title": title_text,
        "author": author_str,
        "journal": journal_text,
        "published_date": year,
        "abstract": abstract_text
    }


# -----------------------------
# Detect Language
# -----------------------------
def detect_language(text):
    if not text or text == "Abstract not available":
        return "en"
    try:
        return detect(text)
    except:
        return "en"


# -----------------------------
# MAIN SCRAPER FUNCTION
# -----------------------------
def scrape_pubmed(url):
    """
    Main entry point for PubMed scraping.
    """
    pmid = extract_pmid(url)
    if not pmid:
        print(f"Invalid PubMed URL: {url}")
        return None
        
    xml_content = fetch_pubmed_data(pmid)
    data = parse_pubmed_xml(xml_content)
    
    if not data:
        return None
        
    # Language detection
    language = detect_language(data["abstract"][:1000])
    
    # Final structured output matching schema
    result = {
        "source_url": url,
        "source_type": "pubmed",
        "author": data["author"],
        "published_date": data["published_date"],
        "language": language,
        "region": "Global",
        "title": data["title"],
        "journal": data["journal"],
        "abstract": data["abstract"],
        
        # Placeholders for integration in main script
        "topic_tags": [],
        "trust_score": None,
        "content_chunks": []
    }
    
    return result


