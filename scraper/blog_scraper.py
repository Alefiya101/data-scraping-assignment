import json
import requests
import re
from bs4 import BeautifulSoup
from newspaper import Article
from langdetect import detect
from urllib.parse import urlparse


# -----------------------------
# Detect Language
# -----------------------------
def detect_language(text):
    if not text:
        return "unknown"
    try:
        return detect(text)
    except:
        return "unknown"


# -----------------------------
# AUTHOR EXTRACTION (BeautifulSoup ONLY)
# -----------------------------
def extract_author_bs(url, html=None):
    try:
        if not html:
            html = requests.get(url, timeout=10).text

        soup = BeautifulSoup(html, "html.parser")

        # 1. META TAGS
        meta_tags = [
            {"name": "author"},
            {"property": "article:author"},
            {"name": "parsely-author"},
            {"name": "twitter:creator"}
        ]

        for tag_attrs in meta_tags:
            tag = soup.find("meta", tag_attrs)
            if tag and tag.get("content"):
                return tag.get("content").strip()

        # 2. JSON-LD
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    author = data.get("author")
                    if isinstance(author, dict) and "name" in author:
                        return author["name"]
                    elif isinstance(author, list):
                        names = [a.get("name") for a in author if "name" in a]
                        if names:
                            return ", ".join(names)
            except:
                continue

        # 3. CLASS / ID BASED
        candidates = soup.find_all(
            attrs={
                "class": lambda x: x and any(k in x.lower() for k in ["author", "byline", "writer"])
            }
        )

        for tag in candidates:
            text = tag.get_text(strip=True)
            if text and len(text) < 100:
                return text

        # 4. REGEX FALLBACK
        text = soup.get_text(" ", strip=True)
        match = re.search(r"by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
        if match:
            return match.group(1)

    except:
        pass

    return "unknown"


# -----------------------------
# MAIN SCRAPER
# -----------------------------
def scrape_blog(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 1. Try Newspaper
        article = Article(url, fetch_images=False)
        # newspaper Article doesn't take headers in constructor directly for download easily in some versions
        # but we can try to download via requests first
        html_content = requests.get(url, headers=headers, timeout=15).text
        article.set_html(html_content)
        article.parse()

        content = article.text
        title = article.title
        
        # Fallback to BeautifulSoup if content is too short (possible paywall/JS issue)
        soup = BeautifulSoup(html_content, "html.parser")
        if len(content) < 200:
            # Try to grab common article bodies
            body_tag = soup.find("article") or soup.find("main") or soup.find("div", {"class": "article-body"})
            if body_tag:
                content = body_tag.get_text(" ", strip=True)
                
        # Extract outbound links
        links = soup.find_all("a", href=True)
        outbound_links = list(set([l['href'] for l in links if l['href'].startswith("http") and urlparse(url).netloc not in l['href']]))

        author = extract_author_bs(url, html_content)
        publish_date = article.publish_date.strftime("%Y-%m-%d") if article.publish_date else "unknown"
        language = article.meta_lang if article.meta_lang else detect_language(content[:500])

        result = {
            "source_url": url,
            "source_type": "blog",
            "author": author,
            "published_date": publish_date,
            "language": language,
            "region": "unknown",
            "title": title or "unknown",
            "description": article.meta_description if article.meta_description else "unknown",
            "content": content,
            "outbound_links": outbound_links,
            "link_count": len(outbound_links),
            "html": html_content # keep for debugging if needed
        }

        return result

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None