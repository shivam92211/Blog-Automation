#!/bin/bash
# Test script to demonstrate auto-recovery feature

set -e

echo "========================================"
echo "Testing Auto-Recovery Feature"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Installing dependencies first...${NC}"
    make install
fi

source venv/bin/activate

echo -e "${BLUE}Test 1: Clearing all categories${NC}"
python3 -c "from app.models.database import get_sync_db; db = get_sync_db(); result = db.categories.delete_many({}); print(f'Deleted {result.deleted_count} categories')"
echo ""

echo -e "${BLUE}Test 2: Checking database (should show 0 categories)${NC}"
make check-db
echo ""

echo -e "${YELLOW}Test 3: Running 'make run' (should auto-initialize and continue)${NC}"
echo -e "${YELLOW}This will detect no categories, initialize them, and retry${NC}"
echo ""
echo "Press Ctrl+C after you see it start working (it will take a while to complete)"
echo ""
sleep 3

# Note: This will actually run the blog automation, which takes time
# In a real test, we'd want to mock this or add a dry-run mode
echo "Running: make run"
echo ""

# Run with timeout so it doesn't take too long
timeout 60 make run || true

echo ""
echo -e "${GREEN}Test Complete!${NC}"
echo ""
echo -e "${BLUE}Final check - categories should exist:${NC}"
make check-db
