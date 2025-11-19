"""
Blog Publishing Job
Runs daily (9AM) to write and publish blog for today's scheduled topic
"""
from datetime import datetime, date
from typing import Optional
import re

from app.models import (
    get_db, Topic, Blog, Category,
    TopicStatus, BlogStatus, Log, JobType, JobStatus
)
from app.services import gemini_service, hashnode_service, image_upload_service
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class BlogPublisherJob:
    """Daily blog writing and publishing job"""

    def __init__(self):
        self.min_word_count = settings.MIN_BLOG_WORD_COUNT
        self.max_word_count = settings.MAX_BLOG_WORD_COUNT
        self.min_tags = settings.MIN_TAGS_COUNT
        self.max_tags = settings.MAX_TAGS_COUNT
        self.meta_min_length = settings.META_DESCRIPTION_MIN_LENGTH
        self.meta_max_length = settings.META_DESCRIPTION_MAX_LENGTH

    def run(self):
        """Main entry point for the job"""
        start_time = datetime.utcnow()
        logger.info("=" * 80)
        logger.info("BLOG PUBLISHING JOB STARTED")
        logger.info("=" * 80)

        try:
            with get_db() as db:
                # Log job start
                self._log_job_status(db, JobStatus.STARTED)

                # Step 1: Validate prerequisites
                self._validate_prerequisites()

                # Step 2: Fetch today's topic
                topic = self._fetch_todays_topic(db)
                if not topic:
                    logger.info("No topic scheduled for today. Exiting gracefully.")
                    return

                logger.info(f"Found topic: {topic['title']} (ID: {topic['_id']})")

                # Step 3: Update topic status
                self._update_topic_status(db, topic, TopicStatus.IN_PROGRESS)

                # Step 4: Get category context
                from bson import ObjectId
                category_id = topic["category_id"]
                # Convert to ObjectId if it's a string
                if isinstance(category_id, str):
                    category_id = ObjectId(category_id)
                category = db.categories.find_one({"_id": category_id})

                # Step 5-7: Generate and validate blog content
                blog_data = self._generate_and_validate_blog(topic, category)

                # Step 8: Store blog in database
                blog = self._store_blog(db, topic, blog_data)

                # Step 8.5: Generate and upload cover image (NEW)
                cover_image_url = self._generate_and_upload_cover_image(blog)
                if cover_image_url:
                    # Update blog with cover image URL
                    db.blogs.update_one(
                        {"_id": blog["_id"]},
                        {"$set": {"cover_image_url": cover_image_url}}
                    )
                    blog["cover_image_url"] = cover_image_url

                # Step 9-10: Publish to Hashnode and update database
                self._publish_and_update(db, blog, topic)

                # Log job completion
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                # Fetch updated blog for final logging
                updated_blog = db.blogs.find_one({"_id": blog["_id"]})

                self._log_job_status(
                    db,
                    JobStatus.COMPLETED,
                    {
                        "topic_id": str(topic["_id"]),
                        "blog_id": str(blog["_id"]),
                        "category": category["name"],
                        "word_count": blog["word_count"],
                        "hashnode_url": updated_blog.get("hashnode_url"),
                        "execution_time_seconds": execution_time
                    }
                )

                logger.info("=" * 80)
                logger.info(f"BLOG PUBLISHED SUCCESSFULLY")
                logger.info(f"Title: {blog['title']}")
                logger.info(f"URL: {updated_blog.get('hashnode_url')}")
                logger.info(f"Word Count: {blog['word_count']}")
                logger.info(f"Execution time: {execution_time:.2f} seconds")
                logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Blog publishing job failed: {e}", exc_info=True)
            with get_db() as db:
                self._log_job_status(
                    db,
                    JobStatus.FAILED,
                    {"error": str(e)}
                )
            raise

    def _validate_prerequisites(self):
        """Validate that all prerequisites are met"""
        logger.info("Validating prerequisites...")

        # API keys are validated in settings.py
        logger.info("✓ API keys configured")

    def _fetch_todays_topic(self, db):
        """
        Fetch topic scheduled for today
        Returns None if no topic found (normal scenario)
        """
        logger.info("Fetching today's scheduled topic...")

        # Convert date to datetime for MongoDB compatibility
        today = datetime.combine(date.today(), datetime.min.time())
        topic_doc = db.topics.find_one({
            "scheduled_date": today,
            "status": TopicStatus.PENDING.value
        })

        return topic_doc

    def _update_topic_status(self, db, topic: dict, status: TopicStatus):
        """Update topic status"""
        db.topics.update_one(
            {"_id": topic["_id"]},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"✓ Updated topic status to: {status}")

    def _generate_and_validate_blog(self, topic: dict, category: dict) -> dict:
        """
        Generate blog content using Gemini and validate quality
        """
        logger.info("Generating blog content...")

        # Parse keywords
        keywords = topic["keywords"].split(", ") if topic.get("keywords") else []

        # Generate blog content
        blog_data = gemini_service.generate_blog_content(
            topic_title=topic["title"],
            category_name=category["name"],
            category_description=category.get("description", ""),
            topic_description=topic.get("description", ""),
            keywords=keywords
        )

        logger.info("✓ Blog content generated")

        # Validate blog content
        self._validate_blog_content(blog_data)

        logger.info("✓ Blog content validated")

        return blog_data

    def _validate_blog_content(self, blog_data: dict):
        """
        Validate generated blog content meets quality standards
        Raises ValueError if validation fails
        """
        logger.info("Validating blog content...")

        # Check required fields
        required_fields = ["title", "content", "meta_description", "tags"]
        for field in required_fields:
            if field not in blog_data or not blog_data[field]:
                raise ValueError(f"Missing or empty required field: {field}")

        # Validate title
        if len(blog_data["title"]) < 10:
            raise ValueError("Title too short")

        # Validate content
        content = blog_data["content"]
        if len(content) < 500:
            raise ValueError("Content too short")

        # Count words
        word_count = len(re.findall(r'\w+', content))
        logger.info(f"  Word count: {word_count}")

        if word_count < self.min_word_count:
            logger.warning(f"⚠ Word count below target ({word_count} < {self.min_word_count})")
            # Don't fail, just warn

        if word_count > self.max_word_count:
            logger.warning(f"⚠ Word count above target ({word_count} > {self.max_word_count})")
            # Don't fail, just warn

        # Validate meta description
        meta_len = len(blog_data["meta_description"])
        if meta_len < self.meta_min_length or meta_len > self.meta_max_length:
            logger.warning(
                f"⚠ Meta description length not optimal "
                f"({meta_len} chars, ideal: {self.meta_min_length}-{self.meta_max_length})"
            )

        # Validate tags
        tags = blog_data["tags"]
        if not isinstance(tags, list):
            raise ValueError("Tags must be a list")

        if len(tags) < self.min_tags:
            raise ValueError(f"Too few tags (minimum {self.min_tags})")

        if len(tags) > self.max_tags:
            logger.warning(f"⚠ Too many tags, will use first {self.max_tags}")
            blog_data["tags"] = tags[:self.max_tags]

        # Validate content structure
        if not re.search(r'^##\s', content, re.MULTILINE):
            logger.warning("⚠ Content might lack proper heading structure")

        logger.info("  ✓ Title OK")
        logger.info(f"  ✓ Content OK ({word_count} words)")
        logger.info(f"  ✓ Meta description OK ({meta_len} chars)")
        logger.info(f"  ✓ Tags OK ({len(blog_data['tags'])} tags)")

    def _store_blog(self, db, topic: dict, blog_data: dict) -> dict:
        """
        Store generated blog in database
        """
        logger.info("Storing blog in database...")

        # Count words
        word_count = len(re.findall(r'\w+', blog_data["content"]))

        # Create blog document
        blog_doc = Blog.create(
            topic_id=str(topic["_id"]),
            title=blog_data["title"],
            content=blog_data["content"],
            meta_description=blog_data["meta_description"],
            tags=blog_data["tags"],
            word_count=word_count,
            status=BlogStatus.DRAFT
        )

        # Insert blog document
        result = db.blogs.insert_one(blog_doc)
        blog_doc["_id"] = result.inserted_id

        logger.info(f"✓ Blog stored (ID: {blog_doc['_id']}, status: DRAFT)")

        return blog_doc

    def _publish_and_update(self, db, blog: dict, topic: dict):
        """
        Publish blog to Hashnode and update database
        """
        logger.info("Publishing to Hashnode...")

        try:
            # Publish to Hashnode with cover image
            publish_result = hashnode_service.publish_post(
                title=blog["title"],
                content=blog["content"],
                tags=blog["tags"],
                meta_description=blog["meta_description"],
                cover_image_url=blog.get("cover_image_url")
            )

            logger.info(f"✓ Published to Hashnode: {publish_result['url']}")

            # Update blog status
            db.blogs.update_one(
                {"_id": blog["_id"]},
                {
                    "$set": {
                        "status": BlogStatus.PUBLISHED.value,
                        "hashnode_post_id": publish_result["post_id"],
                        "hashnode_url": publish_result["url"],
                        "published_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Update topic status
            db.topics.update_one(
                {"_id": topic["_id"]},
                {
                    "$set": {
                        "status": TopicStatus.COMPLETED.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            logger.info("✓ Database updated with publish details")

            # Cleanup temporary image file after successful publish
            if blog.get("cover_image_local_path"):
                self._cleanup_temp_image(blog["cover_image_local_path"])

        except Exception as e:
            logger.error(f"Failed to publish to Hashnode: {e}")

            # Update blog status to draft (keep content for manual retry)
            db.blogs.update_one(
                {"_id": blog["_id"]},
                {
                    "$set": {
                        "status": BlogStatus.DRAFT.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Update topic status to failed
            db.topics.update_one(
                {"_id": topic["_id"]},
                {
                    "$set": {
                        "status": TopicStatus.FAILED.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            raise

    def _log_job_status(self, db, status: JobStatus, details: dict = None):
        """Log job status to database"""
        log_doc = Log.create(
            job_type=JobType.BLOG_PUBLISHING,
            status=status,
            details=details or {}
        )
        db.logs.insert_one(log_doc)

    def _generate_and_upload_cover_image(self, blog: dict) -> Optional[str]:
        """
        Generate cover image and upload to public hosting

        Args:
            blog: Blog document with title, tags, etc.

        Returns:
            Public URL of uploaded image, or None if failed
        """
        if not settings.ENABLE_BLOG_IMAGES:
            logger.info("Blog image generation is disabled")
            return None

        if not settings.IMGUR_CLIENT_ID:
            logger.warning("IMGUR_CLIENT_ID not set - skipping image generation")
            return None

        logger.info("Generating cover image for blog...")

        try:
            # Step 1: Generate image using Gemini
            image_path = gemini_service.generate_blog_cover_image(
                blog_title=blog["title"],
                blog_description=blog.get("meta_description"),
                keywords=blog.get("tags", [])
            )

            if not image_path:
                logger.warning("Image generation failed - continuing without image")
                return None

            # Store local path in blog for later cleanup
            blog["cover_image_local_path"] = image_path

            # Step 2: Upload to Imgur
            image_url = image_upload_service.upload_to_imgur(
                image_path=image_path,
                title=blog["title"]
            )

            if not image_url:
                logger.warning("Image upload failed - cleaning up local file")
                image_upload_service.cleanup_local_image(image_path)
                return None

            logger.info(f"✓ Cover image uploaded successfully: {image_url}")
            return image_url

        except Exception as e:
            logger.error(f"Failed to generate/upload cover image: {e}", exc_info=True)
            return None

    def _cleanup_temp_image(self, image_path: str):
        """
        Delete temporary image file after successful publishing

        Args:
            image_path: Path to temporary image file
        """
        try:
            image_upload_service.cleanup_local_image(image_path)
        except Exception as e:
            # Don't fail the job for cleanup errors
            logger.warning(f"Failed to cleanup temp image: {e}")


# Singleton instance
blog_publisher = BlogPublisherJob()


def run_blog_publishing():
    """Entry point for scheduler"""
    blog_publisher.run()
