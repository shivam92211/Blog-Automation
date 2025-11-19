"""
NewsData.io API Service
Fetches latest tech news to inform blog topic generation
"""
from newsdataapi import NewsDataApiClient
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)


class NewsDataService:
    """Service for fetching and processing news from NewsData.io API"""

    def __init__(self):
        """Initialize NewsData.io API client"""
        self.api_key = settings.NEWSDATA_API_KEY
        self.client = NewsDataApiClient(apikey=self.api_key)
        self.max_articles = settings.NEWSDATA_MAX_ARTICLES
        self.lookback_days = settings.NEWSDATA_LOOKBACK_DAYS
        logger.info("NewsDataService initialized")

    def fetch_tech_news(self, max_articles: Optional[int] = None) -> List[Dict]:
        """
        Fetch latest technology news from NewsData.io

        Args:
            max_articles: Maximum number of articles to fetch (default from settings)

        Returns:
            List of article dictionaries with title, description, link, etc.
        """
        max_results = max_articles or self.max_articles
        logger.info(f"Fetching latest tech news (max: {max_results} articles)")

        try:
            # Fetch latest tech news in English
            response = self.client.latest_api(
                category='technology',
                language='en',
                max_result=max_results
            )

            if response.get('status') == 'success':
                articles = response.get('results', [])
                logger.info(f"Successfully fetched {len(articles)} tech articles from newsdata.io")
                return articles
            else:
                logger.error(f"NewsData API returned non-success status: {response}")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch news from newsdata.io: {str(e)}", exc_info=True)
            return []

    def extract_trending_topics(self, articles: List[Dict]) -> List[Dict]:
        """
        Extract trending topics and keywords from news articles

        Args:
            articles: List of article dictionaries from API

        Returns:
            List of topic dictionaries with title, description, keywords, etc.
        """
        topics = []

        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            keywords = article.get('keywords', [])

            # Skip articles without sufficient information
            if not title:
                continue

            topics.append({
                'title': title,
                'description': description or 'N/A',
                'keywords': keywords or [],
                'link': article.get('link', ''),
                'pub_date': article.get('pubDate', ''),
                'source': article.get('source_id', 'Unknown')
            })

        logger.info(f"Extracted {len(topics)} trending topics from {len(articles)} articles")
        return topics

    def get_news_context(self, category_name: Optional[str] = None) -> str:
        """
        Get formatted news context for Gemini AI prompt

        Args:
            category_name: Category name (currently not used, future enhancement)

        Returns:
            Formatted string with trending news for prompt inclusion
        """
        logger.info(f"Getting news context for category: {category_name or 'technology'}")

        # Fetch latest news
        articles = self.fetch_tech_news()

        if not articles:
            logger.warning("No articles fetched, returning empty context")
            return ""

        # Format top 10 articles for context
        context_lines = []
        context_lines.append("TRENDING TECH NEWS (Past 48 hours):")
        context_lines.append("=" * 60)

        for i, article in enumerate(articles[:10], 1):
            title = article.get('title', 'N/A')
            description = article.get('description', '')
            source = article.get('source_id', 'Unknown')

            # Add article title and source
            context_lines.append(f"\n{i}. {title}")
            context_lines.append(f"   Source: {source}")

            # Add truncated description if available
            if description and description != 'N/A':
                truncated_desc = description[:200] + "..." if len(description) > 200 else description
                context_lines.append(f"   {truncated_desc}")

        context_lines.append("\n" + "=" * 60)
        context = "\n".join(context_lines)

        logger.info(f"Generated news context: {len(context)} characters from {min(10, len(articles))} articles")
        return context

    def get_trending_keywords(self, articles: Optional[List[Dict]] = None) -> List[str]:
        """
        Extract trending keywords from articles

        Args:
            articles: List of articles (will fetch if not provided)

        Returns:
            List of unique keywords sorted by frequency
        """
        if articles is None:
            articles = self.fetch_tech_news()

        if not articles:
            return []

        # Collect all keywords
        all_keywords = []
        for article in articles:
            keywords = article.get('keywords', [])
            if keywords:
                all_keywords.extend(keywords)

        # Count frequency and return unique keywords
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        trending = [kw for kw, count in keyword_counts.most_common(20)]

        logger.info(f"Extracted {len(trending)} trending keywords from {len(articles)} articles")
        return trending


# Singleton instance
newsdata_service = NewsDataService()
