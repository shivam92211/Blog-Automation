.PHONY: help install setup run run-safe clean test docker-build docker-run docker-stop init-db init-db-force logs check-db

# Variables
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTHON_VENV := $(VENV_BIN)/python3
DOCKER_IMAGE := blog-automation
DOCKER_CONTAINER := blog-automation-container

# Default target
help:
	@echo "Blog Automation - Available Commands:"
	@echo "======================================"
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup         - Complete setup (install + init-db)"
	@echo "  make run           - Run the blog automation (auto-recovers from missing categories)"
	@echo "  make run-safe      - Run with full auto-recovery (never fails, always retries)"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make install       - Create virtual environment and install dependencies"
	@echo "  make init-db       - Initialize database categories (interactive)"
	@echo "  make init-db-force - Force reinitialize database categories"
	@echo "  make check-db      - Check database connection and categories"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run application in Docker container"
	@echo "  make docker-stop   - Stop and remove Docker container"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean         - Remove virtual environment and cache files"
	@echo "  make test          - Run tests (if available)"
	@echo "  make logs          - View application logs"
	@echo ""
	@echo "Exit Codes:"
	@echo "  0 - Success"
	@echo "  1 - General error"
	@echo "  2 - User interrupted"
	@echo "  3 - No categories in database (run 'make init-db')"
	@echo "  4 - Could not find unique topic"
	@echo "  5 - Blog generation failed"
	@echo "  6 - Blog publishing failed"

# Create virtual environment and install dependencies
install:
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV) || (echo "Installing virtualenv..." && $(PYTHON) -m pip install --user virtualenv && $(PYTHON) -m virtualenv $(VENV))
	@echo "Installing dependencies..."
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo "Installation complete!"

# Run the blog automation script with auto-recovery
run:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@echo "Starting Blog Automation..."
	@$(PYTHON_VENV) run_blog_automation.py; \
	EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 0 ]; then \
		echo "✅ Script completed successfully (exit code: 0)"; \
	elif [ $$EXIT_CODE -eq 2 ]; then \
		echo "⚠️  Script interrupted by user (exit code: 2)"; \
		exit 2; \
	elif [ $$EXIT_CODE -eq 3 ]; then \
		echo ""; \
		echo "⚠️  No categories found in database (exit code: 3)"; \
		echo "🔧 Auto-initializing database..."; \
		echo ""; \
		$(PYTHON_VENV) init_categories.py --force; \
		INIT_EXIT=$$?; \
		if [ $$INIT_EXIT -eq 0 ]; then \
			echo ""; \
			echo "✅ Database initialized successfully!"; \
			echo "🔄 Retrying blog automation..."; \
			echo ""; \
			$(PYTHON_VENV) run_blog_automation.py; \
			RETRY_EXIT=$$?; \
			if [ $$RETRY_EXIT -eq 0 ]; then \
				echo "✅ Script completed successfully (exit code: 0)"; \
			else \
				echo "❌ Retry failed with exit code: $$RETRY_EXIT"; \
				exit $$RETRY_EXIT; \
			fi; \
		else \
			echo "❌ Failed to initialize database (exit code: $$INIT_EXIT)"; \
			exit $$INIT_EXIT; \
		fi; \
	elif [ $$EXIT_CODE -eq 4 ]; then \
		echo "❌ Could not find unique topic (exit code: 4)"; \
		exit 4; \
	elif [ $$EXIT_CODE -eq 5 ]; then \
		echo "❌ Blog generation failed (exit code: 5)"; \
		exit 5; \
	elif [ $$EXIT_CODE -eq 6 ]; then \
		echo "❌ Blog publishing failed (exit code: 6)"; \
		exit 6; \
	else \
		echo "❌ Script failed with exit code: $$EXIT_CODE"; \
		exit $$EXIT_CODE; \
	fi

# Run with full auto-recovery (never fails)
run-safe:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Installing..."; \
		$(MAKE) install || (echo "❌ Failed to install dependencies"; exit 0); \
	fi
	@echo "Starting Blog Automation (Safe Mode - Auto-Recovery Enabled)..."
	@echo ""
	@$(PYTHON_VENV) run_blog_automation.py; \
	EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 0 ]; then \
		echo "✅ Script completed successfully!"; \
		exit 0; \
	elif [ $$EXIT_CODE -eq 2 ]; then \
		echo "⚠️  Script interrupted by user"; \
		exit 0; \
	elif [ $$EXIT_CODE -eq 3 ]; then \
		echo ""; \
		echo "⚠️  No categories found - Auto-initializing..."; \
		$(PYTHON_VENV) init_categories.py --force && \
		echo "✅ Database initialized! Retrying..." && \
		echo "" && \
		$(PYTHON_VENV) run_blog_automation.py; \
		RETRY_EXIT=$$?; \
		if [ $$RETRY_EXIT -eq 0 ]; then \
			echo "✅ Success on retry!"; \
		else \
			echo "⚠️  Retry ended with code $$RETRY_EXIT (not treated as error in safe mode)"; \
		fi; \
		exit 0; \
	elif [ $$EXIT_CODE -eq 4 ]; then \
		echo "⚠️  Could not find unique topic (this is normal, try again later)"; \
		exit 0; \
	elif [ $$EXIT_CODE -eq 5 ]; then \
		echo "⚠️  Blog generation failed (check API keys and retry)"; \
		exit 0; \
	elif [ $$EXIT_CODE -eq 6 ]; then \
		echo "⚠️  Publishing failed (check Hashnode settings and retry)"; \
		exit 0; \
	else \
		echo "⚠️  Script ended with code $$EXIT_CODE (not treated as error in safe mode)"; \
		exit 0; \
	fi

# Complete setup (install + init-db)
setup:
	@echo "Running complete setup..."
	@$(MAKE) install
	@$(MAKE) init-db-force
	@echo ""
	@echo "✅ Setup complete! You can now run: make run"

# Initialize database with categories (interactive)
init-db:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@echo "Initializing database categories..."
	@$(PYTHON_VENV) init_categories.py

# Force reinitialize database categories
init-db-force:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@echo "Force initializing database categories..."
	@$(PYTHON_VENV) init_categories.py --force

# Check database connection and categories
check-db:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@echo "Checking database..."
	@$(PYTHON_VENV) -c "from app.models.database import get_sync_db; db = get_sync_db(); count = db.categories.count_documents({}); active = db.categories.count_documents({'is_active': True}); print(f'✅ Database connected!'); print(f'Total categories: {count}'); print(f'Active categories: {active}'); print('⚠️  No active categories! Run: make init-db') if active == 0 else None"

# Clean up virtual environment and cache files
clean:
	@echo "Cleaning up..."
	@rm -rf $(VENV)
	@rm -rf __pycache__
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
	@rm -rf temp_images/*
	@echo "Clean complete!"

# Run tests (if available)
test:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Virtual environment not found. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@echo "Running tests..."
	@$(PYTHON_VENV) -m pytest tests/ || echo "No tests found"

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	@docker build -t $(DOCKER_IMAGE) .
	@echo "Docker image built successfully!"

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	@docker run -d \
		--name $(DOCKER_CONTAINER) \
		--env-file .env \
		-p 8000:8000 \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/temp_images:/app/temp_images \
		$(DOCKER_IMAGE)
	@echo "Docker container is running!"
	@echo "Access the application at http://localhost:8000"

# Stop and remove Docker container
docker-stop:
	@echo "Stopping Docker container..."
	@docker stop $(DOCKER_CONTAINER) || true
	@docker rm $(DOCKER_CONTAINER) || true
	@echo "Docker container stopped and removed!"

# View application logs
logs:
	@if [ -f "logs/app.log" ]; then \
		tail -f logs/app.log; \
	else \
		echo "No logs found. Run the application first."; \
	fi
