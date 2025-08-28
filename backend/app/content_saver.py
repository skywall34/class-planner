"""
Local Content Saving Module
Saves generated content locally for debugging and logging purposes
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import hashlib


class LocalContentSaver:
    """Handles local saving of generated content"""
    
    def __init__(self):
        self.enabled = os.getenv("SAVE_CONTENT_LOCALLY", "False").lower() == "true"
        self.base_path = Path(os.getenv("LOCAL_CONTENT_PATH", "./data/generated_content"))
        self.save_format = os.getenv("SAVE_FORMAT", "both").lower()
        self.include_metadata = os.getenv("INCLUDE_METADATA", "True").lower() == "true"
        
        # Create directory if it doesn't exist
        if self.enabled:
            self.base_path.mkdir(parents=True, exist_ok=True)
            print(f"Local content saving enabled: {self.base_path}")
    
    def save_content(self, session_id: str, content: str, user_prompt: str = "", 
                    content_type: str = "ebook", metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Save generated content locally
        
        Args:
            session_id: Session identifier
            content: The generated content
            user_prompt: User's original prompt
            content_type: Type of content (ebook, summary, etc.)
            metadata: Additional metadata to save
            
        Returns:
            Path to saved file or None if saving disabled
        """
        if not self.enabled:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create filename with timestamp and session
            base_filename = f"{timestamp}_{session_id[:8]}_{content_type}"
            
            # Create session directory
            session_dir = self.base_path / session_id[:8]
            session_dir.mkdir(exist_ok=True)
            
            saved_files = []
            
            # Save markdown format
            if self.save_format in ["markdown", "both"]:
                md_file = session_dir / f"{base_filename}.md"
                
                # Add metadata header to markdown
                md_content = content
                if self.include_metadata and user_prompt:
                    md_content = f"""<!-- 
Generated on: {datetime.now().isoformat()}
Session ID: {session_id}
User Prompt: {user_prompt}
Content Type: {content_type}
-->

{content}"""
                
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                saved_files.append(str(md_file))
                print(f"Content saved to: {md_file}")
            
            # Save JSON format with metadata
            if self.save_format in ["json", "both"]:
                json_file = session_dir / f"{base_filename}.json"
                
                json_data = {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "content_type": content_type,
                    "user_prompt": user_prompt,
                    "content": content,
                    "content_hash": hashlib.md5(content.encode()).hexdigest(),
                    "content_length": len(content),
                    "metadata": metadata or {}
                }
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                saved_files.append(str(json_file))
                print(f"Metadata saved to: {json_file}")
            
            return saved_files[0] if saved_files else None
            
        except Exception as e:
            print(f"Error saving content locally: {e}")
            return None
    
    def save_agent_log(self, session_id: str, agent_type: str, input_data: str, 
                      output_data: str, processing_time: float) -> Optional[str]:
        """
        Save agent processing logs locally
        
        Args:
            session_id: Session identifier
            agent_type: Type of agent (summarizer, generator, etc.)
            input_data: Input data for the agent
            output_data: Output data from the agent
            processing_time: Time taken for processing
            
        Returns:
            Path to saved log file or None if saving disabled
        """
        if not self.enabled:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            
            # Create logs directory
            logs_dir = self.base_path / session_id[:8] / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = logs_dir / f"{timestamp}_{agent_type}.json"
            
            log_data = {
                "session_id": session_id,
                "agent_type": agent_type,
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": processing_time,
                "input_data": input_data,
                "output_data": output_data,
                "input_length": len(input_data),
                "output_length": len(output_data)
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            print(f"Agent log saved: {log_file}")
            return str(log_file)
            
        except Exception as e:
            print(f"Error saving agent log: {e}")
            return None
    
    def list_saved_content(self, session_id: Optional[str] = None) -> list:
        """
        List all saved content files
        
        Args:
            session_id: Optional session ID to filter by
            
        Returns:
            List of saved content file paths
        """
        if not self.enabled or not self.base_path.exists():
            return []
        
        files = []
        search_path = self.base_path / session_id[:8] if session_id else self.base_path
        
        for file_path in search_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.md', '.json']:
                files.append(str(file_path))
        
        return sorted(files, reverse=True)  # Most recent first
    
    def get_content_summary(self) -> Dict[str, Any]:
        """Get summary of all saved content"""
        if not self.enabled or not self.base_path.exists():
            return {"enabled": False}
        
        summary = {
            "enabled": True,
            "base_path": str(self.base_path),
            "total_sessions": len([d for d in self.base_path.iterdir() if d.is_dir()]),
            "total_files": len(list(self.base_path.rglob("*.md"))) + len(list(self.base_path.rglob("*.json"))),
            "disk_usage_mb": sum(f.stat().st_size for f in self.base_path.rglob("*") if f.is_file()) / 1024 / 1024
        }
        
        return summary


# Global instance
content_saver = LocalContentSaver()