from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SessionCreate(BaseModel):
    pass

class DocumentUpload(BaseModel):
    session_id: str
    user_prompt: str = ""
    enhance: bool = False

class RevisionRequest(BaseModel):
    feedback: str
    revision_type: Optional[str] = "general"

class EnhancementRequest(BaseModel):
    enhancement_type: str = "research"
    specific_topics: Optional[List[str]] = None

class SessionResponse(BaseModel):
    session_id: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ContentResponse(BaseModel):
    content: str
    accuracy_score: Optional[float] = None
    content_type: str
    user_prompt: str

class ProgressUpdate(BaseModel):
    stage: str
    message: str
    progress_percent: Optional[int] = None
    accuracy_score: Optional[float] = None