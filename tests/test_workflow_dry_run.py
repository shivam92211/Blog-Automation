#!/usr/bin/env python3
"""
Dry-run test of complete workflow (without actual Hashnode publishing)
Tests: News Fetching → Topic Generation → Blog Generation (no publish)
"""
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services import newsdata_service, gemini_service
from config.logging_config import get_logger

logger = get_logger(__name__)


def test_complete_workflow_dry_run():
    """Test complete workflow without publishing"""
    print("=" * 80)
    print("COMPLETE WORKFLOW DRY-RUN TEST")
    print("(Tests everything except actual Hashnode publishing)")
    print("=" * 80)

    results = {"news": False, "topics": False, "blog": False}

    # STEP 1: Fetch news with retry
    print("\n" + "=" * 80)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 1: FETCHING NEWS (with retry)")
    print("=" * 80)

    news_context = ""
    for attempt in range(1, 4):  # 3 attempts
        print(f"\n[Attempt {attempt}/3] Fetching tech news...")

        try:
            articles = newsdata_service.fetch_tech_news(max_articles=10)

            if articles and len(articles) > 0:
                news_context = newsdata_service.get_news_context("Technology")
                print(f"✓ SUCCESS: Fetched {len(articles)} articles")
                print(f"✓ News context: {len(news_context)} characters")
                print(f"\nPreview:\n{news_context[:400]}...")
                results["news"] = True
                break
            else:
                raise Exception("No articles returned")

        except Exception as e:
            print(f"✗ FAILED: {e}")
            if attempt < 3:
                print(f"⏳ Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("✗ All attempts failed. Continuing without news context.")

    # STEP 2: Generate topics
    print("\n" + "=" * 80)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 2: GENERATING TOPICS")
    print("=" * 80)

    topics = []
    try:
        print(f"\nGenerating 3 topics with news context...")

        topics = gemini_service.generate_topics(
            category_name="Technology",
            category_description="Latest tech trends, AI, software development",
            existing_topics=["How to Build a REST API", "Python for Data Science"],
            count=3,
            news_context=news_context
        )

        if topics:
            print(f"✓ SUCCESS: Generated {len(topics)} topics")
            print("\nTopics:")
            for i, topic in enumerate(topics, 1):
                print(f"\n{i}. {topic.get('title')}")
                print(f"   Keywords: {', '.join(topic.get('keywords', []))}")
            results["topics"] = True
        else:
            raise Exception("No topics generated")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()

    # STEP 3: Generate blog content (DRY-RUN - no publishing)
    if topics:
        print("\n" + "=" * 80)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 3: GENERATING BLOG CONTENT")
        print("=" * 80)

        try:
            print(f"\nGenerating blog for: {topics[0].get('title')}")

            blog_data = gemini_service.generate_blog_content(
                topic_title=topics[0].get('title'),
                category_name="Technology",
                category_description="Latest tech trends",
                topic_description=topics[0].get('description'),
                keywords=topics[0].get('keywords', [])
            )

            if blog_data:
                import re
                word_count = len(re.findall(r'\w+', blog_data.get('content', '')))

                print(f"✓ SUCCESS: Blog content generated")
                print(f"\n   Title: {blog_data.get('title')}")
                print(f"   Meta: {blog_data.get('meta_description')}")
                print(f"   Tags: {', '.join(blog_data.get('tags', []))}")
                print(f"   Word count: {word_count}")
                print(f"   Content preview:\n")
                print("   " + "-" * 76)
                print("   " + blog_data.get('content', '')[:300].replace('\n', '\n   '))
                print("   " + "-" * 76)
                print(f"\n   ℹ️  DRY-RUN: Skipping actual Hashnode publishing")
                results["blog"] = True
            else:
                raise Exception("No blog content generated")

        except Exception as e:
            print(f"✗ FAILED: {e}")
            import traceback
            traceback.print_exc()

    # SUMMARY
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    print(f"\n1. News Fetching:     {'✓ PASS' if results['news'] else '✗ FAIL'}")
    print(f"2. Topic Generation:  {'✓ PASS' if results['topics'] else '✗ FAIL'}")
    print(f"3. Blog Generation:   {'✓ PASS' if results['blog'] else '✗ FAIL'}")

    all_pass = all(results.values())

    print("\n" + "=" * 80)
    if all_pass:
        print("🎉 ALL TESTS PASSED - WORKFLOW IS WORKING!")
        print("\nYou can now:")
        print("1. Run scheduled test: python test_complete_workflow.py --mode scheduled")
        print("2. Or run full test: python test_complete_workflow.py --mode immediate")
    else:
        print("⚠️  SOME TESTS FAILED - CHECK ERRORS ABOVE")

    print("=" * 80)

    return all_pass


if __name__ == "__main__":
    success = test_complete_workflow_dry_run()
    sys.exit(0 if success else 1)
