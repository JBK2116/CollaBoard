// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

class MeetingsManager {
    constructor() {
        this.elements = {
            meetingsGrid: document.getElementById('meetingsGrid'),
            emptyState: document.getElementById('emptyState'),
            statusFilter: document.getElementById('statusFilter'),
            sortBy: document.getElementById('sortBy'),
            searchInput: document.getElementById('searchInput')
        };
        
        this.meetingCards = [];
        this.filteredCards = [];
        this.searchTimeout = null;
        
        this.init();
    }

    init() {
        if (!this.validateElements()) return;
        
        this.parseMeetingData();
        this.bindEvents();
        this.filterMeetings();
        
        console.log('MeetingsManager initialized with', this.meetingCards.length, 'meetings');
    }

    validateElements() {
        const missing = Object.entries(this.elements)
            .filter(([key, element]) => !element)
            .map(([key]) => key);
            
        if (missing.length > 0) {
            console.error('Missing required elements:', missing);
            return false;
        }
        return true;
    }

    parseMeetingData() {
        const cards = this.elements.meetingsGrid.querySelectorAll('.meeting-card');
        
        this.meetingCards = Array.from(cards).map(card => {
            const meetingData = {
                element: card,
                id: this.getDeleteButton(card)?.dataset.meetingId || null,
                title: this.getTextContent(card, '.meeting-title'),
                description: this.getTextContent(card, '.meeting-description'),
                status: card.dataset.status || 'unknown',
                type: card.dataset.type || 'unknown',
                dates: this.parseDates(card),
                meta: this.parseMeta(card)
            };
            
            // Store parsed data on element for easy access
            card._meetingData = meetingData;
            return meetingData;
        });
    }

    getTextContent(card, selector) {
        const element = card.querySelector(selector);
        return element ? element.textContent.trim() : '';
    }

    getDeleteButton(card) {
        return card.querySelector('.btn-danger[data-meeting-id]');
    }

    parseDates(card) {
        const dateItems = card.querySelectorAll('.date-item');
        const dates = {};
        
        dateItems.forEach(item => {
            const label = this.getTextContent(item, '.date-label').replace(':', '').toLowerCase();
            const value = this.getTextContent(item, '.date-value');
            
            dates[label] = {
                raw: value,
                parsed: this.parseDate(value)
            };
        });
        
        return dates;
    }

    parseDate(dateString) {
        // Handle relative dates
        const now = new Date();
        const lowerDate = dateString.toLowerCase();
        
        if (lowerDate.includes('ago')) {
            const match = lowerDate.match(/(\d+)\s*(day|week|month|year)s?\s*ago/);
            if (match) {
                const [, amount, unit] = match;
                const date = new Date(now);
                
                switch (unit) {
                    case 'day': date.setDate(date.getDate() - parseInt(amount)); break;
                    case 'week': date.setDate(date.getDate() - (parseInt(amount) * 7)); break;
                    case 'month': date.setMonth(date.getMonth() - parseInt(amount)); break;
                    case 'year': date.setFullYear(date.getFullYear() - parseInt(amount)); break;
                }
                
                return date;
            }
        }
        
        // Handle standard dates
        const parsed = new Date(dateString);
        return isNaN(parsed.getTime()) ? null : parsed;
    }

    parseMeta(card) {
        const metaItems = card.querySelectorAll('.meta-item');
        const meta = {};
        
        metaItems.forEach(item => {
            const text = item.textContent.trim();
            if (text.includes('minute')) {
                meta.duration = parseInt(text) || 0;
            } else if (text.includes('question')) {
                meta.questions = parseInt(text) || 0;
            } else if (text.includes('participant')) {
                meta.participants = parseInt(text) || 0;
            }
        });
        
        return meta;
    }

    bindEvents() {
        // Use event delegation for better performance
        document.addEventListener('click', this.handleClick.bind(this));
        
        // Debounced search
        this.elements.searchInput.addEventListener('input', () => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => this.filterMeetings(), 300);
        });
        
        // Filter changes
        this.elements.statusFilter.addEventListener('change', () => this.filterMeetings());
        this.elements.sortBy.addEventListener('change', () => this.sortMeetings());
        
        // Enhanced hover effects with delegation
        this.elements.meetingsGrid.addEventListener('mouseenter', this.handleMouseEnter.bind(this), true);
        this.elements.meetingsGrid.addEventListener('mouseleave', this.handleMouseLeave.bind(this), true);
    }

    handleClick(e) {
        // Delete button
        if (e.target.matches('.btn-danger[data-meeting-id]')) {
            const meetingId = e.target.dataset.meetingId;
            const meetingTitle = e.target.dataset.meetingTitle;
            this.deleteMeeting(meetingId, meetingTitle);
        }
    }

    handleMouseEnter(e) {
        if (e.target.closest('.meeting-card')) {
            const card = e.target.closest('.meeting-card');
            this.animateCard(card, 'enter');
        }
    }

    handleMouseLeave(e) {
        if (e.target.closest('.meeting-card')) {
            const card = e.target.closest('.meeting-card');
            this.animateCard(card, 'leave');
        }
    }

    animateCard(card, action) {
        // Use CSS classes instead of inline styles
        if (action === 'enter') {
            card.classList.add('card-hover');
        } else {
            card.classList.remove('card-hover');
        }
    }

    filterMeetings() {
        const statusValue = this.elements.statusFilter.value;
        const searchValue = this.elements.searchInput.value.toLowerCase().trim();
        
        this.filteredCards = this.meetingCards.filter(meeting => {
            const statusMatch = statusValue === 'all' || meeting.status === statusValue;
            const searchMatch = !searchValue || 
                               meeting.title.toLowerCase().includes(searchValue) || 
                               meeting.description.toLowerCase().includes(searchValue);
            
            return statusMatch && searchMatch;
        });
        
        this.updateDisplay();
    }

    sortMeetings() {
        const sortValue = this.elements.sortBy.value;
        
        this.filteredCards.sort((a, b) => {
            switch (sortValue) {
                case 'title':
                    return a.title.localeCompare(b.title);
                
                case 'last-activity':
                    const dateA = a.dates.updated?.parsed || a.dates.created?.parsed || new Date(0);
                    const dateB = b.dates.updated?.parsed || b.dates.created?.parsed || new Date(0);
                    return dateB - dateA; // Newest first
                
                case 'created':
                default:
                    const createdA = a.dates.created?.parsed || new Date(0);
                    const createdB = b.dates.created?.parsed || new Date(0);
                    return createdB - createdA; // Newest first
            }
        });
        
        this.updateDisplay();
    }

    updateDisplay() {
        // Hide all cards first
        this.meetingCards.forEach(meeting => {
            meeting.element.style.display = 'none';
        });
        
        // Show filtered cards in order
        this.filteredCards.forEach((meeting, index) => {
            meeting.element.style.display = 'block';
            meeting.element.style.order = index;
        });
        
        // Handle empty state
        if (this.filteredCards.length === 0) {
            this.elements.meetingsGrid.style.display = 'none';
            this.elements.emptyState.style.display = 'block';
            this.updateEmptyStateMessage();
        } else {
            this.elements.meetingsGrid.style.display = 'grid';
            this.elements.emptyState.style.display = 'none';
        }
    }

    updateEmptyStateMessage() {
        const hasSearch = this.elements.searchInput.value.trim();
        const hasFilter = this.elements.statusFilter.value !== 'all';
        
        if (hasSearch || hasFilter) {
            this.elements.emptyState.querySelector('.empty-title').textContent = 'No meetings found';
            this.elements.emptyState.querySelector('.empty-description').textContent = 
                'Try adjusting your search or filter criteria.';
        } else {
            this.elements.emptyState.querySelector('.empty-title').textContent = 'No meetings yet';
            this.elements.emptyState.querySelector('.empty-description').textContent = 
                'Create your first meeting to start engaging with participants and gather valuable insights.';
        }
    }

    deleteMeeting(meetingId, meetingTitle) {
        if (!meetingId || !meetingTitle) {
            console.error('Missing meeting ID or title for deletion');
            return;
        }
        
        const message = `Are you sure you want to delete "${meetingTitle}"? This action cannot be undone.`;
        if (!confirm(message)) return;
        
        const meetingIndex = this.meetingCards.findIndex(m => m.id === meetingId);
        if (meetingIndex === -1) {
            console.error('Meeting not found:', meetingId);
            return;
        }
        
        const meeting = this.meetingCards[meetingIndex];
        
        // Show loading state
        const deleteButton = meeting.element.querySelector('.btn-danger[data-meeting-id]');
        if (deleteButton) {
            deleteButton.disabled = true;
            deleteButton.textContent = 'Deleting...';
        }
        
        // Send AJAX request
        fetch(`/director/delete-meeting/${meetingId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin' // Include cookies for Django session
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Success - animate deletion
            this.animateDelete(meeting.element, () => {
                // Remove from arrays
                this.meetingCards.splice(meetingIndex, 1);
                this.filteredCards = this.filteredCards.filter(m => m.id !== meetingId);
                
                // Remove from DOM
                meeting.element.remove();
                
                // Update display
                this.updateDisplay();
                
                // Show success message
                this.showMessage(`"${meetingTitle}" has been deleted successfully.`, 'success');
            });
        })
        .catch(error => {
            console.error('Error deleting meeting:', error);
            
            // Reset button state
            if (deleteButton) {
                deleteButton.disabled = false;
                deleteButton.textContent = 'Delete';
            }
            
            // Show error message
            this.showMessage('Failed to delete meeting. Please try again.', 'error');
        });
    }

    animateDelete(element, callback) {
        element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        element.style.opacity = '0';
        element.style.transform = 'scale(0.95)';
        
        setTimeout(callback, 300);
    }

    showMessage(text, type = 'info') {
        const existingMessage = document.querySelector('.flash-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `flash-message flash-message--${type}`;
        messageDiv.textContent = text;
        
        // Add to DOM
        document.body.appendChild(messageDiv);
        
        // Animate in
        requestAnimationFrame(() => {
            messageDiv.classList.add('flash-message--visible');
        });
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            messageDiv.classList.remove('flash-message--visible');
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, 300);
        }, 4000);
    }

    // Public API for external use
    refresh() {
        this.parseMeetingData();
        this.filterMeetings();
    }

    addMeeting(meetingData) {
        // For when new meetings are added via AJAX
        console.log('Adding new meeting:', meetingData);
        // Implementation would depend on your Django integration
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.meetingsManager = new MeetingsManager();
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MeetingsManager;
}