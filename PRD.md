# Product Requirements Document (PRD)
## Startup Ideas Directory Web Application

### 1. Executive Summary

**Product Name:** IdeasVault  
**Vision:** A community-driven platform where entrepreneurs, innovators, and dreamers can share, discover, and vote on startup ideas to foster innovation and collaboration.

**Technology Stack:**
- **Frontend:** Datastar (hypermedia framework) + Basecoat.ui (component library)
- **Backend:** Python + FastAPI (hypermedia API server)
- **Database:** Turso (SQLite cloud database)
- **Deployment:** Edge-optimized with Turso's global distribution

### 2. Product Overview

IdeasVault is a web application that serves as a centralized directory for startup ideas where users can:
- Browse and discover innovative startup concepts
- Submit their own startup ideas to the community
- Vote and provide feedback on existing ideas
- Filter and search ideas by category, popularity, or recency

### 3. Target Audience

**Primary Users:**
- Aspiring entrepreneurs seeking inspiration
- Investors looking for innovative concepts
- Students and professionals interested in startup ecosystem
- Innovation managers in corporations

**Secondary Users:**
- Startup accelerators and incubators
- Business consultants
- Academic researchers studying entrepreneurship trends

### 4. Core Features

#### 4.1 Idea Submission System
- **Simple Upload Form:** Users can submit startup ideas with title, description, category, and optional tags
- **Rich Text Support:** Allow basic formatting for idea descriptions
- **Category Classification:** Predefined categories (SaaS, E-commerce, FinTech, HealthTech, etc.)
- **Anonymous/Named Submissions:** Option to submit ideas anonymously or with attribution

#### 4.2 Voting & Engagement System
- **Upvote/Downvote Mechanism:** Reddit-style voting system
- **Vote Tracking:** Real-time vote count updates using Datastar's SSE capabilities
- **Duplicate Prevention:** One vote per user per idea
- **Engagement Metrics:** Track views, votes, and comments per idea

#### 4.3 Discovery & Navigation
- **Homepage Feed:** Trending and recent ideas with real-time updates
- **Search Functionality:** Full-text search across idea titles and descriptions
- **Filtering Options:** By category, vote count, submission date, and trending status
- **Sorting Options:** Most popular, newest, most controversial, trending

#### 4.4 User Management
- **Simple Registration:** Email-based user accounts
- **User Profiles:** Basic profile with submitted ideas and voting history
- **Moderation Tools:** Flag inappropriate content, admin review system

### 5. Technical Architecture

#### 5.1 Frontend Architecture (Datastar + Basecoat.ui)
```html
<!-- Example Datastar implementation -->
<div data-store='{"sort": "trending", "category": "all"}'>
  <button data-on-click="@patch('/ideas/sort/popular')">
    Most Popular
  </button>
  <div data-text="$ideas.length + ' ideas found'"></div>
</div>
```

**Key Benefits:**
- **Minimal JavaScript:** Datastar handles reactivity with HTML attributes
- **Server-Driven UI:** State management handled on backend
- **Real-time Updates:** SSE for live vote counts and new submissions
- **Component Consistency:** Basecoat.ui provides consistent UI components

#### 5.2 Backend Architecture (Python + FastAPI)

**FastAPI Server Structure:**
```python
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from sse_starlette import EventSourceResponse

app = FastAPI(title="IdeasVault API")
templates = Jinja2Templates(directory="templates")

# Hypermedia endpoints returning HTML
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    ideas = await get_trending_ideas()
    return templates.TemplateResponse("index.html", {
        "request": request, "ideas": ideas
    })

# SSE endpoint for real-time updates
@app.get("/events/votes/{idea_id}")
async def vote_stream(idea_id: int):
    return EventSourceResponse(vote_event_generator(idea_id))
```

**Key Backend Features:**
- **Hypermedia API:** RESTful endpoints returning HTML fragments
- **Real-time Events:** FastAPI + SSE-Starlette for live updates
- **Template Engine:** Jinja2 for server-side HTML rendering
- **Data Processing:** Server-side filtering, sorting, and search
- **Authentication:** JWT tokens with secure HTTP-only cookies
- **Database ORM:** SQLAlchemy with async support for Turso
- **Validation:** Pydantic models for request/response validation

#### 5.3 Database Schema (Turso SQLite)
```sql
-- Ideas table
CREATE TABLE ideas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  tags TEXT, -- JSON array of tags
  user_id INTEGER,
  vote_count INTEGER DEFAULT 0,
  view_count INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_anonymous BOOLEAN DEFAULT FALSE,
  status TEXT DEFAULT 'active' -- active, flagged, removed
);

-- Users table
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE,
  password_hash TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_admin BOOLEAN DEFAULT FALSE
);

-- Votes table
CREATE TABLE votes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  idea_id INTEGER NOT NULL,
  vote_type INTEGER NOT NULL, -- 1 for upvote, -1 for downvote
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  FOREIGN KEY (idea_id) REFERENCES ideas(id),
  UNIQUE(user_id, idea_id)
);

-- Views tracking table
CREATE TABLE idea_views (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  idea_id INTEGER NOT NULL,
  user_id INTEGER, -- nullable for anonymous views
  ip_address TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (idea_id) REFERENCES ideas(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 6. User Experience Flow

#### 6.1 Homepage Experience
1. **Landing Page:** Clean interface showing trending ideas with Basecoat.ui components
2. **Real-time Updates:** New submissions and vote changes appear without page refresh
3. **Quick Actions:** One-click voting, easy idea submission
4. **Discovery Tools:** Category filters, search bar, sorting options

#### 6.2 Idea Submission Flow
1. **Simple Form:** Title, description, category selection using Basecoat.ui form components
2. **Live Preview:** Real-time preview of how the idea will appear
3. **Validation:** Client and server-side validation with immediate feedback
4. **Success State:** Confirmation with link to view submitted idea

#### 6.3 Voting Experience
1. **One-Click Voting:** Instant feedback with Datastar reactive updates
2. **Visual Feedback:** Clear indication of user's vote status
3. **Real-time Counts:** Live vote count updates across all users
4. **Vote History:** Users can see their voting activity in their profile

### 7. Technical Implementation Plan

#### 7.1 Phase 1: MVP Core Features
- Basic idea submission and display
- Simple voting system
- User registration and authentication
- Homepage with idea listing

#### 7.2 Phase 2: Enhanced Discovery
- Advanced search and filtering
- Category-based browsing
- Trending algorithm implementation
- User profiles and history

#### 7.3 Phase 3: Community Features
- Comment system on ideas
- Idea collaboration features
- Moderation and reporting tools
- Analytics dashboard

### 8. FastAPI Endpoints

#### 8.1 Core Endpoints (Python/FastAPI)
```python
# Homepage and Ideas
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request) -> HTMLResponse

@app.get("/ideas", response_class=HTMLResponse) 
async def list_ideas(category: str = None, sort: str = "trending") -> HTMLResponse

@app.post("/ideas", response_class=HTMLResponse)
async def create_idea(request: Request, idea: IdeaCreate) -> HTMLResponse

@app.get("/ideas/{idea_id}", response_class=HTMLResponse)
async def get_idea(idea_id: int, request: Request) -> HTMLResponse

@app.patch("/ideas/{idea_id}/vote", response_class=HTMLResponse)
async def vote_idea(idea_id: int, vote_type: int, user: User = Depends(get_current_user)) -> HTMLResponse

@app.get("/search", response_class=HTMLResponse)
async def search_ideas(q: str, request: Request) -> HTMLResponse

@app.get("/categories", response_class=HTMLResponse)
async def list_categories(request: Request) -> HTMLResponse

# Authentication endpoints
@app.post("/auth/register", response_class=HTMLResponse)
async def register(request: Request, user_data: UserCreate) -> HTMLResponse

@app.post("/auth/login", response_class=HTMLResponse)
async def login(request: Request, credentials: UserLogin) -> HTMLResponse

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, user: User = Depends(get_current_user)) -> HTMLResponse
```

#### 8.2 Real-time SSE Endpoints
```python
@app.get("/events/ideas")
async def ideas_stream() -> EventSourceResponse:
    return EventSourceResponse(idea_updates_generator())

@app.get("/events/votes/{idea_id}")
async def vote_stream(idea_id: int) -> EventSourceResponse:
    return EventSourceResponse(vote_event_generator(idea_id))
```

### 9. Data Models

#### 9.1 Idea Model
```typescript
interface Idea {
  id: number;
  title: string;
  description: string;
  category: string;
  tags: string[];
  userId?: number;
  voteCount: number;
  viewCount: number;
  createdAt: Date;
  updatedAt: Date;
  isAnonymous: boolean;
  status: 'active' | 'flagged' | 'removed';
}
```

#### 9.2 Vote Model
```typescript
interface Vote {
  id: number;
  userId: number;
  ideaId: number;
  voteType: 1 | -1; // 1 for upvote, -1 for downvote
  createdAt: Date;
}
```

### 10. Security & Performance Considerations

#### 10.1 Security
- **Input Validation:** Sanitize all user inputs to prevent XSS
- **Rate Limiting:** Prevent spam submissions and vote manipulation
- **Authentication:** Secure session management
- **Data Privacy:** GDPR-compliant user data handling

#### 10.2 Performance
- **Edge Distribution:** Leverage Turso's global SQLite replicas
- **Caching Strategy:** Cache popular ideas and categories
- **Optimistic Updates:** Immediate UI feedback with Datastar
- **Lazy Loading:** Paginated idea loading for large datasets

### 11. Success Metrics

#### 11.1 Engagement Metrics
- **Daily Active Users (DAU)**
- **Ideas Submitted per Day**
- **Votes Cast per Day**
- **Average Session Duration**
- **User Retention Rate**

#### 11.2 Quality Metrics
- **Average Votes per Idea**
- **Ideas with >10 Votes**
- **User Engagement Rate (votes/views)**
- **Search Success Rate**

### 12. Future Enhancements

#### 12.1 Advanced Features
- **AI-Powered Recommendations:** Suggest similar ideas
- **Collaboration Tools:** Allow users to collaborate on ideas
- **Investor Dashboard:** Special interface for investors
- **Export Functionality:** Export ideas in various formats
- **Integration APIs:** Connect with startup tools and platforms

#### 12.2 Monetization Options
- **Premium Features:** Advanced analytics, priority placement
- **Investor Tools:** Enhanced discovery and contact features
- **API Access:** Paid API for third-party integrations
- **Sponsored Ideas:** Promoted idea placements

### 13. Technical Advantages of Chosen Stack

#### 13.1 Datastar Benefits
- **Minimal Complexity:** No complex JavaScript frameworks to maintain
- **Real-time Capable:** Built-in SSE support for live updates
- **Backend-Driven:** Centralized state management and business logic
- **Performance:** Minimal client-side overhead

#### 13.2 Basecoat.ui Benefits
- **Consistent Design:** Professional UI components out of the box
- **Framework Agnostic:** Works perfectly with Datastar's approach
- **Responsive:** Mobile-first design system
- **Customizable:** Tailwind-based for easy theming

#### 13.3 Turso Benefits
- **Global Distribution:** Low-latency access worldwide
- **SQLite Compatibility:** Familiar SQL interface with cloud benefits
- **Scalability:** Automatic scaling with edge deployment
- **Cost-Effective:** Pay-per-use pricing model

### 14. Development Timeline

#### 14.1 Week 1-2: Foundation
- Python/FastAPI project setup with virtual environment
- Turso database connection and SQLAlchemy models
- Basic authentication system with JWT tokens
- Jinja2 templates setup with Basecoat.ui components
- Core idea submission and display endpoints

#### 14.2 Week 3-4: Core Features
- Voting system implementation with real-time SSE updates
- Search and filtering functionality with SQLite FTS
- User profiles and idea management
- Datastar frontend integration for reactive UI

#### 14.3 Week 5-6: Polish & Launch
- UI/UX refinements with Basecoat.ui theming
- Performance optimization and caching
- FastAPI testing with pytest
- Production deployment setup

### 15. Python/FastAPI Implementation Details

#### 15.1 Project Structure
```
ideasvault/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py      # Turso connection
│   │   ├── idea.py          # Idea SQLAlchemy model
│   │   ├── user.py          # User SQLAlchemy model
│   │   └── vote.py          # Vote SQLAlchemy model
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ideas.py         # Ideas endpoints
│   │   ├── auth.py          # Authentication endpoints
│   │   └── events.py        # SSE endpoints
│   ├── templates/
│   │   ├── base.html        # Base template with Datastar/Basecoat
│   │   ├── index.html       # Homepage
│   │   ├── ideas/
│   │   └── partials/        # HTML fragments for Datastar
│   └── utils/
│       ├── auth.py          # JWT utilities
│       ├── database.py      # Database utilities
│       └── templates.py     # Template helpers
├── static/
│   ├── css/                 # Basecoat.ui styles
│   └── js/                  # Datastar library
├── requirements.txt
├── .env
└── tests/
```

#### 15.2 Key Dependencies
```python
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
jinja2>=3.1.0
python-multipart>=0.0.6
libsql-client>=0.3.0       # Turso client
sqlalchemy>=2.0.0
alembic>=1.12.0            # Database migrations
sse-starlette>=1.6.0       # Server-sent events
pyjwt>=2.8.0               # JWT authentication
passlib[bcrypt]>=1.7.4     # Password hashing
python-jose>=3.3.0
pydantic>=2.4.0
pytest>=7.4.0             # Testing
httpx>=0.25.0              # Testing client
```

#### 15.3 FastAPI + Datastar Integration Pattern
```python
# Example endpoint returning HTML for Datastar
@app.patch("/ideas/{idea_id}/vote")
async def vote_idea(
    idea_id: int, 
    vote_type: int,
    request: Request,
    user: User = Depends(get_current_user)
):
    # Process vote in database
    updated_idea = await process_vote(idea_id, user.id, vote_type)
    
    # Return HTML fragment for Datastar to update
    return templates.TemplateResponse(
        "partials/idea_vote_buttons.html",
        {
            "request": request,
            "idea": updated_idea,
            "user_vote": vote_type
        }
    )
```

#### 15.4 Database Integration (Turso + SQLAlchemy)
```python
# app/models/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Turso connection string
DATABASE_URL = f"sqlite+aiosqlite:///{os.getenv('TURSO_DATABASE_URL')}"

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

---

This PRD leverages the unique strengths of each technology in your stack: Datastar's backend-driven reactivity, Basecoat.ui's polished components, and Turso's distributed SQLite database for a performant, scalable startup ideas directory.