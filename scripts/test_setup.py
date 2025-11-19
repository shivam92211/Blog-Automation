"""
Test setup script
Validates that all components are configured correctly
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from config.logging_config import setup_logging, get_logger
from app.models import get_db, Category
from app.services import gemini_service, hashnode_service

setup_logging()
logger = get_logger(__name__)


def test_database():
    """Test database connection"""
    logger.info("Testing database connection...")
    try:
        with get_db() as db:
            # MongoDB: Test connection by listing collections
            collections = db.list_collection_names()
            assert len(collections) > 0

            # MongoDB: Check if categories exist
            category_count = db.categories.count_documents({})
            logger.info(f"  ✓ Database connected ({category_count} categories found)")
            return True
    except Exception as e:
        logger.error(f"  ✗ Database connection failed: {e}")
        return False


def test_gemini_api():
    """Test Gemini API connection"""
    logger.info("Testing Gemini API...")
    try:
        # Simple test: generate 1 topic
        topics = gemini_service.generate_topics(
            category_name="Test Category",
            category_description="This is a test",
            existing_topics=[],
            count=1
        )
        assert len(topics) > 0
        logger.info(f"  ✓ Gemini API working (generated test topic)")
        return True
    except Exception as e:
        logger.error(f"  ✗ Gemini API failed: {e}")
        return False


def test_hashnode_api():
    """Test Hashnode API connection"""
    logger.info("Testing Hashnode API...")
    try:
        # Test by fetching publication info
        pub_info = hashnode_service.get_publication_info()
        logger.info(f"  ✓ Hashnode API working (publication: {pub_info.get('title')})")
        return True
    except Exception as e:
        logger.error(f"  ✗ Hashnode API failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("=" * 80)
    logger.info("SETUP VALIDATION")
    logger.info("=" * 80)

    tests = [
        ("Database", test_database),
        ("Gemini API", test_gemini_api),
        ("Hashnode API", test_hashnode_api)
    ]

    results = []
    for name, test_func in tests:
        logger.info(f"\n{name}:")
        results.append(test_func())

    logger.info("\n" + "=" * 80)
    logger.info("RESULTS")
    logger.info("=" * 80)

    for (name, _), result in zip(tests, results):
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{name}: {status}")

    all_passed = all(results)
    if all_passed:
        logger.info("\n✓ All tests passed! System is ready.")
        sys.exit(0)
    else:
        logger.error("\n✗ Some tests failed. Please fix configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
