#!/usr/bin/env python3
"""
Quick script to add a test topic for today
"""
from datetime import date, datetime
from app.models.database import get_sync_db
from app.models.models import Topic, TopicStatus

# Get database
db = get_sync_db()

# Get a category
category = db.categories.find_one({"is_active": True})

if category:
    # Create a test topic for today
    # Convert date to datetime for MongoDB compatibility
    today_datetime = datetime.combine(date.today(), datetime.min.time())

    topic_doc = Topic.create(
        category_id=str(category["_id"]),
        title="Understanding Web3 Wallet Security: Best Practices for 2025",
        description="A comprehensive guide to securing Web3 wallets and protecting digital assets",
        keywords="web3 security, wallet protection, cryptocurrency safety, blockchain security",
        scheduled_date=today_datetime,
        status=TopicStatus.PENDING
    )

    # Insert the topic
    result = db.topics.insert_one(topic_doc)

    print(f"✅ Test topic created successfully!")
    print(f"Topic ID: {result.inserted_id}")
    print(f"Title: {topic_doc['title']}")
    print(f"Category: {category['name']}")
    print(f"Scheduled for: {date.today()}")
else:
    print("❌ No active categories found")
