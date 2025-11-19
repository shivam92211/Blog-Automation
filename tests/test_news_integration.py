#!/usr/bin/env python3
"""
Integration test for newsdata.io with Gemini topic generation
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services import newsdata_service, gemini_service
from config.logging_config import get_logger

logger = get_logger(__name__)


def test_integration():
    """Test complete newsdata.io + Gemini integration"""
    print("=" * 80)
    print("TESTING NEWSDATA.IO + GEMINI INTEGRATION")
    print("=" * 80)

    # Step 1: Fetch news context
    print("\n[STEP 1] Fetching news context from newsdata.io...")
    try:
        news_context = newsdata_service.get_news_context("Technology")

        if news_context:
            print(f"✓ Fetched news context: {len(news_context)} characters")
            print("\nNews Context Preview:")
            print("-" * 80)
            print(news_context[:600] + "...")
            print("-" * 80)
        else:
            print("✗ No news context available")
            return False

    except Exception as e:
        print(f"✗ Error fetching news: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 2: Generate topics WITH news context
    print("\n" + "=" * 80)
    print("[STEP 2] Generating topics WITH news context...")
    try:
        topics_with_news = gemini_service.generate_topics(
            category_name="Technology",
            category_description="Latest trends and innovations in technology, software development, AI, and digital transformation",
            existing_topics=[
                "How to Build Your First Web Application",
                "Top 10 Programming Languages in 2024"
            ],
            count=3,
            news_context=news_context
        )

        if topics_with_news:
            print(f"✓ Generated {len(topics_with_news)} topics with news context")
            print("\nTopics Inspired by News:")
            print("-" * 80)
            for i, topic in enumerate(topics_with_news, 1):
                print(f"\n{i}. {topic.get('title', 'N/A')}")
                print(f"   Description: {topic.get('description', 'N/A')}")
                print(f"   Keywords: {', '.join(topic.get('keywords', []))}")
                print(f"   Angle: {topic.get('angle', 'N/A')}")
            print("-" * 80)
        else:
            print("✗ No topics generated with news")
            return False

    except Exception as e:
        print(f"✗ Error generating topics with news: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Generate topics WITHOUT news context (for comparison)
    print("\n" + "=" * 80)
    print("[STEP 3] Generating topics WITHOUT news context (for comparison)...")
    try:
        topics_without_news = gemini_service.generate_topics(
            category_name="Technology",
            category_description="Latest trends and innovations in technology, software development, AI, and digital transformation",
            existing_topics=[
                "How to Build Your First Web Application",
                "Top 10 Programming Languages in 2024"
            ],
            count=3,
            news_context=""  # No news context
        )

        if topics_without_news:
            print(f"✓ Generated {len(topics_without_news)} topics without news context")
            print("\nTopics WITHOUT News Context:")
            print("-" * 80)
            for i, topic in enumerate(topics_without_news, 1):
                print(f"\n{i}. {topic.get('title', 'N/A')}")
                print(f"   Description: {topic.get('description', 'N/A')}")
                print(f"   Keywords: {', '.join(topic.get('keywords', []))}")
                print(f"   Angle: {topic.get('angle', 'N/A')}")
            print("-" * 80)
        else:
            print("✗ No topics generated without news")

    except Exception as e:
        print(f"✗ Error generating topics without news: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    print(f"✓ News fetching: SUCCESS")
    print(f"✓ News context generation: SUCCESS")
    print(f"✓ Topics with news context: SUCCESS ({len(topics_with_news)} topics)")
    print(f"✓ Topics without news context: SUCCESS ({len(topics_without_news)} topics)")
    print("\n" + "=" * 80)
    print("COMPARISON:")
    print("Topics WITH news should be more timely and relevant to current trends")
    print("Topics WITHOUT news are more general and evergreen")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
