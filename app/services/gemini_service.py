"""
Gemini API integration service
Handles topic generation and blog content creation
"""
import json
import time
from typing import List, Dict, Optional
import google.generativeai as genai
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class GeminiService:
    """Service for interacting with Google Gemini API"""

    def __init__(self):
        # Initialize Gemini client
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.timeout = settings.API_TIMEOUT
        self.max_retries = settings.API_MAX_RETRIES

    def _call_with_retry(self, func, *args, **kwargs):
        """
        Call a function with exponential backoff retry logic

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function

        Returns:
            Function result

        Raises:
            Exception: If all retries exhausted
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()

                # Don't retry on authentication errors
                if "authentication" in error_msg or "api key" in error_msg:
                    logger.error(f"Authentication error: {e}")
                    raise

                # Log the error
                logger.warning(
                    f"API call failed (attempt {attempt}/{self.max_retries}): {e}"
                )

                # If not last attempt, wait and retry
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All retry attempts exhausted")
                    raise

    def generate_topics(
        self,
        category_name: str,
        category_description: str,
        existing_topics: List[str],
        count: int = 7,
        news_context: str = ""
    ) -> List[Dict]:
        """
        Generate unique blog topics for a category

        Args:
            category_name: Name of the category
            category_description: Description of what this category covers
            existing_topics: List of existing topic titles to avoid
            count: Number of topics to generate (default 7)
            news_context: Optional trending news context for inspiration

        Returns:
            List of topic dictionaries with keys: title, description, keywords, angle

        Raises:
            Exception: If topic generation fails
        """
        logger.info(f"Generating {count} topics for category: {category_name}")
        if news_context:
            logger.info(f"Using news context: {len(news_context)} characters")

        # Build the prompt
        prompt = self._build_topic_generation_prompt(
            category_name,
            category_description,
            existing_topics,
            count,
            news_context
        )

        # Define response schema for structured output
        response_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "angle": {"type": "string"}
                },
                "required": ["title", "description", "keywords", "angle"]
            }
        }

        # Call Gemini API with retry logic
        def call_api():
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": settings.GEMINI_MAX_TOKENS_TOPICS,
                }
            )
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                }
            )
            return response.text

        response_text = self._call_with_retry(call_api)

        # Parse JSON response
        try:
            # Extract JSON from response (might have markdown code blocks)
            json_text = self._extract_json(response_text)
            logger.debug(f"Extracted JSON text: {json_text[:500]}...")
            topics = json.loads(json_text)

            if not isinstance(topics, list):
                logger.error(f"Response is not a list. Type: {type(topics)}")
                logger.error(f"Full response text: {response_text}")
                raise ValueError("Response is not a list")

            # Validate each topic has required fields
            valid_topics = []
            required_fields = ['title', 'description', 'keywords', 'angle']

            for idx, topic in enumerate(topics):
                if not isinstance(topic, dict):
                    logger.warning(f"Topic {idx} is not a dictionary, skipping")
                    continue

                # Check if all required fields are present and not empty
                if all(field in topic and topic[field] for field in required_fields):
                    valid_topics.append(topic)
                else:
                    missing = [f for f in required_fields if f not in topic or not topic[f]]
                    logger.warning(f"Topic {idx} missing required fields: {missing}, skipping")

            if not valid_topics:
                raise ValueError("No valid topics found in response")

            logger.info(f"Successfully generated {len(valid_topics)} valid topics (out of {len(topics)} total)")
            return valid_topics

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")

    def generate_blog_content(
        self,
        topic_title: str,
        category_name: str,
        category_description: str,
        topic_description: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate comprehensive blog content for a topic

        Args:
            topic_title: The topic title
            category_name: Category name for context
            category_description: Category description for context
            topic_description: Optional topic description
            keywords: Optional list of keywords

        Returns:
            Dictionary with keys: title, content, meta_description, tags, estimated_read_time

        Raises:
            Exception: If blog generation fails
        """
        logger.info(f"Generating blog content for topic: {topic_title}")

        # Build the prompt
        prompt = self._build_blog_generation_prompt(
            topic_title,
            category_name,
            category_description,
            topic_description,
            keywords
        )

        # Define response schema for structured output
        response_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "meta_description": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "estimated_read_time": {"type": "string"}
            },
            "required": ["title", "content", "meta_description", "tags", "estimated_read_time"]
        }

        # Call Gemini API with retry logic
        def call_api():
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": settings.GEMINI_MAX_TOKENS_BLOG,
                }
            )
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                }
            )
            return response.text

        response_text = self._call_with_retry(call_api)

        # Parse JSON response
        try:
            json_text = self._extract_json(response_text)
            blog_data = json.loads(json_text)

            logger.info(f"Successfully generated blog content: {len(blog_data.get('content', ''))} characters")
            return blog_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")

    def _build_topic_generation_prompt(
        self,
        category_name: str,
        category_description: str,
        existing_topics: List[str],
        count: int,
        news_context: str = ""
    ) -> str:
        """Build prompt for topic generation"""

        avoid_list = "\n".join([f"- {topic}" for topic in existing_topics[-20:]])  # Last 20 topics

        # Build news section if context is provided
        news_section = ""
        if news_context:
            news_section = f"""

{news_context}

Use these trending news articles as inspiration to create timely, relevant topics.
IMPORTANT: Do NOT copy headlines directly. Create unique angles and perspectives that add value beyond the news.
Consider how current trends relate to your category and what readers would want to learn.
"""

        prompt = f"""You are an expert content strategist generating blog topics.

Context:
- Category: {category_name}
- Description: {category_description}
- Target Audience: Mixed (beginners to professionals)
- Purpose: Educational, engaging, SEO-friendly content
{news_section}
Task:
Generate exactly {count} unique, high-quality blog topics for this category.

Requirements:
1. Each topic should be specific and actionable (not generic)
2. Topics should be 8-15 words long
3. Cover different content angles: how-to, listicle, case-study, tutorial, opinion, comparison, beginner-guide
4. Make them timely and relevant to 2025
5. Include a mix of difficulty levels:
   - 2 beginner-friendly topics
   - 3 intermediate topics
   - 2 advanced topics
{"6. Draw inspiration from trending news but create original, value-added perspectives" if news_context else ""}

Topics to AVOID (already covered):
{avoid_list if existing_topics else "None (first batch)"}

Output Format:
Return a valid JSON array with exactly {count} objects. Each object must contain:
{{
  "title": "The complete topic title",
  "description": "One-sentence description of what the blog will cover",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "angle": "how-to|listicle|case-study|tutorial|opinion|comparison|beginner-guide"
}}

CRITICAL REQUIREMENTS:
- Return ONLY valid JSON - no markdown, no code blocks, no additional text
- Ensure the JSON is complete - do not truncate the last item
- All {count} items must be complete with all fields filled
- Test your JSON is valid before returning
"""
        return prompt

    def _build_blog_generation_prompt(
        self,
        topic_title: str,
        category_name: str,
        category_description: str,
        topic_description: Optional[str],
        keywords: Optional[List[str]]
    ) -> str:
        """Build prompt for blog content generation"""

        keywords_str = ", ".join(keywords) if keywords else "relevant keywords"

        prompt = f"""You are an expert technical blog writer.

Task: Write a comprehensive, engaging blog post

Topic: {topic_title}
Category: {category_name}
Context: {category_description}
{f"Additional Context: {topic_description}" if topic_description else ""}
Target Keywords: {keywords_str}

Requirements:

1. LENGTH: 1200-1500 words

2. STRUCTURE:
   - Compelling introduction that hooks the reader
   - 4-6 main sections with clear H2/H3 headings
   - Real-world examples or case studies
   - Actionable takeaways in each section
   - Strong conclusion with call-to-action

3. WRITING STYLE:
   - Conversational yet professional tone
   - Use "you" to address readers directly
   - Short paragraphs (3-4 sentences maximum)
   - Include bullet points for lists
   - Add relevant statistics or facts where appropriate
   - Use transitions between sections

4. SEO OPTIMIZATION:
   - Use topic keywords naturally (2-3% density)
   - Include related keywords and variations
   - Optimize headings for search
   - Write for humans first, search engines second

5. TECHNICAL ACCURACY:
   - Ensure all technical information is current (2025)
   - Cite concepts accurately
   - Avoid outdated information or deprecated practices
   - Include code examples if relevant

6. FORMATTING:
   - Use Markdown format
   - Use ## for main headings, ### for subheadings
   - Include code snippets with language tags if relevant
   - Use **bold** for emphasis
   - Use > for important callouts

Output Format (JSON):
{{
  "title": "Final optimized blog title (may refine the original)",
  "content": "Full blog content in Markdown format",
  "meta_description": "SEO meta description (150-160 characters)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "estimated_read_time": "X min read"
}}

IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting.
"""
        return prompt

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from response text
        Handles cases where JSON is wrapped in markdown code blocks
        """
        text = text.strip()

        # Check if wrapped in markdown code block
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        elif text.startswith("```"):
            text = text[3:]  # Remove ```

        # Remove trailing code block marker
        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        # Determine if we're expecting an array or object
        # Arrays should start with [, objects with {
        if text.startswith('['):
            start_char = '['
            end_char = ']'
        elif text.startswith('{'):
            start_char = '{'
            end_char = '}'
        else:
            # Try to find the first occurrence
            first_array = text.find('[')
            first_object = text.find('{')

            if first_array >= 0 and (first_object < 0 or first_array < first_object):
                start_char = '['
                end_char = ']'
            elif first_object >= 0:
                start_char = '{'
                end_char = '}'
            else:
                return text.strip()

        # Find the start position
        start_idx = text.index(start_char)

        # Count brackets/braces to find the matching closing one
        extracted_text = text[start_idx:]
        depth = 0
        in_string = False
        escape_next = False
        last_valid_idx = -1

        for i, char in enumerate(extracted_text):
            # Handle string escaping
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            # Only count brackets/braces outside of strings
            if not in_string:
                if char == start_char:
                    depth += 1
                elif char == end_char:
                    depth -= 1
                    if depth == 0:
                        # Found the matching closing bracket/brace
                        last_valid_idx = start_idx + i
                        break

        if last_valid_idx > start_idx:
            text = text[start_idx:last_valid_idx+1]
        else:
            # Fallback to rfind if counting fails
            end_idx = text.rfind(end_char)
            if end_idx > start_idx:
                text = text[start_idx:end_idx+1]

        return text.strip()

    def generate_blog_cover_image(
        self,
        blog_title: str,
        blog_description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate blog cover image using Gemini image generation

        Args:
            blog_title: The blog post title
            blog_description: Optional blog description for context
            keywords: Optional list of keywords
            save_path: Path to save the generated image

        Returns:
            Path to saved image file, or None if generation failed
        """
        if not settings.ENABLE_BLOG_IMAGES:
            logger.info("Blog image generation is disabled")
            return None

        logger.info(f"Generating cover image for blog: {blog_title[:50]}...")

        try:
            # Import required modules for image generation
            from PIL import Image
            import io
            import os
            from datetime import datetime

            # Build image generation prompt
            prompt = self._build_image_generation_prompt(blog_title, blog_description, keywords)

            # Note: Image generation requires google-generativeai >= 1.0.0
            # Current version (0.8.5) does not support imagen API
            logger.warning("Image generation is not supported in google-generativeai 0.8.5")
            logger.info("To enable image generation, upgrade to google-generativeai >= 1.0.0")
            return None

            # TODO: Uncomment when upgrading to google-generativeai >= 1.0.0
            # # Generate image using Imagen
            # def generate_image():
            #     response = self.client.models.generate_image(
            #         model='imagen-3.0-generate-001',
            #         prompt=prompt,
            #         config=types.GenerateImageConfig(
            #             number_of_images=1,
            #             aspect_ratio='16:9',
            #             safety_filter_level='BLOCK_MEDIUM_AND_ABOVE',
            #             person_generation='ALLOW_ADULT'
            #         )
            #     )
            #     return response
            #
            # # Call with retry
            # response = self._call_with_retry(generate_image)
            #
            # # Extract image from response
            # if not response or not hasattr(response, 'generated_images') or not response.generated_images:
            #     logger.error("No images generated in response")
            #     return None
            #
            # # Get the first generated image
            # generated_image = response.generated_images[0]
            #
            # # Get image data (bytes)
            # if hasattr(generated_image, 'image') and hasattr(generated_image.image, 'image_bytes'):
            #     image_data = generated_image.image.image_bytes
            # elif hasattr(generated_image, 'image_bytes'):
            #     image_data = generated_image.image_bytes
            # else:
            #     logger.error("Could not extract image bytes from response")
            #     return None
            #
            # # Convert bytes to PIL Image
            # image = Image.open(io.BytesIO(image_data))
            #
            # # Generate save path if not provided
            # if not save_path:
            #     timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            #     filename = f"blog_cover_{timestamp}.png"
            #     save_path = str(settings.IMAGE_TEMP_DIR / filename)
            #
            # # Ensure temp directory exists
            # os.makedirs(os.path.dirname(save_path), exist_ok=True)
            #
            # # Save image
            # image.save(save_path, format='PNG')
            # file_size = os.path.getsize(save_path) / 1024  # KB
            #
            # logger.info(f"✓ Cover image generated and saved: {save_path} ({file_size:.1f} KB)")
            # return save_path

        except Exception as e:
            logger.error(f"Failed to generate cover image: {e}", exc_info=True)
            return None

    def _build_image_generation_prompt(
        self,
        blog_title: str,
        blog_description: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> str:
        """Build prompt for image generation"""

        keywords_str = ", ".join(keywords) if keywords else ""

        prompt = f"""Create a professional, eye-catching blog cover image for:

Title: {blog_title}
{f"Description: {blog_description}" if blog_description else ""}
{f"Keywords: {keywords_str}" if keywords_str else ""}

Requirements:
- Modern and professional design
- Tech/digital theme with clean aesthetics
- Suitable for a technology blog post
- Abstract or conceptual representation (no text or specific people)
- Vibrant but professional color scheme
- High quality, suitable for web publishing
- 16:9 aspect ratio (landscape orientation)

Style: Modern, professional, tech-forward, visually appealing"""

        return prompt


# Singleton instance
gemini_service = GeminiService()
