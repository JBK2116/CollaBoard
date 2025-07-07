/**
 * Meeting Form Manager
 * Handles dynamic question management, real-time preview, and form validation
 */

class MeetingFormManager {
    constructor() {
        this.maxQuestions = 20;
        this.elements = {};
        this.eventManager = new EventManager();
        this.validators = new FormValidators();
        this.formsetPrefix = 'form'; // Django default prefix unless changed in view
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
        this.updateCharCounter(this.elements.meetingTitle, this.elements.titleCounter, 60);
        this.updateCharCounter(this.elements.meetingDescription, this.elements.descriptionCounter, 200);
        this.elements.questionsContainer.querySelectorAll('.question-input').forEach((input, i) => {
            const charCounter = input.parentElement.querySelector('.question-char-counter');
            this.updateCharCounter(input, charCounter, 150);
        });
        this.updateQuestionCount();
        console.log('MeetingFormManager initialized successfully');
    }

    /**
     * Get and validate all required DOM elements
     */
    getDOMElements() {
        const ids = [
            'meetingForm', 'questionsContainer', 'addQuestionBtn', 'meetingTitle',
            'meetingDescription', 'meetingDuration', 'questionCount', 'titleCounter',
            'descriptionCounter',
            'previewTitle', 'previewDescription', 'previewDuration', 'previewQuestionCount',
            'mockTitle', 'mockQuestion1', 'mockQuestion2', 'mockQuestion3'
        ];
        let missing = [];
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) this.elements[id] = el;
            else missing.push(id);
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
        this.eventManager.addListener(this.elements.addQuestionBtn, 'click', () => this.addQuestion());
        this.eventManager.addListener(this.elements.meetingForm, 'submit', (e) => this.handleFormSubmit(e));
        this.eventManager.addListener(this.elements.meetingTitle, 'input', this.debounce(() => {
            this.updateCharCounter(this.elements.meetingTitle, this.elements.titleCounter, 60);
            this.updatePreview();
            this.validateField(this.elements.meetingTitle, { required: true, maxLength: 60 });
        }, 100));
        this.eventManager.addListener(this.elements.meetingDescription, 'input', this.debounce(() => {
            this.updateCharCounter(this.elements.meetingDescription, this.elements.descriptionCounter, 200);
            this.updatePreview();
            this.validateField(this.elements.meetingDescription, { maxLength: 200 });
        }, 100));
        this.eventManager.addListener(this.elements.meetingDuration, 'change', () => {
            this.updatePreview();
            this.validateField(this.elements.meetingDuration, { required: true });
        });
        this.eventManager.addListener(this.elements.questionsContainer, 'input', (e) => this.handleQuestionInput(e));
        this.eventManager.addListener(this.elements.questionsContainer, 'click', (e) => this.handleQuestionDelete(e));
        const cancelLink = document.getElementById('cancelLink');
        if (cancelLink) {
            this.eventManager.addListener(cancelLink, 'click', (e) => this.handleCancel(e));
        }
    }

    /**
     * Add a new question field
     */
    addQuestion() {
        const totalForms = this.getTotalForms();
        if (totalForms >= this.maxQuestions) {
            this.elements.addQuestionBtn.disabled = true;
            this.showNotification('Maximum questions reached', 'warning');
            return;
        }
        // Clone the empty form template (last form, or use a hidden template if you have one)
        const formIdx = totalForms;
        const managementForm = this.elements.questionsContainer.querySelector('input[name$="-TOTAL_FORMS"]');
        let emptyForm = this.elements.questionsContainer.querySelector('.question-field:last-child');
        if (!emptyForm) return;
        const newForm = emptyForm.cloneNode(true);
        // Clear input value and errors
        const input = newForm.querySelector('.question-input');
        input.value = '';
        newForm.querySelector('.question-char-counter').textContent = '0';
        newForm.querySelector('.form-error').textContent = '';
        // Update all name/id attributes for Django formset
        this.updateFormAttributes(newForm, formIdx);
        // Enable delete button
        newForm.querySelector('.delete-question').disabled = false;
        // Insert new form
        this.elements.questionsContainer.appendChild(newForm);
        // Update management form
        managementForm.value = formIdx + 1;
        this.updateQuestionCount();
        this.renumberQuestions();
    }

    updateFormAttributes(formElem, idx) {
        // Update input name/id for Django formset
        const input = formElem.querySelector('.question-input');
        input.name = `${this.formsetPrefix}-${idx}-text`;
        input.id = `${this.formsetPrefix}-${idx}-text`;
        // Update error div if needed
        const errorDiv = formElem.querySelector('.form-error');
        if (errorDiv) errorDiv.id = `error_${this.formsetPrefix}_${idx}_text`;
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
        const questionFields = Array.from(this.elements.questionsContainer.querySelectorAll('.question-field'));
        questionFields.forEach((field, i) => {
            field.dataset.question = i + 1;
            field.querySelector('.question-number').textContent = `Question ${i + 1}`;
            this.updateFormAttributes(field, i);
        });
    }

    /**
     * Update question count display
     */
    updateQuestionCount() {
        const count = this.getTotalForms();
        this.elements.questionCount.textContent = count;
        this.elements.previewQuestionCount.textContent = `${count} question${count > 1 ? 's' : ''}`;
    }

    /**
     * Update character counter with color coding
     */
    updateCharCounter(input, counter, maxLength) {
        if (!input || !counter) return;
        counter.textContent = input.value.length;
        if (input.value.length > maxLength) {
            counter.classList.add('over-limit');
        } else {
            counter.classList.remove('over-limit');
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
        const duration = this.elements.meetingDuration.options[this.elements.meetingDuration.selectedIndex]?.text || 'Duration';
        this.elements.previewDuration.textContent = duration;
    }

    /**
     * Update questions preview
     */
    updateQuestionsPreview() {
        const questionInputs = this.elements.questionsContainer.querySelectorAll('.question-input');
        questionInputs.forEach((input, i) => {
            const mockQ = this.elements[`mockQuestion${i + 1}`];
            if (mockQ) mockQ.textContent = input.value || `Question ${i + 1} will appear here...`;
        });
    }

    /**
     * Handle question input events
     */
    handleQuestionInput(e) {
        if (e.target.classList.contains('question-input')) {
            const charCounter = e.target.parentElement.querySelector('.question-char-counter');
            this.updateCharCounter(e.target, charCounter, 150);
            this.updateQuestionsPreview();
        }
    }

    /**
     * Handle question delete button clicks
     */
    handleQuestionDelete(e) {
        if (e.target.closest('.delete-question')) {
            const questionFields = Array.from(this.elements.questionsContainer.querySelectorAll('.question-field'));
            if (questionFields.length <= 1) return; // Always keep at least one
            const field = e.target.closest('.question-field');
            field.remove();
            // Update management form
            const managementForm = this.elements.questionsContainer.querySelector('input[name$="-TOTAL_FORMS"]');
            managementForm.value = questionFields.length - 1;
            this.updateQuestionCount();
            this.renumberQuestions();
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
        if (!this.validateField(this.elements.meetingTitle, { required: true, maxLength: 60 })) {
            isValid = false;
        }
        
        // Validate duration
        if (!this.validateField(this.elements.meetingDuration, { required: true })) {
            isValid = false;
        }
        
        // Validate questions
        const questionInputs = this.elements.questionsContainer.querySelectorAll('.question-input');
        questionInputs.forEach(input => {
            if (!this.validateField(input, { required: true, maxLength: 150 })) {
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

    getTotalForms() {
        const managementForm = this.elements.questionsContainer.querySelector('input[name$="-TOTAL_FORMS"]');
        return parseInt(managementForm.value, 10);
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

// Modal close logic for success/error overlays
(function() {
    function removeQueryParam(param) {
        const url = new URL(window.location.href);
        url.searchParams.delete(param);
        // Remove all params if none left, else update
        const newUrl = url.search ? url.pathname + url.search : url.pathname;
        window.history.replaceState({}, document.title, newUrl);
    }
    function closeModal(modalId, param) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('modal-fade-out');
            setTimeout(() => { modal.style.display = 'none'; }, 350);
            removeQueryParam(param);
        }
    }
    document.addEventListener('DOMContentLoaded', function() {
        const successBtn = document.getElementById('closeSuccessModal');
        if (successBtn) {
            successBtn.addEventListener('click', function() {
                closeModal('successModal', 'created');
            });
        }
        const errorBtn = document.getElementById('closeErrorModal');
        if (errorBtn) {
            errorBtn.addEventListener('click', function() {
                closeModal('errorModal', 'creation_error');
            });
        }
    });
})();

// Optional: Fade-out animation for modal close
const style = document.createElement('style');
style.innerHTML = `
.modal-fade-out {
    animation: fadeOutModal 0.35s cubic-bezier(0.4,0,0.2,1) forwards;
}
@keyframes fadeOutModal {
    from { opacity: 1; }
    to { opacity: 0; }
}`;
document.head.appendChild(style);