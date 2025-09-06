from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
import json

from ..models import get_db, Idea, Vote, User, IdeaView
from ..utils.auth import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ideas", response_class=HTMLResponse)
async def list_ideas(
    request: Request,
    category: Optional[str] = None,
    sort: str = "trending",
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    query = select(Idea).where(Idea.status == "active")
    
    # Filter by category
    if category and category != "all":
        query = query.where(Idea.category == category)
    
    # Apply sorting
    if sort == "newest":
        query = query.order_by(desc(Idea.created_at))
    elif sort == "popular":
        query = query.order_by(desc(Idea.vote_count))
    elif sort == "controversial":
        query = query.order_by(desc(func.abs(Idea.vote_count)))
    else:  # trending (default)
        # Simple trending: recent ideas with votes
        query = query.order_by(desc(Idea.vote_count + func.julianday('now') - func.julianday(Idea.created_at)))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    ideas = result.scalars().all()
    
    return templates.TemplateResponse(
        "ideas/list.html", 
        {"request": request, "ideas": ideas, "category": category, "sort": sort}
    )

@router.post("/ideas", response_class=HTMLResponse)
async def create_idea(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    tags: Optional[str] = Form(None),
    is_anonymous: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    # Create new idea
    new_idea = Idea(
        title=title,
        description=description,
        category=category,
        tags=tags,
        user_id=current_user.id if current_user and not is_anonymous else None,
        is_anonymous=is_anonymous
    )
    
    db.add(new_idea)
    await db.commit()
    await db.refresh(new_idea)
    
    return templates.TemplateResponse("partials/idea_created.html", {
        "request": request, 
        "idea": new_idea
    })

@router.get("/ideas/{idea_id}", response_class=HTMLResponse)
async def get_idea(
    idea_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    # Fetch idea with vote count
    result = await db.execute(
        select(Idea).where(Idea.id == idea_id, Idea.status == "active")
    )
    idea = result.scalar_one_or_none()
    
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    # Get user's vote if authenticated
    user_vote = None
    if current_user:
        vote_result = await db.execute(
            select(Vote).where(Vote.idea_id == idea_id, Vote.user_id == current_user.id)
        )
        user_vote_obj = vote_result.scalar_one_or_none()
        user_vote = user_vote_obj.vote_type if user_vote_obj else None
        
        # Record view
        view = IdeaView(idea_id=idea_id, user_id=current_user.id)
        db.add(view)
    else:
        # Record anonymous view with IP
        ip_address = request.client.host if request.client else None
        view = IdeaView(idea_id=idea_id, ip_address=ip_address)
        db.add(view)
    
    # Update view count
    idea.view_count += 1
    await db.commit()
    
    return templates.TemplateResponse("ideas/detail.html", {
        "request": request, 
        "idea": idea, 
        "user_vote": user_vote
    })

@router.patch("/ideas/{idea_id}/vote", response_class=HTMLResponse)
async def vote_idea(
    idea_id: int,
    request: Request,
    vote_type: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if idea exists
    idea_result = await db.execute(
        select(Idea).where(Idea.id == idea_id, Idea.status == "active")
    )
    idea = idea_result.scalar_one_or_none()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    # Check for existing vote
    existing_vote_result = await db.execute(
        select(Vote).where(Vote.idea_id == idea_id, Vote.user_id == current_user.id)
    )
    existing_vote = existing_vote_result.scalar_one_or_none()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Remove vote (toggle off)
            await db.delete(existing_vote)
            idea.vote_count -= vote_type
            user_vote = None
        else:
            # Change vote
            old_vote_type = existing_vote.vote_type
            existing_vote.vote_type = vote_type
            idea.vote_count = idea.vote_count - old_vote_type + vote_type
            user_vote = vote_type
    else:
        # Create new vote
        new_vote = Vote(
            user_id=current_user.id,
            idea_id=idea_id,
            vote_type=vote_type
        )
        db.add(new_vote)
        idea.vote_count += vote_type
        user_vote = vote_type
    
    await db.commit()
    await db.refresh(idea)
    
    return templates.TemplateResponse("partials/vote_buttons.html", {
        "request": request, 
        "idea": idea, 
        "user_vote": user_vote
    })