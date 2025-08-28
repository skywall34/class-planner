import os
import hashlib
import secrets
from typing import Optional
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.max_requests = 10  # Max requests per minute
        self.time_window = 60   # 60 seconds
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if now - req_time < self.time_window
        ]
        
        # Check if under limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True

class SecurityManager:
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.blocked_ips = set()
        
    def validate_file_type(self, filename: str) -> bool:
        """Validate file type based on extension."""
        allowed_extensions = {'.txt', '.pdf', '.docx', '.md'}
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in allowed_extensions
    
    def validate_file_size(self, file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """Validate file size (default 10MB)."""
        return file_size <= max_size
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks."""
        # Remove path separators and dangerous characters
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        sanitized = filename
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Limit length
        if len(sanitized) > 100:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[:95] + ext
            
        return sanitized
    
    def sanitize_text_content(self, text: str) -> str:
        """Sanitize text content to remove potentially malicious content."""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit text length to prevent memory exhaustion
        max_length = 1000000  # 1MB of text
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def check_rate_limit(self, request: Request) -> bool:
        """Check if request is within rate limits."""
        client_ip = self.get_client_ip(request)
        
        if client_ip in self.blocked_ips:
            return False
            
        return self.rate_limiter.is_allowed(client_ip)
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded IP first
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else 'unknown'
    
    def validate_session_id(self, session_id: str) -> bool:
        """Validate session ID format."""
        if not session_id:
            return False
        
        # Check length and format (UUID-like)
        if len(session_id) != 36:
            return False
        
        # Check for valid UUID format
        try:
            parts = session_id.split('-')
            if len(parts) != 5:
                return False
            if len(parts[0]) != 8 or len(parts[1]) != 4 or len(parts[2]) != 4 or len(parts[3]) != 4 or len(parts[4]) != 12:
                return False
            # Try to parse as hex
            for part in parts:
                int(part, 16)
        except ValueError:
            return False
        
        return True
    
    def validate_user_prompt(self, user_prompt: str) -> bool:
        """Validate user prompt parameter."""
        # Allow empty prompts (will use default)
        if not user_prompt:
            return True
        
        # Limit prompt length to prevent abuse
        max_length = 1000  # 1000 characters should be enough for instructions
        if len(user_prompt) > max_length:
            return False
            
        # Check for potentially malicious content (basic check)
        dangerous_patterns = ['<script', 'javascript:', 'data:text/html', 'vbscript:']
        user_prompt_lower = user_prompt.lower()
        for pattern in dangerous_patterns:
            if pattern in user_prompt_lower:
                return False
                
        return True
    
    def hash_content(self, content: str) -> str:
        """Create hash of content for integrity checking."""
        return hashlib.sha256(content.encode()).hexdigest()

# Global security manager instance
security_manager = SecurityManager()

def check_rate_limit_middleware(request: Request):
    """Middleware to check rate limits."""
    if not security_manager.check_rate_limit(request):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )

def validate_upload_file(filename: str, file_size: int):
    """Validate uploaded file."""
    if not security_manager.validate_file_type(filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only TXT, PDF, DOCX, and MD files are allowed."
        )
    
    if not security_manager.validate_file_size(file_size):
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB."
        )

def validate_session_id(session_id: str):
    """Validate session ID."""
    if not security_manager.validate_session_id(session_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID format."
        )

def validate_user_prompt(user_prompt: str):
    """Validate user prompt parameter."""
    if not security_manager.validate_user_prompt(user_prompt):
        raise HTTPException(
            status_code=400,
            detail="Invalid user prompt. Please ensure it's under 1000 characters and doesn't contain malicious content."
        )