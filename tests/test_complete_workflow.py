#!/usr/bin/env python3
"""
Complete End-to-End Workflow Test with Scheduling
Tests: News Fetching (22:30) → Topic Generation (22:33) → Blog Publishing (22:36)
"""
import sys
import os
import time
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import pytz

from app.services import newsdata_service, gemini_service, hashnode_service
from app.models import get_db, TopicStatus, BlogStatus
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

# Test results tracking
test_results = {
    "news_fetch": {"status": "pending", "attempts": 0, "data": None},
    "topic_generation": {"status": "pending", "data": None},
    "blog_publishing": {"status": "pending", "data": None}
}


def fetch_news_with_retry(max_retries=3, retry_interval=120):
    """
    Fetch news with retry logic (2-minute intervals)

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        retry_interval: Seconds between retries (default: 120 = 2 minutes)
    """
    print("\n" + "=" * 80)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 1: FETCHING NEWS (with retry)")
    print("=" * 80)

    for attempt in range(1, max_retries + 1):
        test_results["news_fetch"]["attempts"] = attempt

        print(f"\n[Attempt {attempt}/{max_retries}] Fetching latest tech news...")

        try:
            # Fetch news
            articles = newsdata_service.fetch_tech_news(max_articles=10)

            if articles and len(articles) > 0:
                # Success!
                news_context = newsdata_service.get_news_context("Technology")

                test_results["news_fetch"]["status"] = "success"
                test_results["news_fetch"]["data"] = {
                    "articles_count": len(articles),
                    "context_length": len(news_context),
                    "context_preview": news_context[:300]
                }

                print(f"✓ SUCCESS: Fetched {len(articles)} articles")
                print(f"✓ Generated news context: {len(news_context)} characters")
                print(f"\nNews Preview:")
                print("-" * 80)
                print(news_context[:500])
                print("-" * 80)

                return news_context
            else:
                raise Exception("No articles returned from API")

        except Exception as e:
            print(f"✗ FAILED: {e}")

            if attempt < max_retries:
                print(f"⏳ Retrying in {retry_interval} seconds ({retry_interval//60} minutes)...")
                time.sleep(retry_interval)
            else:
                print(f"✗ All {max_retries} attempts failed. Proceeding without news context.")
                test_results["news_fetch"]["status"] = "failed"
                return ""

    return ""


def generate_topics_with_news(news_context):
    """
    Generate topics using Gemini with news context

    Args:
        news_context: News context string from newsdata.io
    """
    print("\n" + "=" * 80)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 2: GENERATING TOPICS")
    print("=" * 80)

    try:
        # Generate 3 topics for testing
        print(f"\nGenerating 3 topics with news context ({len(news_context)} chars)...")

        topics = gemini_service.generate_topics(
            category_name="Technology",
            category_description="Latest trends in tech, AI, software development, and digital innovation",
            existing_topics=[
                "How to Build a REST API in 2024",
                "Top 10 Python Libraries for Data Science"
            ],
            count=3,
            news_context=news_context
        )

        if topics and len(topics) > 0:
            test_results["topic_generation"]["status"] = "success"
            test_results["topic_generation"]["data"] = topics

            print(f"✓ SUCCESS: Generated {len(topics)} topics")
            print("\nGenerated Topics:")
            print("-" * 80)

            for i, topic in enumerate(topics, 1):
                print(f"\n{i}. {topic.get('title', 'N/A')}")
                print(f"   Description: {topic.get('description', 'N/A')}")
                print(f"   Keywords: {', '.join(topic.get('keywords', []))}")
                print(f"   Angle: {topic.get('angle', 'N/A')}")

            print("-" * 80)
            return topics
        else:
            raise Exception("No topics generated")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        test_results["topic_generation"]["status"] = "failed"
        import traceback
        traceback.print_exc()
        return []


def generate_and_publish_blog(topic):
    """
    Generate blog content and publish to Hashnode

    Args:
        topic: Topic dictionary from topic generation
    """
    print("\n" + "=" * 80)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 3: GENERATING & PUBLISHING BLOG")
    print("=" * 80)

    try:
        # Generate blog content
        print(f"\nGenerating blog content for: {topic.get('title')}")

        blog_data = gemini_service.generate_blog_content(
            topic_title=topic.get('title'),
            category_name="Technology",
            category_description="Latest trends in tech, AI, software development",
            topic_description=topic.get('description'),
            keywords=topic.get('keywords', [])
        )

        if not blog_data:
            raise Exception("No blog content generated")

        print(f"✓ Blog content generated: {len(blog_data.get('content', ''))} characters")
        print(f"   Title: {blog_data.get('title')}")
        print(f"   Meta: {blog_data.get('meta_description')}")
        print(f"   Tags: {', '.join(blog_data.get('tags', []))}")

        # Count words
        import re
        word_count = len(re.findall(r'\w+', blog_data.get('content', '')))
        print(f"   Word count: {word_count}")

        # Publish to Hashnode
        print(f"\n📤 Publishing to Hashnode...")

        result = hashnode_service.publish_post(
            title=blog_data.get('title'),
            content=blog_data.get('content'),
            tags=blog_data.get('tags', []),
            meta_description=blog_data.get('meta_description')
        )

        if result and result.get('url'):
            test_results["blog_publishing"]["status"] = "success"
            test_results["blog_publishing"]["data"] = {
                "title": blog_data.get('title'),
                "url": result.get('url'),
                "post_id": result.get('post_id'),
                "word_count": word_count
            }

            print(f"✓ SUCCESS: Published to Hashnode!")
            print(f"   URL: {result.get('url')}")
            print(f"   Post ID: {result.get('post_id')}")
            return result
        else:
            raise Exception("Publishing failed - no URL returned")

    except Exception as e:
        print(f"✗ FAILED: {e}")
        test_results["blog_publishing"]["status"] = "failed"
        import traceback
        traceback.print_exc()
        return None


def print_test_summary():
    """Print final test results summary"""
    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)

    print("\n1. NEWS FETCHING:")
    if test_results["news_fetch"]["status"] == "success":
        data = test_results["news_fetch"]["data"]
        print(f"   ✓ SUCCESS (after {test_results['news_fetch']['attempts']} attempt(s))")
        print(f"   - Articles fetched: {data['articles_count']}")
        print(f"   - Context length: {data['context_length']} chars")
    elif test_results["news_fetch"]["status"] == "failed":
        print(f"   ✗ FAILED (after {test_results['news_fetch']['attempts']} attempts)")
    else:
        print(f"   ⏸ PENDING/SKIPPED")

    print("\n2. TOPIC GENERATION:")
    if test_results["topic_generation"]["status"] == "success":
        topics = test_results["topic_generation"]["data"]
        print(f"   ✓ SUCCESS")
        print(f"   - Topics generated: {len(topics)}")
        if topics:
            print(f"   - First topic: {topics[0].get('title', 'N/A')}")
    elif test_results["topic_generation"]["status"] == "failed":
        print(f"   ✗ FAILED")
    else:
        print(f"   ⏸ PENDING/SKIPPED")

    print("\n3. BLOG PUBLISHING:")
    if test_results["blog_publishing"]["status"] == "success":
        data = test_results["blog_publishing"]["data"]
        print(f"   ✓ SUCCESS")
        print(f"   - Title: {data['title']}")
        print(f"   - URL: {data['url']}")
        print(f"   - Word count: {data['word_count']}")
    elif test_results["blog_publishing"]["status"] == "failed":
        print(f"   ✗ FAILED")
    else:
        print(f"   ⏸ PENDING/SKIPPED")

    print("\n" + "=" * 80)

    # Overall result
    all_success = all(
        test_results[key]["status"] == "success"
        for key in ["news_fetch", "topic_generation", "blog_publishing"]
    )

    if all_success:
        print("🎉 ALL TESTS PASSED - COMPLETE WORKFLOW SUCCESSFUL!")
    else:
        print("⚠️  SOME TESTS FAILED - CHECK DETAILS ABOVE")

    print("=" * 80)


def run_immediate_test():
    """Run all tests immediately without scheduling"""
    print("\n" + "=" * 80)
    print("RUNNING IMMEDIATE END-TO-END TEST")
    print("=" * 80)

    # Step 1: Fetch news (with retry)
    news_context = fetch_news_with_retry(max_retries=3, retry_interval=10)  # 10 sec for testing

    if test_results["news_fetch"]["status"] != "success":
        print("\n⚠️  News fetch failed, but continuing with empty context...")

    # Step 2: Generate topics
    topics = generate_topics_with_news(news_context)

    if not topics or test_results["topic_generation"]["status"] != "success":
        print("\n✗ Cannot proceed to publishing without topics")
        print_test_summary()
        return False

    # Step 3: Generate and publish blog (use first topic)
    generate_and_publish_blog(topics[0])

    # Print summary
    print_test_summary()

    return test_results["blog_publishing"]["status"] == "success"


def run_scheduled_test(news_time="22:30", topic_time="22:33", blog_time="22:36"):
    """
    Run tests with scheduling

    Args:
        news_time: Time to fetch news (HH:MM)
        topic_time: Time to generate topics (HH:MM)
        blog_time: Time to publish blog (HH:MM)
    """
    print("\n" + "=" * 80)
    print("SETTING UP SCHEDULED END-TO-END TEST")
    print("=" * 80)

    # Parse times
    now = datetime.now()
    timezone = pytz.timezone(settings.TIMEZONE)

    def parse_time(time_str):
        """Parse HH:MM to datetime"""
        hour, minute = map(int, time_str.split(':'))
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time has passed today, schedule for tomorrow
        if scheduled < now:
            scheduled += timedelta(days=1)

        return timezone.localize(scheduled)

    news_scheduled = parse_time(news_time)
    topic_scheduled = parse_time(topic_time)
    blog_scheduled = parse_time(blog_time)

    print(f"\nScheduled Times:")
    print(f"  1. News Fetching:     {news_scheduled.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  2. Topic Generation:  {topic_scheduled.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"  3. Blog Publishing:   {blog_scheduled.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Create scheduler
    scheduler = BackgroundScheduler(timezone=timezone)

    # Shared data between jobs
    shared_data = {"news_context": "", "topics": []}

    def job_1_fetch_news():
        """Job 1: Fetch news"""
        shared_data["news_context"] = fetch_news_with_retry(max_retries=3, retry_interval=120)

    def job_2_generate_topics():
        """Job 2: Generate topics"""
        shared_data["topics"] = generate_topics_with_news(shared_data["news_context"])

    def job_3_publish_blog():
        """Job 3: Publish blog"""
        if shared_data["topics"]:
            generate_and_publish_blog(shared_data["topics"][0])
        else:
            print("✗ No topics available for publishing")

        # Print summary and shutdown
        print_test_summary()
        scheduler.shutdown()

    # Schedule jobs
    scheduler.add_job(job_1_fetch_news, DateTrigger(run_date=news_scheduled), id="news_fetch")
    scheduler.add_job(job_2_generate_topics, DateTrigger(run_date=topic_scheduled), id="topic_gen")
    scheduler.add_job(job_3_publish_blog, DateTrigger(run_date=blog_scheduled), id="blog_pub")

    # Start scheduler
    scheduler.start()
    print("\n✓ Scheduler started. Waiting for scheduled jobs to execute...")
    print("  Press Ctrl+C to stop\n")

    try:
        # Keep running until blog is published
        while scheduler.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        scheduler.shutdown()
        print_test_summary()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Complete workflow test")
    parser.add_argument(
        "--mode",
        choices=["immediate", "scheduled"],
        default="immediate",
        help="Test mode: immediate or scheduled"
    )
    parser.add_argument(
        "--news-time",
        default="22:30",
        help="Time to fetch news (HH:MM, for scheduled mode)"
    )
    parser.add_argument(
        "--topic-time",
        default="22:33",
        help="Time to generate topics (HH:MM, for scheduled mode)"
    )
    parser.add_argument(
        "--blog-time",
        default="22:36",
        help="Time to publish blog (HH:MM, for scheduled mode)"
    )

    args = parser.parse_args()

    if args.mode == "immediate":
        success = run_immediate_test()
        sys.exit(0 if success else 1)
    else:
        run_scheduled_test(args.news_time, args.topic_time, args.blog_time)


if __name__ == "__main__":
    main()
