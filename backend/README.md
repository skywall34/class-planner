# GeneAcademy Backend Server

A FastAPI-based educational content generation platform that transforms research papers and documents into comprehensive educational content using specialized AI agents.

## Architecture Overview

The backend is built using a modern Python stack with FastAPI as the core framework, providing REST API endpoints and Server-Sent Events for real-time communication.

### Technology Stack

- **FastAPI** - High-performance web framework with automatic OpenAPI documentation
- **Python 3.11+** - Modern Python with type hints and async/await support
- **uv** - Fast Python package manager and dependency resolver
- **SQLite** - Lightweight database for session and content management
- **Server-Sent Events** - Real-time progress updates during document processing
- **OpenAI API** - GPT-3.5-turbo for AI-powered content generation
- **Pydantic** - Data validation and serialization with type safety

## Project Structure

```
backend/
 app/
    __init__.py         # Package initialization
    main.py             # FastAPI application, routes, and SSE handlers
    agents.py           # AI agent implementations with rate limiting
    database.py         # SQLite database operations and schema
    models.py           # Pydantic data models for validation
    security.py         # Security middleware and validation
 data/                   # SQLite database storage
 uploads/                # Temporary file storage
 pyproject.toml          # Project dependencies and configuration
 uv.lock                 # Dependency lockfile
 README.md              # This file
```

## Core Components

### 1. AI Agent Pipeline (`agents.py`)

The system uses five specialized AI agents that process documents sequentially:

#### LLMClient

- **Rate Limiting**: 20 requests/minute with 1-second minimum intervals
- **Request Tracking**: Automatic logging and timing of all API calls
- **Error Handling**: Graceful degradation with detailed error messages
- **Token Management**: Configurable max tokens per request (2000-3000)

#### Agent Types

1. **SummarizationAgent** - Extracts key concepts and creates structured summaries
2. **ContentGenerationAgent** - Transforms summaries into comprehensive ebooks
3. **AccuracyReviewAgent** - Validates content accuracy (0-100 score)
4. **ResearchEnhancementAgent** - Adds supplementary material (optional)
5. **RevisionAgent** - Handles user feedback and content revisions

#### Processing Pipeline

```
Document � Summarize � Generate � Review � [Auto-Revise if <85% accuracy] � [Enhance if requested]
```

Each step makes exactly **one API request** to prevent rate limit violations.

### 2. Database Layer (`database.py`)

SQLite database with the following schema:

#### Tables

- **sessions** - User sessions with processing status tracking
- **documents** - Uploaded file metadata and content
- **generated_content** - AI-generated educational content with versioning
- **agent_logs** - Processing logs and performance metrics
- **revision_history** - Content revision tracking for user feedback

#### Features

- **Async Operations** - Non-blocking database operations with aiosqlite
- **Session Management** - UUID-based session tracking
- **Content Versioning** - Track content changes and revisions
- **Performance Logging** - Agent execution times and success rates

### 3. API Endpoints (`main.py`)

#### REST API

- `POST /api/session/create` - Create new processing session
- `POST /api/upload` - Upload document for processing (TXT, PDF, DOCX, MD)
- `GET /api/status/{session_id}` - Check processing status
- `GET /api/content/{session_id}` - Retrieve generated content
- `POST /api/revise` - Request content revisions
- `POST /api/enhance` - Request content enhancement

#### Server-Sent Events

- `GET /api/events/{session_id}` - Real-time progress updates during processing via SSE

#### Static File Serving

- Frontend templates and assets served from `../frontend/`
- Automatic path resolution for cross-platform compatibility

### 4. Data Models (`models.py`)

Pydantic models ensure type safety and data validation:

```python
class SessionCreate(BaseModel):
    user_prompt: str = ""
    enhance: bool = False

class RevisionRequest(BaseModel):
    session_id: str
    feedback: str

class EnhancementRequest(BaseModel):
    session_id: str
    enhancement_type: str
```

### 5. Security (`security.py`)

- **Rate Limiting** - IP-based request limiting (10 requests/minute default)
- **File Validation** - Type checking and size limits (10MB max)
- **CORS Support** - Configurable cross-origin resource sharing
- **Input Sanitization** - All user inputs validated through Pydantic models

## Environment Configuration

Required environment variables in `.env` file:

```bash
# OpenAI API Configuration (Required)
OPENAI_API_KEY=your-openai-api-key-here

# Database Configuration (Optional)
DATABASE_URL=sqlite:///./data/geneacademy.db

# Security Configuration (Optional)
MAX_FILE_SIZE=10485760          # 10MB in bytes
RATE_LIMIT_REQUESTS=10          # Requests per minute per IP
RATE_LIMIT_WINDOW=60           # Time window in seconds

# Application Configuration (Optional)
DEBUG=False
CORS_ORIGINS=*
```

## Installation and Setup

### Prerequisites

- Python 3.11 or higher
- uv package manager
- OpenAI API key

### Installation

```bash
cd backend

# Install dependencies
uv sync

# Install development dependencies
uv sync --dev
```

### Running the Server

```bash
# Development server with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The server will be available at `http://localhost:8000`

### API Documentation

- **Interactive Docs**: `http://localhost:8000/docs`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## File Processing Workflow

1. **Upload Validation**

   - File type checking (TXT, PDF, DOCX, MD)
   - Size validation (max 10MB)
   - Content extraction based on file type

2. **AI Processing Pipeline**

   - Sequential processing through specialized agents
   - Real-time progress updates via Server-Sent Events
   - Automatic quality checks and revisions
   - Optional content enhancement

3. **Content Storage**

   - Database storage with session tracking
   - Version control for revisions
   - Performance metrics logging

4. **Content Delivery**
   - REST API endpoints for content retrieval
   - Markdown-formatted educational content
   - Download functionality for generated ebooks

## Performance Characteristics

- **Rate Limited**: Maximum 20 OpenAI API calls per minute
- **Concurrent Sessions**: Multiple users can process documents simultaneously
- **Processing Time**: Typically 30-90 seconds per document depending on size
- **Memory Usage**: Minimal with streaming file processing
- **Database**: SQLite provides adequate performance for small to medium loads

## Development Commands

```bash
# Run tests (when available)
uv run pytest

# Code formatting
uv run black .

# Type checking
uv run mypy .

# Dependency updates
uv sync --upgrade

# Database inspection
sqlite3 data/geneacademy.db ".tables"
```

## Error Handling and Monitoring

- **Graceful Degradation**: API failures don't crash the system
- **Detailed Logging**: Console logs for all LLM interactions
- **Request Tracking**: Numbered requests with timing information
- **Error Responses**: Structured HTTP error responses with details
- **SSE Recovery**: Automatic reconnection handling with event acknowledgment

## Scaling Considerations

- **Database**: SQLite suitable for development; consider PostgreSQL for production
- **File Storage**: Local uploads directory; consider cloud storage for production
- **API Rate Limits**: Currently conservative; can be adjusted based on OpenAI plan
- **Caching**: Consider Redis for session caching in production
- **Load Balancing**: FastAPI supports multiple workers for horizontal scaling

## Security Best Practices

- **API Keys**: Never commit API keys to version control
- **Input Validation**: All user inputs validated through Pydantic models
- **File Uploads**: Restricted file types and size limits
- **Rate Limiting**: Prevents API abuse and quota exhaustion
- **CORS**: Configurable origin restrictions for production deployment
