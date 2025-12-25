#!/usr/bin/env python3
"""
Test script to debug Hashnode API issues
"""
import requests
import json
from config import settings

# Test data
title = "Architecting Scalable DevOps Pipelines for 2025's Terabyte Internet Traffic Surge"
content = "Test content"
tags = ["DevOps", "Scalability", "CI/CD"]
cover_image_url = "https://blog-automation-phrase-trade.s3.eu-north-1.amazonaws.com/blog-covers/blog_image_1766664453_Architecting_Scalable_DevOps_P.png"

def escape_graphql_string(text: str) -> str:
    """Escape special characters for GraphQL string"""
    if not text:
        return ""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace("\n", "\\n")
    text = text.replace("\r", "\\r")
    text = text.replace("\t", "\\t")
    return text

def format_tags(tags: list) -> str:
    """Format tags for GraphQL mutation - must match ^[a-z0-9-]{1,250}$"""
    import re
    if not tags:
        return "[]"

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

# Escape strings
title_escaped = escape_graphql_string(title)
content_escaped = escape_graphql_string(content)
tags_formatted = format_tags(tags)

# Build mutation
mutation = f"""
mutation PublishPost {{
  publishPost(input: {{
    publicationId: "{settings.HASHNODE_PUBLICATION_ID}"
    title: "{title_escaped}"
    contentMarkdown: "{content_escaped}"
    tags: {tags_formatted}
    coverImageOptions: {{ coverImageURL: "{cover_image_url}" }}
  }}) {{
    post {{
      id
      slug
      url
    }}
  }}
}}
"""

print("=" * 60)
print("Testing Hashnode API")
print("=" * 60)
print(f"\nPublication ID: {settings.HASHNODE_PUBLICATION_ID}")
print(f"API URL: {settings.HASHNODE_API_URL}")
print(f"\nMutation:")
print(mutation)
print("\n" + "=" * 60)

# Make request
headers = {
    "Authorization": settings.HASHNODE_API_TOKEN,
    "Content-Type": "application/json"
}

try:
    response = requests.post(
        settings.HASHNODE_API_URL,
        json={"query": mutation},
        headers=headers,
        timeout=30
    )

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    print(json.dumps(response.json(), indent=2))

except Exception as e:
    print(f"\nError: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response text: {e.response.text}")
