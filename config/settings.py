"""
Configuration settings loaded from environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# MongoDB Database
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "blog_automation")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY must be set in environment variables")

# Hashnode
HASHNODE_API_TOKEN = os.getenv("HASHNODE_API_TOKEN")
HASHNODE_PUBLICATION_ID = os.getenv("HASHNODE_PUBLICATION_ID")
HASHNODE_API_URL = "https://gql.hashnode.com/"

if not HASHNODE_API_TOKEN:
    raise ValueError("HASHNODE_API_TOKEN must be set in environment variables")
if not HASHNODE_PUBLICATION_ID:
    raise ValueError("HASHNODE_PUBLICATION_ID must be set in environment variables")

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
GEMINI_MAX_TOKENS_BLOG = 8000
API_TIMEOUT = 60
API_MAX_RETRIES = 3

# Image Generation Settings
ENABLE_BLOG_IMAGES = os.getenv("ENABLE_BLOG_IMAGES", "true").lower() == "true"
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "imagen-3.0-generate-001")  # Imagen 3.0 for image generation
IMAGE_ASPECT_RATIO = os.getenv("IMAGE_ASPECT_RATIO", "16:9")
IMAGE_TEMP_DIR = BASE_DIR / "temp_images"

# AWS S3 Upload Service
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Validate AWS credentials if image generation is enabled
if ENABLE_BLOG_IMAGES:
    if not AWS_S3_BUCKET_NAME:
        raise ValueError("AWS_S3_BUCKET_NAME must be set when ENABLE_BLOG_IMAGES is true")
    if not AWS_ACCESS_KEY_ID:
        raise ValueError("AWS_ACCESS_KEY_ID must be set when ENABLE_BLOG_IMAGES is true")
    if not AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS_SECRET_ACCESS_KEY must be set when ENABLE_BLOG_IMAGES is true")

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
