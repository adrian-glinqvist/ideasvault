from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import get_db, User, Idea
from ..utils.auth import create_access_token, verify_password, get_password_hash, get_current_user_optional

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
    # Check if user already exists
    existing_user_result = await db.execute(
        select(User).where((User.email == email) | (User.username == username))
    )
    existing_user = existing_user_result.scalar_one_or_none()
    
    if existing_user:
        if existing_user.email == email:
            error_msg = "Email already registered"
        else:
            error_msg = "Username already taken"
        return templates.TemplateResponse("partials/register_error.html", {
            "request": request, 
            "error": error_msg
        })
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(
        email=email,
        username=username,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return templates.TemplateResponse("partials/register_success.html", {
        "request": request, 
        "user": new_user,
        "token": access_token
    })

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # Find user by email
    user_result = await db.execute(
        select(User).where(User.email == email)
    )
    user = user_result.scalar_one_or_none()
    
    # Verify user and password
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("partials/login_error.html", {
            "request": request, 
            "error": "Invalid email or password"
        })
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return templates.TemplateResponse("partials/login_success.html", {
        "request": request, 
        "user": user,
        "token": access_token
    })

@router.get("/profile", response_class=HTMLResponse)
async def profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # Get user's ideas and votes
    user_ideas_result = await db.execute(
        select(Idea).where(Idea.user_id == current_user.id).order_by(Idea.created_at.desc())
    )
    user_ideas = user_ideas_result.scalars().all()
    
    return templates.TemplateResponse("auth/profile.html", {
        "request": request, 
        "user": current_user,
        "user_ideas": user_ideas
    })