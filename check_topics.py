#!/usr/bin/env python3
"""Check topics in database"""
import sys
sys.path.insert(0, '/home/shivam/App/Work/Phrase_trade/blog_automation')

from app.models.database import get_db

with get_db() as db:
    topics = list(db.topics.find().sort("scheduled_date", 1))
    print(f"Found {len(topics)} topics in database:\n")
    for topic in topics:
        print(f"  - {topic['scheduled_date'].date()}: {topic['title']}")
        print(f"    Status: {topic['status']}, Keywords: {topic['keywords'][:50]}...")
        print()
