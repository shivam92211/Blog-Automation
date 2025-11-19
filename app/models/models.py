"""
MongoDB document models and helper classes
Replaces SQLAlchemy models with MongoDB-compatible structures
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from enum import Enum


# Enums for status fields
class TopicStatus(str, Enum):
    """Topic processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BlogStatus(str, Enum):
    """Blog publishing status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    FAILED = "failed"


class JobType(str, Enum):
    """Job types for logging"""
    TOPIC_GENERATION = "topic_generation"
    BLOG_WRITING = "blog_writing"
    BLOG_PUBLISHING = "blog_publishing"


class JobStatus(str, Enum):
    """Job execution status"""
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


# MongoDB Document Helper Classes
class MongoDocument:
    """Base class for MongoDB document helpers"""

    @staticmethod
    def to_object_id(id_str: str) -> ObjectId:
        """Convert string ID to ObjectId"""
        if isinstance(id_str, ObjectId):
            return id_str
        return ObjectId(id_str)

    @staticmethod
    def from_object_id(obj_id: ObjectId) -> str:
        """Convert ObjectId to string"""
        return str(obj_id)

    @classmethod
    def prepare_document(cls, data: Dict[str, Any], exclude_id: bool = False) -> Dict[str, Any]:
        """Prepare document for MongoDB insertion"""
        doc = data.copy()

        # Convert _id if present
        if "_id" in doc and exclude_id:
            del doc["_id"]

        # Add timestamps if not present
        if "created_at" not in doc:
            doc["created_at"] = datetime.utcnow()
        if "updated_at" not in doc:
            doc["updated_at"] = datetime.utcnow()

        return doc


class Category(MongoDocument):
    """Category document model"""

    @staticmethod
    def create(
        name: str,
        description: Optional[str] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create a new category document"""
        return {
            "name": name,
            "description": description,
            "is_active": is_active,
            "last_used_date": None,
            "usage_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @staticmethod
    def to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to dict with string ID"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
        return doc


class Topic(MongoDocument):
    """Topic document model"""

    @staticmethod
    def create(
        category_id: str,
        title: str,
        description: Optional[str] = None,
        keywords: Optional[str] = None,
        scheduled_date: datetime = None,
        status: TopicStatus = TopicStatus.PENDING
    ) -> Dict[str, Any]:
        """Create a new topic document"""
        return {
            "category_id": category_id,
            "title": title,
            "description": description or "",
            "keywords": keywords or "",
            "status": status.value if isinstance(status, TopicStatus) else status,
            "scheduled_date": scheduled_date,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @staticmethod
    def to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to dict"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
        return doc


class Blog(MongoDocument):
    """Blog document model"""

    @staticmethod
    def create(
        topic_id: str,
        title: str,
        content: str,
        meta_description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        word_count: int = 0,
        status: BlogStatus = BlogStatus.DRAFT,
        cover_image_url: Optional[str] = None,
        cover_image_local_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new blog document"""
        return {
            "topic_id": topic_id,
            "title": title,
            "content": content,
            "meta_description": meta_description,
            "tags": tags or [],
            "word_count": word_count,
            "status": status.value if isinstance(status, BlogStatus) else status,
            "hashnode_post_id": None,
            "hashnode_url": None,
            "cover_image_url": cover_image_url,
            "cover_image_local_path": cover_image_local_path,
            "published_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @staticmethod
    def to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to dict"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
        return doc


class GenerationHistory(MongoDocument):
    """Generation history document model"""

    @staticmethod
    def create(
        category_id: str,
        topic_title: str,
        topic_keywords: str,
        topic_hash: str
    ) -> Dict[str, Any]:
        """Create a new generation history document"""
        return {
            "category_id": category_id,
            "topic_title": topic_title,
            "topic_keywords": topic_keywords,
            "topic_hash": topic_hash,
            "generated_at": datetime.utcnow()
        }

    @staticmethod
    def to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to dict"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
        return doc


class Log(MongoDocument):
    """Log document model"""

    @staticmethod
    def create(
        job_type: JobType,
        status: JobStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new log document"""
        return {
            "job_type": job_type.value if isinstance(job_type, JobType) else job_type,
            "status": status.value if isinstance(status, JobStatus) else status,
            "details": details or {},
            "created_at": datetime.utcnow()
        }

    @staticmethod
    def to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to dict"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
        return doc
