# Quick Start Guide

## Run the Script

```bash
python3 run_blog_automation.py
```

## What Happens

The script will automatically:

1. ✅ Pick a random category
2. ✅ Generate a unique topic (tries up to 5 times)
3. ✅ Check against database for duplicates
4. ✅ Store the topic
5. ✅ Generate blog content (1200-1500 words)
6. ✅ Store the blog
7. ✅ Publish to Hashnode

**Sleep Time:** 10-30 seconds between each step (randomized)

## Output Example

```
============================================================
🚀 BLOG AUTOMATION SCRIPT STARTED
============================================================
📁 Fetching a random category...
✓ Selected category: Web Development
Category selected (sleeping for 15s)
🔄 Starting unique topic search (max 5 attempts)...

--- Attempt 1/5 ---
🤖 Generating topic for category: Web Development
📰 Fetching trending tech news...
News fetched successfully (sleeping for 22s)
🎯 Calling Gemini AI to generate topic...
✓ Generated topic: Building Real-time Collaborative Apps with WebSockets
Topic generated, checking uniqueness (sleeping for 18s)
🔍 Checking uniqueness for: Building Real-time Collaborative Apps...
📊 Comparing against 45 topics and 12 history records
✓ Topic is unique!
🎉 Found unique topic on attempt 1!
Unique topic found (sleeping for 25s)
💾 Storing topic in database...
✓ Topic stored with ID: 6a7b8c9d0e1f2g3h4i5j6k7l
Topic stored (sleeping for 13s)
📝 Generating blog content for: Building Real-time...
✓ Blog generated successfully!
   Title: Building Real-time Collaborative Apps with WebSockets
   Word Count: 1456
   Tags: websockets, realtime, nodejs, webdev
Blog content generated (sleeping for 28s)
💾 Storing blog in database...
✓ Blog stored with ID: 7b8c9d0e1f2g3h4i5j6k7l8m
Blog stored (sleeping for 19s)
🚀 Publishing blog to Hashnode...
✓ Blog published successfully!
   Post ID: abc123def456
   URL: https://yourblog.hashnode.dev/building-realtime-collaborative-apps
============================================================
✅ BLOG AUTOMATION COMPLETED SUCCESSFULLY!
⏱️  Total time: 245.67 seconds
============================================================
```

## If Something Goes Wrong

- **"No active categories found"** → Run database initialization
- **"Could not find unique topic after 5 attempts"** → Topics might be too similar, try again later
- **API errors** → Check your API keys in `.env`
- **Publishing fails** → Check Hashnode credentials

## Files Created

After running, you'll have:
- Topic in `topics` collection
- Blog in `blogs` collection
- Published post on Hashnode
