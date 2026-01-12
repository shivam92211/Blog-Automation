"""
Pydantic-based Blog Content Validators

Provides comprehensive validation for blog content to ensure:
- Proper markdown structure with headings
- Minimum word count
- Complete sections (intro, body, conclusion)
- SEO field requirements
"""

import re
from typing import List, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator, model_validator


@dataclass
class BlogContentMetrics:
    """Metrics extracted from blog content markdown"""
    h2_count: int = 0
    h3_count: int = 0
    paragraph_count: int = 0
    word_count: int = 0
    has_introduction: bool = False
    has_conclusion_section: bool = False
    content_ends_properly: bool = False
    heading_titles: List[str] = None
    
    def __post_init__(self):
        if self.heading_titles is None:
            self.heading_titles = []
    
    @property
    def total_headings(self) -> int:
        return self.h2_count + self.h3_count
    
    def to_dict(self) -> dict:
        return {
            "h2_count": self.h2_count,
            "h3_count": self.h3_count,
            "total_headings": self.total_headings,
            "paragraph_count": self.paragraph_count,
            "word_count": self.word_count,
            "has_introduction": self.has_introduction,
            "has_conclusion_section": self.has_conclusion_section,
            "content_ends_properly": self.content_ends_properly,
            "heading_titles": self.heading_titles,
        }


def analyze_content_structure(content: str) -> BlogContentMetrics:
    """
    Analyze markdown content structure to extract metrics.
    
    Args:
        content: The markdown blog content
        
    Returns:
        BlogContentMetrics with structure analysis
    """
    if not content or not content.strip():
        return BlogContentMetrics()
    
    lines = content.strip().split('\n')
    
    # Count H2 and H3 headings
    h2_pattern = re.compile(r'^##\s+(.+)$')
    h3_pattern = re.compile(r'^###\s+(.+)$')
    
    h2_count = 0
    h3_count = 0
    heading_titles = []
    first_heading_line = -1
    last_h2_line = -1
    
    for i, line in enumerate(lines):
        h2_match = h2_pattern.match(line.strip())
        h3_match = h3_pattern.match(line.strip())
        
        if h2_match:
            h2_count += 1
            heading_titles.append(h2_match.group(1).strip())
            if first_heading_line == -1:
                first_heading_line = i
            last_h2_line = i
        elif h3_match:
            h3_count += 1
            heading_titles.append(h3_match.group(1).strip())
            if first_heading_line == -1:
                first_heading_line = i
    
    # Check for introduction (content before first heading)
    has_introduction = False
    if first_heading_line > 0:
        intro_content = '\n'.join(lines[:first_heading_line]).strip()
        # Intro should have at least some meaningful content (50+ chars)
        if len(intro_content) >= 50:
            has_introduction = True
    elif first_heading_line == -1:
        # No headings at all - check if there's content
        has_introduction = len(content.strip()) >= 50
    
    # Check for conclusion section (content after last H2)
    has_conclusion_section = False
    if last_h2_line >= 0 and last_h2_line < len(lines) - 1:
        conclusion_content = '\n'.join(lines[last_h2_line + 1:]).strip()
        if len(conclusion_content) >= 100:
            has_conclusion_section = True
    
    # Count paragraphs (non-empty blocks of text)
    paragraph_count = 0
    in_paragraph = False
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#') and not stripped.startswith('```'):
            if not in_paragraph:
                paragraph_count += 1
                in_paragraph = True
        else:
            in_paragraph = False
    
    # Count words
    # Remove markdown formatting for accurate word count
    text_content = content
    # Remove code blocks
    text_content = re.sub(r'```[\s\S]*?```', '', text_content)
    # Remove inline code
    text_content = re.sub(r'`[^`]+`', '', text_content)
    # Remove markdown links but keep link text
    text_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text_content)
    # Remove headings markers
    text_content = re.sub(r'^#+\s+', '', text_content, flags=re.MULTILINE)
    # Remove bold/italic markers
    text_content = re.sub(r'\*+([^*]+)\*+', r'\1', text_content)
    text_content = re.sub(r'_+([^_]+)_+', r'\1', text_content)
    
    words = text_content.split()
    word_count = len([w for w in words if len(w) > 0])
    
    # Check if content ends properly
    content_stripped = content.strip()
    proper_endings = ['.', '!', '?', ')', '"', "'", '`', '>', '-', '*', '```']
    suspicious_endings = [',', ' and', ' or', ' the', ' a', ' an', ' in', ' on', ' at', ' to', ' for', ' with']
    
    content_ends_properly = (
        any(content_stripped.endswith(end) for end in proper_endings) and
        not any(content_stripped.endswith(end) for end in suspicious_endings)
    )
    
    return BlogContentMetrics(
        h2_count=h2_count,
        h3_count=h3_count,
        paragraph_count=paragraph_count,
        word_count=word_count,
        has_introduction=has_introduction,
        has_conclusion_section=has_conclusion_section,
        content_ends_properly=content_ends_properly,
        heading_titles=heading_titles,
    )


class ValidatedBlogContent(BaseModel):
    """
    Pydantic model for validated blog content.
    
    Validates:
    - Title length (10-200 chars)
    - SEO title length (40-70 chars)
    - Content structure (headings, word count, sections)
    - Meta description length (120-156 chars) - Hashnode limit
    - Tags (1-10 items)
    """
    
    title: str = Field(..., min_length=10, max_length=200)
    seo_title: str = Field(..., min_length=40, max_length=70)
    content: str = Field(..., min_length=500)
    meta_description: str = Field(..., min_length=120, max_length=156)  # Hashnode limit is 156
    tags: List[str] = Field(..., min_length=1, max_length=10)
    estimated_read_time: str = Field(default="5 min read")
    
    # Computed fields (set during validation)
    word_count: int = Field(default=0)
    content_metrics: Optional[dict] = Field(default=None)
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError(f"Title too short: {len(v)} chars (minimum 10)")
        return v.strip()
    
    @field_validator('seo_title')
    @classmethod
    def validate_seo_title(cls, v: str) -> str:
        length = len(v.strip())
        if length < 40:
            raise ValueError(f"SEO title too short: {length} chars (minimum 40)")
        if length > 70:
            raise ValueError(f"SEO title too long: {length} chars (maximum 70)")
        return v.strip()
    
    @field_validator('meta_description')
    @classmethod
    def validate_meta_description(cls, v: str) -> str:
        length = len(v.strip())
        if length < 120:
            raise ValueError(f"Meta description too short: {length} chars (minimum 120)")
        if length > 156:
            raise ValueError(f"Meta description too long: {length} chars (maximum 156 for Hashnode)")
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        if not isinstance(v, list):
            raise ValueError("Tags must be a list")
        if len(v) < 1:
            raise ValueError("Must have at least 1 tag")
        if len(v) > 10:
            raise ValueError(f"Too many tags: {len(v)} (maximum 10)")
        # Clean tags
        return [tag.strip() for tag in v if tag.strip()]
    
    @model_validator(mode='after')
    def validate_content_structure(self) -> 'ValidatedBlogContent':
        """Validate the content has proper markdown structure"""
        metrics = analyze_content_structure(self.content)
        
        errors = []
        
        # Check minimum H2 headings (main sections)
        if metrics.h2_count < 3:
            errors.append(
                f"Blog must have at least 3 main sections (## headings). "
                f"Found: {metrics.h2_count}"
            )
        
        # Check total headings
        if metrics.total_headings < 4:
            errors.append(
                f"Blog must have at least 4 headings total (## or ###). "
                f"Found: {metrics.total_headings}"
            )
        
        # Check word count (minimum 800 words)
        if metrics.word_count < 800:
            errors.append(
                f"Blog content too short: {metrics.word_count} words (minimum 800)"
            )
        
        # Check for introduction
        if not metrics.has_introduction:
            errors.append(
                "Blog must start with an introduction paragraph before the first heading"
            )
        
        # Check content ending (not truncated)
        if not metrics.content_ends_properly:
            errors.append(
                "Content appears to be truncated or incomplete (suspicious ending)"
            )
        
        if errors:
            raise ValueError("; ".join(errors))
        
        # Set computed fields
        self.word_count = metrics.word_count
        self.content_metrics = metrics.to_dict()
        
        return self


def validate_blog_data(blog_data: dict) -> Tuple[bool, List[str], Optional[dict]]:
    """
    Validate blog data and return validation result.
    
    Args:
        blog_data: Dictionary with blog content fields
        
    Returns:
        Tuple of (is_valid, error_messages, validated_data)
        - is_valid: True if validation passed
        - error_messages: List of error strings (empty if valid)
        - validated_data: The validated dict with computed fields (None if invalid)
    """
    try:
        validated = ValidatedBlogContent.model_validate(blog_data)
        return True, [], validated.model_dump()
    except Exception as e:
        error_str = str(e)
        # Parse Pydantic validation errors
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                field = '.'.join(str(loc) for loc in err.get('loc', []))
                msg = err.get('msg', str(err))
                errors.append(f"{field}: {msg}" if field else msg)
        else:
            # Simple error message
            errors = [error_str]
        
        return False, errors, None
