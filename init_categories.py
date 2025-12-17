#!/usr/bin/env python3
"""
Initialize database with categories
Run this once to set up your categories
"""
import sys
from datetime import datetime

sys.path.insert(0, '/home/shivam/App/Work/Phrase_trade/Blog-Automation')

from app.models.database import get_sync_db

def init_categories():
    """Initialize categories in the database"""
    db = get_sync_db()

    # Define categories
    categories = [
        {"name": "Web Development", "description": "Modern web technologies, frameworks, and best practices", "is_active": True},
        {"name": "AI & Machine Learning", "description": "Artificial intelligence, ML algorithms, and applications", "is_active": True},
        {"name": "DevOps", "description": "CI/CD, containerization, infrastructure, and automation", "is_active": True},
        {"name": "Cybersecurity", "description": "Security best practices, vulnerabilities, and protection", "is_active": True},
        {"name": "Cloud Computing", "description": "AWS, Azure, GCP, and cloud-native technologies", "is_active": True},
        {"name": "Mobile Development", "description": "iOS, Android, and cross-platform mobile apps", "is_active": True},
        {"name": "Data Science", "description": "Data analysis, visualization, and big data technologies", "is_active": True},
        {"name": "Blockchain", "description": "Cryptocurrency, smart contracts, and distributed systems", "is_active": True},
    ]

    print("🗄️  Initializing categories...")

    # Check if categories already exist
    existing_count = db.categories.count_documents({})
    if existing_count > 0:
        print(f"⚠️  Found {existing_count} existing categories.")
        response = input("Do you want to clear and reinitialize? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            db.categories.delete_many({})
            print("✓ Cleared existing categories")
        else:
            print("❌ Cancelled")
            return

    # Insert categories
    for cat in categories:
        cat['usage_count'] = 0
        cat['last_used_date'] = None
        cat['created_at'] = datetime.utcnow()
        cat['updated_at'] = datetime.utcnow()

    result = db.categories.insert_many(categories)
    print(f"✓ Inserted {len(result.inserted_ids)} categories:")

    for cat in categories:
        status = "✅ Active" if cat['is_active'] else "⏸️  Inactive"
        print(f"   - {cat['name']}: {cat['description']} ({status})")

    print("\n🎉 Database initialized successfully!")
    print("\nYou can now run: python3 run_blog_automation.py")

if __name__ == "__main__":
    try:
        init_categories()
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
