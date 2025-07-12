// Clean, efficient JavaScript for create meeting form
document.addEventListener('DOMContentLoaded', function() {
    let questionCount = document.querySelectorAll('.question-item').length;
    
    // Initialize everything
    setupCharacterCounters();
    setupValidation();
    setupQuestionManagement();
    
    // Character counter setup - works for any input/textarea
    function setupCharacterCounters() {
        const fields = [
            { element: '#id_title', counter: '#titleCount', max: 40 },
            { element: '#id_description', counter: '#descriptionCount', max: 300 }
        ];
        
        fields.forEach(field => {
            const element = document.querySelector(field.element);
            const counter = document.querySelector(field.counter);
            if (element && counter) {
                setupCounter(element, counter, field.max);
            }
        });
        
        // Setup counters for existing questions
        document.querySelectorAll('.question-input').forEach(setupQuestionCounter);
    }
    
    function setupCounter(element, counter, maxLength) {
        const updateCounter = () => {
            const length = element.value.length;
            counter.textContent = `${length}/${maxLength}`;
            
            // Update counter color based on usage
            counter.className = 'char-count';
            if (length > maxLength * 0.9) counter.classList.add('danger');
            else if (length > maxLength * 0.8) counter.classList.add('warning');
        };
        
        element.addEventListener('input', updateCounter);
        updateCounter(); // Initialize
    }
    
    function setupQuestionCounter(textarea) {
        const counter = textarea.closest('.form-group').querySelector('.char-count');
        if (counter) {
            setupCounter(textarea, counter, 300);
        }
    }
    
    // Real-time validation
    function setupValidation() {
        const fields = [
            { element: '#id_title', error: '#titleError', validator: validateTitle },
            { element: '#id_description', error: '#descriptionError', validator: validateDescription },
            { element: '#id_duration', error: '#durationError', validator: validateDuration }
        ];
        
        fields.forEach(field => {
            const element = document.querySelector(field.element);
            const errorDiv = document.querySelector(field.error);
            
            if (element && errorDiv) {
                element.addEventListener('blur', () => {
                    const error = field.validator(element.value);
                    showError(element, errorDiv, error);
                });
                
                element.addEventListener('input', () => {
                    if (element.classList.contains('error')) {
                        const error = field.validator(element.value);
                        if (!error) clearError(element, errorDiv);
                    }
                });
            }
        });
    }
    
    // Validation functions
    function validateTitle(value) {
        if (!value.trim()) return 'Meeting title is required';
        if (value.length > 40) return 'Title must be 40 characters or less';
        return null;
    }
    
    function validateDescription(value) {
        if (!value.trim()) return 'Meeting description is required';
        if (value.length > 300) return 'Description must be 300 characters or less';
        return null;
    }
    
    function validateDuration(value) {
        const num = parseInt(value);
        if (!num || num < 1 || num > 60) return 'Duration must be between 1 and 60 minutes';
        return null;
    }
    
    function validateQuestion(value) {
        if (!value.trim()) return 'Question is required';
        if (value.length > 300) return 'Question must be 300 characters or less';
        return null;
    }
    
    function showError(element, errorDiv, message) {
        if (message) {
            element.classList.add('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        } else {
            clearError(element, errorDiv);
        }
    }
    
    function clearError(element, errorDiv) {
        element.classList.remove('error');
        errorDiv.style.display = 'none';
    }
    
    // Question management
    function setupQuestionManagement() {
        document.getElementById('addQuestionBtn').addEventListener('click', addQuestion);
    }
    
    function addQuestion() {
        if (questionCount >= 20) {
            alert('Maximum 20 questions allowed');
            return;
        }
        
        const template = document.getElementById('questionTemplate');
        const clone = template.content.cloneNode(true);
        const questionItem = clone.querySelector('.question-item');
        
        // Set up the new question
        questionItem.setAttribute('data-form-index', questionCount);
        questionItem.querySelector('.question-number').textContent = `Question ${questionCount + 1}`;
        
        // Set up form field
        const textarea = questionItem.querySelector('textarea');
        textarea.name = `form-${questionCount}-description`;
        textarea.id = `id_form-${questionCount}-description`;
        
        // Add to container
        document.getElementById('questionsContainer').appendChild(questionItem);
        
        // Update management form
        document.getElementById('id_form-TOTAL_FORMS').value = questionCount + 1;
        questionCount++;
        
        // Setup counter for new question
        setupQuestionCounter(textarea);
        
        // Setup validation for new question
        const errorDiv = questionItem.querySelector('.error-message');
        textarea.addEventListener('blur', () => {
            const error = validateQuestion(textarea.value);
            showError(textarea, errorDiv, error);
        });
        
        textarea.addEventListener('input', () => {
            if (textarea.classList.contains('error')) {
                const error = validateQuestion(textarea.value);
                if (!error) clearError(textarea, errorDiv);
            }
        });
        
        // Focus the new question
        textarea.focus();
    }
    
    // Form submission validation
    document.getElementById('createMeetingForm').addEventListener('submit', function(e) {
        let isValid = true;
        const errors = [];
        
        // Validate meeting fields
        const titleError = validateTitle(document.getElementById('id_title').value);
        const descriptionError = validateDescription(document.getElementById('id_description').value);
        const durationError = validateDuration(document.getElementById('id_duration').value);
        
        if (titleError) {
            showError(document.getElementById('id_title'), document.getElementById('titleError'), titleError);
            isValid = false;
        }
        
        if (descriptionError) {
            showError(document.getElementById('id_description'), document.getElementById('descriptionError'), descriptionError);
            isValid = false;
        }
        
        if (durationError) {
            showError(document.getElementById('id_duration'), document.getElementById('durationError'), durationError);
            isValid = false;
        }
        
        // Validate questions
        const questionTextareas = document.querySelectorAll('.question-input');
        let hasValidQuestion = false;
        
        questionTextareas.forEach(textarea => {
            const error = validateQuestion(textarea.value);
            const errorDiv = textarea.closest('.form-group').querySelector('.error-message');
            
            if (error) {
                showError(textarea, errorDiv, error);
                isValid = false;
            } else {
                hasValidQuestion = true;
                clearError(textarea, errorDiv);
            }
        });
        
        if (!hasValidQuestion) {
            isValid = false;
            errors.push('At least one question is required');
        }
        
        if (!isValid) {
            e.preventDefault();
            if (errors.length > 0) {
                alert(errors.join('\n'));
            }
        } else {
            // Show loading state
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating Meeting...';
        }
    });
});

// Global function for removing questions
function removeQuestion(button) {
    const questionItem = button.closest('.question-item');
    const questionsContainer = document.getElementById('questionsContainer');
    const questionItems = questionsContainer.querySelectorAll('.question-item');
    
    // Don't allow removing the last question
    if (questionItems.length <= 1) {
        alert('At least one question is required');
        return;
    }
    
    // Remove the question
    questionItem.remove();
    
    // Update form count
    const totalForms = document.getElementById('id_form-TOTAL_FORMS');
    totalForms.value = parseInt(totalForms.value) - 1;
    
    // Renumber remaining questions
    renumberQuestions();
}

function renumberQuestions() {
    const questions = document.querySelectorAll('.question-item');
    
    questions.forEach((question, index) => {
        // Update visual numbering
        question.querySelector('.question-number').textContent = `Question ${index + 1}`;
        
        // Update form field names
        const textarea = question.querySelector('textarea');
        textarea.name = `form-${index}-description`;
        textarea.id = `id_form-${index}-description`;
        
        // Update data attribute
        question.setAttribute('data-form-index', index);
    });
}