// Edit Meeting JavaScript
// Handles dynamic form interactions, validation, and preview updates

// DOM Elements
const form = document.getElementById('meetingForm');
const questionsContainer = document.getElementById('questionsContainer');
const addQuestionBtn = document.getElementById('addQuestionBtn');
const titleInput = document.getElementById('meetingTitle');
const descriptionInput = document.getElementById('meetingDescription');
const durationSelect = document.getElementById('meetingDuration');
const questionCount = document.getElementById('questionCount');
const titleCounter = document.getElementById('titleCounter');
const previewTitle = document.getElementById('previewTitle');
const previewDescription = document.getElementById('previewDescription');
const previewDuration = document.getElementById('previewDuration');
const previewQuestionCount = document.getElementById('previewQuestionCount');
const mockTitle = document.getElementById('mockTitle');
const mockQuestion1 = document.getElementById('mockQuestion1');
const mockQuestion2 = document.getElementById('mockQuestion2');
const mockQuestion3 = document.getElementById('mockQuestion3');
const deleteMeetingBtn = document.getElementById('deleteMeetingBtn');
const cancelLink = document.getElementById('cancelLink');

// Question Management
let questionCounter = 5; // Start with 5 pre-filled questions
const maxQuestions = 20;
let hasUnsavedChanges = false;
let originalFormData = {};

// Store original form data for change detection
function storeOriginalData() {
    originalFormData = {
        title: titleInput.value,
        description: descriptionInput.value,
        duration: durationSelect.value,
        meetingType: document.querySelector('input[name="meeting_type"]:checked').value,
        questions: Array.from(questionsContainer.querySelectorAll('.question-input')).map(input => input.value)
    };
}

// Check for changes
function checkForChanges() {
    const currentData = {
        title: titleInput.value,
        description: descriptionInput.value,
        duration: durationSelect.value,
        meetingType: document.querySelector('input[name="meeting_type"]:checked').value,
        questions: Array.from(questionsContainer.querySelectorAll('.question-input')).map(input => input.value)
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
            name="questions[]" 
            class="form-control question-input" 
            placeholder="Enter your question..."
            maxlength="200"
            required
        >
        <div class="char-counter">
            <span class="question-char-counter">0</span>/200
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
        updateCharCounter(this, charCounter);
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
function updateCharCounter(input, counter) {
    const count = input.value.length;
    counter.textContent = count;
    
    if (count > 180) {
        counter.style.color = 'var(--accent-warning)';
    } else if (count > 150) {
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
    const questionInputs = questionsContainer.querySelectorAll('.question-input');
    const mockQuestions = [mockQuestion1, mockQuestion2, mockQuestion3];
    
    mockQuestions.forEach((mock, index) => {
        if (index < questionInputs.length) {
            const questionText = questionInputs[index].value || `Question ${index + 1} will appear here...`;
            mock.textContent = questionText;
        } else {
            mock.textContent = `Question ${index + 1} will appear here...`;
        }
    });
}

// Event Listeners Setup
function setupEventListeners() {
    // Add question button
    addQuestionBtn.addEventListener('click', addQuestion);

    // Character counting for title
    titleInput.addEventListener('input', function() {
        updateCharCounter(this, titleCounter);
        updatePreview();
        checkForChanges();
    });

    // Character counting for questions (delegated event)
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('question-input')) {
            const charCounter = e.target.parentElement.querySelector('.question-char-counter');
            updateCharCounter(e.target, charCounter);
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
        updatePreview();
        checkForChanges();
    });
    
    durationSelect.addEventListener('change', function() {
        updatePreview();
        checkForChanges();
    });

    // Radio button changes
    document.addEventListener('change', function(e) {
        if (e.target.name === 'meeting_type') {
            checkForChanges();
        }
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // DJANGO-INTEGRATION: This will be handled by Django form processing
        console.log('Form submitted - Django will handle meeting update');
        
        // Add loading state
        const submitBtn = document.getElementById('updateBtn');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Updating...';
        submitBtn.disabled = true;
        
        // Simulate form submission (remove in Django implementation)
        setTimeout(() => {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            hasUnsavedChanges = false;
            document.title = 'Edit Meeting - CollaBoard';
            // DJANGO-INTEGRATION: Redirect to meeting detail or dashboard
            // window.location.href = '/director/meeting/meeting-id/';
        }, 2000);
    });

    // Delete meeting confirmation
    deleteMeetingBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (confirm('Are you sure you want to permanently delete this meeting? This action cannot be undone.')) {
            if (confirm('This will delete all meeting data including questions and any responses. Are you absolutely sure?')) {
                // DJANGO-INTEGRATION: Handle meeting deletion
                console.log('Meeting deletion confirmed - Django will handle this');
                
                // Add loading state
                deleteMeetingBtn.textContent = 'Deleting...';
                deleteMeetingBtn.disabled = true;
                
                // Simulate deletion (remove in Django implementation)
                setTimeout(() => {
                    // DJANGO-INTEGRATION: Redirect to meetings list
                    // window.location.href = '/director/my-meetings/';
                    alert('Meeting deleted successfully');
                }, 2000);
            }
        }
    });

    // Cancel confirmation with unsaved changes
    cancelLink.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (hasUnsavedChanges) {
            if (confirm('You have unsaved changes. Are you sure you want to cancel? All changes will be lost.')) {
                // DJANGO-INTEGRATION: href="{% url 'my_meetings' %}"
                window.location.href = '#';
            }
        } else {
            // DJANGO-INTEGRATION: href="{% url 'my_meetings' %}"
            window.location.href = '#';
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

    // Setup event listeners
    setupEventListeners();
    
    // Store original form data
    storeOriginalData();
    
    // Update initial preview
    updatePreview();
}

// Start the application
init();