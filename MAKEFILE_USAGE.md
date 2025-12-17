# Makefile Usage Guide

Complete guide for using the Makefile to manage your blog automation project.

## Quick Start

```bash
# First time setup
make setup

# Run the blog automation
make run

# That's it! 🎉
```

## All Available Commands

### Setup Commands

#### `make setup`
Complete setup including installation and database initialization.
```bash
make setup
```
This will:
1. Create virtual environment
2. Install all dependencies
3. Initialize database with default categories
4. Prepare project for first run

**When to use**: First time setting up the project, or after a `make clean`

---

#### `make install`
Install dependencies only without database initialization.
```bash
make install
```
This will:
1. Create Python virtual environment
2. Upgrade pip
3. Install all requirements from `requirements.txt`

**When to use**:
- First time setup (if you want to initialize DB manually later)
- After adding new dependencies to `requirements.txt`
- After `make clean`

---

#### `make init-db`
Initialize database with categories (interactive mode).
```bash
make init-db
```
This will:
1. Connect to MongoDB
2. Check for existing categories
3. Ask for confirmation if categories exist
4. Insert default categories

**When to use**:
- First time database setup
- When you want control over reinitializing

---

#### `make init-db-force`
Force reinitialize database without confirmation.
```bash
make init-db-force
```
This will:
1. Connect to MongoDB
2. Clear existing categories (no confirmation)
3. Insert default categories

**When to use**:
- Automated scripts
- When you definitely want to reset categories
- Part of `make setup`

---

#### `make check-db`
Check database connection and category status.
```bash
make check-db
```
This will:
1. Test MongoDB connection
2. Count total categories
3. Count active categories
4. Warn if no active categories

**Output example**:
```
Checking database...
✅ Database connected!
Total categories: 8
Active categories: 8
```

**When to use**:
- Troubleshooting connection issues
- Verifying setup before running
- After database changes

---

### Run Commands

#### `make run`
Run the blog automation script.
```bash
make run
```
This will:
1. Check if venv exists (installs if not)
2. Run `run_blog_automation.py`
3. Display appropriate message based on exit code

**Output examples**:
```
✅ Script completed successfully (exit code: 0)
❌ No categories found. Run 'make init-db' first (exit code: 3)
❌ Could not find unique topic (exit code: 4)
❌ Blog generation failed (exit code: 5)
❌ Blog publishing failed (exit code: 6)
```

**Exit codes**: See [EXIT_CODES.md](EXIT_CODES.md) for details

---

### Docker Commands

#### `make docker-build`
Build Docker image for the application.
```bash
make docker-build
```
This will:
1. Build Docker image from Dockerfile
2. Tag as `blog-automation`

**When to use**:
- First time Docker setup
- After code changes
- After Dockerfile modifications

---

#### `make docker-run`
Run application in Docker container.
```bash
make docker-run
```
This will:
1. Start container in detached mode
2. Load environment variables from `.env`
3. Mount logs and temp_images directories
4. Expose port 8000

**When to use**:
- Running in production
- Isolated environment needed
- After `make docker-build`

---

#### `make docker-stop`
Stop and remove Docker container.
```bash
make docker-stop
```
This will:
1. Stop running container
2. Remove container

**When to use**:
- Stopping the application
- Before rebuilding image
- Cleanup

---

### Utility Commands

#### `make clean`
Remove virtual environment and cache files.
```bash
make clean
```
This will:
1. Remove `venv` directory
2. Remove all `__pycache__` directories
3. Remove `*.pyc` files
4. Remove `*.egg-info` directories
5. Remove `.pytest_cache`
6. Clear `temp_images/`

**When to use**:
- Fresh start needed
- Disk space cleanup
- Before committing to git
- Troubleshooting dependency issues

**Note**: After `make clean`, you'll need to run `make setup` or `make install`

---

#### `make logs`
View application logs in real-time.
```bash
make logs
```
This will:
1. Tail the `logs/app.log` file
2. Show new entries as they appear

**When to use**:
- Monitoring script execution
- Debugging issues
- Watching progress

**To exit**: Press `Ctrl+C`

---

#### `make test`
Run tests (if available).
```bash
make test
```
This will:
1. Run pytest on `tests/` directory

**When to use**:
- After code changes
- Before committing
- CI/CD pipeline

**Note**: Currently shows "No tests found" if no tests exist

---

#### `make help`
Display all available commands and exit codes.
```bash
make help
# or just
make
```
This will:
1. Show all available commands
2. List exit codes and their meanings

---

## Common Workflows

### First Time Setup

```bash
# Complete setup
make setup

# Verify everything works
make check-db

# Run your first blog
make run
```

### Daily Usage

```bash
# Just run it!
make run
```

### After Git Pull

```bash
# Update dependencies
make install

# Run
make run
```

### Clean Start

```bash
# Clean everything
make clean

# Fresh setup
make setup

# Run
make run
```

### Troubleshooting

```bash
# Check database
make check-db

# If no categories
make init-db-force

# Check logs
make logs

# Clean and reinstall
make clean
make setup
```

### Docker Workflow

```bash
# Build image
make docker-build

# Run in Docker
make docker-run

# Check logs (from host)
make logs

# Stop when done
make docker-stop
```

### Development Workflow

```bash
# Make code changes
# ...

# Test locally
make run

# Build Docker image
make docker-build

# Test in Docker
make docker-run

# Check logs
make logs

# Stop Docker
make docker-stop
```

## Automated Usage

### Cron Job Example

```bash
# Add to crontab (crontab -e)
# Run every day at 9 AM
0 9 * * * cd /home/shivam/App/Work/Phrase_trade/Blog-Automation && make run >> /var/log/blog-automation.log 2>&1
```

### Shell Script Example

```bash
#!/bin/bash

cd /path/to/Blog-Automation

# Run with error handling
if make run; then
    echo "Blog published successfully at $(date)"
else
    EXIT_CODE=$?
    echo "Failed with exit code: $EXIT_CODE at $(date)"

    # Handle specific errors
    if [ $EXIT_CODE -eq 3 ]; then
        echo "Initializing database..."
        make init-db-force
        make run  # Retry
    fi
fi
```

## Tips & Tricks

### 1. Check Exit Codes
```bash
make run
echo "Exit code: $?"
```

### 2. Run in Background
```bash
# Run in background
nohup make run > output.log 2>&1 &

# Check progress
tail -f output.log
```

### 3. Chain Commands
```bash
# Clean, setup, and run
make clean && make setup && make run
```

### 4. Conditional Execution
```bash
# Only run if database check passes
make check-db && make run
```

### 5. Silent Mode
```bash
# Suppress most output
make run > /dev/null
```

### 6. Force Reinstall
```bash
# Completely fresh environment
make clean
rm -rf venv
make install
```

## Environment Variables

The Makefile uses these variables (you can override):

```bash
# Override Python version
make install PYTHON=python3.11

# Override virtual environment location
make install VENV=myenv

# Override Docker image name
make docker-build DOCKER_IMAGE=my-blog-automation
```

## Troubleshooting

### "make: command not found"
Install make:
```bash
# Ubuntu/Debian
sudo apt-get install make

# macOS (usually pre-installed)
brew install make
```

### "Virtual environment not found"
Run:
```bash
make install
```

### "No active categories"
Run:
```bash
make init-db
```

### Permission denied
Make sure you're in the project directory:
```bash
cd /home/shivam/App/Work/Phrase_trade/Blog-Automation
```

### Docker not found
Install Docker:
```bash
# Ubuntu/Debian
sudo apt-get install docker.io
```

## Exit Codes

See [EXIT_CODES.md](EXIT_CODES.md) for complete exit code reference.

Quick reference:
- `0` - Success
- `1` - General error
- `2` - User interrupted
- `3` - No categories (run `make init-db`)
- `4` - No unique topic
- `5` - Blog generation failed
- `6` - Publishing failed

## Related Files

- `Makefile` - The actual Makefile
- `run_blog_automation.py` - Main script
- `init_categories.py` - Database initialization
- `requirements.txt` - Python dependencies
- `.env` - Environment configuration
- `EXIT_CODES.md` - Exit code reference
- `README.md` - Project documentation

## Support

For issues:
1. Check `make help`
2. Review [EXIT_CODES.md](EXIT_CODES.md)
3. Check logs: `make logs`
4. Review [README.md](README.md)

---

**Happy Automating! 🚀**
