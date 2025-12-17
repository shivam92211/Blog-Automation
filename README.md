# Blog Automation Script

An intelligent, AI-powered blog automation system that generates unique, SEO-optimized blog posts and publishes them to Hashnode automatically. Built with Python, Google Gemini AI, and MongoDB.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Output Example](#output-example)
- [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)
- [API Information](#api-information)
- [Contributing](#contributing)

---

## Overview

This standalone Python script automates the entire blog creation and publishing workflow:

1. Selects a content category intelligently
2. Fetches trending tech news for context
3. Generates unique, relevant topics using AI
4. Validates topic uniqueness (70% similarity threshold)
5. Creates comprehensive blog posts (1200-1500 words)
6. Publishes directly to your Hashnode blog
7. Tracks everything in MongoDB

**No scheduler, no FastAPI, no complexity** - just run the script whenever you want to publish a new blog post!

---

## Features

### AI-Powered Content Generation
- **Google Gemini AI** integration for intelligent topic and content generation
- Context-aware topics based on trending tech news
- SEO-optimized blog posts with meta descriptions and tags

### Intelligent Uniqueness Detection
- **70% similarity threshold** using combined Jaccard + Sequence matching
- Checks against **6 months** of historical topics
- Prevents duplicate or highly similar content

### Smart Category Management
- **8 pre-configured categories**: Web Development, AI & Machine Learning, DevOps, Cybersecurity, Cloud Computing, Mobile Development, Data Science, Blockchain
- Fair rotation to ensure balanced content
- Easy to add custom categories

### Robust Error Handling
- **Exponential backoff retry logic** for API calls (2s, 4s, 8s delays)
- Up to **5 attempts** to find unique topics
- Graceful handling of API rate limits and overload

### Rate Limit Protection
- **10-30 second random delays** between each step
- Prevents API throttling
- Respects service rate limits

### Comprehensive Logging
- Detailed progress logs with timestamps
- Emoji indicators for easy scanning
- Full error stack traces for debugging

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  1. SELECT CATEGORY (Random from active categories)     │
│     ↓ Sleep 10-30s                                       │
│  2. FETCH TRENDING NEWS (NewsData.io API)               │
│     ↓ Sleep 10-30s                                       │
│  3. GENERATE TOPIC (Google Gemini AI)                   │
│     ↓ Sleep 10-30s                                       │
│  4. CHECK UNIQUENESS (70% similarity threshold)         │
│     ↓ Retry up to 5 times if duplicate                  │
│     ↓ Sleep 10-30s                                       │
│  5. STORE TOPIC (MongoDB)                               │
│     ↓ Sleep 10-30s                                       │
│  6. GENERATE BLOG (1200-1500 words, Gemini AI)         │
│     ↓ Sleep 10-30s                                       │
│  7. STORE BLOG (MongoDB)                                │
│     ↓ Sleep 10-30s                                       │
│  8. PUBLISH TO HASHNODE (GraphQL API)                   │
│     ↓                                                     │
│  9. UPDATE DATABASE (Post ID, URL, timestamps)          │
│     ↓                                                     │
│ 10. SUCCESS! (Show total time and publication URL)      │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### System Requirements
- **Python 3.9+** (tested on Python 3.13)
- **MongoDB** (local or cloud instance like MongoDB Atlas)
- **Internet connection** (for API calls)

### Required API Keys
You'll need free accounts and API keys from:

1. **Google Gemini AI** - [Get API Key](https://ai.google.dev/)
   - Free tier available
   - Used for topic and blog generation

2. **Hashnode** - [Get API Token](https://hashnode.com/settings/developer)
   - Free blogging platform
   - GraphQL API for publishing

3. **NewsData.io** - [Get API Key](https://newsdata.io/register)
   - Free tier: 200 requests/day
   - Used for trending tech news

4. **AWS S3** (Optional) - [AWS Console](https://aws.amazon.com/)
   - Only needed if you want cover images
   - Can be disabled with `ENABLE_BLOG_IMAGES=false`

---

## Installation

### 1. Clone or Download the Repository

```bash
cd /path/to/your/projects
# If you have the code, navigate to the directory
cd Blog-Automation
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up MongoDB

**Option A: Local MongoDB**
```bash
# Install MongoDB Community Edition
# On Ubuntu/Debian:
sudo apt-get install mongodb

# Start MongoDB
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

**Option B: MongoDB Atlas (Cloud)**
1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster
3. Get connection string (looks like: `mongodb+srv://user:pass@cluster.mongodb.net/`)
4. Use this in your `.env` file

### 5. Initialize Categories

```bash
python3 init_categories.py
```

This creates 8 default categories in your database.

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# ===== REQUIRED: MongoDB Configuration =====
MONGODB_URL=mongodb://localhost:27017
# For MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=blog_automation

# ===== REQUIRED: API Keys =====
# Google Gemini AI (https://ai.google.dev/)
GEMINI_API_KEY=your_gemini_api_key_here

# Hashnode (https://hashnode.com/settings/developer)
HASHNODE_API_TOKEN=your_hashnode_token_here
HASHNODE_PUBLICATION_ID=your_publication_id_here

# NewsData.io (https://newsdata.io/)
NEWSDATA_API_KEY=your_newsdata_api_key_here

# ===== OPTIONAL: Application Settings =====
ENVIRONMENT=development
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
TIMEZONE=Asia/Kolkata

# ===== OPTIONAL: AWS S3 (for cover images) =====
# Set ENABLE_BLOG_IMAGES=false if you don't want images
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
```

### Important Notes

**Getting your Hashnode Publication ID:**
1. Go to your Hashnode dashboard
2. Open your publication settings
3. The publication ID is in the URL or can be found via GraphQL query

**Disabling Image Generation:**
If you don't want to use AWS S3 for cover images, add:
```env
ENABLE_BLOG_IMAGES=false
```

---

## Usage

### Quick Start with Makefile (Recommended)

The easiest way to use the blog automation with **automatic error recovery**:

```bash
# Complete setup (first time only)
make setup

# Run the blog automation (auto-recovers from missing categories!)
make run

# Or use safe mode (never fails, perfect for cron jobs)
make run-safe

# Check database status
make check-db

# View all available commands
make help
```

**New Feature:** `make run` now automatically initializes the database if categories are missing! See [AUTO_RECOVERY.md](AUTO_RECOVERY.md) for details.

### Makefile Commands

```bash
# Setup Commands
make setup         # Complete setup (install + init-db)
make install       # Install dependencies only
make init-db       # Initialize database (interactive)
make init-db-force # Force reinitialize database
make check-db      # Check database connection

# Run Commands
make run           # Run the blog automation script

# Docker Commands
make docker-build  # Build Docker image
make docker-run    # Run in Docker container
make docker-stop   # Stop Docker container

# Utility Commands
make clean         # Clean up venv and cache
make logs          # View application logs
make test          # Run tests
```

### Alternative Methods

**Using the shell script:**
```bash
chmod +x run.sh
./run.sh
```

**Direct execution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Run the script
python3 run_blog_automation.py
```

### What Happens When You Run

1. Script initializes services (MongoDB, Gemini, NewsData, Hashnode)
2. Selects a random active category
3. Fetches latest tech news (10-20 articles)
4. Generates a unique topic (retries up to 5 times if needed)
5. Creates comprehensive blog post with:
   - SEO-optimized title
   - 1200-1500 word content
   - Meta description (150-160 characters)
   - 3-7 relevant tags
6. Publishes to your Hashnode blog
7. Shows success message with publication URL

**Total Time:** Approximately 3-5 minutes (including sleep delays)

---

## Project Structure

```
Blog-Automation/
│
├── run_blog_automation.py      # ⭐ Main script - Run this!
├── init_categories.py          # Initialize database categories
├── run.sh                      # Quick run helper script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this!)
├── .gitignore                  # Git ignore rules
│
├── README.md                   # This file
├── USAGE.md                    # Detailed usage examples
├── SETUP_COMPLETE.md           # Setup verification guide
├── FINAL_STATUS.md             # Current project status
│
├── config/                     # Configuration
│   ├── settings.py            # Settings loader (reads .env)
│   ├── logging_config.py      # Logging configuration
│   └── __init__.py
│
├── app/                        # Application code
│   ├── __init__.py
│   │
│   ├── models/                 # Database models
│   │   ├── database.py        # MongoDB connection (sync & async)
│   │   ├── models.py          # Document schemas
│   │   └── __init__.py
│   │
│   ├── services/               # External API integrations
│   │   ├── gemini_service.py       # Google Gemini AI
│   │   ├── hashnode_service.py     # Hashnode GraphQL API
│   │   ├── newsdata_service.py     # NewsData.io API
│   │   ├── image_upload_service.py # AWS S3 uploads (optional)
│   │   └── __init__.py
│   │
│   └── utils/                  # Utility functions
│       ├── uniqueness.py      # Similarity detection
│       └── __init__.py
│
├── logs/                       # Application logs
│   └── app.log                # Structured JSON logs
│
├── temp_images/                # Temporary image storage
│   └── .gitkeep
│
└── venv/                       # Python virtual environment
```

---

## Output Example

```
============================================================
🚀 BLOG AUTOMATION SCRIPT STARTED
============================================================
📁 Fetching a random category...
✓ Selected category: Cybersecurity
Category selected (sleeping for 18s)

🔄 Starting unique topic search (max 5 attempts)...

--- Attempt 1/5 ---
🤖 Generating topic for category: Cybersecurity
📰 Fetching trending tech news...
Successfully fetched 10 tech articles from newsdata.io
News fetched successfully (sleeping for 12s)

🎯 Calling Gemini AI to generate topic...
✓ Generated topic: Securing Your Digital Aura: Protecting Privacy with AI Smart Glasses in 2025

Topic generated, checking uniqueness (sleeping for 23s)

🔍 Checking uniqueness for: Securing Your Digital Aura...
📊 Comparing against 2 topics and 2 history records
✓ Topic is unique!
🎉 Found unique topic on attempt 1!

Unique topic found (sleeping for 21s)

💾 Storing topic in database...
✓ Topic stored with ID: 6942e3413f2c8d9f15f9474a
Topic stored (sleeping for 18s)

📝 Generating blog content for: Securing Your Digital Aura...
✓ Blog generated successfully!
   Title: Securing Your Digital Aura: AI Smart Glasses Privacy Guide
   Word Count: 1456
   Tags: cybersecurity, privacy, ai, wearables, smart-glasses

Blog content generated (sleeping for 27s)

💾 Storing blog in database...
✓ Blog stored with ID: 6942e4b6744d06c397c57494
Blog stored (sleeping for 26s)

🚀 Publishing blog to Hashnode...
✓ Blog published successfully!
   Post ID: 6942e4b7744d06c397c57495
   URL: https://yourblog.hashnode.dev/securing-your-digital-aura

============================================================
✅ BLOG AUTOMATION COMPLETED SUCCESSFULLY!
⏱️  Total time: 245.67 seconds
============================================================
```

---

## Error Handling

### What the Script Does

1. **Topic Not Unique?**
   - Tries up to 5 times to generate a different topic
   - Each attempt checks against 6 months of history
   - Exits with error if all attempts fail

2. **API Rate Limited?**
   - Implements exponential backoff (2s, 4s, 8s)
   - Respects `Retry-After` headers
   - Max 3 retry attempts per API call

3. **Gemini API Overloaded (503)?**
   - Automatically retries with delays
   - Logs the issue clearly
   - This is a temporary Google API issue

4. **Network Issues?**
   - Timeout after 60 seconds per request
   - Clear error messages with stack traces
   - Database operations remain consistent

5. **Publishing Fails?**
   - Checks for valid response structure
   - Updates database only on success
   - Stores draft if publishing fails

### Exit Codes

The script returns specific exit codes to help with automation and error handling:

| Code | Meaning | Solution |
|------|---------|----------|
| `0` | Success | Blog published successfully |
| `1` | General error | Check logs for details |
| `2` | User interrupted | Script was stopped by user (Ctrl+C) |
| `3` | No categories in database | Run `make init-db` or `python3 init_categories.py` |
| `4` | No unique topic found | All 5 attempts produced duplicate topics, try again later |
| `5` | Blog generation failed | Gemini AI failed to generate content, check API key |
| `6` | Publishing failed | Hashnode API error, check token and publication ID |

**Checking Exit Codes:**
```bash
# Run script and check exit code
make run
echo "Exit code: $?"

# Or with direct Python
python3 run_blog_automation.py
echo "Exit code: $?"

# Use in shell scripts
if make run; then
    echo "Success!"
else
    echo "Failed with exit code: $?"
fi
```

---

## Troubleshooting

### Common Issues

#### 1. "No active categories found in database" (Exit Code: 3)

**Solution:**
```bash
# Using Makefile (recommended)
make init-db

# Or directly
python3 init_categories.py

# Force reinitialize (non-interactive)
python3 init_categories.py --force
```

#### 2. "ModuleNotFoundError: No module named 'X'"

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. "Authentication error: Invalid API token"

**Solution:**
- Check your API keys in `.env`
- Ensure no extra spaces or quotes
- Verify keys are active on respective platforms

#### 4. "MongoDB connection refused"

**Solution:**
- Check MongoDB is running: `sudo systemctl status mongodb`
- Verify connection string in `.env`
- For Atlas, check IP whitelist settings

#### 5. "503 UNAVAILABLE - The model is overloaded"

**Solution:**
- This is a temporary Google Gemini API issue
- The script retries automatically
- Try running the script again later
- Peak times may have higher load

#### 6. "Failed to publish: Invalid response from Hashnode"

**Solution:**
- Verify `HASHNODE_PUBLICATION_ID` is correct
- Check your Hashnode API token is valid
- Ensure publication is not private/draft

---

## API Information

### Google Gemini AI
- **Model Used:** `gemini-2.5-flash`
- **Temperature:** 0.7 (balanced creativity)
- **Max Retries:** 3 with exponential backoff
- **Timeout:** 60 seconds
- **Rate Limits:** Handled automatically

### Hashnode GraphQL API
- **Endpoint:** `https://gql.hashnode.com/`
- **Authentication:** Bearer token
- **Operations:** `publishPost` mutation
- **Rate Limits:** Automatic retry with backoff

### NewsData.io API
- **Free Tier:** 200 requests/day
- **Articles per Request:** 10-20
- **Category:** Technology
- **Language:** English
- **Lookback:** Last 2 days

### MongoDB
- **Collections:** 5 (categories, topics, blogs, generation_history, logs)
- **Connection Pool:** 1-10 connections
- **Timeout:** 30 seconds
- **Indexes:** Optimized for frequent queries

---

## Database Schema

### Collections

**1. categories**
```json
{
  "_id": ObjectId,
  "name": "Web Development",
  "description": "Modern web technologies...",
  "is_active": true,
  "usage_count": 5,
  "last_used_date": ISODate,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**2. topics**
```json
{
  "_id": ObjectId,
  "title": "Topic title",
  "category_id": ObjectId,
  "category_name": "Category",
  "status": "PENDING|IN_PROGRESS|COMPLETED",
  "scheduled_date": ISODate,
  "hash": "sha256_hash",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

**3. blogs**
```json
{
  "_id": ObjectId,
  "topic_id": ObjectId,
  "category_id": ObjectId,
  "title": "Blog title",
  "content": "Full markdown content",
  "meta_description": "SEO description",
  "tags": ["tag1", "tag2"],
  "word_count": 1456,
  "status": "DRAFT|PUBLISHED",
  "hashnode_post_id": "post_id",
  "hashnode_url": "https://...",
  "published_at": ISODate,
  "created_at": ISODate,
  "updated_at": ISODate
}
```

---

## Advanced Configuration

### Customizing Settings

Edit `config/settings.py` to change:

- **Similarity Threshold:** `SIMILARITY_THRESHOLD = 0.7` (70%)
- **History Lookback:** `HISTORY_LOOKBACK_MONTHS = 6`
- **Topic Attempts:** Modify in script: `max_topic_attempts = 5`
- **Word Count:** `MIN_BLOG_WORD_COUNT = 1000`, `MAX_BLOG_WORD_COUNT = 2000`
- **Tags Count:** `MIN_TAGS_COUNT = 3`, `MAX_TAGS_COUNT = 7`

### Adding Custom Categories

```python
python3
>>> from app.models.database import get_sync_db
>>> db = get_sync_db()
>>> db.categories.insert_one({
...     "name": "IoT & Edge Computing",
...     "description": "Internet of Things and edge computing topics",
...     "is_active": True,
...     "usage_count": 0,
...     "last_used_date": None
... })
```

---

## Contributing

This is a personal automation project, but improvements are welcome!

### Areas for Improvement
- [ ] Add image generation using Stable Diffusion or DALL-E
- [ ] Support multiple blog platforms (Medium, Dev.to)
- [ ] Add scheduling capability (cron integration)
- [ ] Implement content calendar
- [ ] Add A/B testing for titles
- [ ] Multi-language support

---

## License

This project is for personal use. Modify as needed for your own blog automation.

---

## Credits

**Built with:**
- [Google Gemini AI](https://ai.google.dev/) - Content generation
- [Hashnode](https://hashnode.com/) - Blog hosting
- [NewsData.io](https://newsdata.io/) - Trending news
- [MongoDB](https://www.mongodb.com/) - Database
- [Python](https://www.python.org/) - Core language

---

## Support

For issues or questions:
1. Check [TROUBLESHOOTING](#troubleshooting) section
2. Review [SETUP_COMPLETE.md](SETUP_COMPLETE.md) for setup verification
3. Check logs in `logs/app.log`

---

**Happy Blogging! 🚀**
