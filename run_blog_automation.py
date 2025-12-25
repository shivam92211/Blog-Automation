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
    """Standalone blog automation runner"""

    def __init__(self):
        self.db = get_sync_db()
        self.gemini = GeminiService()
        self.news_service = NewsDataService()
        self.hashnode = HashnodeService()
        self.image_service = ImageUploadService()

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
        """Get a random category from database"""
        logger.info("📁 Fetching a random category...")
        categories = list(self.db.categories.find({"is_active": True}))

        if not categories:
            logger.error("No active categories found in database")
            logger.error("Please run: make init-db (or python3 init_categories.py)")
            raise Exception("No active categories found in database")

        category = random.choice(categories)
        logger.info(f"✓ Selected category: {category['name']}")
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
    
    def generate_image_with_retry(self, topic: str, category_name: str) -> Optional[str]:
        """
        Generate image with retry logic:
        Fail 1 -> wait 2m -> retry
        Fail 2 -> wait 5m -> retry
        Fail 3 -> wait 10m -> retry
        Fail 4 -> exit and return None (proceed without image)
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
                    # 2. Upload to S3
                    logger.info("☁️ Uploading image to S3...")
                    image_url = self.image_service.upload_and_cleanup(local_path, title=topic)
                    
                    if image_url:
                        logger.info(f"✓ Image generated and uploaded: {image_url}")
                        return image_url
                    else:
                        logger.warning("Failed to upload image to S3")
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
                meta_description=blog_data.get('meta_description', '')
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

    def run(self) -> int:
        """Main execution flow

        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        logger.info("=" * 60)
        logger.info("🚀 BLOG AUTOMATION SCRIPT STARTED")
        logger.info("=" * 60)
        start_time = time.time()

        try:
            # Step 1: Get category
            try:
                category = self.get_random_category()
            except Exception as e:
                logger.error(f"Failed to get category: {str(e)}")
                return EXIT_NO_CATEGORIES

            self.sleep("Category selected")

            # Step 2: Find unique topic
            topic = self.find_unique_topic(category['name'], category.get('description', ''))
            if not topic:
                logger.error("❌ FAILED: Could not find a unique topic")
                return EXIT_NO_UNIQUE_TOPIC

            self.sleep("Unique topic found")

            # Step 3: Store topic
            try:
                topic_id = self.store_topic(topic, category)
            except Exception as e:
                logger.error(f"Failed to store topic: {str(e)}")
                return EXIT_ERROR

            self.sleep("Topic stored")

            # Step 4: Generate Image (New Step)
            cover_image_url = None
            try:
                cover_image_url = self.generate_image_with_retry(topic, category['name'])
            except Exception as e:
                logger.error(f"Failed during image generation process: {e}")
                # We continue even if image generation fails
            
            self.sleep("Image generation step completed")

            # Step 5: Generate blog
            try:
                blog_data = self.generate_blog(topic_id, topic, category)
                if not blog_data:
                    logger.error("❌ FAILED: Could not generate blog content")
                    return EXIT_BLOG_GENERATION_FAILED
            except Exception as e:
                logger.error(f"Failed to generate blog: {str(e)}")
                return EXIT_BLOG_GENERATION_FAILED

            self.sleep("Blog content generated")

            # Step 6: Store blog
            try:
                blog_id = self.store_blog(blog_data, topic_id, category, cover_image_url)
            except Exception as e:
                logger.error(f"Failed to store blog: {str(e)}")
                return EXIT_ERROR

            self.sleep("Blog stored")

            # Step 7: Publish blog
            try:
                success = self.publish_blog(blog_id, blog_data, cover_image_url)
                if not success:
                    logger.error("❌ FAILED: Could not publish blog")
                    return EXIT_PUBLISH_FAILED
            except Exception as e:
                logger.error(f"Failed to publish blog: {str(e)}")
                return EXIT_PUBLISH_FAILED

            # Update topic status to completed
            try:
                self.db.topics.update_one(
                    {"_id": ObjectId(topic_id)},
                    {"$set": {"status": "COMPLETED", "updated_at": datetime.now(timezone.utc)}}
                )
            except Exception as e:
                logger.warning(f"Failed to update topic status: {str(e)}")

            # Success!
            elapsed_time = time.time() - start_time
            logger.info("=" * 60)
            logger.info("✅ BLOG AUTOMATION COMPLETED SUCCESSFULLY!")
            logger.info(f"⏱️  Total time: {elapsed_time:.2f} seconds")
            logger.info("=" * 60)
            return EXIT_SUCCESS

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