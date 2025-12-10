"""
Topic Normalizer - Maps messy topic phrases to canonical topic keys.

This module prevents topic fragmentation in the knowledge base by:
1. Loading existing topics from kb_metadata.json
2. Using embedding similarity to find the closest existing topic
3. If similarity > threshold, returning the existing topic name
4. Otherwise, returning the input as-is (new topic)

Example:
    "Agentic AI creation using CrewAI" -> "Agentic AI" (if similar enough)
    "quantum entanglement" -> "quantum mechanics" (if similar enough)
"""

import json
from pathlib import Path
from typing import Optional, Tuple, List
from sentence_transformers import SentenceTransformer
import numpy as np

# Constants
ROOT = Path(__file__).resolve().parent
METADATA_PATH = ROOT / "knowledge_base" / "kb_metadata.json"
SIMILARITY_THRESHOLD = 0.75  # Topics above this similarity are merged

# Lazy-load model
_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("intfloat/e5-base-v2")
    return _model


def load_existing_topics() -> List[str]:
    """Load all existing topic names from kb_metadata.json."""
    if not METADATA_PATH.exists():
        return []
    try:
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return list(data.get("topics", {}).keys())
    except Exception:
        return []


def normalize_topic(raw_topic: str, existing_topics: Optional[List[str]] = None) -> Tuple[str, Optional[str], float]:
    """
    Normalize a topic phrase to a canonical topic key.
    
    Args:
        raw_topic: The raw topic phrase from conversation (e.g., "Agentic AI creation using CrewAI")
        existing_topics: Optional list of existing topics. If None, loads from kb_metadata.json.
    
    Returns:
        Tuple of (canonical_topic, matched_existing_topic_or_None, similarity_score)
        - canonical_topic: The topic name to use (either existing or raw)
        - matched_existing_topic_or_None: The existing topic it matched to, or None if new
        - similarity_score: The similarity score (0-1)
    
    Example:
        >>> normalize_topic("Agentic AI creation using CrewAI")
        ("Agentic AI", "Agentic AI", 0.89)
    """
    if existing_topics is None:
        existing_topics = load_existing_topics()
    
    if not existing_topics:
        return (raw_topic, None, 0.0)
    
    # Quick exact match check (case-insensitive)
    for topic in existing_topics:
        if topic.lower() == raw_topic.lower():
            return (topic, topic, 1.0)
    
    # Use embeddings for semantic matching
    model = _get_model()
    
    # E5 requires "query: " prefix for queries
    raw_embedding = model.encode(f"query: {raw_topic}", normalize_embeddings=True)
    
    # E5 requires "passage: " prefix for passages (existing topics)
    topic_embeddings = model.encode(
        [f"passage: {t}" for t in existing_topics],
        normalize_embeddings=True
    )
    
    # Compute cosine similarities
    similarities = np.dot(topic_embeddings, raw_embedding)
    
    best_idx = np.argmax(similarities)
    best_score = float(similarities[best_idx])
    best_match = existing_topics[best_idx]
    
    if best_score >= SIMILARITY_THRESHOLD:
        return (best_match, best_match, best_score)
    else:
        return (raw_topic, None, best_score)


def get_related_topics(topic: str, existing_topics: Optional[List[str]] = None, top_k: int = 3) -> List[Tuple[str, float]]:
    """
    Find topics related to the given topic.
    
    Args:
        topic: The topic to find related topics for
        existing_topics: Optional list of existing topics
        top_k: Number of related topics to return
    
    Returns:
        List of (topic_name, similarity_score) tuples, sorted by similarity
    """
    if existing_topics is None:
        existing_topics = load_existing_topics()
    
    if not existing_topics:
        return []
    
    model = _get_model()
    
    query_embedding = model.encode(f"query: {topic}", normalize_embeddings=True)
    topic_embeddings = model.encode(
        [f"passage: {t}" for t in existing_topics],
        normalize_embeddings=True
    )
    
    similarities = np.dot(topic_embeddings, query_embedding)
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    return [(existing_topics[i], float(similarities[i])) for i in top_indices]


if __name__ == "__main__":
    # Quick test
    test_cases = [
        "Agentic AI creation using CrewAI",
        "AI agent creation using Crew AI",
        "quantum mechanics basics",
        "transformers architecture",
        "biology fundamentals",
    ]
    
    print("Topic Normalization Test")
    print("=" * 60)
    topics = load_existing_topics()
    print(f"Existing topics: {topics[:5]}... ({len(topics)} total)")
    print()
    
    for test in test_cases:
        canonical, matched, score = normalize_topic(test, topics)
        print(f"Input: {test}")
        print(f"  -> Canonical: {canonical}")
        print(f"     Matched: {matched}, Score: {score:.3f}")
        print()
