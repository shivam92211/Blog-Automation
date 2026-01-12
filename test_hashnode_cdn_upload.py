#!/usr/bin/env python3
"""
Test script for Hashnode CDN image upload
Creates a test image and uploads it to Hashnode CDN
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Add the project root to the path
sys.path.insert(0, '/home/shivam/App/Work/Phrase_trade/Blog-Automation')

from config import settings
from app.services.hashnode_cdn_service import HashnodeCDNService
from config.logging_config import get_logger

logger = get_logger(__name__)


def create_test_image(filename: str = "test_cover.png") -> str:
    """
    Create a simple test image

    Args:
        filename: Output filename

    Returns:
        Path to created image
    """
    # Create a 1200x630 image (standard blog cover size)
    width, height = 1200, 630
    image = Image.new('RGB', (width, height), color='#2563eb')  # Blue background

    # Draw some text
    draw = ImageDraw.Draw(image)

    # Try to use a decent font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Add title text
    title = "Test Blog Cover"
    draw.text((width//2, height//2 - 50), title, fill='white', font=font, anchor='mm')

    # Add subtitle
    subtitle = "Hashnode CDN Upload Test"
    draw.text((width//2, height//2 + 50), subtitle, fill='#e5e7eb', font=small_font, anchor='mm')

    # Save image
    image_path = os.path.join(os.getcwd(), filename)
    image.save(image_path)
    logger.info(f"Created test image: {image_path}")

    return image_path


def test_upload():
    """Test uploading an image to Hashnode CDN"""

    # Get API token from settings
    if not settings.HASHNODE_PUBLICATIONS or len(settings.HASHNODE_PUBLICATIONS) == 0:
        logger.error("No Hashnode publications configured")
        return False

    # Use the first active publication's API token
    api_token = None
    for pub in settings.HASHNODE_PUBLICATIONS:
        if pub.is_active:
            api_token = pub.api_token
            logger.info(f"Using API token from publication: {pub.name}")
            break

    if not api_token:
        logger.error("No active publication found with API token")
        return False

    # Create test image
    logger.info("Creating test image...")
    image_path = create_test_image()

    try:
        # Initialize CDN service
        logger.info("Initializing Hashnode CDN service...")
        cdn_service = HashnodeCDNService(api_token=api_token)

        # Upload image
        logger.info("Uploading image to Hashnode CDN...")
        cdn_url = cdn_service.upload_and_cleanup(image_path)

        if cdn_url:
            logger.info("✅ SUCCESS!")
            logger.info(f"   CDN URL: {cdn_url}")
            return True
        else:
            logger.error("❌ FAILED: Upload returned None")
            return False

    except Exception as e:
        logger.error(f"❌ FAILED: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("HASHNODE CDN UPLOAD TEST")
    logger.info("=" * 60)

    success = test_upload()

    logger.info("=" * 60)
    if success:
        logger.info("✅ Test completed successfully!")
        sys.exit(0)
    else:
        logger.info("❌ Test failed")
        sys.exit(1)
