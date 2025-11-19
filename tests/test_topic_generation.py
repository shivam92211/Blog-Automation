#!/usr/bin/env python3
"""Test script to trigger topic generation manually"""
import sys
sys.path.insert(0, '/home/shivam/App/Work/Phrase_trade/blog_automation')

from app.jobs.topic_generator import run_topic_generation

if __name__ == "__main__":
    print("Starting topic generation test...")
    try:
        run_topic_generation()
        print("\nTopic generation completed successfully!")
    except Exception as e:
        print(f"\nTopic generation failed: {e}")
        import traceback
        traceback.print_exc()
