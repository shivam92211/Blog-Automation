#!/bin/bash
# Quick script to run scheduled test with times relative to now

source venv/bin/activate

# Calculate times: current time + 1, 4, 7 minutes
CURRENT=$(date +%s)
NEWS_TIME=$(date -d "@$((CURRENT + 60))" +%H:%M)      # +1 min
TOPIC_TIME=$(date -d "@$((CURRENT + 240))" +%H:%M)    # +4 min
BLOG_TIME=$(date -d "@$((CURRENT + 420))" +%H:%M)     # +7 min

echo "=================================="
echo "Running Scheduled Workflow Test"
echo "=================================="
echo ""
echo "Current time: $(date +%H:%M:%S)"
echo ""
echo "Scheduled:"
echo "  News Fetch:  $NEWS_TIME (+1 min)"
echo "  Topic Gen:   $TOPIC_TIME (+4 min)"
echo "  Blog Pub:    $BLOG_TIME (+7 min)"
echo ""
echo "Press Ctrl+C to cancel"
echo "=================================="
echo ""

python test_complete_workflow.py --mode scheduled \
  --news-time "$NEWS_TIME" \
  --topic-time "$TOPIC_TIME" \
  --blog-time "$BLOG_TIME"
