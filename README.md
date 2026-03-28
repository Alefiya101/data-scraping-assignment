# Multi-Source Academic Trust Pipeline: Technical Specification and Documentation

## Project Overview
The Academic Trust Pipeline is a centralized Python system designed to extract, analyze, and evaluate the credibility of data from three distinct digital sources: Academic Journals (PubMed), social media platforms (YouTube), and professional blog environments. The system implements a rigorous "Scrape-Enrich-Score" architecture to provide a unified data schema across disparate information streams.

---

## Technical Architecture

### 1. Data Acquisition Phase
The system utilizes specialized scraping drivers tailored to the unique technical constraints of each source:
- **YouTube Driver**: Employs direct caption extraction for rapid text retrieval and the Google API for harvesting high-fidelity engagement metrics.
- **Blog Driver**: Leverages advanced article parsing libraries combined with structural HTML fallbacks to ensure content integrity despite modern web obfuscation (e.g., paywalls or dynamic script loading).
- **PubMed Driver**: Interfaces directly with the NCBI E-Utilities API, ensuring that academic metadata is sourced directly from verified institutional databases rather than interpreted HTML.

### 2. Scholastic Enrichment Phase
Once acquired, the raw data undergoes automated processing via:
- **Lexical Chunking**: Strategic text segmentation designed to facilitate downstream natural language analysis or large-scale indexing.
- **Automated Metadata Tagging**: A keyword-based heuristic system that classifies content by topic (e.g., Medicine, Machine Learning, Nutrition) to enable efficient retrieval.

### 3. Trust Evaluation Phase
Each data entry is assigned a "Trust Score" (normalized between 0.0 and 1.0) calculated via a weighted multi-factor algorithm defined in the scoring module.

---

## Library Selection and Justification

### newspaper3k
Used within the blog scraping module to provide specialized article body extraction. Unlike general-purpose HTML parsers, this library is specifically tuned to identify the core narrative of a webpage while discarding non-relevant elements such as advertisements, navigation structures, and sidebar content.

### youtube-transcript-api
Integrated into the YouTube module to facilitate the high-speed retrieval of video captions. This library operates headlessly, avoiding the performance overhead and stability issues associated with standard browser automation (e.g., Selenium).

### google-api-python-client
Utilized for the retrieval of secondary video metadata. This information, specifically view counts and subscriber-to-view ratios, is a critical input for the trust scoring algorithm's evaluation of channel reputation and viewer loyalty.

### BeautifulSoup4
Employed as the primary structural parser across all modules. It provides the granular control necessary for extracting specific metadata (e.g., Dublin Core tags, OpenGraph data, or XML nodes from PubMed) where automated libraries may fail to capture nuanced details.

### requests
Serving as the fundamental communication layer of the application. It ensures synchronous, reliable HTTP interaction with web servers and APIs, providing the stability required for bulk data extraction.

### langdetect
Implemented as a quality control gate within the utility layer. It verifies that the extracted content is in a supported language, thereby preventing linguistic noise from skewing the scoring or tagging results.

---

## Trust Scoring Methodology and Weights

The trust scoring engine evaluates information based on five primary dimensions:

- **Author Expertise (25%)**: Evaluates professional credentials (e.g., MD, PhD) and historical engagement metrics to determine the creator's authority on the subject matter.
- **Domain Authority (25%)**: Prioritizes institutional domains (.gov, .edu) and a curated database of high-reputation publishers (e.g., Nature, CDC, Mayo Clinic).
- **Temporal Recency (20%)**: Employs an exponential decay function to penalize older content, ensuring that time-sensitive scientific information remains relevant.
- **Citation Fidelity (20%)**: Analyzes outbound link structures to reward sources that cite other high-authority research or publications.
- **Medical Safety Compliance (10%)**: A critical safety check for health-related content, rewarding the presence of professional medical disclaimers and penalizing their absence.

---

## Robustness and Edge Case Handling

- **Unfinished Metadata Handling**: In instances where critical fields such as "Author" or "Publish Date" are absent, the system assigns an automatic 30% penalty to the final trust score, accounting for the lack of transparency.
- **Abusive Link Detection**: The engine calculates "Link Density" (links per 100 words). If this ratio exceeds professional standards, the source is flagged as a potential "link farm" and suppressed.
- **Medical Keyword Sensitivity**: The algorithm dynamically identifies medically-sensitive topics. For these entries, the absence of a disclaimer triggers a severe penalty to mitigate the risk of health misinformation.
- **Lexical Diversity Analysis**: The system detects potential "keyword stuffing" or spam-like repetitions by evaluating the ratio of unique terms to total word count.
- **Parser Fallback Strategies**: The blog scraper implements a hierarchical search pattern, moving from high-level article scrapers to manual "article" or "main" tag extraction if the primary method is obstructed by dynamic content.
