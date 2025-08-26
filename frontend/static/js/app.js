class GeneAcademy {
    constructor() {
        this.sessionId = null;
        this.websocket = null;
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
                body: JSON.stringify({
                    user_ip: this.getClientIP()
                })
            });
            
            const data = await response.json();
            this.sessionId = data.session_id;
            console.log('Session created:', this.sessionId);
        } catch (error) {
            console.error('Error creating session:', error);
            this.showError('Failed to create session');
        }
    }

    getClientIP() {
        // This is a simplified version - in production you'd want proper IP detection
        return 'unknown';
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
        formData.append('duration', document.getElementById('duration').value);
        formData.append('enhance', document.getElementById('enhance').checked);

        // Show progress section
        this.showSection('progress');
        this.setProgress(0, 'Uploading document...');
        
        // Setup WebSocket for progress updates
        this.setupWebSocket();

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

    setupWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleProgressUpdate(data);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket closed');
        };
    }

    handleProgressUpdate(data) {
        const { stage, message, accuracy_score } = data;
        
        switch (stage) {
            case 'upload_complete':
                this.setProgress(25, message);
                this.updateAIStep(1, 'active');
                break;
            case 'processing':
                this.setProgress(50, message);
                this.updateAIStep(1, 'completed');
                this.updateAIStep(2, 'active');
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