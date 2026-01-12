"""
Configuration settings loaded from environment variables
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup basic logging for configuration loading
logging.basicConfig(level=logging.INFO)
config_logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# MongoDB Database
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "blog_automation")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY must be set in environment variables")

GEMINI_TIER_ONE_API_KEY = os.getenv("GEMINI_TIER_ONE_API_KEY")  # Optional, falls back to standard key if needed

# Hashnode Configuration
HASHNODE_API_URL = "https://gql.hashnode.com/"

# JWT Tokens for Hashnode CDN Upload
HASHNODE_JWT_TOKENS = {
    "Shivam": os.getenv("HASHNODE_JWT_SHIVAM", ""),
    "Gaurav": os.getenv("HASHNODE_JWT_GAURAV", ""),
}

# Multi-Publication Configuration
class PublicationConfig:
    """Configuration for a single Hashnode publication"""

    def __init__(self, config_dict: Dict[str, Any]):
        self.name = config_dict['name']
        self.api_token = config_dict['api_token']
        self.publication_id = config_dict['publication_id']
        self.categories = config_dict.get('categories', [])
        self.is_active = config_dict.get('is_active', True)
        self.wait_after_publish_minutes = config_dict.get('wait_after_publish_minutes', 5)

        # Get JWT token for this publication (for CDN uploads)
        self.jwt_token = HASHNODE_JWT_TOKENS.get(self.name, "")

    def get_category_names(self) -> List[str]:
        """Get list of category names assigned to this publication"""
        return self.categories

    def __repr__(self):
        return f"PublicationConfig(name='{self.name}', categories={len(self.categories)}, active={self.is_active})"


# Load Multi-Publication Configuration
HASHNODE_PUBLICATIONS_JSON = os.getenv("HASHNODE_PUBLICATIONS_JSON")
HASHNODE_PUBLICATIONS: List[PublicationConfig] = []

if HASHNODE_PUBLICATIONS_JSON:
    try:
        publications_data = json.loads(HASHNODE_PUBLICATIONS_JSON)
        HASHNODE_PUBLICATIONS = [PublicationConfig(pub) for pub in publications_data]
        config_logger.info(f"✓ Loaded {len(HASHNODE_PUBLICATIONS)} Hashnode publications")
        for pub in HASHNODE_PUBLICATIONS:
            config_logger.info(f"  - {pub.name}: {len(pub.categories)} categories")
    except json.JSONDecodeError as e:
        config_logger.error(f"Failed to parse HASHNODE_PUBLICATIONS_JSON: {e}")
        config_logger.warning("Falling back to single publication mode")
    except KeyError as e:
        config_logger.error(f"Missing required field in publication config: {e}")
        config_logger.warning("Falling back to single publication mode")

# Backward Compatibility: Single Publication Mode
HASHNODE_API_TOKEN = os.getenv("HASHNODE_API_TOKEN")
HASHNODE_PUBLICATION_ID = os.getenv("HASHNODE_PUBLICATION_ID")

if not HASHNODE_PUBLICATIONS:
    if HASHNODE_API_TOKEN and HASHNODE_PUBLICATION_ID:
        config_logger.info("Using single publication mode (backward compatibility)")
        HASHNODE_PUBLICATIONS = [PublicationConfig({
            'name': 'Default Publication',
            'api_token': HASHNODE_API_TOKEN,
            'publication_id': HASHNODE_PUBLICATION_ID,
            'categories': [],  # All categories
            'is_active': True,
            'wait_after_publish_minutes': 0
        })]
    else:
        raise ValueError(
            "Either HASHNODE_PUBLICATIONS_JSON or both HASHNODE_API_TOKEN and "
            "HASHNODE_PUBLICATION_ID must be set in environment variables"
        )


# Validation: Ensure categories are assigned to exactly one publication
def validate_publication_categories() -> bool:
    """Validate that each category is assigned to at most one publication"""
    all_categories = []
    for pub in HASHNODE_PUBLICATIONS:
        for cat in pub.categories:
            if cat in all_categories:
                raise ValueError(
                    f"Category '{cat}' is assigned to multiple publications. "
                    f"Each category must belong to exactly one publication."
                )
            all_categories.append(cat)

    if all_categories:
        config_logger.info(f"✓ Category validation passed: {len(all_categories)} unique categories")
    return True

# Run validation
validate_publication_categories()

# NewsData.io API
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
if not NEWSDATA_API_KEY:
    raise ValueError("NEWSDATA_API_KEY must be set in environment variables")

NEWSDATA_MAX_ARTICLES = int(os.getenv("NEWSDATA_MAX_ARTICLES", "20"))
NEWSDATA_LOOKBACK_DAYS = int(os.getenv("NEWSDATA_LOOKBACK_DAYS", "2"))

# Application
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
TIMEZONE = os.getenv("TIMEZONE", "UTC")

# Scheduler
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"

# Topic Generation Schedule (24-hour format)
# Configurable via environment variables
TOPIC_GENERATION_HOUR = int(os.getenv("TOPIC_GENERATION_HOUR", "23"))
TOPIC_GENERATION_MINUTE = int(os.getenv("TOPIC_GENERATION_MINUTE", "15"))
TOPIC_GENERATION_DAY = os.getenv("TOPIC_GENERATION_DAY", "*")  # * = every day, or mon/tue/wed/etc

TOPIC_GENERATION_SCHEDULE = {
    "hour": TOPIC_GENERATION_HOUR,
    "minute": TOPIC_GENERATION_MINUTE,
    "day_of_week": TOPIC_GENERATION_DAY
}

# Blog Publishing Schedule (24-hour format)
# Configurable via environment variables
BLOG_PUBLISHING_HOUR = int(os.getenv("BLOG_PUBLISHING_HOUR", "23"))
BLOG_PUBLISHING_MINUTE = int(os.getenv("BLOG_PUBLISHING_MINUTE", "18"))

BLOG_PUBLISHING_SCHEDULE = {
    "hour": BLOG_PUBLISHING_HOUR,
    "minute": BLOG_PUBLISHING_MINUTE
}

# Content Settings
TOPIC_COUNT_PER_WEEK = 7
MIN_BLOG_WORD_COUNT = 1000
MAX_BLOG_WORD_COUNT = 2000
TARGET_BLOG_WORD_COUNT = 1400
META_DESCRIPTION_MIN_LENGTH = 150
META_DESCRIPTION_MAX_LENGTH = 160
MIN_TAGS_COUNT = 3
MAX_TAGS_COUNT = 7

# Uniqueness Settings
SIMILARITY_THRESHOLD = 0.7  # Topics with >70% similarity are considered duplicates
HISTORY_LOOKBACK_MONTHS = 6  # Check for duplicates in last 6 months

# API Settings
# Using Gemini 2.5 Flash model
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS_TOPICS = 4000
GEMINI_MAX_TOKENS_BLOG = 16384  # Increased to prevent truncation of blog content (Gemini 2.5 Flash max)
API_TIMEOUT = 60
API_MAX_RETRIES = 3

# AWS S3 Upload Service
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Image Generation Settings
# Only enable if AWS credentials are available
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "imagen-3.0-generate-001")  # Imagen 3.0 for image generation
IMAGE_ASPECT_RATIO = os.getenv("IMAGE_ASPECT_RATIO", "16:9")
IMAGE_TEMP_DIR = BASE_DIR / "temp_images"

# Check if AWS credentials are available
_aws_credentials_available = bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_S3_BUCKET_NAME)

# Enable blog images only if explicitly set to true AND AWS credentials are available
_user_wants_images = os.getenv("ENABLE_BLOG_IMAGES", "false").lower() == "true"
ENABLE_BLOG_IMAGES = _user_wants_images and _aws_credentials_available

# Warn if user wants images but credentials are missing
if _user_wants_images and not _aws_credentials_available:
    import warnings
    warnings.warn(
        "ENABLE_BLOG_IMAGES is set to true, but AWS credentials are missing. "
        "Image generation will be disabled. Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, "
        "and AWS_S3_BUCKET_NAME to enable image generation.",
        UserWarning
    )

# MongoDB Connection Settings
MONGODB_MAX_POOL_SIZE = 10
MONGODB_MIN_POOL_SIZE = 1
MONGODB_SERVER_SELECTION_TIMEOUT = 30000  # milliseconds

# Content Angles
CONTENT_ANGLES = [
    "how-to",
    "listicle",
    "case-study",
    "tutorial",
    "opinion",
    "comparison",
    "beginner-guide"
]

# Difficulty Levels
DIFFICULTY_LEVELS = {
    "beginner": 2,
    "intermediate": 3,
    "advanced": 2
}

# Image Generation Enabled flag
IMAGE_GENERATION_ENABLED = ENABLE_BLOG_IMAGES


# Settings object for easy import
class Settings:
    """Settings object with all configuration"""

    # Base
    BASE_DIR = BASE_DIR
    ENVIRONMENT = ENVIRONMENT
    LOG_LEVEL = LOG_LEVEL
    LOG_FILE = LOG_FILE
    TIMEZONE = TIMEZONE

    # MongoDB
    MONGODB_URL = MONGODB_URL
    MONGODB_DB_NAME = MONGODB_DB_NAME
    MONGODB_MAX_POOL_SIZE = MONGODB_MAX_POOL_SIZE
    MONGODB_MIN_POOL_SIZE = MONGODB_MIN_POOL_SIZE
    MONGODB_SERVER_SELECTION_TIMEOUT = MONGODB_SERVER_SELECTION_TIMEOUT

    # API Keys
    GEMINI_API_KEY = GEMINI_API_KEY
    GEMINI_TIER_ONE_API_KEY = GEMINI_TIER_ONE_API_KEY

    # Hashnode - Multi-Publication Support
    HASHNODE_PUBLICATIONS = HASHNODE_PUBLICATIONS
    # Backward Compatibility
    HASHNODE_API_TOKEN = HASHNODE_API_TOKEN
    HASHNODE_PUBLICATION_ID = HASHNODE_PUBLICATION_ID
    HASHNODE_API_URL = HASHNODE_API_URL

    NEWSDATA_API_KEY = NEWSDATA_API_KEY

    # NewsData
    NEWSDATA_MAX_ARTICLES = NEWSDATA_MAX_ARTICLES
    NEWSDATA_LOOKBACK_DAYS = NEWSDATA_LOOKBACK_DAYS

    # Content Settings
    TOPIC_COUNT_PER_WEEK = TOPIC_COUNT_PER_WEEK
    MIN_BLOG_WORD_COUNT = MIN_BLOG_WORD_COUNT
    MAX_BLOG_WORD_COUNT = MAX_BLOG_WORD_COUNT
    TARGET_BLOG_WORD_COUNT = TARGET_BLOG_WORD_COUNT
    META_DESCRIPTION_MIN_LENGTH = META_DESCRIPTION_MIN_LENGTH
    META_DESCRIPTION_MAX_LENGTH = META_DESCRIPTION_MAX_LENGTH
    MIN_TAGS_COUNT = MIN_TAGS_COUNT
    MAX_TAGS_COUNT = MAX_TAGS_COUNT

    # Uniqueness
    SIMILARITY_THRESHOLD = SIMILARITY_THRESHOLD
    HISTORY_LOOKBACK_MONTHS = HISTORY_LOOKBACK_MONTHS

    # Gemini AI
    GEMINI_MODEL = GEMINI_MODEL
    GEMINI_TEMPERATURE = GEMINI_TEMPERATURE
    GEMINI_MAX_TOKENS_TOPICS = GEMINI_MAX_TOKENS_TOPICS
    GEMINI_MAX_TOKENS_BLOG = GEMINI_MAX_TOKENS_BLOG
    API_TIMEOUT = API_TIMEOUT
    API_MAX_RETRIES = API_MAX_RETRIES

    # Images
    ENABLE_BLOG_IMAGES = ENABLE_BLOG_IMAGES
    IMAGE_GENERATION_ENABLED = IMAGE_GENERATION_ENABLED
    IMAGE_MODEL = IMAGE_MODEL
    IMAGE_ASPECT_RATIO = IMAGE_ASPECT_RATIO
    IMAGE_TEMP_DIR = IMAGE_TEMP_DIR

    # AWS S3
    AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY
    AWS_S3_BUCKET_NAME = AWS_S3_BUCKET_NAME
    AWS_REGION = AWS_REGION

    # Content
    CONTENT_ANGLES = CONTENT_ANGLES
    DIFFICULTY_LEVELS = DIFFICULTY_LEVELS


# Create singleton instance
settings = Settings()
