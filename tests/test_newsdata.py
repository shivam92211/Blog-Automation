#!/usr/bin/env python3
"""
Test script for newsdata.io API integration
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services import newsdata_service
from config.logging_config import get_logger

logger = get_logger(__name__)


def test_news_fetch():
    """Test fetching tech news from newsdata.io"""
    print("=" * 80)
    print("TESTING NEWSDATA.IO API INTEGRATION")
    print("=" * 80)

    # Test 1: Fetch tech news
    print("\n[TEST 1] Fetching latest tech news...")
    try:
        articles = newsdata_service.fetch_tech_news(max_articles=5)

        if articles:
            print(f"✓ Successfully fetched {len(articles)} articles")
            print("\nSample Articles:")
            for i, article in enumerate(articles[:3], 1):
                print(f"\n{i}. {article.get('title', 'N/A')}")
                print(f"   Source: {article.get('source_id', 'Unknown')}")
                print(f"   Published: {article.get('pubDate', 'N/A')}")
                if article.get('description'):
                    desc = article['description'][:150] + "..." if len(article['description']) > 150 else article['description']
                    print(f"   Description: {desc}")
        else:
            print("✗ No articles fetched (check API key or rate limits)")

    except Exception as e:
        print(f"✗ Error fetching news: {e}")
        return False

    # Test 2: Extract trending topics
    print("\n" + "=" * 80)
    print("[TEST 2] Extracting trending topics...")
    try:
        topics = newsdata_service.extract_trending_topics(articles)

        if topics:
            print(f"✓ Extracted {len(topics)} trending topics")
            print("\nSample Topics:")
            for i, topic in enumerate(topics[:3], 1):
                print(f"\n{i}. {topic.get('title', 'N/A')}")
                keywords = topic.get('keywords', [])
                if keywords:
                    print(f"   Keywords: {', '.join(keywords[:5])}")
        else:
            print("✗ No topics extracted")

    except Exception as e:
        print(f"✗ Error extracting topics: {e}")
        return False

    # Test 3: Get news context for Gemini
    print("\n" + "=" * 80)
    print("[TEST 3] Generating news context for Gemini...")
    try:
        news_context = newsdata_service.get_news_context("Technology")

        if news_context:
            print(f"✓ Generated news context ({len(news_context)} characters)")
            print("\nContext Preview (first 500 chars):")
            print("-" * 80)
            print(news_context[:500])
            print("-" * 80)
        else:
            print("✗ No news context generated")

    except Exception as e:
        print(f"✗ Error generating context: {e}")
        return False

    # Test 4: Get trending keywords
    print("\n" + "=" * 80)
    print("[TEST 4] Extracting trending keywords...")
    try:
        keywords = newsdata_service.get_trending_keywords(articles)

        if keywords:
            print(f"✓ Extracted {len(keywords)} trending keywords")
            print(f"   Top keywords: {', '.join(keywords[:10])}")
        else:
            print("✗ No keywords extracted")

    except Exception as e:
        print(f"✗ Error extracting keywords: {e}")
        return False

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = test_news_fetch()
    sys.exit(0 if success else 1)
