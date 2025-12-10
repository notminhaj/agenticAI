"""
Test Topic Normalization

Tests the topic normalizer to ensure it correctly maps:
- Exact matches (case-insensitive)
- Semantic matches (embedding similarity)
- New topics (below threshold)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from topic_normalizer import normalize_topic, load_existing_topics


def test_topic_normalization():
    """Test topic normalization functionality."""
    print("=" * 60)
    print("TOPIC NORMALIZATION TESTS")
    print("=" * 60)
    
    existing = load_existing_topics()
    print(f"\nExisting topics ({len(existing)}):")
    for t in existing[:10]:
        print(f"  - {t}")
    if len(existing) > 10:
        print(f"  ... and {len(existing) - 10} more")
    
    test_cases = [
        # (input, expected_to_match_existing)
        ("Agentic AI", True),  # Exact match
        ("agentic ai", True),  # Case insensitive
        ("Agentic AI creation using CrewAI", True),  # Should match "Agentic AI"
        ("AI agent creation using Crew AI", True),  # Should match "Agentic AI" or similar
        ("quantum mechanics", True),  # Exact match
        ("quantum physics basics", True),  # Should match "quantum mechanics"
        ("completely unrelated topic xyz123", False),  # New topic
    ]
    
    print("\n" + "-" * 60)
    print("TEST RESULTS")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for input_topic, should_match in test_cases:
        canonical, matched, score = normalize_topic(input_topic, existing)
        
        did_match = matched is not None
        status = "PASS" if did_match == should_match else "FAIL"
        
        if status == "PASS":
            passed += 1
        else:
            failed += 1
        
        print(f"\n[{status}] Input: '{input_topic}'")
        print(f"       Canonical: '{canonical}'")
        print(f"       Matched: {matched}, Score: {score:.3f}")
        print(f"       Expected match: {should_match}, Got match: {did_match}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_topic_normalization()
    sys.exit(0 if success else 1)
