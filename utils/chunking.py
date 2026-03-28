import nltk

def download_nltk_resources():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')
    except (LookupError, AttributeError):
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)

# Run once
download_nltk_resources()


def chunk_text(text: str, max_words: int = 150) -> list:
    """
    Split text into chunks of roughly max_words using NLTK sentence tokenization.
    This ensures chunks do not break in the middle of a sentence.
    """
    if not text:
        return []
        
    try:
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)
    except:
        # Fallback if NLTK fails
        sentences = text.split(". ")

    chunks = []
    current_chunk = []
    current_word_count = 0
    
    for sentence in sentences:
        words_in_sentence = len(sentence.split())
        
        # If adding this sentence would exceed max_words, finalize current chunk
        if current_word_count + words_in_sentence > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0
            
        current_chunk.append(sentence)
        current_word_count += words_in_sentence
        
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks


def chunk_transcript(transcript_list: list, chunk_duration: int = 60) -> list:
    """
    Split the YouTube transcript (list of dicts) into chunks based on time duration.
    """
    if not transcript_list:
        return []
        
    chunks = []
    current_chunk_text = []
    current_start = -1.0
    
    for item in transcript_list:
        start_time = item.get('start', 0.0)
        
        if current_start < 0:
            current_start = start_time
            
        current_chunk_text.append(item.get('text', ""))
        
        # Group segments until the target duration is reached
        if start_time - current_start >= chunk_duration:
            chunks.append(" ".join(current_chunk_text))
            current_chunk_text = []
            current_start = -1.0
            
    # Add the last remaining chunk
    if current_chunk_text:
        chunks.append(" ".join(current_chunk_text))
        
    return chunks
