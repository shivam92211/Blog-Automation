#!/usr/bin/env python3
"""
Script to apply bucket policy to make images publicly accessible
Since ACLs are disabled, we need to use bucket policies instead
"""
import boto3
import json
from config import settings

def apply_bucket_policy():
    """Apply a bucket policy to make all blog-covers publicly accessible"""

    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

    bucket_name = settings.AWS_S3_BUCKET_NAME

    # Define bucket policy to allow public read access to blog-covers/*
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadBlogCovers",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/blog-covers/*"
            }
        ]
    }

    try:
        print(f"Applying bucket policy to: {bucket_name}")
        print(f"This will make all objects in 'blog-covers/' publicly readable")

        # Convert policy to JSON string
        policy_string = json.dumps(bucket_policy)

        # Apply the bucket policy
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=policy_string
        )

        print(f"✓ Successfully applied bucket policy!")
        print(f"\nAll images in 'blog-covers/' are now publicly accessible.")
        print(f"\nTest URL: https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/blog-covers/blog_image_1766663657_Securing_Cloud-Native_AI_Chatb.png")

    except Exception as e:
        print(f"✗ Failed to apply bucket policy: {e}")
        print(f"\nAlternative: You can manually set this policy in AWS Console:")
        print(json.dumps(bucket_policy, indent=2))
        return False

    return True

if __name__ == "__main__":
    apply_bucket_policy()
