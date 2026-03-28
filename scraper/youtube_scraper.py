import requests
from youtube_transcript_api import YouTubeTranscriptApi
from langdetect import detect
import re
import json

API_KEY = "AIzaSyCnB5aTEDTe06fn1pZyGX_rL76j0vRe9NU"


# -----------------------------
# Extract Video ID
# -----------------------------
def extract_video_id(url):
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1]
    return None


# -----------------------------
# Get Metadata
# -----------------------------
def get_video_metadata(video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "snippet,statistics",
        "id": video_id,
        "key": API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("HTTP Error:", response.status_code)
        return None

    data = response.json()
    if "items" not in data or len(data["items"]) == 0:
        return None

    video = data["items"][0]
    snippet = video["snippet"]
    stats = video.get("statistics", {})
    channel_id = snippet.get("channelId")

    # Fetch channel stats (for subscribers)
    sub_count = 0
    if channel_id:
        channel_url = "https://www.googleapis.com/youtube/v3/channels"
        c_params = {"part": "statistics", "id": channel_id, "key": API_KEY}
        c_res = requests.get(channel_url, params=c_params)
        if c_res.status_code == 200:
            c_data = c_res.json()
            if "items" in c_data and len(c_data["items"]) > 0:
                sub_count = int(c_data["items"][0]["statistics"].get("subscriberCount", 0))

    # Extract links from description
    description = snippet.get("description", "")
    outbound_links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', description)

    return {
        "author": snippet.get("channelTitle"),
        "published_date": snippet.get("publishedAt"),
        "title": snippet.get("title"),
        "description": description,
        "language": snippet.get("defaultAudioLanguage"),
        "region": snippet.get("defaultLanguage"),
        "view_count": int(stats.get("viewCount", 0)),
        "like_count": int(stats.get("likeCount", 0)),
        "comment_count": int(stats.get("commentCount", 0)),
        "subscriber_count": sub_count,
        "outbound_links": outbound_links
    }


# -----------------------------
# Get Transcript
# -----------------------------
def get_transcript(video_id):
    try:
        # Compatibility check for different library versions
        try:
            return YouTubeTranscriptApi.get_transcript(video_id)
        except AttributeError:
            # Fallback for versions where get_transcript is not directly available
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en'])
            return transcript.fetch()
    except Exception:
        # Silently fail as requested, summary logic will fallback to description
        return None


# -----------------------------
# Clean Transcript
# -----------------------------
def clean_transcript(transcript):
    if not transcript:
        return None

    cleaned = []
    for item in transcript:
        text = item['text']
        # Remove [Music], [Applause]
        text = re.sub(r"\[.*?\]", "", text)
        # Remove extra spaces
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            cleaned.append(text)

    return " ".join(cleaned)


# -----------------------------
# Summarize Text (Fallback for description)
# -----------------------------
def summarize_text(text, max_sentences=4, max_chars=400):
    if not text:
        return None

    sentences = text.split(". ")
    summary = []
    total_length = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        summary.append(sentence)
        total_length += len(sentence)
        if len(summary) >= max_sentences or total_length >= max_chars:
            break

    result = ". ".join(summary)
    if result and not result.endswith("."):
        result += "."
    return result


# -----------------------------
# Clean Description
# -----------------------------
def clean_description(desc, max_lines=4):
    if not desc:
        return None

    lines = desc.split("\n")
    meaningful = []
    for line in lines:
        line = line.strip()
        if (
            len(line) < 20 or
            "http" in line.lower() or
            "#" in line or
            "subscribe" in line.lower()
        ):
            continue
        meaningful.append(line)
        if len(meaningful) == max_lines:
            break

    return ". ".join(meaningful)


# -----------------------------
# Detect Language
# -----------------------------
def detect_language(text):
    if not text:
        return None
    try:
        return detect(text)
    except:
        return None


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def scrape_youtube(video_url):
    video_id = extract_video_id(video_url)

    if not video_id:
        print("Invalid YouTube URL")
        return None

    metadata = get_video_metadata(video_id)
    if not metadata:
        return None

    transcript = get_transcript(video_id)
    cleaned_transcript = clean_transcript(transcript)

    # Summary and language logic
    if cleaned_transcript:
        summary = summarize_text(cleaned_transcript)
        language = detect_language(cleaned_transcript)
    else:
        summary = clean_description(metadata["description"])
        language = detect_language(summary)

    result = {
        "source_url": video_url,
        "source_type": "youtube",
        "author": metadata["author"],
        "published_date": metadata["published_date"],
        "language": language,
        "region": metadata["region"] or "Global",
        "description": summary,
        "transcript": cleaned_transcript,
        "topic_tags": [],
        "trust_score": None,
        "content_chunks": []
    }

    return result


# -----------------------------
# TEST RUN
# -----------------------------
if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=xV1-V1E5ZlQ"
    data = scrape_youtube(url)
    print(json.dumps(data, indent=2))