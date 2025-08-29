# GeneAcademy Educational Content Generation Platform

A comprehensive platform that transforms research papers and documents into structured educational content using specialized AI agents. Built with modern Python and web technologies, featuring cost-optimized mixed LLM usage, real-time SSE updates, and privacy-focused design for optimal performance and developer experience.

## Features

- **Document Upload**: Support for TXT, PDF, DOCX, and Markdown files
- **AI-Powered Processing**: Multi-agent pipeline for intelligent content generation
- **Real-time Progress**: Server-Sent Events (SSE) based progress tracking with live updates
- **Content Editing**: Built-in markdown editor with live preview
- **Multiple Durations**: Support for week, multi-week, and semester courses
- **Content Enhancement**: Optional research enhancement and cross-referencing
- **Revision System**: Request revisions based on user feedback
- **Download Options**: Export generated content as markdown files
- **Modern UI**: Beautiful, responsive interface built with Tailwind CSS

## Architecture

The platform consists of two main components:

### Backend (Python)

- **FastAPI**: High-performance REST API with automatic OpenAPI documentation
- **SQLite**: Lightweight database for session and content management
- **AI Agents**: Specialized LLM agents for different processing tasks
- **Server-Sent Events**: Real-time communication for progress updates
- **Security**: Rate limiting, input validation, and file type restrictions

### Frontend (Web)

- **Modern HTML5/CSS3/JavaScript**: Clean, responsive web interface
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Vite**: Fast build tool and development server
- **EventSource Client**: Real-time communication with backend via SSE
- **Markdown Rendering**: Live preview with syntax highlighting

## Project Structure

```
class-planner/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application and routes
│   │   ├── database.py      # Database models and operations
│   │   ├── agents.py        # AI agent implementations
│   │   ├── models.py        # Pydantic data models
│   │   └── security.py      # Security utilities and middleware
│   ├── pyproject.toml       # Python dependencies and project config
│   └── .python-version      # Python version specification
├── frontend/
│   ├── src/
│   │   └── input.css        # Tailwind CSS input file
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css    # Generated Tailwind CSS
│   │   └── js/
│   │       └── app.js       # Frontend JavaScript application
│   ├── templates/
│   │   └── index.html       # Main HTML template
│   ├── package.json         # Node.js dependencies
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   ├── postcss.config.js    # PostCSS configuration
│   └── vite.config.js       # Vite configuration
├── .env.example             # Environment variables template
└── README.md               # This file
```

## Prerequisites

Before running the project, ensure you have the following installed:

- **Python 3.11+**: The backend requires Python 3.11 or higher
- **uv**: Fast Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Node.js 18+**: For frontend build tools and dependencies
- **npm/yarn**: Package manager for Node.js dependencies

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd class-planner
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies using uv
uv sync

# Install development dependencies (optional)
uv sync --dev

# Set up environment variables
cp ../.env.example ../.env
# Edit .env and add your OpenAI API key
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install Node.js dependencies
npm install

# Build Tailwind CSS
npm run build-css
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
# Required: OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Database Configuration
DATABASE_URL=sqlite:///./data/geneacademy.db

# Optional: Security Configuration
MAX_FILE_SIZE=10485760  # 10MB in bytes
RATE_LIMIT_REQUESTS=10  # Requests per minute per IP
RATE_LIMIT_WINDOW=60    # Time window in seconds

# Optional: Application Configuration
DEBUG=False
CORS_ORIGINS=*
```

## Running the Application

### Development Mode

#### Start Backend Server

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Start Frontend Development Server

```bash
cd frontend
npm run dev
```

#### Build Tailwind CSS (in watch mode)

```bash
cd frontend
npm run build-css
```

### Production Mode

#### Backend

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
npm run build
npm run preview
```

### Access the Application

- **Frontend**: http://localhost:3000 (development) or http://localhost:4173 (preview)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)

## AI Agent Pipeline

The platform uses a sophisticated multi-agent system to process documents:

### 1. Summarization Agent (GPT-3.5-turbo)

- **Purpose**: Extract key concepts and create structured summaries
- **Output**: Learning objectives, key concepts, chapter outlines
- **Focus**: Preserves technical accuracy while organizing content
- **Optimization**: Uses cost-effective GPT-3.5-turbo for analysis tasks

### 2. Content Generation Agent (Mixed Models)

- **Purpose**: Transform summaries into comprehensive ebooks
- **Output**: Full educational content with examples and exercises
- **Focus**: Engaging, structured learning materials
- **Optimization**: Uses GPT-3.5-turbo for analysis, GPT-4.1 for content generation

### 3. Accuracy Review Agent (GPT-3.5-turbo)

- **Purpose**: Validate generated content against source material
- **Output**: Accuracy score (0-100) and correction suggestions
- **Focus**: Ensures factual correctness and completeness
- **Optimization**: Uses cost-effective GPT-3.5-turbo for review tasks

### 4. Research Enhancement Agent (Optional, GPT-3.5-turbo)

- **Purpose**: Add supplementary material and context
- **Output**: Enhanced content with case studies and applications
- **Focus**: Real-world relevance and deeper understanding
- **Optimization**: Uses cost-effective GPT-3.5-turbo for enhancement tasks

### 5. Revision Agent (GPT-3.5-turbo)

- **Purpose**: Handle user feedback and revision requests
- **Output**: Updated content based on user specifications
- **Focus**: Maintains consistency while applying changes
- **Optimization**: Uses cost-effective GPT-3.5-turbo for revision tasks

## API Endpoints

### Session Management

- `POST /api/session/create` - Create new processing session
- `GET /api/session/{session_id}` - Get session details and status

### Document Processing

- `POST /api/upload` - Upload document for processing
- `GET /api/status/{session_id}` - Check processing status
- `GET /api/content/{session_id}` - Retrieve generated content

### Content Management

- `POST /api/revise/{content_id}` - Request content revision
- `POST /api/enhance/{content_id}` - Add research enhancement
- `GET /api/download/{content_id}` - Download content (future feature)

### Real-time Communication

- `GET /api/events/{session_id}` - Server-Sent Events stream for progress updates
- `POST /api/events/{event_id}/acknowledge` - Acknowledge received event

## Database Schema

The platform uses SQLite with the following structure:

### Tables

- **sessions**: User sessions and processing status (UUID-based, no IP collection)
- **documents**: Uploaded documents and metadata
- **generated_content**: AI-generated educational content with user prompts
- **agent_logs**: Processing logs and performance metrics
- **processing_events**: SSE events for real-time updates with auto-acknowledgment
- **revision_history**: Content revision tracking

## Security Features

- **File Validation**: Restricts file types (TXT, PDF, DOCX, MD) and sizes (max 10MB)
- **Input Sanitization**: Cleans and validates all user inputs
- **Session Management**: Secure UUID-based session handling (no IP collection)
- **Privacy-Focused**: Minimal data collection, no unnecessary user tracking
- **Content Integrity**: Secure event streaming with auto-acknowledgment

## Frontend Development

### Tailwind CSS Workflow

The project uses Tailwind CSS for styling with the following workflow:

1. **Edit Styles**: Modify `frontend/src/input.css`
2. **Build CSS**: Run `npm run build-css` to generate output
3. **Development**: Use watch mode for automatic rebuilds

### Custom Components

The project includes custom Tailwind components:

- `.btn-primary` / `.btn-secondary` - Button styles
- `.card` - Card container component
- `.input-field` - Form input styling
- `.upload-area` - File upload zone
- `.progress-bar` / `.progress-fill` - Progress indicators

### Vite Configuration

Vite is configured for:

- Development server with API proxy
- Hot module replacement
- API proxy for backend communication
- Production builds with optimization

## Development Tools

### Backend Tools (included with --dev)

- **pytest**: Testing framework
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Frontend Tools

- **Vite**: Build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **PostCSS**: CSS processing
- **Autoprefixer**: CSS vendor prefixes

## Usage Guide

1. **Upload Document**: Select a research paper or document (TXT, PDF, DOCX, MD)
2. **Configure Options**:
   - Choose learning duration (week, multi-week, semester)
   - Optionally enable research enhancement
3. **Process Content**: AI agents will process through multiple stages
4. **Review Results**: View generated content with accuracy scoring
5. **Edit & Refine**: Use built-in editor or request revisions
6. **Download**: Export content as markdown files

## Troubleshooting

### Common Issues

1. **Backend won't start**

   - Check Python version: `python --version` (should be 3.11+)
   - Verify uv installation: `uv --version`
   - Check environment variables in `.env`

2. **Frontend build errors**

   - Update Node.js: `node --version` (should be 18+)
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Rebuild Tailwind: `npm run build-css`

3. **File upload fails**

   - Check file type (TXT, PDF, DOCX, MD only)
   - Verify file size (max 10MB)
   - Check backend logs for errors

4. **SSE connection fails**
   - Ensure backend is running on port 8000
   - Check firewall settings
   - Verify API proxy configuration in Vite
   - Check browser console for EventSource errors

5. **Messages arrive in batches**
   - This should be fixed with auto-acknowledgment
   - Check that SSE polling is at 0.5s intervals
   - Verify no proxy is buffering the SSE stream

### Logs and Debugging

- **Backend logs**: Available in terminal where uvicorn is running
- **Database**: SQLite file at `backend/data/geneacademy.db`
- **Agent logs**: Stored in database `agent_logs` table
- **Frontend logs**: Available in browser developer console

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Development Setup

```bash
# Backend development
cd backend
uv sync --dev
uv run pytest  # Run tests
uv run black .  # Format code
uv run mypy .  # Type checking

# Frontend development
cd frontend
npm install
npm run dev  # Start development server
npm run build-css  # Build Tailwind CSS
```

## Support

For questions, issues, or contributions:

1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Join our community discussions

## Future Features

- PDF generation for downloads
- Multi-language support  
- Advanced revision workflows
- User authentication and accounts
- Content templates and presets
- Integration with learning management systems
- Advanced analytics and reporting
- Rate limiting implementation for production
- Batch processing for multiple documents
- Export to various formats (EPUB, Word, etc.)

---

Built by the GeneAcademy Team

## Architecture Evolution

This platform has evolved from a WebSocket-based system to a more efficient and cost-effective architecture:

- **v1.0**: Initial implementation with WebSocket communication and GPT-4 for all tasks
- **v2.0**: Current implementation with SSE communication and mixed model usage
  - 60-70% cost reduction through strategic model selection
  - Improved reliability with SSE auto-acknowledgment
  - Enhanced privacy with no IP collection
  - Direct AI output without unnecessary preamble
  - Real-time updates with 0.5s polling intervals

## Recent Updates

- ✅ **SSE Implementation**: Replaced WebSocket with Server-Sent Events for better reliability
- ✅ **Cost Optimization**: Mixed model usage (GPT-3.5-turbo + GPT-4.1) reduces costs by ~60-70%
- ✅ **Privacy Improvements**: Removed IP collection, UUID-only session management
- ✅ **Real-time Updates**: Auto-acknowledgment prevents message batching issues
- ✅ **Direct Output**: Optimized prompts eliminate unnecessary preamble from AI responses
