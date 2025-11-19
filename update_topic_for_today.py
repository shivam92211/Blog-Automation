#!/usr/bin/env python3
"""Update a topic to be scheduled for today"""
import sys
sys.path.insert(0, '/home/shivam/App/Work/Phrase_trade/blog_automation')

from datetime import datetime
from app.models.database import get_db

with get_db() as db:
    # Find the first pending topic
    topic = db.topics.find_one({"status": "pending"})
    
    if topic:
        # Update it to today's date
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        db.topics.update_one(
            {"_id": topic["_id"]},
            {"$set": {"scheduled_date": today}}
        )
        print(f"Updated topic to today: {topic['title']}")
        print(f"New scheduled date: {today.date()}")
    else:
        print("No pending topics found")
