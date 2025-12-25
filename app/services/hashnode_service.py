"""
Hashnode API integration service
Handles blog publishing to Hashnode
"""
import re
import time
import requests
from typing import Dict, Optional
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class HashnodeService:
    """Service for interacting with Hashnode GraphQL API"""

    def __init__(self):
        self.api_url = settings.HASHNODE_API_URL
        self.api_token = settings.HASHNODE_API_TOKEN
        self.publication_id = settings.HASHNODE_PUBLICATION_ID
        self.timeout = settings.API_TIMEOUT
        self.max_retries = settings.API_MAX_RETRIES

    def _call_with_retry(self, func, *args, **kwargs):
        """
        Call a function with progressive retry delays: 1min, 5min, 10min

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            Exception: If all retries exhausted
        """
        # Progressive retry delays: 1 min, 5 min, 10 min
        retry_delays = [60, 300, 600]  # seconds

        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0

                # Don't retry on authentication errors
                if status_code == 401:
                    logger.error(f"Authentication error: Invalid API token")
                    raise

                # Handle rate limiting
                if status_code == 429:
                    wait_time = int(e.response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    if attempt < self.max_retries:
                        time.sleep(wait_time)
                        continue
                    raise

                # Log the error
                logger.warning(
                    f"API call failed (attempt {attempt}/{self.max_retries}): {e}"
                )

                # If not last attempt, wait and retry with progressive delays
                if attempt < self.max_retries:
                    wait_time = retry_delays[attempt - 1]  # Get delay for this attempt
                    minutes = wait_time // 60
                    logger.info(f"⏳ Waiting {minutes} minute(s) before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    raise

            except Exception as e:
                logger.warning(f"Unexpected error (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    wait_time = retry_delays[attempt - 1]
                    minutes = wait_time // 60
                    logger.info(f"⏳ Waiting {minutes} minute(s) before retry...")
                    time.sleep(wait_time)
                else:
                    raise

    def publish_post(
        self,
        title: str,
        content: str,
        tags: list,
        meta_description: Optional[str] = None,
        cover_image_url: Optional[str] = None
    ) -> Dict:
        """
        Publish a blog post to Hashnode

        Args:
            title: Blog post title
            content: Blog content in Markdown format
            tags: List of tag slugs (e.g., ["blockchain", "web3"])
            meta_description: Optional SEO meta description
            cover_image_url: Optional URL to cover image (must be publicly accessible)

        Returns:
            Dictionary with keys: post_id, url, slug

        Raises:
            Exception: If publishing fails
        """
        logger.info(f"Publishing post to Hashnode: {title}")

        # Build GraphQL mutation
        mutation = self._build_publish_mutation(
            title, content, tags, meta_description, cover_image_url
        )

        # Call Hashnode API with retry logic
        def call_api():
            headers = {
                "Authorization": self.api_token,
                "Content-Type": "application/json"
            }

            response = requests.post(
                self.api_url,
                json={"query": mutation},
                headers=headers,
                timeout=self.timeout
            )

            # Raise exception for HTTP errors
            response.raise_for_status()

            data = response.json()

            # Check for GraphQL errors
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown error")
                raise Exception(f"GraphQL error: {error_msg}")

            return data

        response_data = self._call_with_retry(call_api)

        # Extract post information
        try:
            post_data = response_data["data"]["publishPost"]["post"]
            result = {
                "post_id": post_data["id"],
                "url": post_data["url"],
                "slug": post_data["slug"]
            }
            logger.info(f"Successfully published post: {result['url']}")
            return result

        except (KeyError, TypeError) as e:
            logger.error(f"Failed to extract post data from response: {e}")
            logger.error(f"Response: {response_data}")
            raise ValueError(f"Invalid response structure: {e}")

    def _build_publish_mutation(
        self,
        title: str,
        content: str,
        tags: list,
        meta_description: Optional[str],
        cover_image_url: Optional[str] = None
    ) -> str:
        """
        Build GraphQL mutation for publishing a post

        Note: Hashnode uses tag slugs, not tag objects
        """
        # Escape special characters in strings
        title_escaped = self._escape_graphql_string(title)
        content_escaped = self._escape_graphql_string(content)
        meta_escaped = self._escape_graphql_string(meta_description) if meta_description else ""

        # Format tags as array of tag input objects
        tags_formatted = self._format_tags(tags)

        # Build meta tags section
        meta_tags = ""
        if meta_description:
            meta_tags = f'metaTags: {{ description: "{meta_escaped}" }}'

        # Build cover image section
        cover_image = ""
        if cover_image_url:
            cover_image = f'coverImageOptions: {{ coverImageURL: "{cover_image_url}" }}'
            logger.info(f"Including cover image in post: {cover_image_url}")

        mutation = f"""
        mutation PublishPost {{
          publishPost(input: {{
            publicationId: "{self.publication_id}"
            title: "{title_escaped}"
            contentMarkdown: "{content_escaped}"
            tags: {tags_formatted}
            {meta_tags}
            {cover_image}
          }}) {{
            post {{
              id
              slug
              url
            }}
          }}
        }}
        """

        return mutation

    def _format_tags(self, tags: list) -> str:
        """
        Format tags for GraphQL mutation
        Hashnode accepts tag objects with slug and name

        Tag slugs must match ^[a-z0-9-]{1,250}$ (only lowercase letters, numbers, and hyphens)

        Args:
            tags: List of tag strings

        Returns:
            Formatted string like: [{slug: "blockchain", name: "Blockchain"}, ...]
        """
        if not tags:
            return "[]"

        # Convert tags to slug format (lowercase, replace spaces and invalid chars with hyphens)
        formatted_tags = []
        for tag in tags:
            # Convert to lowercase
            slug = tag.lower()
            # Replace spaces with hyphens
            slug = slug.replace(" ", "-")
            # Replace any invalid characters (not a-z, 0-9, or -) with hyphens
            slug = re.sub(r'[^a-z0-9-]', '-', slug)
            # Remove consecutive hyphens
            slug = re.sub(r'-+', '-', slug)
            # Remove leading/trailing hyphens
            slug = slug.strip('-')
            # Limit to 250 characters
            slug = slug[:250]

            name = tag.title()
            formatted_tags.append(f'{{slug: "{slug}", name: "{name}"}}')

        return "[" + ", ".join(formatted_tags) + "]"

    def _escape_graphql_string(self, text: str) -> str:
        """
        Escape special characters for GraphQL string
        """
        if not text:
            return ""

        # Escape backslashes first
        text = text.replace("\\", "\\\\")
        # Escape double quotes
        text = text.replace('"', '\\"')
        # Escape newlines
        text = text.replace("\n", "\\n")
        # Escape carriage returns
        text = text.replace("\r", "\\r")
        # Escape tabs
        text = text.replace("\t", "\\t")

        return text

    def get_publication_info(self) -> Dict:
        """
        Get information about the configured publication
        Useful for testing API connection

        Returns:
            Dictionary with publication info

        Raises:
            Exception: If request fails
        """
        logger.info(f"Fetching publication info for ID: {self.publication_id}")

        query = f"""
        query {{
          publication(id: "{self.publication_id}") {{
            id
            title
            url
            about {{
              text
            }}
          }}
        }}
        """

        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }

        response = requests.post(
            self.api_url,
            json={"query": query},
            headers=headers,
            timeout=self.timeout
        )

        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown error")
            raise Exception(f"GraphQL error: {error_msg}")

        return data["data"]["publication"]


# Singleton instance
hashnode_service = HashnodeService()
