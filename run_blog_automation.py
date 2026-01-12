#!/usr/bin/env python3
"""
Simple Blog Automation Script
Run this script whenever you want to generate and publish a blog post.

Workflow:
1. Fetch trending news and generate a topic using Gemini AI
2. Check if topic is unique (not similar to existing topics in DB)
3. If duplicate, generate another topic (max 5 attempts)
4. Store unique topic in database
5. Generate image (with retry logic)
6. Generate blog content for the topic
7. Store blog in database
8. Publish blog to Hashnode
"""

import sys
import time
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import random

# Add the project root to the path
sys.path.insert(0, '/home/shivam/App/Work/Phrase_trade/Blog-Automation')

from config.settings import settings
from app.models.database import get_sync_db
from app.services.gemini_service import GeminiService
from app.services.newsdata_service import NewsDataService
from app.services.hashnode_service import HashnodeService
from app.services.image_upload_service import ImageUploadService
from app.utils.uniqueness import calculate_similarity, generate_topic_hash
from bson import ObjectId

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USER_INTERRUPT = 2
EXIT_NO_CATEGORIES = 3
EXIT_NO_UNIQUE_TOPIC = 4
EXIT_BLOG_GENERATION_FAILED = 5
EXIT_PUBLISH_FAILED = 6

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BlogAutomationRunner:
    """Multi-publication blog automation runner"""

    def __init__(self):
        self.db = get_sync_db()
        self.gemini = GeminiService()
        self.news_service = NewsDataService()
        self.image_service = ImageUploadService()
        self.publications = settings.HASHNODE_PUBLICATIONS

        # Validate publications
        if not self.publications:
            raise ValueError("No Hashnode publications configured")

        logger.info(f"Initialized with {len(self.publications)} publications")
        for pub in self.publications:
            logger.info(f"  - {pub.name}: {len(pub.categories)} categories")

        # Configuration
        self.max_topic_attempts = 5
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.sleep_duration = random.randint(10, 30)  # 10-30 seconds

    def sleep(self, message: str = ""):
        """Sleep with a message"""
        duration = random.randint(10, 30)
        if message:
            logger.info(f"{message} (sleeping for {duration}s)")
        else:
            logger.info(f"Sleeping for {duration} seconds...")
        time.sleep(duration)

    def get_random_category(self) -> Dict[str, Any]:
        """Get a random category from database (legacy method for backward compatibility)"""
        logger.info("📁 Fetching a random category...")
        categories = list(self.db.categories.find({"is_active": True}))

        if not categories:
            logger.error("No active categories found in database")
            logger.error("Please run: make init-db (or python3 init_categories.py)")
            raise Exception("No active categories found in database")

        category = random.choice(categories)
        logger.info(f"✓ Selected category: {category['name']}")
        return category

    def get_category_for_publication(self, publication) -> Optional[Dict[str, Any]]:
        """
        Get a random active category that belongs to this publication

        Args:
            publication: PublicationConfig instance

        Returns:
            Category dict or None if no categories available
        """
        # If publication has specific categories, filter by them
        if publication.categories:
            categories = list(self.db.categories.find({
                "is_active": True,
                "name": {"$in": publication.categories}
            }))
        else:
            # Legacy mode: all categories
            categories = list(self.db.categories.find({"is_active": True}))

        if not categories:
            logger.warning(f"No active categories found for publication: {publication.name}")
            return None

        category = random.choice(categories)
        logger.info(f"✓ Selected category: {category['name']} for {publication.name}")
        return category

    def generate_topic(self, category_name: str, category_description: str = "") -> Optional[str]:
        """Generate a single topic using Gemini AI"""
        logger.info(f"🤖 Generating topic for category: {category_name}")

        # Fetch trending news context
        logger.info("📰 Fetching trending tech news...")
        news_context = self.news_service.get_news_context(category_name)

        from datetime import timedelta
        lookback_date = datetime.now(timezone.utc) - timedelta(days=180)
        historical_topics = list(self.db.topics.find({
            "created_at": {"$gte": lookback_date}
        }))
        existing_topic_titles = [topic['title'] for topic in historical_topics]

        self.sleep("News fetched successfully")

        # Generate topics (we'll use just the first one)
        logger.info("🎯 Calling Gemini AI to generate topic...")
        topics = self.gemini.generate_topics(
            category_name=category_name,
            category_description=category_description or f"Content about {category_name}",
            existing_topics=existing_topic_titles,
            count=1,
            news_context=news_context
        )

        if not topics or len(topics) == 0:
            logger.error("❌ Gemini AI failed to generate topics")
            return None

        # Extract just the title from the first topic dict
        topic = topics[0].get('title') if isinstance(topics[0], dict) else topics[0]
        logger.info(f"✓ Generated topic: {topic}")
        return topic

    def is_topic_unique(self, topic: str) -> bool:
        """Check if topic is unique compared to existing topics in DB"""
        logger.info(f"🔍 Checking uniqueness for: {topic}")

        # Get historical topics (last 6 months)
        from datetime import timedelta
        lookback_date = datetime.now(timezone.utc) - timedelta(days=180)

        historical_topics = list(self.db.topics.find({
            "created_at": {"$gte": lookback_date}
        }))

        # Also check generation history
        history_records = list(self.db.generation_history.find({
            "generated_at": {"$gte": lookback_date}
        }))

        logger.info(f"📊 Comparing against {len(historical_topics)} topics and {len(history_records)} history records")

        # Check against topics
        for existing in historical_topics:
            similarity = calculate_similarity(topic, existing['title'], method="combined")
            if similarity >= self.similarity_threshold:
                logger.warning(f"❌ Topic too similar ({similarity:.2%}) to: {existing['title']}")
                return False

        # Check against generation history
        for record in history_records:
            for generated_topic in record.get('generated_topics', []):
                similarity = calculate_similarity(topic, generated_topic, method="combined")
                if similarity >= self.similarity_threshold:
                    logger.warning(f"❌ Topic too similar ({similarity:.2%}) to historical: {generated_topic}")
                    return False

        logger.info("✓ Topic is unique!")
        return True

    def find_unique_topic(self, category_name: str, category_description: str = "") -> Optional[str]:
        """Keep generating topics until we find a unique one"""
        logger.info(f"🔄 Starting unique topic search (max {self.max_topic_attempts} attempts)...")

        for attempt in range(1, self.max_topic_attempts + 1):
            logger.info(f"\n--- Attempt {attempt}/{self.max_topic_attempts} ---")

            # Generate topic
            topic = self.generate_topic(category_name, category_description)
            if not topic:
                logger.warning("Failed to generate topic, trying again...")
                self.sleep("Waiting before retry")
                continue

            self.sleep("Topic generated, checking uniqueness")

            # Check uniqueness
            if self.is_topic_unique(topic):
                logger.info(f"🎉 Found unique topic on attempt {attempt}!")
                return topic
            else:
                logger.info(f"Topic is duplicate, will try again...")
                self.sleep("Waiting before next attempt")

        logger.error(f"❌ Could not find unique topic after {self.max_topic_attempts} attempts")
        return None

    def store_topic(self, topic: str, category: Dict[str, Any]) -> str:
        """Store topic in database"""
        logger.info("💾 Storing topic in database...")

        topic_doc = {
            "title": topic,
            "category_id": category['_id'],
            "category_name": category['name'],
            "status": "PENDING",
            "scheduled_date": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "hash": generate_topic_hash(topic)
        }

        result = self.db.topics.insert_one(topic_doc)
        topic_id = str(result.inserted_id)

        logger.info(f"✓ Topic stored with ID: {topic_id}")

        # Also update generation history
        history_doc = {
            "category_id": category['_id'],
            "category_name": category['name'],
            "generated_topics": [topic],
            "generated_at": datetime.now(timezone.utc)
        }
        self.db.generation_history.insert_one(history_doc)

        return topic_id
    
    def generate_image_with_retry(self, topic: str, category_name: str, api_token: str) -> Optional[str]:
        """
        Generate image with retry logic:
        Fail 1 -> wait 2m -> retry
        Fail 2 -> wait 5m -> retry
        Fail 3 -> wait 10m -> retry
        Fail 4 -> exit and return None (proceed without image)

        Args:
            topic: Blog topic/title
            category_name: Category name
            api_token: Hashnode API token for CDN upload

        Returns:
            Hashnode CDN URL if successful, None otherwise
        """
        if not settings.ENABLE_BLOG_IMAGES:
            return None

        logger.info(f"🎨 Starting image generation for: {topic}")

        # Retry delays in seconds: 2min, 5min, 10min
        retry_delays = [120, 300, 600]
        max_attempts = len(retry_delays) + 1

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Image generation attempt {attempt}/{max_attempts}")

                # 1. Generate Image (returns local path)
                local_path = self.gemini.generate_blog_cover_image(
                    blog_title=topic,
                    keywords=[category_name]
                )

                if local_path:
                    # 2. Upload to both S3 and Hashnode CDN
                    logger.info("☁️ Uploading image to S3 and Hashnode CDN...")

                    # Get JWT token for this publication (if available)
                    jwt_token = None
                    for pub in self.publications:
                        if pub.api_token == api_token:
                            jwt_token = pub.jwt_token
                            break

                    result = self.image_service.upload_and_cleanup(
                        local_path,
                        title=topic,
                        upload_to="both",
                        hashnode_api_token=api_token,
                        hashnode_jwt_token=jwt_token
                    )

                    if result.get("success"):
                        # Prefer Hashnode CDN URL for publishing to Hashnode
                        cdn_url = result.get("hashnode_url") or result.get("s3_url")
                        if cdn_url:
                            logger.info(f"✓ Image generated and uploaded: {cdn_url}")
                            if result.get("hashnode_url"):
                                logger.info("   Using Hashnode CDN URL for publishing")
                            else:
                                logger.warning("   Hashnode CDN upload failed, using S3 URL")
                            return cdn_url
                    else:
                        logger.warning("Failed to upload image to any CDN")
                else:
                    logger.warning("Failed to generate image (no path returned)")

            except Exception as e:
                logger.error(f"Image generation error: {e}")

            # If we are here, something failed. Check if we should retry.
            if attempt < max_attempts:
                wait_time = retry_delays[attempt - 1]
                minutes = wait_time // 60
                logger.warning(f"⚠️ Image generation failed. Retrying in {minutes} minutes...")
                time.sleep(wait_time)
            else:
                logger.error("❌ All image generation attempts failed. Proceeding without image.")

        return None

    def generate_blog(self, topic_id: str, topic_title: str, category: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate blog content using Gemini AI"""
        logger.info(f"📝 Generating blog content for: {topic_title}")

        # Update topic status
        self.db.topics.update_one(
            {"_id": ObjectId(topic_id)},
            {"$set": {"status": "IN_PROGRESS", "updated_at": datetime.now(timezone.utc)}}
        )

        # Generate blog
        blog_data = self.gemini.generate_blog_content(
            topic_title=topic_title,
            category_name=category['name'],
            category_description=category.get('description', f"Content about {category['name']}")
        )

        if not blog_data:
            logger.error("❌ Failed to generate blog content")
            return None

        logger.info(f"✓ Blog generated successfully!")
        logger.info(f"   Title: {blog_data.get('title')}")
        logger.info(f"   SEO Title: {blog_data.get('seo_title', 'N/A')}")
        logger.info(f"   Word Count: {blog_data.get('word_count')}")
        logger.info(f"   Tags: {', '.join(blog_data.get('tags', []))}")

        return blog_data

    def store_blog(self, blog_data: Dict[str, Any], topic_id: str, category: Dict[str, Any], cover_image_url: Optional[str] = None) -> str:
        """Store blog in database"""
        logger.info("💾 Storing blog in database...")

        blog_doc = {
            "topic_id": ObjectId(topic_id),
            "category_id": category['_id'],
            "category_name": category['name'],
            "title": blog_data['title'],
            "seo_title": blog_data.get('seo_title', ''),
            "content": blog_data['content'],
            "meta_description": blog_data.get('meta_description', ''),
            "tags": blog_data.get('tags', []),
            "word_count": blog_data.get('word_count', 0),
            "status": "DRAFT",
            "cover_image_url": cover_image_url,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        result = self.db.blogs.insert_one(blog_doc)
        blog_id = str(result.inserted_id)

        logger.info(f"✓ Blog stored with ID: {blog_id}")
        return blog_id

    def publish_blog(self, blog_id: str, blog_data: Dict[str, Any], cover_image_url: Optional[str] = None) -> bool:
        """Publish blog to Hashnode"""
        logger.info("🚀 Publishing blog to Hashnode...")

        try:
            # Publish to Hashnode
            result = self.hashnode.publish_post(
                title=blog_data['title'],
                content=blog_data['content'],
                tags=blog_data.get('tags', []),
                cover_image_url=cover_image_url,
                meta_description=blog_data.get('meta_description', ''),
                seo_title=blog_data.get('seo_title')
            )

            # The result dict has: post_id, url, slug
            if result and 'post_id' in result:
                post_id = result.get('post_id')
                post_url = result.get('url', '')

                logger.info(f"✓ Blog published successfully!")
                logger.info(f"   Post ID: {post_id}")
                logger.info(f"   URL: {post_url}")

                # Update blog in database
                self.db.blogs.update_one(
                    {"_id": ObjectId(blog_id)},
                    {
                        "$set": {
                            "status": "PUBLISHED",
                            "hashnode_post_id": post_id,
                            "hashnode_url": post_url,
                            "published_at": datetime.now(timezone.utc),
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )

                return True
            else:
                logger.error(f"❌ Failed to publish: Invalid response from Hashnode")
                return False

        except Exception as e:
            logger.error(f"❌ Error during publishing: {str(e)}")
            return False

    def publish_blog_to_publication(
        self,
        publication,
        blog_data: Dict[str, Any],
        cover_image_url: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Publish a blog to a specific Hashnode publication

        Args:
            publication: PublicationConfig instance
            blog_data: Blog content data
            cover_image_url: Optional cover image URL

        Returns:
            Result dict with post_id and url if successful, None otherwise
        """
        logger.info(f"🚀 Publishing to {publication.name}...")

        try:
            # Create publication-specific Hashnode service
            hashnode = HashnodeService(
                api_token=publication.api_token,
                publication_id=publication.publication_id,
                publication_name=publication.name
            )

            # Publish
            result = hashnode.publish_post(
                title=blog_data['title'],
                content=blog_data['content'],
                tags=blog_data.get('tags', []),
                cover_image_url=cover_image_url,
                meta_description=blog_data.get('meta_description', ''),
                seo_title=blog_data.get('seo_title')
            )

            if result and 'post_id' in result:
                logger.info(f"✓ Published to {publication.name}!")
                logger.info(f"   URL: {result.get('url', 'N/A')}")
                return result
            else:
                logger.error(f"❌ Failed to publish to {publication.name}")
                return None

        except Exception as e:
            logger.error(f"❌ Error publishing to {publication.name}: {str(e)}")
            return None

    def run_single_publication(self, publication) -> bool:
        """
        Run complete blog generation and publishing flow for a single publication

        Args:
            publication: PublicationConfig instance

        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info(f"📚 PUBLICATION: {publication.name}")
        logger.info(f"📂 Categories: {', '.join(publication.categories)}")
        logger.info("=" * 60)

        try:
            # Step 1: Get category for this publication
            category = self.get_category_for_publication(publication)
            if not category:
                logger.error(f"❌ No categories available for {publication.name}")
                return False

            self.sleep("Category selected")

            # Step 2: Find unique topic
            topic = self.find_unique_topic(category['name'], category.get('description', ''))
            if not topic:
                logger.error(f"❌ Could not find unique topic for {publication.name}")
                return False

            self.sleep("Unique topic found")

            # Step 3: Store topic
            topic_id = self.store_topic(topic, category)
            self.sleep("Topic stored")

            # Step 4: Generate image
            cover_image_url = None
            try:
                cover_image_url = self.generate_image_with_retry(
                    topic,
                    category['name'],
                    api_token=publication.api_token
                )
            except Exception as e:
                logger.error(f"Image generation failed: {e}")
                # Continue without image

            self.sleep("Image generation completed")

            # Step 5: Generate blog content
            blog_data = self.generate_blog(topic_id, topic, category)
            if not blog_data:
                logger.error(f"❌ Could not generate blog for {publication.name}")
                return False

            self.sleep("Blog content generated")

            # Step 6: Store blog in database (before publishing)
            blog_id = self.store_blog(blog_data, topic_id, category, cover_image_url)
            self.sleep("Blog stored")

            # Step 7: Publish to this specific publication
            result = self.publish_blog_to_publication(publication, blog_data, cover_image_url)

            if result:
                # Update blog with publication info
                self.db.blogs.update_one(
                    {"_id": ObjectId(blog_id)},
                    {
                        "$set": {
                            f"publications.{publication.name}": {
                                "status": "PUBLISHED",
                                "hashnode_post_id": result.get('post_id'),
                                "hashnode_url": result.get('url'),
                                "published_at": datetime.now(timezone.utc)
                            },
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )

                # Update topic status
                self.db.topics.update_one(
                    {"_id": ObjectId(topic_id)},
                    {"$set": {"status": "COMPLETED"}}
                )

                logger.info(f"✅ {publication.name} - COMPLETED")
                return True
            else:
                logger.error(f"❌ {publication.name} - FAILED")
                return False

        except Exception as e:
            logger.error(f"❌ Error in {publication.name}: {str(e)}")
            return False

    def run(self) -> int:
        """
        Main execution flow - processes all active publications

        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        logger.info("=" * 60)
        logger.info("🚀 MULTI-PUBLICATION BLOG AUTOMATION STARTED")
        logger.info(f"📊 Processing {len(self.publications)} publications")
        logger.info("=" * 60)

        start_time = time.time()
        results = []

        try:
            for idx, publication in enumerate(self.publications, 1):
                # Skip inactive publications
                if not publication.is_active:
                    logger.info(f"⏭️  Skipping inactive publication: {publication.name}")
                    continue

                logger.info(f"\n{'='*60}")
                logger.info(f"📍 Publication {idx}/{len(self.publications)}")
                logger.info(f"{'='*60}\n")

                # Run blog generation and publishing for this publication
                success = self.run_single_publication(publication)
                results.append({
                    'publication': publication.name,
                    'success': success
                })

                # Wait between publications (but not after the last one)
                active_pubs = [p for p in self.publications if p.is_active]
                is_last = (idx == len(active_pubs))

                if not is_last and publication.wait_after_publish_minutes > 0:
                    wait_minutes = publication.wait_after_publish_minutes
                    logger.info(f"⏳ Waiting {wait_minutes} minutes before next publication...")
                    time.sleep(wait_minutes * 60)

            # Summary
            elapsed_time = time.time() - start_time
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful

            logger.info("\n" + "=" * 60)
            logger.info("📊 MULTI-PUBLICATION SUMMARY")
            logger.info("=" * 60)
            logger.info(f"✅ Successful: {successful}/{len(results)}")
            logger.info(f"❌ Failed: {failed}/{len(results)}")
            logger.info(f"⏱️  Total time: {elapsed_time:.2f} seconds")

            for result in results:
                status = "✅" if result['success'] else "❌"
                logger.info(f"  {status} {result['publication']}")

            logger.info("=" * 60)

            # Return success if at least one publication succeeded
            return EXIT_SUCCESS if successful > 0 else EXIT_ERROR

        except KeyboardInterrupt:
            logger.warning("\n⚠️  Script interrupted by user")
            return EXIT_USER_INTERRUPT
        except Exception as e:
            logger.error(f"\n❌ FATAL ERROR: {str(e)}", exc_info=True)
            return EXIT_ERROR


if __name__ == "__main__":
    try:
        runner = BlogAutomationRunner()
        exit_code = runner.run()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Failed to initialize runner: {str(e)}")
        sys.exit(EXIT_ERROR)