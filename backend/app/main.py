from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import os
import json
from typing import Optional, List
import asyncio
from datetime import datetime

from database import create_database, DatabaseManager
from agents import ContentPipeline
from models import SessionCreate, RevisionRequest, EnhancementRequest

app = FastAPI(title="GeneAcademy", description="Educational Content Generation Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

db_manager = DatabaseManager()
pipeline = ContentPipeline()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_connections: dict = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.session_connections[session_id] = websocket

    def disconnect(self, websocket: WebSocket, session_id: str):
        self.active_connections.remove(websocket)
        if session_id in self.session_connections:
            del self.session_connections[session_id]

    async def send_progress(self, session_id: str, message: dict):
        if session_id in self.session_connections:
            websocket = self.session_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    create_database()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("../frontend/templates/index.html", "r") as f:
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
    session_id: str = None,
    duration: str = "week",
    enhance: bool = False
):
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
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
    
    # Send progress update
    await manager.send_progress(session_id, {
        "stage": "upload_complete",
        "message": "Document uploaded successfully"
    })
    
    # Process document asynchronously
    asyncio.create_task(process_document_async(session_id, doc_id, text_content, duration, enhance))
    
    return {"message": "Document uploaded successfully", "document_id": doc_id}

async def process_document_async(session_id: str, doc_id: str, text: str, duration: str, enhance: bool):
    try:
        await manager.send_progress(session_id, {
            "stage": "processing",
            "message": "Starting content generation..."
        })
        
        result = await pipeline.process_document(text, duration, enhance)
        
        # Save generated content
        content_id = str(uuid.uuid4())
        await db_manager.save_generated_content(
            content_id, doc_id, "ebook", duration, 
            result['content'], result['accuracy_score']
        )
        
        await db_manager.update_session_status(session_id, "completed")
        
        await manager.send_progress(session_id, {
            "stage": "completed",
            "message": "Content generation completed",
            "accuracy_score": result['accuracy_score']
        })
        
    except Exception as e:
        await db_manager.update_session_status(session_id, "error")
        await manager.send_progress(session_id, {
            "stage": "error",
            "message": f"Error processing document: {str(e)}"
        })

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

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle any WebSocket messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)