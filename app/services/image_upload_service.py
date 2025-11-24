"""
Image Upload Service
Handles uploading blog cover images to AWS S3 and cleanup
"""
import os
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class ImageUploadService:
    """Service for uploading images to external hosting (AWS S3)"""

    def __init__(self):
        """Initialize AWS S3 client"""
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.s3_client = None

        if self.bucket_name:
            try:
                # Initialize S3 client with credentials
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region
                )
                logger.info("AWS S3 client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AWS S3 client: {e}")
        else:
            logger.warning("AWS_S3_BUCKET_NAME not set - image upload disabled")

    def upload_to_s3(self, image_path: str, title: Optional[str] = None) -> Optional[str]:
        """
        Upload image to AWS S3 and return public URL

        Args:
            image_path: Local path to image file
            title: Optional image title (used for generating object name)

        Returns:
            Public URL of uploaded image, or None if upload failed
        """
        if not self.s3_client:
            logger.warning("AWS S3 client not initialized - skipping upload")
            return None

        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None

        try:
            logger.info(f"Uploading image to AWS S3: {image_path}")

            # Generate object name from filename
            filename = os.path.basename(image_path)
            object_name = f"blog-covers/{filename}"

            # Upload file to S3 with public-read ACL
            self.s3_client.upload_file(
                image_path,
                self.bucket_name,
                object_name,
                ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/png'}
            )

            # Construct public URL
            image_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_name}"
            logger.info(f"✓ Image uploaded successfully: {image_url}")
            return image_url

        except ClientError as e:
            logger.error(f"Failed to upload image to S3: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}", exc_info=True)
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
        Upload image to AWS S3 and optionally cleanup on failure

        Args:
            image_path: Local path to image file
            title: Optional image title
            cleanup_on_failure: If True, delete local file even if upload fails

        Returns:
            Public URL of uploaded image, or None if upload failed
        """
        # Upload
        image_url = self.upload_to_s3(image_path, title=title)

        # Cleanup on failure if requested
        if not image_url and cleanup_on_failure:
            logger.info("Upload failed, cleaning up local image")
            self.cleanup_local_image(image_path)

        return image_url


# Singleton instance
image_upload_service = ImageUploadService()
