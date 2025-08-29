class GeneAcademy {
    constructor() {
        this.sessionId = null;
        this.currentContent = '';
        this.isEditing = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupNavigation();
        this.createSession();
    }

    initializeElements() {
        // Form elements
        this.uploadForm = document.getElementById('upload-form');
        this.fileInput = document.getElementById('file-input');
        this.fileName = document.getElementById('file-name');
        this.uploadBtn = document.getElementById('upload-btn');
        
        // Sections
        this.uploadSection = document.getElementById('upload-section');
        this.progressSection = document.getElementById('progress-section');
        this.resultsSection = document.getElementById('results-section');
        
        // Progress elements
        this.progressFill = document.getElementById('progress-fill');
        this.progressStatus = document.getElementById('progress-status');
        this.progressDetails = document.getElementById('progress-details');
        
        // Results elements
        this.accuracyScore = document.getElementById('accuracy-score');
        this.contentPreview = document.getElementById('content-preview');
        this.contentEditor = document.getElementById('content-editor');
        this.contentTextarea = document.getElementById('content-textarea');
        
        // Action buttons
        this.editBtn = document.getElementById('edit-btn');
        this.downloadBtn = document.getElementById('download-btn');
        this.saveEditBtn = document.getElementById('save-edit-btn');
        this.cancelEditBtn = document.getElementById('cancel-edit-btn');
        this.revisionBtn = document.getElementById('revision-btn');
        
        // Revision elements
        this.revisionFeedback = document.getElementById('revision-feedback');
    }

    setupEventListeners() {
        // File input
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop
        const uploadArea = document.querySelector('.upload-area');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
            uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            uploadArea.addEventListener('drop', (e) => this.handleDrop(e));
        }
        
        // Form submission
        if (this.uploadForm) {
            this.uploadForm.addEventListener('submit', (e) => this.handleUpload(e));
        }
        
        // Action buttons
        if (this.editBtn) this.editBtn.addEventListener('click', () => this.toggleEdit(true));
        if (this.saveEditBtn) this.saveEditBtn.addEventListener('click', () => this.saveEdit());
        if (this.cancelEditBtn) this.cancelEditBtn.addEventListener('click', () => this.toggleEdit(false));
        if (this.downloadBtn) this.downloadBtn.addEventListener('click', () => this.downloadContent());
        if (this.revisionBtn) this.revisionBtn.addEventListener('click', () => this.requestRevision());

        // Hero buttons
        const getStartedBtn = document.getElementById('get-started-btn');
        const learnMoreBtn = document.getElementById('learn-more-btn');
        
        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', () => this.scrollToSection('#upload-section'));
        }
        
        if (learnMoreBtn) {
            learnMoreBtn.addEventListener('click', () => this.scrollToSection('#about'));
        }
    }

    async createSession() {
        try {
            const response = await fetch('/api/session/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            
            const data = await response.json();
            this.sessionId = data.session_id;
            console.log('Session created:', this.sessionId);
        } catch (error) {
            console.error('Error creating session:', error);
            this.showError('Failed to create session');
        }
    }


    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.fileName.textContent = file.name;
            this.validateFile(file);
        }
    }

    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('dragover');
    }

    handleDragLeave(event) {
        event.currentTarget.classList.remove('dragover');
    }

    handleDrop(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('dragover');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.fileInput.files = files;
            this.fileName.textContent = files[0].name;
            this.validateFile(files[0]);
        }
    }

    validateFile(file) {
        const allowedTypes = ['.txt', '.pdf', '.docx', '.md'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        const maxSize = 10 * 1024 * 1024; // 10MB

        if (!allowedTypes.includes(fileExt)) {
            this.showError('Unsupported file type. Please use TXT, PDF, DOCX, or MD files.');
            return false;
        }

        if (file.size > maxSize) {
            this.showError('File too large. Maximum size is 10MB.');
            return false;
        }

        return true;
    }

    async handleUpload(event) {
        event.preventDefault();
        
        if (!this.sessionId) {
            this.showError('Session not ready. Please wait and try again.');
            return;
        }

        const formData = new FormData();
        const file = this.fileInput.files[0];
        
        if (!file) {
            this.showError('Please select a file to upload.');
            return;
        }

        if (!this.validateFile(file)) {
            return;
        }

        // Prepare form data
        formData.append('file', file);
        formData.append('session_id', this.sessionId);
        formData.append('user_prompt', document.getElementById('user-prompt').value.trim());
        formData.append('enhance', document.getElementById('enhance').checked);

        // Show progress section
        this.showSection('progress');
        this.setProgress(0, 'Uploading document...');
        
        // Setup SSE for progress updates
        this.setupEventSource();

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (response.ok) {
                this.setProgress(25, 'Document uploaded successfully. Processing...');
            } else {
                throw new Error(result.message || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showError('Upload failed: ' + error.message);
            this.showSection('upload');
        }
    }

    setupEventSource() {
        // Close existing connection if any
        if (this.eventSource) {
            this.eventSource.close();
        }

        // Determine the correct SSE URL based on current host
        let sseUrl;
        if (window.location.port === '3000') {
            // Frontend dev server - use proxy
            sseUrl = `/api/events/${this.sessionId}`;
        } else {
            // Direct backend access
            const backendHost = window.location.hostname + ':8000';
            sseUrl = `http://${backendHost}/api/events/${this.sessionId}`;
        }
        
        console.log(`Connecting to SSE: ${sseUrl}`);
        this.eventSource = new EventSource(sseUrl);
        this.sseUrl = sseUrl;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.eventSource.onopen = () => {
            console.log('SSE connected');
            this.reconnectAttempts = 0;
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('SSE event received:', data.event_type, data.event_data?.message);
                
                // Handle different event types
                if (data.event_type === 'connected') {
                    console.log('SSE connection confirmed');
                } else if (data.event_type === 'heartbeat') {
                    console.log('Heartbeat received:', data.event_data.message);
                    // Don't show heartbeat messages to user, just log them
                } else {
                    this.handleProgressUpdate(data.event_data);
                    // Note: Events are now auto-acknowledged on the backend
                }
            } catch (e) {
                console.error('Error parsing SSE data:', e, event.data);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            
            // SSE will automatically reconnect, but we can add manual retry logic
            if (this.eventSource.readyState === EventSource.CLOSED) {
                console.log('SSE connection closed, attempting manual reconnect...');
                this.reconnectSSE();
            }
        };
    }
    
    reconnectSSE() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 30000); // Exponential backoff
            
            console.log(`Attempting SSE reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.setupEventSource();
            }, delay);
        } else {
            console.error('Max SSE reconnection attempts reached');
            this.showError('Connection lost. Please refresh the page if processing seems stuck.');
        }
    }
    
    async acknowledgeEvent(eventId) {
        try {
            await fetch(`/api/events/${eventId}/acknowledge`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Failed to acknowledge event:', eventId, error);
        }
    }

    handleProgressUpdate(data) {
        const { stage, message, accuracy_score, request_count, duration } = data;
        
        switch (stage) {
            case 'connected':
                console.log('SSE connection confirmed');
                break;
            case 'upload_complete':
                this.setProgress(25, message);
                this.updateAIStep(1, 'active');
                break;
            case 'processing':
                this.setProgress(40, message);
                this.updateAIStep(1, 'completed');
                this.updateAIStep(2, 'active');
                break;
            case 'llm_processing':
                // Show which specific LLM request is being processed
                const progressIncrement = Math.min(40 + (request_count * 8), 85); // Progress based on request count, capped at 85%
                this.setProgress(progressIncrement, `${message} (Request #${request_count})`);
                this.updateAIStep(2, 'active');
                break;
            case 'llm_completed':
                console.log(`LLM request completed: ${message}`);
                // Update progress slightly for completed requests
                if (request_count <= 3) {
                    this.updateAIStep(2, 'active');
                } else {
                    this.updateAIStep(3, 'active');
                }
                break;
            case 'llm_error':
                this.showError(`LLM Processing Error: ${message}`);
                this.updateAIStep(2, 'error');
                break;
            case 'agent_completed':
                console.log(`Agent completed: ${message}`);
                // Update AI steps based on agent progress
                this.updateAIStep(3, 'active');
                break;
            case 'content_saved':
                console.log(`Content saved: ${message}`);
                this.updateAIStep(4, 'active');
                break;
            case 'completed':
                this.setProgress(100, 'Content generation completed!');
                // Complete all steps
                for (let i = 1; i <= 5; i++) {
                    this.updateAIStep(i, 'completed');
                }
                setTimeout(() => {
                    this.loadGeneratedContent(accuracy_score);
                }, 1000);
                break;
            case 'error':
                this.showError('Processing failed: ' + message);
                this.showSection('upload');
                break;
            default:
                console.log('Progress update:', stage, message);
        }
    }

    updateAIStep(stepNumber, status) {
        const step = document.getElementById(`step-${stepNumber}`);
        if (step) {
            // Remove all status classes
            step.classList.remove('active', 'completed');
            // Add new status class
            if (status !== 'pending') {
                step.classList.add(status);
            }
        }
    }

    async loadGeneratedContent(accuracyScore) {
        try {
            const response = await fetch(`/api/content/${this.sessionId}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayResults(data, accuracyScore);
            } else {
                throw new Error('Failed to load content');
            }
        } catch (error) {
            console.error('Error loading content:', error);
            this.showError('Failed to load generated content');
        }
    }

    displayResults(data, accuracyScore) {
        this.currentContent = data.content;
        this.accuracyScore.textContent = `${Math.round(accuracyScore || data.accuracy_score)}%`;
        
        // Render markdown content
        const htmlContent = marked.parse(this.currentContent);
        this.contentPreview.innerHTML = htmlContent;
        
        // Highlight code blocks
        this.contentPreview.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        this.showSection('results');
    }

    setProgress(percentage, status, details = '') {
        this.progressFill.style.width = `${percentage}%`;
        this.progressStatus.textContent = status;
        this.progressDetails.textContent = details;
    }

    setupNavigation() {
        // Mobile menu toggle
        const mobileMenuBtn = document.getElementById('mobile-menu-btn');
        const mobileMenu = document.getElementById('mobile-menu');
        
        if (mobileMenuBtn && mobileMenu) {
            mobileMenuBtn.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }

        // Mobile services dropdown
        const mobileServicesBtn = document.getElementById('mobile-services-btn');
        const mobileServicesMenu = document.getElementById('mobile-services-menu');
        
        if (mobileServicesBtn && mobileServicesMenu) {
            mobileServicesBtn.addEventListener('click', () => {
                mobileServicesMenu.classList.toggle('hidden');
                const icon = mobileServicesBtn.querySelector('svg');
                icon.classList.toggle('rotate-180');
            });
        }

        // Smooth scrolling for navigation links
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="#"]')) {
                e.preventDefault();
                const targetId = e.target.getAttribute('href');
                this.scrollToSection(targetId);
            }
        });

        // Hide mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (mobileMenu && !mobileMenu.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
    }

    scrollToSection(sectionId) {
        const element = document.querySelector(sectionId);
        if (element) {
            const headerHeight = 80; // Account for fixed header
            const elementPosition = element.offsetTop - headerHeight;
            
            window.scrollTo({
                top: elementPosition,
                behavior: 'smooth'
            });
        }
    }

    showSection(sectionName) {
        // Hide all sections
        this.uploadSection.classList.add('hidden');
        this.progressSection.classList.add('hidden');
        this.resultsSection.classList.add('hidden');
        
        // Show requested section
        switch (sectionName) {
            case 'upload':
                this.uploadSection.classList.remove('hidden');
                break;
            case 'progress':
                this.progressSection.classList.remove('hidden');
                this.scrollToSection('#progress-section');
                break;
            case 'results':
                this.resultsSection.classList.remove('hidden');
                this.scrollToSection('#results-section');
                break;
        }
    }

    toggleEdit(editing) {
        this.isEditing = editing;
        
        if (editing) {
            this.contentPreview.classList.add('hidden');
            this.contentEditor.classList.remove('hidden');
            this.contentTextarea.value = this.currentContent;
            this.editBtn.textContent = '👁️ Preview';
        } else {
            this.contentEditor.classList.add('hidden');
            this.contentPreview.classList.remove('hidden');
            this.editBtn.textContent = '✏️ Edit Content';
        }
    }

    saveEdit() {
        this.currentContent = this.contentTextarea.value;
        const htmlContent = marked.parse(this.currentContent);
        this.contentPreview.innerHTML = htmlContent;
        
        // Re-highlight code blocks
        this.contentPreview.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        this.toggleEdit(false);
        this.showSuccess('Content updated successfully!');
    }

    async requestRevision() {
        const feedback = this.revisionFeedback.value.trim();
        
        if (!feedback) {
            this.showError('Please provide feedback for the revision.');
            return;
        }

        try {
            // For now, just show a success message
            // In a full implementation, this would send the request to the backend
            this.showSuccess('Revision request submitted! This feature will process your feedback.');
            this.revisionFeedback.value = '';
        } catch (error) {
            console.error('Error requesting revision:', error);
            this.showError('Failed to submit revision request');
        }
    }

    downloadContent() {
        const blob = new Blob([this.currentContent], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'generated-content.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showSuccess('Content downloaded successfully!');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '15px 25px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '600',
            zIndex: '1000',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease',
            backgroundColor: type === 'error' ? '#e53e3e' : '#48bb78'
        });
        
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Hide notification after 5 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new GeneAcademy();
});