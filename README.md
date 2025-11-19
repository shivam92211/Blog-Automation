# Blog Automation System

An intelligent blog generation and publishing system that automatically:
- Rotates through categories weekly
- Generates unique topics using Google Gemini AI
- Writes comprehensive blog posts daily
- Publishes to Hashnode automatically
- Prevents content repetition with smart duplicate detection

## 🏗️ Architecture

```
blog_automation/
├── app/
│   ├── models/          # Database models (SQLAlchemy)
│   ├── services/        # External API integrations (Gemini, Hashnode)
│   ├── jobs/            # Scheduled jobs (topic generation, blog publishing)
│   ├── utils/           # Utilities (uniqueness checker, helpers)
│   └── api/             # FastAPI REST endpoints
├── config/              # Configuration and logging
├── scripts/             # Database initialization and testing
├── logs/                # Application logs (created at runtime)
└── main.py             # Application entry point
```

## 📋 Features

### Automated Workflows
- **Weekly Topic Generation** (Monday 6 AM): Generates 7 unique topics for the week
- **Daily Blog Publishing** (Every day 9 AM): Writes and publishes one blog per day
- **Intelligent Category Rotation**: Ensures balanced content across all categories
- **Duplicate Detection**: Prevents similar topics using keyword analysis and hashing

### Manual Operations via API
- View/manage categories
- List upcoming topics
- View published blogs
- Manually trigger jobs
- Monitor system stats and logs

### Quality Assurance
- Word count validation (1200-1500 words target)
- SEO optimization (meta descriptions, tags)
- Content structure validation
- Real-time logging and monitoring

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9+
- PostgreSQL (or MySQL)
- Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Hashnode account with API token ([Get token](https://hashnode.com/settings/developer))

### 2. Installation

```bash
# Clone or navigate to project directory
cd blog_automation

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

**PostgreSQL:**
```bash
# Create database
createdb blog_automation

# Or using psql:
psql -U postgres -c "CREATE DATABASE blog_automation;"
```

**MySQL:**
```bash
# Create database
mysql -u root -p -e "CREATE DATABASE blog_automation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 4. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required environment variables:**
```env
# Database (choose one)
DATABASE_URL=postgresql://user:password@localhost:5432/blog_automation
# DATABASE_URL=mysql://user:password@localhost:3306/blog_automation

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
HASHNODE_API_TOKEN=your_hashnode_token_here
HASHNODE_PUBLICATION_ID=your_publication_id_here

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
ENABLE_SCHEDULER=true
TIMEZONE=UTC
```

**Finding your Hashnode Publication ID:**
1. Go to your Hashnode dashboard
2. Open browser DevTools (F12)
3. Go to Network tab
4. Click on your publication
5. Look for GraphQL requests - the publication ID will be in the payload

### 5. Initialize Database

```bash
# Create tables and seed initial categories
python scripts/init_db.py
```

This will create:
- 8 default categories (Blockchain, Web3, AI, etc.)
- All required database tables
- Indexes for optimal performance

### 6. Test Setup

```bash
# Validate configuration
python scripts/test_setup.py
```

This tests:
- Database connection
- Gemini API authentication
- Hashnode API authentication

### 7. Run Application

```bash
# Start the server
python main.py

# Or using uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will:
- Start the FastAPI server on http://localhost:8000
- Initialize the job scheduler
- Schedule automatic jobs

## 📅 Scheduled Jobs

### Topic Generation (Weekly)
- **Schedule**: Every Monday at 6:00 AM
- **Duration**: 5-10 minutes
- **What it does**:
  1. Selects next category (based on rotation)
  2. Fetches historical topics (6 months lookback)
  3. Generates 7 unique topics via Gemini AI
  4. Validates uniqueness (prevents duplicates)
  5. Schedules topics for Tuesday-Monday
  6. Stores in database

### Blog Publishing (Daily)
- **Schedule**: Every day at 9:00 AM
- **Duration**: 10-15 minutes
- **What it does**:
  1. Fetches today's scheduled topic
  2. Generates comprehensive blog content (1200-1500 words)
  3. Validates quality and structure
  4. Publishes to Hashnode
  5. Updates database with publication details

## 🔧 API Endpoints

Access the interactive API docs at: http://localhost:8000/docs

### Categories
- `GET /api/categories` - List all categories
- `POST /api/categories` - Create new category
- `PATCH /api/categories/{id}` - Update category

### Topics
- `GET /api/topics` - List topics (filterable by status)
- `GET /api/topics/upcoming` - View upcoming scheduled topics

### Blogs
- `GET /api/blogs` - List blogs (filterable by status)
- `GET /api/blogs/{id}` - Get full blog details

### Jobs (Manual Triggers)
- `POST /api/jobs/generate-topics` - Manually generate topics
- `POST /api/jobs/publish-blog` - Manually publish today's blog

### Scheduler
- `GET /api/scheduler/jobs` - View scheduled jobs
- `POST /api/scheduler/run/{job_id}` - Trigger job immediately

### Monitoring
- `GET /api/stats` - System statistics
- `GET /api/logs` - Job execution logs
- `GET /api/health` - Health check

## 📊 Usage Examples

### Add a New Category

```bash
curl -X POST "http://localhost:8000/api/categories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Science",
    "description": "Machine learning, data analysis, and statistics",
    "is_active": true
  }'
```

### View Upcoming Topics

```bash
curl "http://localhost:8000/api/topics/upcoming?days=7"
```

### Manually Generate Topics

```bash
curl -X POST "http://localhost:8000/api/jobs/generate-topics"
```

### Check System Stats

```bash
curl "http://localhost:8000/api/stats"
```

### View Recent Logs

```bash
curl "http://localhost:8000/api/logs?limit=10"
```

## 🔍 Monitoring & Debugging

### Log Files

Logs are stored in `logs/app.log` with structured JSON format:

```json
{
  "timestamp": "2025-11-03T09:15:23Z",
  "level": "INFO",
  "job": "blog_publisher",
  "topic_id": 123,
  "action": "blog_published",
  "details": {
    "word_count": 1450,
    "hashnode_url": "https://...",
    "execution_time_seconds": 87
  }
}
```

### View Logs

```bash
# Real-time monitoring
tail -f logs/app.log

# Filter by level
grep "ERROR" logs/app.log

# Pretty print JSON logs
cat logs/app.log | jq '.'
```

### Database Queries

```sql
-- Check pending topics
SELECT * FROM topics WHERE status = 'pending' ORDER BY scheduled_date;

-- Check published blogs count
SELECT COUNT(*) FROM blogs WHERE status = 'published';

-- Category usage statistics
SELECT name, usage_count, last_used_date FROM categories ORDER BY usage_count DESC;

-- Recent job logs
SELECT * FROM logs ORDER BY created_at DESC LIMIT 10;
```

## 🛠️ Configuration Options

### Scheduling

Edit `config/settings.py`:

```python
# Topic generation: Every Monday at 6 AM
TOPIC_GENERATION_SCHEDULE = {
    "hour": 6,
    "minute": 0,
    "day_of_week": "mon"
}

# Blog publishing: Every day at 9 AM
BLOG_PUBLISHING_SCHEDULE = {
    "hour": 9,
    "minute": 0
}
```

### Content Settings

```python
# Topic generation
TOPIC_COUNT_PER_WEEK = 7
SIMILARITY_THRESHOLD = 0.7  # 70% similarity = duplicate
HISTORY_LOOKBACK_MONTHS = 6

# Blog requirements
MIN_BLOG_WORD_COUNT = 1000
MAX_BLOG_WORD_COUNT = 2000
TARGET_BLOG_WORD_COUNT = 1400
MIN_TAGS_COUNT = 3
MAX_TAGS_COUNT = 7
```

### AI Model Settings

```python
GEMINI_MODEL = "gemini-1.5-pro"
GEMINI_TEMPERATURE = 0.7
API_MAX_RETRIES = 3
```

## 🚨 Troubleshooting

### Issue: Topics are repetitive

**Solution:**
1. Check `SIMILARITY_THRESHOLD` (lower = stricter)
2. Review generation history: `SELECT * FROM generation_history`
3. Add more variety to category descriptions
4. Increase `HISTORY_LOOKBACK_MONTHS`

### Issue: Blog quality is poor

**Solution:**
1. Review Gemini prompt in `app/services/gemini_service.py`
2. Adjust `GEMINI_TEMPERATURE` (lower = more focused)
3. Add more specific requirements to prompt
4. Check if using correct model (`gemini-1.5-pro`)

### Issue: Job didn't run

**Solution:**
1. Check scheduler status: `curl http://localhost:8000/api/scheduler/jobs`
2. Verify `ENABLE_SCHEDULER=true` in `.env`
3. Check logs: `grep "STARTED" logs/app.log`
4. Manually trigger: `curl -X POST http://localhost:8000/api/jobs/generate-topics`

### Issue: Database connection error

**Solution:**
1. Verify database is running: `pg_isready` (PostgreSQL) or `mysqladmin ping` (MySQL)
2. Check `DATABASE_URL` in `.env`
3. Test connection: `python scripts/test_setup.py`
4. Check credentials and permissions

### Issue: Hashnode publishing fails

**Solution:**
1. Verify API token: `curl http://localhost:8000/api/health`
2. Check publication ID is correct
3. Test API: `python scripts/test_setup.py`
4. Check Hashnode API status
5. Review error logs: `grep "hashnode" logs/app.log -i`

## 📈 Scaling & Performance

### Database Optimization

The system includes optimized indexes:
- `topics(scheduled_date, status)` - Fast daily lookups
- `topics(category_id)` - Category filtering
- `generation_history(topic_hash)` - Duplicate detection
- `blogs(status)` - Status filtering

### API Rate Limits

- **Gemini API**: Uses exponential backoff retry
- **Hashnode API**: Respects rate limit headers
- Both: Configured with max 3 retries

### Scalability Options

For high-volume scenarios:
1. Switch to **Celery** for distributed job processing
2. Use **Redis** for caching category data
3. Implement **connection pooling** (already configured)
4. Add **load balancer** for API endpoints

## 🔐 Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use strong database passwords**
3. **Rotate API keys regularly**
4. **Enable CORS only for trusted origins** (edit `main.py`)
5. **Use HTTPS in production**
6. **Implement rate limiting** on API endpoints
7. **Regular database backups**

## 📦 Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use production database with backups
- [ ] Configure proper `DATABASE_URL` (use connection pooling)
- [ ] Set `LOG_LEVEL=WARNING` or `ERROR`
- [ ] Disable uvicorn `--reload` flag
- [ ] Use process manager (systemd, supervisor, PM2)
- [ ] Set up reverse proxy (Nginx, Apache)
- [ ] Enable HTTPS
- [ ] Configure proper CORS origins
- [ ] Set up monitoring (Sentry, Datadog, etc.)
- [ ] Schedule regular database backups
- [ ] Set up log rotation

### Systemd Service Example

```ini
[Unit]
Description=Blog Automation System
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/blog_automation
Environment="PATH=/var/www/blog_automation/venv/bin"
ExecStart=/var/www/blog_automation/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🤝 Contributing

To extend or modify the system:

1. **Add new category**: Use API or directly insert into database
2. **Modify prompts**: Edit `app/services/gemini_service.py`
3. **Adjust scheduling**: Edit `config/settings.py`
4. **Add new job**: Create in `app/jobs/` and register in scheduler
5. **Extend API**: Add routes in `app/api/routes.py`

## 📝 License

This project is provided as-is for educational and commercial use.

## 🆘 Support

For issues, questions, or suggestions:
1. Check troubleshooting section above
2. Review logs in `logs/app.log`
3. Test setup with `python scripts/test_setup.py`
4. Check API docs at `/docs`

---

**Built with:** FastAPI • SQLAlchemy • Google Gemini AI • Hashnode API • APScheduler

**Version:** 1.0.0
