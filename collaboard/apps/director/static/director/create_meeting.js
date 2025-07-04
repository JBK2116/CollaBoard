/**
 * Meeting Form Manager
 * Handles dynamic question management, real-time preview, and form validation
 */

class MeetingFormManager {
    constructor() {
        this.questionCounter = 1;
        this.maxQuestions = 20;
        this.elements = {};
        this.eventManager = new EventManager();
        this.validators = new FormValidators();
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }

    /**
     * Initialize the form manager
     */
    initialize() {
        if (!this.getDOMElements()) {
            console.error('Failed to initialize MeetingFormManager: Missing required elements');
            return;
        }

        this.setupEventListeners();
        this.updatePreview();
        console.log('MeetingFormManager initialized successfully');
    }

    /**
     * Get and validate all required DOM elements
     */
    getDOMElements() {
        const elementIds = [
            'meetingForm', 'questionsContainer', 'addQuestionBtn', 'meetingTitle',
            'meetingDescription', 'meetingDuration', 'questionCount', 'titleCounter',
            'previewTitle', 'previewDescription', 'previewDuration', 'previewQuestionCount',
            'mockTitle', 'mockQuestion1', 'mockQuestion2', 'mockQuestion3'
        ];

        const missing = [];
        
        elementIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                this.elements[id] = element;
            } else {
                missing.push(id);
            }
        });

        if (missing.length > 0) {
            console.error('Missing required elements:', missing);
            return false;
        }

        return true;
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Add question button
        this.eventManager.addListener(
            this.elements.addQuestionBtn, 
            'click', 
            () => this.addQuestion()
        );

        // Form submission
        this.eventManager.addListener(
            this.elements.meetingForm, 
            'submit', 
            (e) => this.handleFormSubmit(e)
        );

        // Title input with debounced preview update
        this.eventManager.addListener(
            this.elements.meetingTitle, 
            'input', 
            this.debounce(() => {
                this.updateCharCounter(this.elements.meetingTitle, this.elements.titleCounter);
                this.updatePreview();
                this.validateField(this.elements.meetingTitle, { required: true, maxLength: 200 });
            }, 100)
        );

        // Description input
        this.eventManager.addListener(
            this.elements.meetingDescription, 
            'input', 
            this.debounce(() => this.updatePreview(), 100)
        );

        // Duration select
        this.eventManager.addListener(
            this.elements.meetingDuration, 
            'change', 
            () => {
                this.updatePreview();
                this.validateField(this.elements.meetingDuration, { required: true });
            }
        );

        // Event delegation for dynamic question inputs
        this.eventManager.addListener(
            this.elements.questionsContainer, 
            'input', 
            (e) => this.handleQuestionInput(e)
        );

        // Event delegation for delete buttons
        this.eventManager.addListener(
            this.elements.questionsContainer, 
            'click', 
            (e) => this.handleQuestionDelete(e)
        );

        // Cancel link with confirmation
        const cancelLink = document.getElementById('cancelLink');
        if (cancelLink) {
            this.eventManager.addListener(
                cancelLink, 
                'click', 
                (e) => this.handleCancel(e)
            );
        }
    }

    /**
     * Add a new question field
     */
    addQuestion() {
        if (this.questionCounter >= this.maxQuestions) {
            this.elements.addQuestionBtn.disabled = true;
            this.showNotification('Maximum questions reached', 'warning');
            return;
        }

        this.questionCounter++;
        const questionField = this.createQuestionElement();
        
        this.elements.questionsContainer.appendChild(questionField);
        this.animateElementIn(questionField);
        
        this.updateQuestionCount();
        this.updatePreview();
    }

    /**
     * Create a new question element
     */
    createQuestionElement() {
        const questionField = document.createElement('div');
        questionField.className = 'question-field';
        questionField.dataset.question = this.questionCounter;
        questionField.style.opacity = '0';
        questionField.style.transform = 'translateY(20px)';

        questionField.innerHTML = `
            <div class="question-header">
                <div class="question-number">Question ${this.questionCounter}</div>
                <button type="button" class="delete-question" aria-label="Delete question">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
            <input 
                type="text" 
                name="questions[]" 
                class="form-control question-input" 
                placeholder="Enter your question..."
                maxlength="200"
                required
            >
            <div class="char-counter">
                <span class="question-char-counter">0</span>/200
            </div>
            <div class="form-error question-error"></div>
        `;

        return questionField;
    }

    /**
     * Delete a question field
     */
    deleteQuestion(questionField) {
        if (this.questionCounter <= 1) {
            this.showNotification('Cannot delete the last question', 'warning');
            return;
        }

        this.animateElementOut(questionField, () => {
            questionField.remove();
            this.questionCounter--;
            this.renumberQuestions();
            this.updateQuestionCount();
            this.updatePreview();
            
            if (this.questionCounter < this.maxQuestions) {
                this.elements.addQuestionBtn.disabled = false;
            }
        });
    }

    /**
     * Renumber all questions after deletion
     */
    renumberQuestions() {
        const questions = this.elements.questionsContainer.querySelectorAll('.question-field');
        questions.forEach((question, index) => {
            const number = index + 1;
            question.dataset.question = number;
            question.querySelector('.question-number').textContent = `Question ${number}`;
            
            const deleteBtn = question.querySelector('.delete-question');
            deleteBtn.disabled = number === 1;
        });
    }

    /**
     * Update question count display
     */
    updateQuestionCount() {
        this.elements.questionCount.textContent = this.questionCounter;
        this.elements.previewQuestionCount.textContent = 
            `${this.questionCounter} question${this.questionCounter !== 1 ? 's' : ''}`;
    }

    /**
     * Update character counter with color coding
     */
    updateCharCounter(input, counter) {
        const count = input.value.length;
        const maxLength = input.getAttribute('maxlength') || 200;
        
        counter.textContent = count;
        
        // Color coding based on usage
        const percentage = (count / maxLength) * 100;
        if (percentage > 90) {
            counter.style.color = 'var(--accent-warning)';
        } else if (percentage > 75) {
            counter.style.color = 'var(--text-secondary)';
        } else {
            counter.style.color = 'var(--text-muted)';
        }
    }

    /**
     * Update live preview
     */
    updatePreview() {
        try {
            // Update title
            const title = this.elements.meetingTitle.value || 'Meeting Title';
            this.elements.previewTitle.textContent = title;
            this.elements.mockTitle.textContent = title;

            // Update description
            const description = this.elements.meetingDescription.value || 'Meeting description will appear here...';
            this.elements.previewDescription.textContent = description;

            // Update duration
            this.updateDurationPreview();

            // Update questions in preview
            this.updateQuestionsPreview();
        } catch (error) {
            console.error('Error updating preview:', error);
        }
    }

    /**
     * Update duration preview
     */
    updateDurationPreview() {
        const duration = this.elements.meetingDuration.value;
        if (duration) {
            const hours = Math.floor(duration / 60);
            const minutes = duration % 60;
            let durationText = '';
            
            if (hours > 0) {
                durationText = `${hours}h${minutes > 0 ? ` ${minutes}m` : ''}`;
            } else {
                durationText = `${minutes}m`;
            }
            
            this.elements.previewDuration.textContent = durationText;
        } else {
            this.elements.previewDuration.textContent = 'Duration';
        }
    }

    /**
     * Update questions preview
     */
    updateQuestionsPreview() {
        const questionInputs = this.elements.questionsContainer.querySelectorAll('.question-input');
        const mockQuestions = [
            this.elements.mockQuestion1, 
            this.elements.mockQuestion2, 
            this.elements.mockQuestion3
        ];
        
        mockQuestions.forEach((mock, index) => {
            if (index < questionInputs.length) {
                const questionText = questionInputs[index].value || `Question ${index + 1} will appear here...`;
                mock.textContent = questionText;
                mock.style.display = 'block';
            } else {
                mock.style.display = 'none';
            }
        });
    }

    /**
     * Handle question input events
     */
    handleQuestionInput(e) {
        if (e.target.classList.contains('question-input')) {
            const charCounter = e.target.parentElement.querySelector('.question-char-counter');
            this.updateCharCounter(e.target, charCounter);
            this.debounce(() => this.updatePreview(), 100)();
            this.validateField(e.target, { required: true, maxLength: 200 });
        }
    }

    /**
     * Handle question delete button clicks
     */
    handleQuestionDelete(e) {
        const deleteBtn = e.target.closest('.delete-question');
        if (deleteBtn) {
            const questionField = deleteBtn.closest('.question-field');
            this.deleteQuestion(questionField);
        }
    }

    /**
     * Handle form submission
     */
    handleFormSubmit(e) {        
        if (!this.validateForm()) {
            this.showNotification('Please fix the errors before submitting', 'error');
            return;
        }

        console.log('Form submitted - Django will handle meeting creation');
        
        const submitBtn = document.getElementById('createBtn');
        if (submitBtn) {
            this.setLoadingState(submitBtn, true); // Send the form info.
        }
    }

    /**
     * Handle cancel with confirmation
     */
    handleCancel(e) {
        e.preventDefault();
        
        if (this.hasUnsavedChanges()) {
            // Make the links path relative to the site's root url
            if (confirm('You have unsaved changes. Are you sure you want to cancel?')) {
                window.location.href = "/director/dashboard/";
            }
        } else {
            window.location.href = "/director/create-meeting/";
        }
    }

    /**
     * Check if form has unsaved changes
     */
    hasUnsavedChanges() {
        const hasTitle = this.elements.meetingTitle.value.trim();
        const hasDescription = this.elements.meetingDescription.value.trim();
        const hasQuestions = Array.from(this.elements.questionsContainer.querySelectorAll('.question-input'))
            .some(input => input.value.trim());
        
        return hasTitle || hasDescription || hasQuestions;
    }

    /**
     * Validate entire form
     */
    validateForm() {
        let isValid = true;
        
        // Validate title
        if (!this.validateField(this.elements.meetingTitle, { required: true, maxLength: 200 })) {
            isValid = false;
        }
        
        // Validate duration
        if (!this.validateField(this.elements.meetingDuration, { required: true })) {
            isValid = false;
        }
        
        // Validate questions
        const questionInputs = this.elements.questionsContainer.querySelectorAll('.question-input');
        questionInputs.forEach(input => {
            if (!this.validateField(input, { required: true, maxLength: 200 })) {
                isValid = false;
            }
        });
        
        return isValid;
    }

    /**
     * Validate individual field
     */
    validateField(field, rules) {
        const errors = this.validators.validate(field.value, rules);
        const errorElement = field.parentElement.querySelector('.form-error, .question-error');
        
        if (errors.length > 0) {
            field.classList.add('error');
            if (errorElement) {
                errorElement.textContent = errors[0];
                errorElement.style.display = 'block';
            }
            return false;
        } else {
            field.classList.remove('error');
            if (errorElement) {
                errorElement.textContent = '';
                errorElement.style.display = 'none';
            }
            return true;
        }
    }

    /**
     * Set loading state for button
     */
    setLoadingState(button, isLoading) {
        if (isLoading) {
            button.dataset.originalText = button.textContent;
            button.textContent = 'Creating...';
            button.disabled = true;
        } else {
            button.textContent = button.dataset.originalText || 'Create & Start';
            button.disabled = false;
        }
    }

    /**
     * Show notification to user
     */
    showNotification(message, type = 'info') {
        // Simple console notification - replace with actual notification system
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    /**
     * Animate element in
     */
    animateElementIn(element) {
        requestAnimationFrame(() => {
            element.style.transition = 'all 0.3s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        });
    }

    /**
     * Animate element out
     */
    animateElementOut(element, callback) {
        element.style.transition = 'all 0.3s ease';
        element.style.opacity = '0';
        element.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            if (callback) callback();
        }, 300);
    }

    /**
     * Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Cleanup method
     */
    destroy() {
        this.eventManager.cleanup();
        console.log('MeetingFormManager destroyed');
    }
}

/**
 * Event Manager for handling event listeners
 */
class EventManager {
    constructor() {
        this.listeners = new Map();
    }

    addListener(element, event, handler) {
        if (!element) {
            console.warn('Attempted to add listener to null element');
            return;
        }

        element.addEventListener(event, handler);
        
        if (!this.listeners.has(element)) {
            this.listeners.set(element, []);
        }
        this.listeners.get(element).push({ event, handler });
    }

    cleanup() {
        this.listeners.forEach((events, element) => {
            events.forEach(({ event, handler }) => {
                element.removeEventListener(event, handler);
            });
        });
        this.listeners.clear();
    }
}

/**
 * Form validation utilities
 */
class FormValidators {
    validate(value, rules) {
        const errors = [];
        
        if (rules.required && !value.trim()) {
            errors.push('This field is required');
        }
        
        if (rules.maxLength && value.length > rules.maxLength) {
            errors.push(`Maximum ${rules.maxLength} characters allowed`);
        }
        
        if (rules.minLength && value.length < rules.minLength) {
            errors.push(`Minimum ${rules.minLength} characters required`);
        }
        
        return errors;
    }
}

// Initialize the form manager
const meetingFormManager = new MeetingFormManager();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (meetingFormManager) {
        meetingFormManager.destroy();
    }
});