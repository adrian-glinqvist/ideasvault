from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..models import get_db, Idea, Vote
from ..utils.auth import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/ideas", response_class=HTMLResponse)
async def list_ideas(
    request: Request,
    category: Optional[str] = None,
    sort: str = "trending",
    db: AsyncSession = Depends(get_db)
):
    # TODO: Implement ideas fetching logic
    ideas = []
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
    # TODO: Implement idea creation logic
    return templates.TemplateResponse("partials/idea_created.html", {"request": request})

@router.get("/ideas/{idea_id}", response_class=HTMLResponse)
async def get_idea(
    idea_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # TODO: Implement single idea fetching
    return templates.TemplateResponse("ideas/detail.html", {"request": request, "idea_id": idea_id})

@router.patch("/ideas/{idea_id}/vote", response_class=HTMLResponse)
async def vote_idea(
    idea_id: int,
    request: Request,
    vote_type: int = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    # TODO: Implement voting logic
    return templates.TemplateResponse("partials/vote_buttons.html", {"request": request, "idea_id": idea_id})