"""
Image Upload Service
Handles uploading blog cover images to Imgur and cleanup
"""
import os
from typing import Optional
from imgurpython import ImgurClient
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class ImageUploadService:
    """Service for uploading images to external hosting (Imgur)"""

    def __init__(self):
        """Initialize Imgur client"""
        self.client_id = settings.IMGUR_CLIENT_ID
        self.client = None

        if self.client_id:
            try:
                # Initialize Imgur client (anonymous upload, no auth secret needed)
                self.client = ImgurClient(self.client_id, None)
                logger.info("Imgur client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Imgur client: {e}")
        else:
            logger.warning("IMGUR_CLIENT_ID not set - image upload disabled")

    def upload_to_imgur(self, image_path: str, title: Optional[str] = None, description: Optional[str] = None) -> Optional[str]:
        """
        Upload image to Imgur and return public URL

        Args:
            image_path: Local path to image file
            title: Optional image title
            description: Optional image description

        Returns:
            Public URL of uploaded image, or None if upload failed
        """
        if not self.client:
            logger.warning("Imgur client not initialized - skipping upload")
            return None

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None

        try:
            logger.info(f"Uploading image to Imgur: {image_path}")

            # Prepare upload config
            config = {
                'album': None,
                'name': title or 'Blog Cover Image',
                'title': title or 'Blog Cover Image',
                'description': description or 'AI-generated blog cover image'
            }

            # Upload image
            uploaded_image = self.client.upload_from_path(image_path, config=config, anon=True)

            if uploaded_image and 'link' in uploaded_image:
                image_url = uploaded_image['link']
                logger.info(f"✓ Image uploaded successfully: {image_url}")
                return image_url
            else:
                logger.error("Upload succeeded but no URL returned")
                return None

        except Exception as e:
            logger.error(f"Failed to upload image to Imgur: {e}", exc_info=True)
            return None

    def cleanup_local_image(self, image_path: Optional[str]) -> bool:
        """
        Delete local temporary image file

        Args:
            image_path: Path to image file to delete

        Returns:
            True if successfully deleted, False otherwise
        """
        if not image_path:
            return True  # Nothing to clean up

        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"✓ Cleaned up temp image: {image_path}")
                return True
            else:
                logger.debug(f"Image file already deleted: {image_path}")
                return True

        except Exception as e:
            logger.warning(f"Failed to cleanup temp image {image_path}: {e}")
            return False

    def upload_and_cleanup(self, image_path: str, title: Optional[str] = None, cleanup_on_failure: bool = True) -> Optional[str]:
        """
        Upload image to Imgur and optionally cleanup on failure

        Args:
            image_path: Local path to image file
            title: Optional image title
            cleanup_on_failure: If True, delete local file even if upload fails

        Returns:
            Public URL of uploaded image, or None if upload failed
        """
        # Upload
        image_url = self.upload_to_imgur(image_path, title=title)

        # Cleanup on failure if requested
        if not image_url and cleanup_on_failure:
            logger.info("Upload failed, cleaning up local image")
            self.cleanup_local_image(image_path)

        return image_url


# Singleton instance
image_upload_service = ImageUploadService()
