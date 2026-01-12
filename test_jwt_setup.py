#!/usr/bin/env python3
"""
Quick test to check if JWT tokens are configured correctly
"""
import sys
import os

sys.path.insert(0, '/home/shivam/App/Work/Phrase_trade/Blog-Automation')

from config import settings

def test_jwt_configuration():
    """Check JWT token configuration"""
    
    print("=" * 60)
    print("JWT TOKEN CONFIGURATION CHECK")
    print("=" * 60)
    print()
    
    # Check publications
    print(f"📚 Found {len(settings.HASHNODE_PUBLICATIONS)} publications:")
    print()
    
    for pub in settings.HASHNODE_PUBLICATIONS:
        print(f"Publication: {pub.name}")
        print(f"  ├─ API Token: {'✓ Set' if pub.api_token else '✗ Missing'}")
        print(f"  ├─ Publication ID: {'✓ Set' if pub.publication_id else '✗ Missing'}")
        
        if pub.jwt_token:
            token_preview = pub.jwt_token[:20] + "..." if len(pub.jwt_token) > 20 else pub.jwt_token
            print(f"  └─ JWT Token: ✓ Set ({token_preview})")
            print(f"     └─ Length: {len(pub.jwt_token)} characters")
        else:
            print(f"  └─ JWT Token: ✗ Not configured")
            print(f"     └─ Images will use S3 only")
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    jwt_count = sum(1 for pub in settings.HASHNODE_PUBLICATIONS if pub.jwt_token)
    total_count = len(settings.HASHNODE_PUBLICATIONS)
    
    if jwt_count == total_count:
        print("✅ All publications have JWT tokens configured!")
        print("   Your system will upload to both S3 and Hashnode CDN.")
        return True
    elif jwt_count > 0:
        print(f"⚠️  Only {jwt_count}/{total_count} publications have JWT tokens.")
        print("   Some publications will use S3 only.")
        return True
    else:
        print("ℹ️  No JWT tokens configured.")
        print("   All images will upload to S3 only (this works fine!).")
        print()
        print("To enable Hashnode CDN uploads:")
        print("  1. See: docs/GET_JWT_TOKEN.md")
        print("  2. Or: QUICK_START.md")
        return True

if __name__ == "__main__":
    try:
        success = test_jwt_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
