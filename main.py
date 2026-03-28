import json
import os
import sys
from scraper.blog_scraper import scrape_blog
from scraper.youtube_scraper import scrape_youtube
from scraper.pubmed_scraper import scrape_pubmed
from utils.tagging import extract_tags
from utils.chunking import chunk_text
from scoring.trust_score import calculate_trust_score

# -----------------------------
SOURCES = [
    # 3 Blog/Article Posts
    {"url": "https://en.wikipedia.org/wiki/Machine_learning", "type": "blog"},
    {"url": "https://en.wikipedia.org/wiki/Blueberry", "type": "blog"},
    {"url": "https://www.chess.com/article/view/10-opening-traps-that-work", "type": "blog"},
    
    # 2 YouTube Videos 
    {"url": "https://www.youtube.com/watch?v=R9OHn5ZF4Uo", "type": "youtube"},
    {"url": "https://www.youtube.com/watch?v=orQKfIXMiA8", "type": "youtube"},
    
    # 1 PubMed Article 
    {"url": "https://pubmed.ncbi.nlm.nih.gov/30206133/", "type": "pubmed"},
]


def process_source(source):
    url = source["url"]
    stype = source["type"]
    
    print(f"\n[*] Processing [{stype.upper()}]: {url}")
    
    # 1. Scraping Phase
    try:
        if stype == "blog":
            data = scrape_blog(url)
        elif stype == "youtube":
            data = scrape_youtube(url)
        elif stype == "pubmed":
            data = scrape_pubmed(url)
        else:
            print(f"[-] ERROR: Unsupported type {stype}")
            return None
            
        if not data:
            print(f"[-] ERROR: Scraper returned null for {url}")
            return None
            
    except Exception as e:
        print(f"[-] CRITICAL ERROR during scraping {url}: {e}")
        return None

    # 2. Tagging & Enrichment
    try:
        data["topic_tags"] = extract_tags(data)
        
        # Determine content for chunking
        content_body = data.get("content") or data.get("transcript") or data.get("abstract") or data.get("description", "")
        data["content_chunks"] = chunk_text(content_body) if content_body else []
        
        # 3. Refined Trust Scoring
        data["trust_score"] = calculate_trust_score(data)
        
        print(f"[+] SUCCESS: Trust Score = {data['trust_score']}")
    except Exception as e:
        print(f"[-] ERROR during enrichment for {url}: {e}")
        return None
        
    # 4. Schema Mapping (Consise output)
    schema_keys = [
        "source_url", "source_type", "author", "published_date", 
        "language", "region", "topic_tags", "trust_score", "content_chunks",
        "transcript", "content", "description"
    ]
    
    return {k: data.get(k, "unknown") for k in schema_keys}


def main():
    print("[*] Starting Academic Trust Pipeline...")
    results = []
    
    for source in SOURCES:
        data = process_source(source)
        if data:
            results.append(data)
            print(f"[+] Successfully processed: {source['url']}")
        else:
            print(f"[!] FAILED to process: {source['url']}")

    print(f"\n[*] Pipeline Complete. Processed {len(results)}/{len(SOURCES)} sources.")
    out_path = "output/scraped_data.json"
    
    # Save Results
    os.makedirs("output", exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"[!] Successfully processed: {len(results)}/6 sources")
    print(f"[!] Output saved to: {out_path}")


if __name__ == "__main__":
    main()
