// Edit Meeting JavaScript
// Handles dynamic form interactions, validation, and preview updates

// DOM Elements
const form = document.getElementById('meetingForm');
const questionsContainer = document.getElementById('questionsContainer');
const addQuestionBtn = document.getElementById('addQuestionBtn');
const titleInput = document.getElementById('id_title');
const descriptionInput = document.getElementById('id_description');
const durationSelect = document.getElementById('id_duration');
const questionCount = document.getElementById('questionCount');
const titleCounter = document.getElementById('titleCounter');
const previewTitle = document.getElementById('previewTitle');
const previewDescription = document.getElementById('previewDescription');
const previewDuration = document.getElementById('previewDuration');
const previewQuestionCount = document.getElementById('previewQuestionCount');
const mockTitle = document.getElementById('mockTitle');
const mockQuestions = document.getElementById('mockQuestions');
const deleteMeetingBtn = document.getElementById('deleteMeetingBtn');
const cancelLink = document.getElementById('cancelLink');
const descriptionCounter = document.getElementById('descriptionCounter');

const meetingId = window.location.pathname.split('/')[3];

// Question Management
let questionCounter = 0; // Will be set based on existing questions
const maxQuestions = 20;
let hasUnsavedChanges = false;
let originalFormData = {};

// Store original form data for change detection
function storeOriginalData() {
    originalFormData = {
        title: titleInput.value,
        description: descriptionInput.value,
        duration: durationSelect.value,
        questions: Array.from(questionsContainer.querySelectorAll('input[name*="text"]')).map(input => input.value)
    };
}

// Check for changes
function checkForChanges() {
    const currentData = {
        title: titleInput.value,
        description: descriptionInput.value,
        duration: durationSelect.value,
        questions: Array.from(questionsContainer.querySelectorAll('input[name*="text"]')).map(input => input.value)
    };

    hasUnsavedChanges = JSON.stringify(originalFormData) !== JSON.stringify(currentData);
    
    // Update UI to show changes
    if (hasUnsavedChanges) {
        document.title = 'Edit Meeting * - CollaBoard';
    } else {
        document.title = 'Edit Meeting - CollaBoard';
    }
}

// Add Question Function
function addQuestion() {
    if (questionCounter >= maxQuestions) {
        addQuestionBtn.disabled = true;
        return;
    }

    questionCounter++;
    const questionField = document.createElement('div');
    questionField.className = 'question-field';
    questionField.dataset.question = questionCounter;
    questionField.style.opacity = '0';
    questionField.style.transform = 'translateY(20px)';

    questionField.innerHTML = `
        <div class="question-header">
            <div class="question-number">Question ${questionCounter}</div>
            <button type="button" class="delete-question" aria-label="Delete question">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        </div>
        <input 
            type="text" 
            name="form-${questionCounter}-text" 
            class="form-control question-input" 
            placeholder="Enter your question..."
            maxlength="150"
            required
        >
        <div class="char-counter">
            <span class="question-char-counter">0</span>/150
        </div>
    `;

    questionsContainer.appendChild(questionField);

    // Animate in
    setTimeout(() => {
        questionField.style.transition = 'all 0.3s ease';
        questionField.style.opacity = '1';
        questionField.style.transform = 'translateY(0)';
    }, 10);

    // Add event listeners
    const questionInput = questionField.querySelector('.question-input');
    const charCounter = questionField.querySelector('.question-char-counter');
    
    questionInput.addEventListener('input', function() {
        updateCharCounter(this, charCounter, 150);
        updatePreview();
        checkForChanges();
    });

    const deleteBtn = questionField.querySelector('.delete-question');
    deleteBtn.addEventListener('click', () => deleteQuestion(questionField));

    updateQuestionCount();
    updatePreview();
    checkForChanges();
}

// Delete Question Function
function deleteQuestion(questionField) {
    if (questionCounter <= 1) return;

    // Animate out
    questionField.style.transition = 'all 0.3s ease';
    questionField.style.opacity = '0';
    questionField.style.transform = 'translateY(-20px)';

    setTimeout(() => {
        questionField.remove();
        questionCounter--;
        renumberQuestions();
        updateQuestionCount();
        updatePreview();
        checkForChanges();
        
        if (questionCounter < maxQuestions) {
            addQuestionBtn.disabled = false;
        }
    }, 300);
}

// Renumber Questions
function renumberQuestions() {
    const questions = questionsContainer.querySelectorAll('.question-field');
    questions.forEach((question, index) => {
        const number = index + 1;
        question.dataset.question = number;
        question.querySelector('.question-number').textContent = `Question ${number}`;
        
        // Update delete button state
        const deleteBtn = question.querySelector('.delete-question');
        deleteBtn.disabled = number === 1;
    });
}

// Update Question Count
function updateQuestionCount() {
    questionCount.textContent = questionCounter;
    previewQuestionCount.textContent = `${questionCounter} question${questionCounter !== 1 ? 's' : ''}`;
}

// Character Counter
function updateCharCounter(input, counter, maxLength) {
    const count = input.value.length;
    counter.textContent = count;
    if (maxLength) {
        counter.nextSibling && (counter.nextSibling.textContent = `/${maxLength}`);
    }
    if (count > (maxLength ? maxLength - 20 : 180)) {
        counter.style.color = 'var(--accent-warning)';
    } else if (count > (maxLength ? maxLength - 50 : 150)) {
        counter.style.color = 'var(--text-secondary)';
    } else {
        counter.style.color = 'var(--text-muted)';
    }
}

// Update Preview
function updatePreview() {
    // Update title
    const title = titleInput.value || 'Meeting Title';
    previewTitle.textContent = title;
    mockTitle.textContent = title;

    // Update description
    const description = descriptionInput.value || 'Meeting description will appear here...';
    previewDescription.textContent = description;

    // Update duration
    const duration = durationSelect.value;
    if (duration) {
        const hours = Math.floor(duration / 60);
        const minutes = duration % 60;
        let durationText = '';
        if (hours > 0) {
            durationText = `${hours}h ${minutes > 0 ? minutes + 'm' : ''}`;
        } else {
            durationText = `${minutes}m`;
        }
        previewDuration.textContent = durationText;
    }

    // Update questions in preview
    const questionInputs = questionsContainer.querySelectorAll('input[name*="text"]');
    
    // Clear existing mock questions
    mockQuestions.innerHTML = '';
    
    questionInputs.forEach((input, index) => {
        const questionText = input.value || `Question ${index + 1} will appear here...`;
        const mockQuestion = document.createElement('div');
        mockQuestion.className = 'mock-question';
        mockQuestion.id = `mockQuestion${index + 1}`;
        mockQuestion.textContent = questionText;
        mockQuestions.appendChild(mockQuestion);
    });
}

// Event Listeners Setup
function setupEventListeners() {
    // Add question button
    addQuestionBtn.addEventListener('click', addQuestion);

    // Character counting for title
    titleInput.addEventListener('input', function() {
        updateCharCounter(this, titleCounter, 60);
        updatePreview();
        checkForChanges();
    });

    // Character counting for questions (delegated event)
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('question-input')) {
            const charCounter = e.target.parentElement.querySelector('.question-char-counter');
            updateCharCounter(e.target, charCounter, 150);
            updatePreview();
            checkForChanges();
        }
    });

    // Delete question buttons (delegated event)
    document.addEventListener('click', function(e) {
        if (e.target.closest('.delete-question')) {
            const questionField = e.target.closest('.question-field');
            deleteQuestion(questionField);
        }
    });

    // Preview updates
    descriptionInput.addEventListener('input', function() {
        updateCharCounter(this, descriptionCounter, 200);
        updatePreview();
        checkForChanges();
    });
    
    durationSelect.addEventListener('change', function() {
        updatePreview();
        checkForChanges();
    });

    // Form submission
    form.addEventListener('submit', function(e) {        
        // Add loading state
        const submitBtn = document.getElementById('updateBtn');
        submitBtn.textContent = 'Updating...';
        submitBtn.disabled = true;
    });

    // Delete meeting confirmation
    deleteMeetingBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (confirm('Are you sure you want to permanently delete this meeting? This action cannot be undone.')) {
            if (confirm('This will delete all meeting data including questions and any responses. Are you absolutely sure?')) {
                // Add loading state
                deleteMeetingBtn.textContent = 'Deleting...';
                deleteMeetingBtn.disabled = true;
                
                // Create and submit a form to Django
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = `/director/delete-meeting/${meetingId}/`;
                
                // Add CSRF token
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken;
                form.appendChild(csrfInput);
                
                document.body.appendChild(form);
                form.submit();
            }
        }
    });

    // Cancel confirmation with unsaved changes
    cancelLink.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (hasUnsavedChanges) {
            if (confirm('You have unsaved changes. Are you sure you want to cancel? All changes will be lost.')) {
                window.location.href = "/director/my-meetings/";
            }
        } else {
            window.location.href = "/director/my-meetings/";
        }
    });

    // Warn before leaving page with unsaved changes
    window.addEventListener('beforeunload', function(e) {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
}

// Initialize the application
function init() {
    // Wait for DOM to be fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
        return;
    }

    // Set initial question counter based on existing questions
    questionCounter = questionsContainer.querySelectorAll('.question-field').length;

    // Setup event listeners
    setupEventListeners();
    
    // Store original form data
    storeOriginalData();
    
    // Update initial preview
    updatePreview();

    // On page load, initialize counters
    updateCharCounter(titleInput, titleCounter, 60);
    updateCharCounter(descriptionInput, descriptionCounter, 200);
    Array.from(questionsContainer.querySelectorAll('input[name*="text"]')).forEach((input, i) => {
        const charCounter = input.parentElement.querySelector('.question-char-counter');
        updateCharCounter(input, charCounter, 150);
    });
}

// Start the application
init();