"""
FastAPI routes for manual operations and monitoring
"""
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models import (
    get_db, Category, Topic, Blog, Log,
    TopicStatus, BlogStatus, JobType
)
from app.jobs import run_topic_generation, run_blog_publishing
from app.scheduler import job_scheduler

router = APIRouter()


# ============================================================================
# Response Models
# ============================================================================

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    last_used_date: Optional[datetime]
    usage_count: int

    class Config:
        from_attributes = True


class TopicResponse(BaseModel):
    id: int
    category_id: int
    title: str
    status: str
    scheduled_date: datetime

    class Config:
        from_attributes = True


class BlogResponse(BaseModel):
    id: int
    topic_id: int
    title: str
    status: str
    word_count: int
    hashnode_url: Optional[str]
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobInfoResponse(BaseModel):
    id: str
    name: str
    next_run_time: Optional[str]
    trigger: str


class StatsResponse(BaseModel):
    total_categories: int
    active_categories: int
    pending_topics: int
    published_blogs: int
    draft_blogs: int
    failed_topics: int


# ============================================================================
# Category Management
# ============================================================================

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(
    active_only: bool = Query(False, description="Show only active categories")
):
    """List all categories"""
    with get_db() as db:
        query = db.query(Category)
        if active_only:
            query = query.filter(Category.is_active == True)

        categories = query.order_by(Category.name).all()
        return categories


@router.post("/categories", response_model=CategoryResponse)
def create_category(
    name: str,
    description: Optional[str] = None,
    is_active: bool = True
):
    """Create a new category"""
    with get_db() as db:
        # Check if category already exists
        existing = db.query(Category).filter(Category.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category already exists")

        category = Category(
            name=name,
            description=description,
            is_active=is_active
        )
        db.add(category)
        db.flush()
        db.refresh(category)

        return category


@router.patch("/categories/{category_id}")
def update_category(
    category_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """Update a category"""
    with get_db() as db:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        if name is not None:
            category.name = name
        if description is not None:
            category.description = description
        if is_active is not None:
            category.is_active = is_active

        category.updated_at = datetime.utcnow()
        db.flush()

        return {"message": "Category updated successfully"}


# ============================================================================
# Topic Management
# ============================================================================

@router.get("/topics", response_model=List[TopicResponse])
def list_topics(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of results")
):
    """List topics"""
    with get_db() as db:
        query = db.query(Topic)

        if status:
            try:
                status_enum = TopicStatus[status.upper()]
                query = query.filter(Topic.status == status_enum)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        topics = (
            query
            .order_by(Topic.scheduled_date.desc())
            .limit(limit)
            .all()
        )

        return topics


@router.get("/topics/upcoming", response_model=List[TopicResponse])
def list_upcoming_topics(
    days: int = Query(7, description="Number of days to look ahead")
):
    """List upcoming scheduled topics"""
    with get_db() as db:
        from datetime import timedelta
        end_date = date.today() + timedelta(days=days)

        topics = (
            db.query(Topic)
            .filter(
                Topic.scheduled_date >= date.today(),
                Topic.scheduled_date <= end_date,
                Topic.status == TopicStatus.PENDING
            )
            .order_by(Topic.scheduled_date)
            .all()
        )

        return topics


# ============================================================================
# Blog Management
# ============================================================================

@router.get("/blogs", response_model=List[BlogResponse])
def list_blogs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Maximum number of results")
):
    """List blogs"""
    with get_db() as db:
        query = db.query(Blog)

        if status:
            try:
                status_enum = BlogStatus[status.upper()]
                query = query.filter(Blog.status == status_enum)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        blogs = (
            query
            .order_by(Blog.created_at.desc())
            .limit(limit)
            .all()
        )

        return blogs


@router.get("/blogs/{blog_id}")
def get_blog(blog_id: int):
    """Get full blog details including content"""
    with get_db() as db:
        blog = db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")

        topic = db.query(Topic).filter(Topic.id == blog.topic_id).first()
        category = db.query(Category).filter(Category.id == topic.category_id).first()

        return {
            "id": blog.id,
            "title": blog.title,
            "content": blog.content,
            "meta_description": blog.meta_description,
            "tags": blog.tags,
            "word_count": blog.word_count,
            "status": blog.status.value,
            "hashnode_url": blog.hashnode_url,
            "published_at": blog.published_at,
            "topic": {
                "id": topic.id,
                "title": topic.title,
                "scheduled_date": topic.scheduled_date
            },
            "category": {
                "id": category.id,
                "name": category.name
            }
        }


# ============================================================================
# Manual Job Triggers
# ============================================================================

@router.post("/jobs/generate-topics")
def trigger_topic_generation():
    """Manually trigger topic generation job"""
    try:
        run_topic_generation()
        return {"message": "Topic generation completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job failed: {str(e)}")


@router.post("/jobs/publish-blog")
def trigger_blog_publishing():
    """Manually trigger blog publishing job"""
    try:
        run_blog_publishing()
        return {"message": "Blog publishing completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job failed: {str(e)}")


# ============================================================================
# Scheduler Management
# ============================================================================

@router.get("/scheduler/jobs", response_model=List[JobInfoResponse])
def list_scheduled_jobs():
    """List all scheduled jobs"""
    jobs = []
    for job_id in ["topic_generation", "blog_publishing"]:
        info = job_scheduler.get_job_info(job_id)
        if info:
            jobs.append(info)
    return jobs


@router.post("/scheduler/run/{job_id}")
def run_job_now(job_id: str):
    """Trigger a scheduled job to run immediately"""
    try:
        job_scheduler.run_job_now(job_id)
        return {"message": f"Job {job_id} triggered successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Stats & Monitoring
# ============================================================================

@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """Get system statistics"""
    with get_db() as db:
        stats = {
            "total_categories": db.query(Category).count(),
            "active_categories": db.query(Category).filter(Category.is_active == True).count(),
            "pending_topics": db.query(Topic).filter(Topic.status == TopicStatus.PENDING).count(),
            "published_blogs": db.query(Blog).filter(Blog.status == BlogStatus.PUBLISHED).count(),
            "draft_blogs": db.query(Blog).filter(Blog.status == BlogStatus.DRAFT).count(),
            "failed_topics": db.query(Topic).filter(Topic.status == TopicStatus.FAILED).count()
        }
        return stats


@router.get("/logs")
def get_logs(
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(50, description="Maximum number of results")
):
    """Get job execution logs"""
    with get_db() as db:
        query = db.query(Log)

        if job_type:
            try:
                job_type_enum = JobType[job_type.upper()]
                query = query.filter(Log.job_type == job_type_enum)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid job type: {job_type}")

        logs = (
            query
            .order_by(Log.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": log.id,
                "job_type": log.job_type.value,
                "status": log.status.value,
                "details": log.details,
                "created_at": log.created_at
            }
            for log in logs
        ]


@router.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with get_db() as db:
            db.execute("SELECT 1")

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )
