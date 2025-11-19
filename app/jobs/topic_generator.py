"""
Topic Generation Job
Runs weekly (Monday 6AM) to generate 7 topics for the week
"""
from datetime import datetime, timedelta
from typing import List, Dict

from app.models import (
    get_db, Category, Topic, GenerationHistory,
    TopicStatus, Log, JobType, JobStatus
)
from app.services import gemini_service, newsdata_service
from app.utils import (
    generate_topic_hash,
    validate_topic_uniqueness,
    extract_keywords
)
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class TopicGeneratorJob:
    """Weekly topic generation job"""

    def __init__(self):
        self.topics_per_week = settings.TOPIC_COUNT_PER_WEEK
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD
        self.lookback_months = settings.HISTORY_LOOKBACK_MONTHS

    def run(self):
        """Main entry point for the job"""
        start_time = datetime.utcnow()
        logger.info("=" * 80)
        logger.info("TOPIC GENERATION JOB STARTED")
        logger.info("=" * 80)

        try:
            with get_db() as db:
                # Log job start
                self._log_job_status(db, JobStatus.STARTED)

                # Step 1: Validate prerequisites
                self._validate_prerequisites(db)

                # Step 2: Select category
                category = self._select_category(db)
                if not category:
                    logger.warning("No active categories available. Exiting.")
                    return

                logger.info(f"Selected category: {category['name']} (ID: {category['_id']})")

                # Step 3: Fetch news context
                news_context = self._fetch_news_context(category)

                # Step 4: Fetch historical topics
                existing_topics = self._fetch_historical_topics(db, str(category["_id"]))
                logger.info(f"Found {len(existing_topics)} existing topics in history")

                # Step 5-7: Generate and validate topics
                validated_topics = self._generate_and_validate_topics(
                    db, category, existing_topics, news_context
                )

                if len(validated_topics) < self.topics_per_week:
                    logger.warning(
                        f"Only generated {len(validated_topics)}/{self.topics_per_week} topics"
                    )

                # Step 7: Assign scheduling
                scheduled_topics = self._assign_scheduling(validated_topics)

                # Step 8: Store topics in database
                self._store_topics(db, category, scheduled_topics)

                # Update category usage
                self._update_category_usage(db, category)

                # Log job completion
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                self._log_job_status(
                    db,
                    JobStatus.COMPLETED,
                    {
                        "category_id": str(category["_id"]),
                        "category_name": category["name"],
                        "topics_generated": len(validated_topics),
                        "execution_time_seconds": execution_time
                    }
                )

                logger.info("=" * 80)
                logger.info(f"TOPIC GENERATION COMPLETED - {len(validated_topics)} topics generated")
                logger.info(f"Execution time: {execution_time:.2f} seconds")
                logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Topic generation job failed: {e}", exc_info=True)
            with get_db() as db:
                self._log_job_status(
                    db,
                    JobStatus.FAILED,
                    {"error": str(e)}
                )
            raise

    def _validate_prerequisites(self, db):
        """Validate that all prerequisites are met"""
        logger.info("Validating prerequisites...")

        # Check database connection (already validated by context manager)
        logger.info("✓ Database connection OK")

        # Check if there are active categories
        active_count = db.categories.count_documents({"is_active": True})
        if active_count == 0:
            raise ValueError("No active categories found")

        logger.info(f"✓ Found {active_count} active categories")

    def _select_category(self, db):
        """
        Select category for topic generation
        Priority: oldest last_used_date, then lowest usage_count
        """
        logger.info("Selecting category...")

        # MongoDB query to find active categories, sorted by last_used_date (nulls first), then usage_count
        category_doc = db.categories.find_one(
            {"is_active": True},
            sort=[
                ("last_used_date", 1),  # 1 = ascending (nulls are naturally first)
                ("usage_count", 1)
            ]
        )

        return category_doc

    def _fetch_news_context(self, category: dict) -> str:
        """
        Fetch news context from newsdata.io for topic generation

        Args:
            category: Category dictionary with name and description

        Returns:
            Formatted news context string (empty if fetch fails)
        """
        logger.info("Fetching latest tech news for context...")

        try:
            news_context = newsdata_service.get_news_context(category.get("name"))
            if news_context:
                logger.info(f"✓ Successfully fetched news context ({len(news_context)} chars)")
            else:
                logger.warning("No news context available, proceeding without news")
            return news_context
        except Exception as e:
            logger.warning(f"Failed to fetch news context: {e}. Proceeding without news.")
            return ""

    def _fetch_historical_topics(self, db, category_id: str) -> List[str]:
        """
        Fetch historical topics for the category
        Looks back N months to prevent recent duplicates
        """
        logger.info(f"Fetching historical topics (last {self.lookback_months} months)...")

        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_months * 30)

        # MongoDB query with $and for multiple conditions
        history_docs = list(db.generation_history.find({
            "category_id": category_id,
            "generated_at": {"$gte": cutoff_date}
        }))

        return [h["topic_title"] for h in history_docs]

    def _generate_and_validate_topics(
        self,
        db,
        category: dict,
        existing_topics: List[str],
        news_context: str = ""
    ) -> List[Dict]:
        """
        Generate topics using Gemini and validate uniqueness
        Retry if duplicates found

        Args:
            db: Database connection
            category: Category dictionary
            existing_topics: List of existing topic titles
            news_context: Optional news context for inspiration
        """
        max_attempts = 3
        validated_topics = []

        for attempt in range(1, max_attempts + 1):
            logger.info(f"Generating topics (attempt {attempt}/{max_attempts})...")

            # Generate topics using Gemini with news context
            topics_needed = self.topics_per_week - len(validated_topics)
            generated_topics = gemini_service.generate_topics(
                category_name=category["name"],
                category_description=category.get("description", ""),
                existing_topics=existing_topics,
                count=topics_needed,
                news_context=news_context
            )

            logger.info(f"Generated {len(generated_topics)} topics from Gemini")

            # Validate uniqueness
            topic_titles = [t["title"] for t in generated_topics]
            all_existing = existing_topics + [t["title"] for t in validated_topics]

            validation_results = validate_topic_uniqueness(
                topic_titles,
                all_existing,
                self.similarity_threshold
            )

            # Filter unique topics
            for topic, result in zip(generated_topics, validation_results):
                if result["is_unique"]:
                    validated_topics.append(topic)
                    logger.info(f"✓ Unique topic: {topic['title']}")
                else:
                    logger.warning(
                        f"✗ Duplicate topic: {topic['title']} "
                        f"(similar to: {result['similar_to']}, "
                        f"score: {result['similarity_score']:.2f})"
                    )

            # Check if we have enough
            if len(validated_topics) >= self.topics_per_week:
                # Take only what we need
                validated_topics = validated_topics[:self.topics_per_week]
                logger.info(f"Successfully validated {len(validated_topics)} unique topics")
                break

            if attempt < max_attempts:
                logger.info(
                    f"Need {self.topics_per_week - len(validated_topics)} more topics, retrying..."
                )

        return validated_topics

    def _assign_scheduling(self, topics: List[Dict]) -> List[Dict]:
        """
        Assign scheduled dates to topics
        Monday generates, Tuesday-Monday publishes
        """
        logger.info("Assigning scheduled dates...")

        # Get next Tuesday (tomorrow if today is Monday)
        today = datetime.utcnow().date()
        # Find next day (will be Tuesday if run on Monday)
        start_date = today + timedelta(days=1)

        scheduled_topics = []
        for i, topic in enumerate(topics):
            scheduled_date = start_date + timedelta(days=i)
            # Convert date to datetime for MongoDB compatibility
            scheduled_datetime = datetime.combine(scheduled_date, datetime.min.time())
            topic["scheduled_date"] = scheduled_datetime
            scheduled_topics.append(topic)
            logger.info(f"  {scheduled_date}: {topic['title']}")

        return scheduled_topics

    def _store_topics(self, db, category: dict, topics: List[Dict]):
        """
        Store topics and generation history in database
        Uses batch insert for efficiency
        """
        logger.info("Storing topics in database...")

        topics_to_insert = []
        history_to_insert = []

        for topic_data in topics:
            # Extract keywords if not provided
            keywords = topic_data.get("keywords", [])
            if isinstance(keywords, list):
                keywords_str = ", ".join(keywords)
            else:
                keywords_str = keywords

            if not keywords_str:
                keywords_set = extract_keywords(topic_data["title"])
                keywords_str = ", ".join(keywords_set)

            # Create topic document
            topic_doc = Topic.create(
                category_id=str(category["_id"]),
                title=topic_data["title"],
                description=topic_data.get("description", ""),
                keywords=keywords_str,
                status=TopicStatus.PENDING,
                scheduled_date=topic_data["scheduled_date"]
            )
            topics_to_insert.append(topic_doc)

            # Create generation history document
            topic_hash = generate_topic_hash(topic_data["title"])
            history_doc = GenerationHistory.create(
                category_id=str(category["_id"]),
                topic_title=topic_data["title"],
                topic_keywords=keywords_str,
                topic_hash=topic_hash
            )
            history_to_insert.append(history_doc)

        # Batch insert topics and history
        if topics_to_insert:
            db.topics.insert_many(topics_to_insert)
        if history_to_insert:
            db.generation_history.insert_many(history_to_insert)

        logger.info(f"✓ Stored {len(topics)} topics in database")

    def _update_category_usage(self, db, category: dict):
        """Update category last_used_date and usage_count"""
        logger.info("Updating category usage...")

        now = datetime.utcnow()
        new_usage_count = category.get("usage_count", 0) + 1

        db.categories.update_one(
            {"_id": category["_id"]},
            {
                "$set": {
                    "last_used_date": now,
                    "updated_at": now
                },
                "$inc": {"usage_count": 1}
            }
        )

        logger.info(f"✓ Updated category (usage_count: {new_usage_count})")

    def _log_job_status(self, db, status: JobStatus, details: dict = None):
        """Log job status to database"""
        log_doc = Log.create(
            job_type=JobType.TOPIC_GENERATION,
            status=status,
            details=details or {}
        )
        db.logs.insert_one(log_doc)


# Singleton instance
topic_generator = TopicGeneratorJob()


def run_topic_generation():
    """Entry point for scheduler"""
    topic_generator.run()
