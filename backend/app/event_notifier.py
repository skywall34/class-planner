"""
Event notification system for SSE-based real-time updates
"""

import uuid
import time
from typing import Dict, Any, Optional
from .database import DatabaseManager


class EventNotifier:
    """Handles event notifications for SSE streaming"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    async def notify(self, session_id: str, event_type: str, event_data: Dict[str, Any]):
        """
        Store an event in the database for SSE streaming
        
        Args:
            session_id: Session identifier
            event_type: Type of event (llm_started, llm_completed, etc.)
            event_data: Event payload data
        """
        try:
            event_id = str(uuid.uuid4())
            
            # Add metadata to event data
            enhanced_data = {
                **event_data,
                'timestamp': time.time(),
                'session_id': session_id
            }
            
            # Store in database
            await self.db_manager.add_processing_event(
                event_id, session_id, event_type, enhanced_data
            )
            
            print(f"Event stored: {event_type} for session {session_id[:8]}...")
            
        except Exception as e:
            print(f"Error storing event: {e}")
    
    async def notify_llm_started(self, session_id: str, request_type: str, request_count: int):
        """Notify that an LLM request has started"""
        await self.notify(session_id, "llm_started", {
            "stage": "llm_processing",
            "message": f"Processing {request_type}...",
            "request_type": request_type,
            "request_count": request_count,
            "estimated_duration": "5-15 seconds"
        })
    
    async def notify_llm_completed(self, session_id: str, request_type: str, request_count: int, duration: float, success: bool = True):
        """Notify that an LLM request has completed"""
        await self.notify(session_id, "llm_completed", {
            "stage": "llm_completed",
            "message": f"Completed {request_type} in {duration:.1f}s",
            "request_type": request_type,
            "request_count": request_count,
            "duration": duration,
            "success": success
        })
    
    async def notify_llm_error(self, session_id: str, request_type: str, request_count: int, error_message: str):
        """Notify that an LLM request has failed"""
        await self.notify(session_id, "llm_error", {
            "stage": "llm_error",
            "message": f"Error in {request_type}: {error_message}",
            "request_type": request_type,
            "request_count": request_count,
            "error": error_message
        })
    
    async def notify_agent_started(self, session_id: str, agent_type: str):
        """Notify that an agent has started processing"""
        await self.notify(session_id, "agent_started", {
            "stage": "processing",
            "message": f"Starting {agent_type}...",
            "agent_type": agent_type
        })
    
    async def notify_agent_completed(self, session_id: str, agent_type: str, processing_time: float, next_agent: Optional[str] = None):
        """Notify that an agent has completed processing"""
        message = f"Completed {agent_type} in {processing_time:.1f}s"
        if next_agent:
            message += f", starting {next_agent}..."
            
        await self.notify(session_id, "agent_completed", {
            "stage": "agent_completed",
            "message": message,
            "agent_type": agent_type,
            "processing_time": processing_time,
            "next_agent": next_agent
        })
    
    async def notify_content_saved(self, session_id: str, content_type: str, content_length: int, local_file: Optional[str] = None):
        """Notify that content has been saved"""
        await self.notify(session_id, "content_saved", {
            "stage": "content_saved",
            "message": f"Saved {content_type} ({content_length} characters)",
            "content_type": content_type,
            "content_length": content_length,
            "local_file": local_file
        })
    
    async def notify_processing_complete(self, session_id: str, accuracy_score: float, total_time: float, content_id: str):
        """Notify that all processing is complete"""
        await self.notify(session_id, "processing_complete", {
            "stage": "completed",
            "message": f"Content generation completed! (Accuracy: {accuracy_score}%)",
            "accuracy_score": accuracy_score,
            "total_processing_time": total_time,
            "content_id": content_id
        })
    
    async def notify_upload_complete(self, session_id: str, filename: str, file_size: int):
        """Notify that file upload is complete"""
        await self.notify(session_id, "upload_complete", {
            "stage": "upload_complete",
            "message": f"Uploaded {filename} ({file_size} bytes)",
            "filename": filename,
            "file_size": file_size
        })
    
    async def notify_error(self, session_id: str, error_message: str, error_stage: str = "processing"):
        """Notify about an error"""
        await self.notify(session_id, "error", {
            "stage": "error",
            "message": f"Error: {error_message}",
            "error": error_message,
            "error_stage": error_stage
        })
    
    async def notify_heartbeat(self, session_id: str, message: str):
        """Send a heartbeat message (for debugging/monitoring)"""
        await self.notify(session_id, "heartbeat", {
            "stage": "heartbeat",
            "message": message
        })


# Global instance
event_notifier = EventNotifier()