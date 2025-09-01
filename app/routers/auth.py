from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import get_db, User
from ..utils.auth import create_access_token, verify_password, get_password_hash

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # TODO: Implement user registration logic
    return templates.TemplateResponse("partials/register_success.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # TODO: Implement login logic
    return templates.TemplateResponse("partials/login_success.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # TODO: Implement profile display
    return templates.TemplateResponse("auth/profile.html", {"request": request})