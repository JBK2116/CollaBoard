// Create Meeting JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    const addQuestionBtn = document.getElementById('addQuestionBtn');
    const questionsContainer = document.getElementById('questionsContainer');
    const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');
    
    let questionCount = 1; // Start with 1 question
    
    // Initialize character counters
    initializeCharacterCounters();
    
    // Add question functionality
    addQuestionBtn.addEventListener('click', function() {
        if (questionCount < 20) { // Maximum 20 questions
            addNewQuestion();
        } else {
            alert('Maximum 20 questions allowed');
        }
    });
    
    function addNewQuestion() {
        // Clone the first question item
        const firstQuestion = questionsContainer.querySelector('.question-item');
        const newQuestion = firstQuestion.cloneNode(true);
        
        // Update the question index
        newQuestion.setAttribute('data-question-index', questionCount);
        
        // Update question number
        const questionNumber = newQuestion.querySelector('.question-number');
        questionNumber.textContent = `Question ${questionCount + 1}`;
        
        // Update form field names and IDs
        updateFormFields(newQuestion, questionCount);
        
        // Clear the textarea value
        const textarea = newQuestion.querySelector('textarea');
        textarea.value = '';
        
        // Reset character counter
        const charCounter = newQuestion.querySelector('.char-count');
        charCounter.textContent = '0/300';
        
        // Add remove button if it doesn't exist
        const questionHeader = newQuestion.querySelector('.question-header');
        if (!questionHeader.querySelector('.btn-remove-question')) {
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'btn-remove-question';
            removeBtn.innerHTML = '<span class="btn-icon">×</span>';
            removeBtn.onclick = function() { removeQuestion(this); };
            questionHeader.appendChild(removeBtn);
        }
        
        // Add the new question to the container
        questionsContainer.appendChild(newQuestion);
        
        // Update question count and total forms
        questionCount++;
        totalFormsInput.value = questionCount;
        
        // Update position values
        updatePositions();
        
        // Initialize character counter for the new question
        initializeCharacterCounter(textarea);
    }
    
    function updateFormFields(questionElement, index) {
        const textarea = questionElement.querySelector('textarea');
        const positionInput = questionElement.querySelector('input[type="hidden"]');
        
        // Update textarea
        textarea.name = `form-${index}-description`;
        textarea.id = `id_form-${index}-description`;
        
        // Update position input
        if (positionInput) {
            positionInput.name = `form-${index}-position`;
            positionInput.id = `id_form-${index}-position`;
            positionInput.value = index + 1;
        }
    }
    
    function updatePositions() {
        const questions = questionsContainer.querySelectorAll('.question-item');
        questions.forEach((question, index) => {
            const positionInput = question.querySelector('input[type="hidden"]');
            if (positionInput) {
                positionInput.value = index + 1;
            }
            
            // Update question number display
            const questionNumber = question.querySelector('.question-number');
            questionNumber.textContent = `Question ${index + 1}`;
            
            // Update form field names
            updateFormFields(question, index);
        });
    }
    
    function initializeCharacterCounters() {
        // Initialize counters for meeting form fields
        const titleInput = document.getElementById('id_title');
        const descriptionTextarea = document.getElementById('id_description');
        const durationInput = document.getElementById('id_duration');
        
        if (titleInput) {
            initializeCharacterCounter(titleInput, 'titleCount', 40);
        }
        
        if (descriptionTextarea) {
            initializeCharacterCounter(descriptionTextarea, 'descriptionCount', 300);
        }
        
        // Initialize counters for existing question textareas
        const questionTextareas = document.querySelectorAll('.question-item textarea');
        questionTextareas.forEach(textarea => {
            initializeCharacterCounter(textarea);
        });
    }
    
    function initializeCharacterCounter(element, counterId = null, maxLength = 300) {
        const counter = counterId ? 
            document.getElementById(counterId) : 
            element.closest('.form-group').querySelector('.char-count');
        
        if (counter) {
            // Update counter on input
            element.addEventListener('input', function() {
                const currentLength = this.value.length;
                counter.textContent = `${currentLength}/${maxLength}`;
                
                // Add warning color if approaching limit
                if (currentLength > maxLength * 0.9) {
                    counter.style.color = '#e53e3e';
                } else if (currentLength > maxLength * 0.8) {
                    counter.style.color = '#ed8936';
                } else {
                    counter.style.color = '#a0aec0';
                }
            });
            
            // Initialize counter
            const currentLength = element.value.length;
            counter.textContent = `${currentLength}/${maxLength}`;
        }
    }
    
    // Form validation
    document.getElementById('createMeetingForm').addEventListener('submit', function(e) {
        let isValid = true;
        const errors = [];
        
        // Validate meeting title
        const titleInput = document.getElementById('id_title');
        if (!titleInput.value.trim()) {
            errors.push('Meeting title is required');
            titleInput.classList.add('error');
            isValid = false;
        } else {
            titleInput.classList.remove('error');
        }
        
        // Validate meeting description
        const descriptionTextarea = document.getElementById('id_description');
        if (!descriptionTextarea.value.trim()) {
            errors.push('Meeting description is required');
            descriptionTextarea.classList.add('error');
            isValid = false;
        } else {
            descriptionTextarea.classList.remove('error');
        }
        
        // Validate duration
        const durationInput = document.getElementById('id_duration');
        const duration = parseInt(durationInput.value);
        if (!duration || duration < 1 || duration > 60) {
            errors.push('Duration must be between 1 and 60 minutes');
            durationInput.classList.add('error');
            isValid = false;
        } else {
            durationInput.classList.remove('error');
        }
        
        // Validate questions
        const questionTextareas = document.querySelectorAll('.question-item textarea');
        let hasValidQuestion = false;
        
        questionTextareas.forEach(textarea => {
            if (textarea.value.trim()) {
                hasValidQuestion = true;
                textarea.classList.remove('error');
            }
        });
        
        if (!hasValidQuestion) {
            errors.push('At least one question is required');
            questionTextareas.forEach(textarea => {
                if (!textarea.value.trim()) {
                    textarea.classList.add('error');
                }
            });
            isValid = false;
        }
        
        if (!isValid) {
            e.preventDefault();
            alert('Please fix the following errors:\n' + errors.join('\n'));
        }
    });
});

// Global function for removing questions (called from HTML)
function removeQuestion(button) {
    const questionItem = button.closest('.question-item');
    const questionsContainer = document.getElementById('questionsContainer');
    const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');
    
    // Don't remove if it's the only question
    const questionItems = questionsContainer.querySelectorAll('.question-item');
    if (questionItems.length <= 1) {
        alert('At least one question is required');
        return;
    }
    
    // Remove the question
    questionItem.remove();
    
    // Update question count
    const remainingQuestions = questionsContainer.querySelectorAll('.question-item');
    totalFormsInput.value = remainingQuestions.length;
    
    // Update positions and form field names
    updatePositions();
    
    // Hide remove button on first question if only one remains
    if (remainingQuestions.length === 1) {
        const removeBtn = remainingQuestions[0].querySelector('.btn-remove-question');
        if (removeBtn) {
            removeBtn.remove();
        }
    }
}

function updatePositions() {
    const questionsContainer = document.getElementById('questionsContainer');
    const questions = questionsContainer.querySelectorAll('.question-item');
    
    questions.forEach((question, index) => {
        // Update question index attribute
        question.setAttribute('data-question-index', index);
        
        // Update question number display
        const questionNumber = question.querySelector('.question-number');
        questionNumber.textContent = `Question ${index + 1}`;
        
        // Update form field names and IDs
        const textarea = question.querySelector('textarea');
        const positionInput = question.querySelector('input[type="hidden"]');
        
        if (textarea) {
            textarea.name = `form-${index}-description`;
            textarea.id = `id_form-${index}-description`;
        }
        
        if (positionInput) {
            positionInput.name = `form-${index}-position`;
            positionInput.id = `id_form-${index}-position`;
            positionInput.value = index + 1;
        }
    });
}