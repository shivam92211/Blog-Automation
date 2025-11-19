"""
Topic uniqueness checking utilities
Implements similarity detection and hash-based duplicate checking
"""
import hashlib
import re
from typing import List, Set
from difflib import SequenceMatcher

# Common English stop words to exclude from keyword extraction
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
    'those', 'as', 'it', 'its', 'how', 'what', 'when', 'where', 'why',
    'who', 'which', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'up', 'down', 'out', 'off', 'over', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'all', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'
}


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison
    - Convert to lowercase
    - Remove punctuation
    - Remove extra whitespace
    """
    # Convert to lowercase
    text = text.lower()

    # Remove punctuation (keep alphanumeric and spaces)
    text = re.sub(r'[^a-z0-9\s]', '', text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text


def extract_keywords(text: str) -> Set[str]:
    """
    Extract meaningful keywords from text
    - Remove stop words
    - Keep only words longer than 2 characters
    - Return unique words
    """
    normalized = normalize_text(text)
    words = normalized.split()

    # Filter out stop words and short words
    keywords = {
        word for word in words
        if word not in STOP_WORDS and len(word) > 2
    }

    return keywords


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts
    Similarity = |intersection| / |union|
    Returns float between 0.0 (completely different) and 1.0 (identical)
    """
    keywords1 = extract_keywords(text1)
    keywords2 = extract_keywords(text2)

    if not keywords1 and not keywords2:
        return 1.0  # Both empty
    if not keywords1 or not keywords2:
        return 0.0  # One empty

    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)

    similarity = len(intersection) / len(union)
    return similarity


def calculate_sequence_similarity(text1: str, text2: str) -> float:
    """
    Calculate sequence similarity using SequenceMatcher
    More sophisticated than Jaccard, considers word order
    Returns float between 0.0 and 1.0
    """
    normalized1 = normalize_text(text1)
    normalized2 = normalize_text(text2)

    return SequenceMatcher(None, normalized1, normalized2).ratio()


def calculate_similarity(text1: str, text2: str, method: str = "combined") -> float:
    """
    Calculate similarity between two texts

    Args:
        text1: First text
        text2: Second text
        method: "jaccard", "sequence", or "combined" (default)

    Returns:
        Similarity score between 0.0 and 1.0
    """
    if method == "jaccard":
        return calculate_jaccard_similarity(text1, text2)
    elif method == "sequence":
        return calculate_sequence_similarity(text1, text2)
    elif method == "combined":
        # Use weighted average of both methods
        jaccard = calculate_jaccard_similarity(text1, text2)
        sequence = calculate_sequence_similarity(text1, text2)
        return (jaccard * 0.6) + (sequence * 0.4)  # Favor keyword matching
    else:
        raise ValueError(f"Unknown similarity method: {method}")


def generate_topic_hash(topic_title: str) -> str:
    """
    Generate SHA-256 hash of normalized topic title
    Used for fast duplicate detection

    Args:
        topic_title: The topic title to hash

    Returns:
        64-character hexadecimal hash string
    """
    # Normalize and extract keywords
    keywords = extract_keywords(topic_title)

    # Sort keywords alphabetically for consistent hashing
    sorted_keywords = sorted(keywords)

    # Create fingerprint by joining sorted keywords
    fingerprint = ' '.join(sorted_keywords)

    # Generate SHA-256 hash
    hash_object = hashlib.sha256(fingerprint.encode('utf-8'))
    return hash_object.hexdigest()


def is_similar_topic(
    new_topic: str,
    existing_topics: List[str],
    threshold: float = 0.7
) -> tuple[bool, str, float]:
    """
    Check if a new topic is similar to any existing topics

    Args:
        new_topic: The new topic to check
        existing_topics: List of existing topic titles
        threshold: Similarity threshold (default 0.7 = 70%)

    Returns:
        Tuple of (is_similar, most_similar_topic, similarity_score)
    """
    max_similarity = 0.0
    most_similar = ""

    for existing in existing_topics:
        similarity = calculate_similarity(new_topic, existing)
        if similarity > max_similarity:
            max_similarity = similarity
            most_similar = existing

    is_similar = max_similarity >= threshold
    return is_similar, most_similar, max_similarity


def validate_topic_uniqueness(
    new_topics: List[str],
    existing_topics: List[str],
    threshold: float = 0.7
) -> List[dict]:
    """
    Validate uniqueness of multiple new topics against existing ones

    Args:
        new_topics: List of new topic titles to validate
        existing_topics: List of existing topic titles
        threshold: Similarity threshold

    Returns:
        List of dicts with validation results:
        [
            {
                "topic": "topic title",
                "is_unique": True/False,
                "similar_to": "most similar existing topic" or None,
                "similarity_score": 0.0-1.0
            },
            ...
        ]
    """
    results = []

    for topic in new_topics:
        is_similar, similar_topic, score = is_similar_topic(
            topic, existing_topics, threshold
        )

        results.append({
            "topic": topic,
            "is_unique": not is_similar,
            "similar_to": similar_topic if is_similar else None,
            "similarity_score": score
        })

    return results


def get_unique_topics(
    new_topics: List[str],
    existing_topics: List[str],
    threshold: float = 0.7
) -> List[str]:
    """
    Filter out similar topics from a list of new topics

    Args:
        new_topics: List of new topic titles
        existing_topics: List of existing topic titles
        threshold: Similarity threshold

    Returns:
        List of unique topics only
    """
    validation_results = validate_topic_uniqueness(
        new_topics, existing_topics, threshold
    )

    unique_topics = [
        result["topic"]
        for result in validation_results
        if result["is_unique"]
    ]

    return unique_topics
