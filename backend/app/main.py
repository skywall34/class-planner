from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import os
import json
import time
from typing import Optional, List
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="../.env")

from .database import create_database, DatabaseManager
from .agents import ContentPipeline
from .models import SessionCreate, RevisionRequest, EnhancementRequest
from .security import validate_user_prompt
from .content_saver import content_saver
from .event_notifier import event_notifier

app = FastAPI(title="GeneAcademy", description="Educational Content Generation Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the path to frontend static files
import pathlib
frontend_static_path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(frontend_static_path)), name="static")

db_manager = DatabaseManager()
pipeline = ContentPipeline()


@app.on_event("startup")
async def startup_event():
    create_database()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    template_path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "templates" / "index.html"
    with open(template_path, "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/session/create")
async def create_session(request: SessionCreate):
    session_id = str(uuid.uuid4())
    await db_manager.create_session(session_id, request.user_ip or "unknown")
    return {"session_id": session_id}

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    status = await db_manager.get_session_status(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "status": status}

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    user_prompt: str = Form(""),
    enhance: bool = Form(False)
):
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Validate user prompt
    validate_user_prompt(user_prompt)
    
    # Validate file type and size
    allowed_types = ['.txt', '.pdf', '.docx', '.md']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    if file.size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large")
    
    # Read file content
    content = await file.read()
    
    # Extract text based on file type
    if file_ext == '.txt' or file_ext == '.md':
        text_content = content.decode('utf-8')
    elif file_ext == '.pdf':
        # PDF processing would go here
        text_content = "PDF processing not implemented yet"
    elif file_ext == '.docx':
        # DOCX processing would go here
        text_content = "DOCX processing not implemented yet"
    
    # Save document
    doc_id = str(uuid.uuid4())
    await db_manager.save_document(doc_id, session_id, text_content, file.filename, file_ext)
    
    # Update session status
    await db_manager.update_session_status(session_id, "processing")
    
    # Notify upload complete
    await event_notifier.notify_upload_complete(session_id, file.filename, file.size)
    
    # Process document asynchronously
    asyncio.create_task(process_document_async(session_id, doc_id, text_content, user_prompt, enhance))
    
    return {"message": "Document uploaded successfully", "document_id": doc_id}

async def process_document_async(session_id: str, doc_id: str, text: str, user_prompt: str, enhance: bool):
    try:
        result = await pipeline.process_document(text, user_prompt, enhance, session_id)
        
        # Save generated content
        content_id = str(uuid.uuid4())
        await db_manager.save_generated_content(
            content_id, doc_id, "ebook", user_prompt, 
            result['content'], result['accuracy_score']
        )
        
        await db_manager.update_session_status(session_id, "completed")
        
    except Exception as e:
        await db_manager.update_session_status(session_id, "error")
        await event_notifier.notify_error(session_id, str(e))

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    status = await db_manager.get_session_status(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "status": status}

@app.get("/api/content/{session_id}")
async def get_content(session_id: str):
    content = await db_manager.get_generated_content(session_id)
    if not content:
        raise HTTPException(status_code=404, detail="No content found for session")
    return content

@app.post("/api/revise/{content_id}")
async def revise_content(content_id: str, request: RevisionRequest):
    # Revision logic would go here
    return {"message": "Revision requested", "content_id": content_id}

@app.post("/api/enhance/{content_id}")
async def enhance_content(content_id: str, request: EnhancementRequest):
    # Enhancement logic would go here
    return {"message": "Enhancement requested", "content_id": content_id}

@app.get("/api/download/{content_id}")
async def download_content(content_id: str, format: str = "markdown"):
    # Download logic would go here
    return {"message": f"Download {format} requested", "content_id": content_id}

@app.get("/api/content-saver/status")
async def get_content_saver_status():
    """Get the status of local content saving"""
    return content_saver.get_content_summary()

@app.get("/api/content-saver/files/{session_id}")
async def get_saved_files(session_id: str):
    """Get list of saved files for a session"""
    return {
        "session_id": session_id,
        "files": content_saver.list_saved_content(session_id)
    }

@app.get("/api/events/{session_id}")
async def stream_events(session_id: str):
    """SSE endpoint for streaming processing events"""
    
    async def event_generator():
        """Generate SSE events from database"""
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'event_type': 'connected', 'event_data': {'message': 'SSE connected', 'session_id': session_id}})}\n\n"
            
            last_check = 0
            while True:
                try:
                    # Get unacknowledged events from database
                    events = await db_manager.get_unacknowledged_events(session_id)
                    
                    for event in events:
                        # Format as SSE event
                        sse_data = {
                            'id': event['id'],
                            'event_type': event['event_type'],
                            'event_data': event['event_data'],
                            'created_at': event['created_at']
                        }
                        
                        yield f"data: {json.dumps(sse_data)}\n\n"
                        print(f"SSE sent: {event['event_type']} to {session_id[:8]}")
                    
                    # Clean up old events periodically
                    current_time = time.time()
                    if current_time - last_check > 300:  # Every 5 minutes
                        await db_manager.cleanup_old_events(1)  # Clean up events older than 1 hour
                        last_check = current_time
                    
                    # Wait before checking again
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"SSE error: {e}")
                    yield f"data: {json.dumps({'event_type': 'error', 'event_data': {'message': f'Stream error: {str(e)}'}})}\n\n"
                    break
                    
        except asyncio.CancelledError:
            print(f"SSE connection cancelled for session {session_id[:8]}")
        except Exception as e:
            print(f"SSE generator error: {e}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/api/events/{event_id}/acknowledge")
async def acknowledge_event(event_id: str):
    """Mark an event as acknowledged"""
    try:
        await db_manager.acknowledge_event(event_id)
        return {"status": "acknowledged", "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge event: {str(e)}")

@app.get("/api/events/{session_id}/poll")
async def poll_events(session_id: str):
    """Polling endpoint as fallback if SSE doesn't work"""
    try:
        events = await db_manager.get_unacknowledged_events(session_id)
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get events: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)