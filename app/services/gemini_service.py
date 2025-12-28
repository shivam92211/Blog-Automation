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

                # If not last attempt, wait and retry with progressive delays
                if attempt < self.max_retries:
                    wait_time = retry_delays[attempt - 1]  # Get delay for this attempt
                    minutes = wait_time // 60
                    logger.info(f"⏳ Waiting {minutes} minute(s) before retry...")
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
                "seo_title": {"type": "string"},
                "content": {"type": "string"},
                "meta_description": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "estimated_read_time": {"type": "string"}
            },
            "required": ["title", "seo_title", "content", "meta_description", "tags", "estimated_read_time"]
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

        # Parse and validate JSON response
        try:
            json_text = self._extract_json(response_text)
            blog_data = json.loads(json_text)

            # Validate all required fields are present and non-empty
            validation_errors = self._validate_blog_data(blog_data)
            if validation_errors:
                logger.error(f"Blog data validation failed: {', '.join(validation_errors)}")
                logger.error(f"Incomplete blog data: {blog_data}")
                raise ValueError(f"Incomplete blog data from Gemini: {', '.join(validation_errors)}")

            # Add word count
            content = blog_data.get('content', '')
            word_count = len(content.split())
            blog_data['word_count'] = word_count

            logger.info(f"Successfully generated blog content: {word_count} words, {len(content)} characters")
            logger.info(f"✓ SEO Title: {blog_data.get('seo_title', 'N/A')[:60]}...")
            logger.info(f"✓ Meta Description: {blog_data.get('meta_description', 'N/A')[:60]}...")
            return blog_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}...")
            logger.error(f"Response text (last 200 chars): ...{response_text[-200:]}")

            # Check if response was truncated
            if not response_text.strip().endswith('}'):
                logger.error("Response appears to be truncated (doesn't end with '}')")
                raise ValueError(f"Truncated JSON response from Gemini - increase max_output_tokens or reduce prompt length")

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
   - DO NOT include the title as an H1 (#) heading in the content
   - Start directly with the introduction paragraph
   - Use ## for main headings, ### for subheadings
   - Include code snippets with language tags if relevant
   - Use **bold** for emphasis
   - Use > for important callouts

Output Format (JSON):
{{
  "title": "Final optimized blog title (may refine the original)",
  "seo_title": "SEO-optimized title for search engines (50-60 characters, include main keyword)",
  "content": "Full blog content in Markdown format",
  "meta_description": "SEO meta description (155-160 characters, compelling and keyword-rich)",
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
        Generate blog cover image using Gemini image generation (v1/Tier One)

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

        # Use Tier One key if available, else fallback (though user said specific key)
        api_key = settings.GEMINI_TIER_ONE_API_KEY or settings.GEMINI_API_KEY

        if not api_key:
             logger.error("No API key available for image generation")
             return None

        logger.info(f"Generating cover image for blog: {blog_title[:50]}...")

        try:
            # Import here to avoid dependency issues if not installed
            from google import genai
            from google.genai import types
            from PIL import Image
            import io
            import os

            client = genai.Client(api_key=api_key)

            prompt_text = self._build_image_generation_prompt(blog_title, blog_description, keywords)

            logger.info(f"Calling Gemini Image API with prompt length: {len(prompt_text)}")

            response = client.models.generate_content(
                model="gemini-2.5-flash-image", # User specified this model
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio="16:9"  # Gemini only supports aspect ratios, not exact dimensions
                    )
                )
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_data = part.inline_data.data
                    image = Image.open(io.BytesIO(image_data))

                    # Resize to exact OG image dimensions (1200x630)
                    # Hashnode recommends 1200x630 for optimal social media sharing
                    target_width = 1200
                    target_height = 630

                    logger.info(f"Original image size: {image.size}")

                    # Resize with high-quality resampling
                    image_resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)

                    logger.info(f"Resized to OG image dimensions: {target_width}x{target_height}")

                    if not save_path:
                        # Create temp path
                        timestamp = int(time.time())
                        safe_title = "".join([c for c in blog_title if c.isalnum() or c in (' ', '-')]).strip().replace(" ", "_")[:30]
                        filename = f"blog_image_{timestamp}_{safe_title}.png"
                        save_path = os.path.join(settings.IMAGE_TEMP_DIR, filename)

                    # Ensure directory exists
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)

                    image_resized.save(save_path, 'PNG', optimize=True, quality=95)
                    logger.info(f"Success! Image saved to: {save_path}")
                    return save_path

            logger.warning("No image data found in the response")
            return None

        except Exception as e:
            logger.error(f"Error occurred during image generation: {e}")
            raise e

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
- High quality, suitable for web publishing and social media sharing
- 16:9 aspect ratio (will be resized to 1200x630 for OG image)
- Design should work well when cropped or resized

Style: Modern, professional, tech-forward, visually appealing"""

        return prompt

    def _validate_blog_data(self, blog_data: Dict) -> List[str]:
        """
        Validate blog data to ensure all required fields are present and valid

        Args:
            blog_data: The generated blog data dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields exist
        required_fields = ["title", "seo_title", "content", "meta_description", "tags"]
        for field in required_fields:
            if field not in blog_data:
                errors.append(f"Missing required field: {field}")
            elif not blog_data[field]:
                errors.append(f"Empty required field: {field}")

        # Validate specific field requirements
        if "title" in blog_data and blog_data["title"]:
            if len(blog_data["title"]) < 10:
                errors.append(f"Title too short: {len(blog_data['title'])} chars (min 10)")
            elif len(blog_data["title"]) > 200:
                errors.append(f"Title too long: {len(blog_data['title'])} chars (max 200)")

        if "seo_title" in blog_data and blog_data["seo_title"]:
            seo_len = len(blog_data["seo_title"])
            if seo_len < 40:
                errors.append(f"SEO title too short: {seo_len} chars (recommended 50-60)")
            elif seo_len > 70:
                errors.append(f"SEO title too long: {seo_len} chars (recommended 50-60, max 70)")

        if "content" in blog_data and blog_data["content"]:
            content_len = len(blog_data["content"])
            if content_len < 500:
                errors.append(f"Content too short: {content_len} chars (min 500)")
            # Check if content seems truncated (doesn't end with proper punctuation or newline)
            content_end = blog_data["content"].strip()[-50:]
            if not any(content_end.endswith(p) for p in ['.', '!', '?', '```', '\n']):
                errors.append("Content appears to be truncated (no proper ending)")

        if "meta_description" in blog_data and blog_data["meta_description"]:
            meta_len = len(blog_data["meta_description"])
            if meta_len < 120:
                errors.append(f"Meta description too short: {meta_len} chars (recommended 155-160)")
            elif meta_len > 170:
                errors.append(f"Meta description too long: {meta_len} chars (max 170)")

        if "tags" in blog_data:
            if not isinstance(blog_data["tags"], list):
                errors.append("Tags must be a list")
            elif len(blog_data["tags"]) < 1:
                errors.append("Must have at least 1 tag")
            elif len(blog_data["tags"]) > 10:
                errors.append(f"Too many tags: {len(blog_data['tags'])} (max 10)")

        return errors


# Singleton instance
gemini_service = GeminiService()
