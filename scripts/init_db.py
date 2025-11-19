"""
Database initialization script
Creates tables and seeds initial data
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import init_db, get_db, Category
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def seed_categories():
    """Seed initial categories"""
    logger.info("Seeding initial categories...")

    default_categories = [
        {
            "name": "Blockchain Technology",
            "description": "Topics covering blockchain fundamentals, consensus mechanisms, distributed ledgers, and decentralized systems"
        },
        {
            "name": "Web3 Development",
            "description": "Smart contracts, dApps, Web3.js, Ethers.js, blockchain development tools and frameworks"
        },
        {
            "name": "Cryptocurrency & DeFi",
            "description": "Cryptocurrencies, decentralized finance, yield farming, liquidity pools, DEXs, and token economics"
        },
        {
            "name": "NFTs & Digital Assets",
            "description": "Non-fungible tokens, digital art, NFT marketplaces, metadata standards, and use cases"
        },
        {
            "name": "AI & Machine Learning",
            "description": "Artificial intelligence, machine learning, deep learning, neural networks, and AI applications"
        },
        {
            "name": "Cloud Computing & DevOps",
            "description": "Cloud platforms (AWS, Azure, GCP), containerization, CI/CD, infrastructure as code, and DevOps practices"
        },
        {
            "name": "Cybersecurity",
            "description": "Security best practices, cryptography, vulnerability assessment, penetration testing, and security tools"
        },
        {
            "name": "Software Architecture",
            "description": "Design patterns, microservices, system design, scalability, and architectural best practices"
        }
    ]

    with get_db() as db:
        # MongoDB: Check if categories exist
        existing_count = db.categories.count_documents({})

        if existing_count > 0:
            logger.info(f"Categories already exist ({existing_count} found). Skipping seed.")
            return

        # MongoDB: Create category documents
        category_docs = [Category.create(cat["name"], cat["description"]) for cat in default_categories]

        # MongoDB: Insert all at once
        result = db.categories.insert_many(category_docs)

        for cat_data in default_categories:
            logger.info(f"  + {cat_data['name']}")

        logger.info(f"✓ Seeded {len(result.inserted_ids)} categories")


def main():
    """Main initialization function"""
    logger.info("=" * 80)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 80)

    try:
        # Create tables
        logger.info("Creating database tables...")
        init_db()
        logger.info("✓ Tables created")

        # Seed initial data
        seed_categories()

        logger.info("=" * 80)
        logger.info("INITIALIZATION COMPLETE")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
