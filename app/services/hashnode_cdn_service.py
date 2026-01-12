"""
Hashnode CDN Image Upload Service
Handles uploading images to Hashnode's CDN via their internal API
"""
import os
import requests
from typing import Optional, Dict
from config.logging_config import get_logger

logger = get_logger(__name__)


class HashnodeCDNService:
    """Service for uploading images to Hashnode's CDN"""

    def __init__(self, api_token: str, jwt_token: Optional[str] = None):
        """
        Initialize Hashnode CDN service

        Args:
            api_token: Hashnode Personal Access Token (PAT)
            jwt_token: Optional JWT token from browser cookies (required for CDN upload)
        """
        self.api_token = api_token
        self.jwt_token = jwt_token
        self.upload_image_endpoint = "https://hashnode.com/api/upload-image"
        self.timeout = 60  # seconds

    def _get_s3_credentials(self, image_extension: str) -> Optional[Dict]:
        """
        Get S3 upload credentials from Hashnode

        Args:
            image_extension: Image file extension (e.g., 'png', 'jpg')

        Returns:
            Dictionary containing 'url' and 'fields' for S3 upload, or None if failed
        """
        try:
            # Request S3 credentials from Hashnode
            url = f"{self.upload_image_endpoint}?imageType={image_extension}"

            # Prefer JWT token if available, fall back to PAT
            if self.jwt_token:
                # Use JWT token in Cookie header (required for upload-image endpoint)
                logger.info(f"Requesting S3 credentials from Hashnode for .{image_extension} image (using JWT)")
                headers = {
                    "Cookie": f"jwt={self.jwt_token}",
                    "Content-Type": "application/json"
                }
                response = requests.get(url, headers=headers, timeout=self.timeout)
            else:
                # Try with PAT (likely to fail with 401, but worth trying)
                logger.info(f"Requesting S3 credentials from Hashnode for .{image_extension} image (using PAT)")
                logger.warning("No JWT token provided - upload may fail with 401 Unauthorized")
                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }
                response = requests.get(url, headers=headers, timeout=self.timeout)

                # If Bearer token fails with 401, try without Bearer prefix
                if response.status_code == 401:
                    logger.info("Bearer token failed, trying without Bearer prefix...")
                    headers["Authorization"] = self.api_token
                    response = requests.get(url, headers=headers, timeout=self.timeout)

            response.raise_for_status()

            data = response.json()

            # Validate response structure
            if "url" not in data or "fields" not in data:
                logger.error(f"Invalid response from Hashnode: missing 'url' or 'fields'")
                return None

            logger.info("Successfully received S3 credentials from Hashnode")
            return data

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 0
            if status_code == 401:
                logger.error("Authentication failed: The upload-image endpoint requires JWT authentication")
                logger.error("Personal Access Tokens may not work for this endpoint")
                logger.error("You may need to use JWT from browser cookies or use S3 only")
            else:
                logger.error(f"HTTP error getting S3 credentials: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get S3 credentials from Hashnode: {e}")
            return None

    def _upload_to_s3(self, s3_url: str, s3_fields: Dict, image_path: str) -> bool:
        """
        Upload image to S3 using provided credentials

        Args:
            s3_url: S3 bucket endpoint URL
            s3_fields: S3 upload credentials (key, bucket, etc.)
            image_path: Local path to image file

        Returns:
            True if upload successful, False otherwise
        """
        try:
            logger.info(f"Uploading image to S3: {image_path}")

            # Prepare multipart form data
            # Include all credential fields from Hashnode
            form_data = {}
            for key, value in s3_fields.items():
                form_data[key] = (None, value)

            # Add the file last (order matters for S3)
            with open(image_path, 'rb') as f:
                form_data['file'] = (os.path.basename(image_path), f, 'application/octet-stream')

                # Upload to S3
                # NOTE: Don't set Content-Type header explicitly - let requests handle it
                response = requests.post(s3_url, files=form_data, timeout=self.timeout)

            # S3 returns 204 No Content on success
            if response.status_code == 204:
                logger.info("Successfully uploaded image to S3")
                return True
            else:
                logger.error(f"S3 upload failed with status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to upload image to S3: {e}")
            return False

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Upload image to Hashnode CDN and return CDN URL

        Args:
            image_path: Local path to image file

        Returns:
            Hashnode CDN URL of uploaded image, or None if upload failed
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None

        try:
            # Get file extension
            _, ext = os.path.splitext(image_path)
            ext = ext.lstrip('.').lower()

            if not ext:
                logger.error("Image file has no extension")
                return None

            # Step 1: Get S3 credentials from Hashnode
            credentials = self._get_s3_credentials(ext)
            if not credentials:
                logger.error("Failed to get S3 credentials")
                return None

            s3_url = credentials["url"]
            s3_fields = credentials["fields"]

            # Step 2: Upload to S3
            upload_success = self._upload_to_s3(s3_url, s3_fields, image_path)
            if not upload_success:
                logger.error("Failed to upload image to S3")
                return None

            # Step 3: Construct CDN URL
            # The CDN URL is: https://cdn.hashnode.com/{key}
            cdn_key = s3_fields.get("key")
            if not cdn_key:
                logger.error("S3 fields missing 'key' for CDN URL construction")
                return None

            cdn_url = f"https://cdn.hashnode.com/{cdn_key}"
            logger.info(f"✓ Image uploaded to Hashnode CDN: {cdn_url}")
            return cdn_url

        except Exception as e:
            logger.error(f"Unexpected error uploading image to Hashnode CDN: {e}")
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

    def upload_and_cleanup(self, image_path: str, cleanup_on_failure: bool = True) -> Optional[str]:
        """
        Upload image to Hashnode CDN and cleanup local temp file

        Args:
            image_path: Local path to image file
            cleanup_on_failure: If True, delete local file even if upload fails

        Returns:
            Hashnode CDN URL of uploaded image, or None if upload failed
        """
        # Upload
        cdn_url = self.upload_image(image_path)

        # Cleanup temp file after upload (success or failure)
        if cdn_url:
            # Upload succeeded - clean up temp file
            logger.info("Upload successful, cleaning up temp image")
            self.cleanup_local_image(image_path)
        elif cleanup_on_failure:
            # Upload failed - clean up if requested
            logger.info("Upload failed, cleaning up temp image")
            self.cleanup_local_image(image_path)

        return cdn_url
