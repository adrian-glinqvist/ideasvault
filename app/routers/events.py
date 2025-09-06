from fastapi import APIRouter, Depends
from sse_starlette import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio
import json
from datetime import datetime, timedelta

from ..models import get_db, Idea, Vote

router = APIRouter()

# In-memory storage for real-time events (in production, use Redis or similar)
_event_queue = asyncio.Queue()

async def broadcast_idea_event(event_type: str, idea_data: dict):
    """Broadcast an idea-related event to all connected clients"""
    await _event_queue.put({
        "event": event_type,
        "data": json.dumps(idea_data),
        "timestamp": datetime.now().isoformat()
    })

@router.get("/ideas")
async def ideas_stream(db: AsyncSession = Depends(get_db)):
    async def event_generator():
        last_check = datetime.now() - timedelta(seconds=30)
        
        while True:
            try:
                # Check for new ideas in the last 30 seconds
                result = await db.execute(
                    select(Idea).where(
                        Idea.created_at > last_check,
                        Idea.status == "active"
                    ).order_by(Idea.created_at.desc()).limit(5)
                )
                new_ideas = result.scalars().all()
                
                if new_ideas:
                    for idea in new_ideas:
                        yield {
                            "event": "new_idea",
                            "data": json.dumps({
                                "id": idea.id,
                                "title": idea.title,
                                "category": idea.category,
                                "vote_count": idea.vote_count,
                                "created_at": idea.created_at.isoformat()
                            })
                        }
                
                # Check for vote updates
                result = await db.execute(
                    select(
                        Idea.id, 
                        Idea.title, 
                        Idea.vote_count
                    ).where(Idea.status == "active")
                    .order_by(Idea.vote_count.desc())
                    .limit(10)
                )
                trending_ideas = result.all()
                
                yield {
                    "event": "trending_update",
                    "data": json.dumps([{
                        "id": idea.id,
                        "title": idea.title,
                        "vote_count": idea.vote_count
                    } for idea in trending_ideas])
                }
                
                last_check = datetime.now()
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                # Handle any database errors gracefully
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }
                await asyncio.sleep(60)  # Wait longer on error
    
    return EventSourceResponse(event_generator())

@router.get("/votes/{idea_id}")
async def vote_stream(idea_id: int, db: AsyncSession = Depends(get_db)):
    async def event_generator():
        last_vote_count = None
        
        while True:
            try:
                # Get current vote count for the idea
                result = await db.execute(
                    select(Idea.vote_count, Idea.title).where(
                        Idea.id == idea_id, 
                        Idea.status == "active"
                    )
                )
                idea_data = result.first()
                
                if idea_data:
                    current_vote_count = idea_data.vote_count
                    
                    # Only send update if vote count changed
                    if last_vote_count is None or last_vote_count != current_vote_count:
                        yield {
                            "event": "vote_update",
                            "data": json.dumps({
                                "idea_id": idea_id,
                                "title": idea_data.title,
                                "vote_count": current_vote_count,
                                "timestamp": datetime.now().isoformat()
                            })
                        }
                        last_vote_count = current_vote_count
                
                await asyncio.sleep(5)  # Check every 5 seconds for votes
                
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e), "idea_id": idea_id})
                }
                await asyncio.sleep(30)  # Wait longer on error
    
    return EventSourceResponse(event_generator())

@router.get("/activity")
async def activity_stream(db: AsyncSession = Depends(get_db)):
    """General activity stream for homepage"""
    async def event_generator():
        while True:
            try:
                # Get recent activity (new ideas and high-vote ideas)
                recent_ideas = await db.execute(
                    select(Idea).where(Idea.status == "active")
                    .order_by(Idea.created_at.desc())
                    .limit(3)
                )
                
                trending_ideas = await db.execute(
                    select(Idea).where(
                        Idea.status == "active",
                        Idea.vote_count > 0
                    ).order_by(Idea.vote_count.desc())
                    .limit(3)
                )
                
                # Get total stats
                stats_result = await db.execute(
                    select(
                        func.count(Idea.id).label('total_ideas'),
                        func.sum(Idea.vote_count).label('total_votes'),
                        func.sum(Idea.view_count).label('total_views')
                    ).where(Idea.status == "active")
                )
                stats = stats_result.first()
                
                yield {
                    "event": "activity_update",
                    "data": json.dumps({
                        "recent_ideas": len(recent_ideas.scalars().all()),
                        "trending_ideas": len(trending_ideas.scalars().all()),
                        "total_ideas": stats.total_ideas or 0,
                        "total_votes": stats.total_votes or 0,
                        "total_views": stats.total_views or 0,
                        "timestamp": datetime.now().isoformat()
                    })
                }
                
                await asyncio.sleep(60)  # Send activity update every minute
                
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }
                await asyncio.sleep(120)  # Wait longer on error
    
    return EventSourceResponse(event_generator())