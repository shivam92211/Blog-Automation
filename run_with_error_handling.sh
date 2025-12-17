#!/bin/bash
# Example script showing how to use exit codes for automation
# This script runs the blog automation and handles different exit codes

set -e  # Exit on error (but we'll handle specific cases)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Blog Automation Runner with Error Handling${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    make install
fi

source venv/bin/activate

# Run the blog automation
echo -e "${GREEN}Running blog automation...${NC}"
python3 run_blog_automation.py
EXIT_CODE=$?

# Handle different exit codes
case $EXIT_CODE in
    0)
        echo ""
        echo -e "${GREEN}✅ SUCCESS! Blog published successfully!${NC}"
        echo -e "${GREEN}Exit code: 0${NC}"
        exit 0
        ;;
    1)
        echo ""
        echo -e "${RED}❌ GENERAL ERROR${NC}"
        echo -e "${RED}Exit code: 1${NC}"
        echo "Check the logs for more details: logs/app.log"
        exit 1
        ;;
    2)
        echo ""
        echo -e "${YELLOW}⚠️  USER INTERRUPTED${NC}"
        echo -e "${YELLOW}Exit code: 2${NC}"
        echo "Script was stopped by user (Ctrl+C)"
        exit 2
        ;;
    3)
        echo ""
        echo -e "${RED}❌ NO CATEGORIES IN DATABASE${NC}"
        echo -e "${RED}Exit code: 3${NC}"
        echo "Solution: Run 'make init-db' to initialize categories"
        echo ""
        echo "Would you like to initialize categories now? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "Initializing categories..."
            python3 init_categories.py --force
            echo ""
            echo "Categories initialized! Run the script again."
        fi
        exit 3
        ;;
    4)
        echo ""
        echo -e "${YELLOW}⚠️  NO UNIQUE TOPIC FOUND${NC}"
        echo -e "${YELLOW}Exit code: 4${NC}"
        echo "All 5 attempts produced duplicate topics."
        echo "This can happen if you've recently published many blogs."
        echo "Try running the script again later or with a different category."
        exit 4
        ;;
    5)
        echo ""
        echo -e "${RED}❌ BLOG GENERATION FAILED${NC}"
        echo -e "${RED}Exit code: 5${NC}"
        echo "Gemini AI failed to generate content."
        echo "Possible causes:"
        echo "  - Invalid or expired GEMINI_API_KEY"
        echo "  - API rate limit reached"
        echo "  - Gemini API is overloaded (503 error)"
        echo "Check your .env file and API key status"
        exit 5
        ;;
    6)
        echo ""
        echo -e "${RED}❌ PUBLISHING FAILED${NC}"
        echo -e "${RED}Exit code: 6${NC}"
        echo "Failed to publish to Hashnode."
        echo "Possible causes:"
        echo "  - Invalid HASHNODE_API_TOKEN"
        echo "  - Wrong HASHNODE_PUBLICATION_ID"
        echo "  - Network connectivity issues"
        echo "Check your .env file and Hashnode settings"
        exit 6
        ;;
    *)
        echo ""
        echo -e "${RED}❌ UNKNOWN ERROR${NC}"
        echo -e "${RED}Exit code: $EXIT_CODE${NC}"
        echo "An unexpected error occurred."
        echo "Check the logs for more details: logs/app.log"
        exit $EXIT_CODE
        ;;
esac
