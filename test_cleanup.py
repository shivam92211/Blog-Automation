#!/usr/bin/env python3
"""
Test script to verify temp image cleanup functionality
"""
import os
import tempfile
from app.services.image_upload_service import image_upload_service

# Create a temporary test image
test_content = b"Test image data"
temp_dir = "temp_images"

# Ensure temp_images directory exists
os.makedirs(temp_dir, exist_ok=True)

# Create a test file
test_file_path = os.path.join(temp_dir, "test_cleanup_image.png")
with open(test_file_path, "wb") as f:
    f.write(test_content)

print(f"Created test file: {test_file_path}")
print(f"File exists before upload: {os.path.exists(test_file_path)}")

# Test upload and cleanup
print("\nTesting upload_and_cleanup...")
image_url = image_upload_service.upload_and_cleanup(test_file_path, title="Test Image")

print(f"\nUpload result: {image_url}")
print(f"File exists after upload: {os.path.exists(test_file_path)}")

if image_url and not os.path.exists(test_file_path):
    print("\n✓ SUCCESS: Image uploaded and temp file cleaned up!")
elif not image_url and not os.path.exists(test_file_path):
    print("\n⚠ Upload failed but temp file was cleaned up")
else:
    print(f"\n✗ FAILED: Temp file still exists at {test_file_path}")
