from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from .models import init_db
from .routers import ideas, auth, events

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_db()
    yield

app = FastAPI(
    title=os.getenv("APP_NAME", "IdeasVault"),
    description="A community-driven platform for sharing and voting on startup ideas",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
origins = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(ideas.router)
app.include_router(auth.router, prefix="/auth")
app.include_router(events.router, prefix="/events")

@app.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})