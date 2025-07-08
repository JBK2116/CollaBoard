document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const currentQuestion = document.getElementById('currentQuestion');
    const responseForm = document.getElementById('responseForm');
    const responseInput = document.getElementById('responseInput');
    const submitBtn = document.getElementById('submitBtn');
    const characterCounter = document.getElementById('characterCounter');
    const statusMessage = document.getElementById('statusMessage');
    const progressIndicator = document.getElementById('progressIndicator');
    const participantCount = document.getElementById('participantCount');
    const connectionStatus = document.getElementById('connectionStatus');
    const meetingEndOverlay = document.getElementById('meetingEndOverlay');
    const questionsAnswered = document.getElementById('questionsAnswered');
    const totalParticipants = document.getElementById('totalParticipants');

    // Session State
    let currentQuestionIndex = -1;
    let totalQuestions = 0;
    let participantId = '';
    let isConnected = false;
    let hasSubmitted = false;
    let responseCount = 0;
    let participantCountValue = 0;

    // No questions at start
    const questions = [];

    // Remove simulation and sample data logic
    // No WebSocket simulation, no random participant count

    function updateQuestion(questionIndex) {
        if (questions.length === 0 || questionIndex < 0 || questionIndex >= questions.length) {
            // No questions yet
            currentQuestion.textContent = 'No question yet';
            progressIndicator.textContent = 'Question – / –';
            responseForm.reset();
            responseInput.disabled = true;
            submitBtn.disabled = true;
            return;
        }
        currentQuestionIndex = questionIndex;
        currentQuestion.style.opacity = '0';
        setTimeout(() => {
            currentQuestion.textContent = questions[questionIndex];
            progressIndicator.textContent = `Question ${questionIndex + 1} of ${questions.length}`;
            currentQuestion.style.opacity = '1';
            resetForm();
            responseInput.disabled = false;
            submitBtn.disabled = false;
            responseInput.focus();
            showStatus('Type your response below...', 'info');
        }, 300);
    }

    function resetForm() {
        responseForm.reset();
        responseInput.value = '';
        updateCharacterCounter();
        hasSubmitted = false;
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
            <span class="btn-text">Submit Response</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22,2 15,22 11,13 2,9 22,2"/>
            </svg>
        `;
    }

    function handleSubmit(event) {
        event.preventDefault();
        const response = responseInput.value.trim();
        if (!response) {
            showStatus('Please enter a response before submitting.', 'error');
            responseInput.focus();
            return;
        }
        if (hasSubmitted) {
            showStatus('You have already submitted a response for this question.', 'warning');
            return;
        }
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <span class="btn-text">Submitting...</span>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinner">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none" stroke-dasharray="31.416" stroke-dashoffset="31.416">
                    <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
                    <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
                </circle>
            </svg>
        `;
        // Here you will send the response via Django Channels
        // For now, just show submitted state
        setTimeout(() => {
            submitBtn.innerHTML = `
                <span class="btn-text">Submitted!</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20,6 9,17 4,12"/>
                </svg>
            `;
            submitBtn.style.background = 'var(--accent-success)';
            hasSubmitted = true;
            responseCount++;
            showStatus('Response submitted! Waiting for next question...', 'success');
        }, 1000);
    }

    function updateCharacterCounter() {
        const length = responseInput.value.length;
        const maxLength = 500;
        const counterText = document.querySelector('.counter-text');
        counterText.textContent = `${length}/${maxLength} characters`;
        if (length > maxLength * 0.9) {
            counterText.style.color = 'var(--accent-warning)';
        } else if (length > maxLength * 0.8) {
            counterText.style.color = 'var(--accent-info)';
        } else {
            counterText.style.color = 'var(--text-muted)';
        }
    }

    function showStatus(message, type = 'info') {
        statusMessage.innerHTML = `
            <div class="status-alert ${type}">
                <span class="status-text">${message}</span>
            </div>
        `;
        if (type === 'info') {
            setTimeout(() => { statusMessage.innerHTML = ''; }, 3000);
        }
    }

    function endMeeting() {
        meetingEndOverlay.style.display = 'flex';
        questionsAnswered.textContent = responseCount;
        totalParticipants.textContent = participantCountValue;
    }

    function handleConnectionChange(connected) {
        isConnected = connected;
        if (connected) {
            connectionStatus.className = 'status-indicator connected';
            connectionStatus.innerHTML = `
                <div class="status-dot"></div>
                <span class="status-text">Connected</span>
            `;
            showStatus('Connected to meeting', 'success');
        } else {
            connectionStatus.className = 'status-indicator disconnected';
            connectionStatus.innerHTML = `
                <div class="status-dot"></div>
                <span class="status-text">Disconnected</span>
            `;
            showStatus('Connection lost - trying to reconnect...', 'error');
        }
    }

    responseForm.addEventListener('submit', handleSubmit);
    responseInput.addEventListener('input', updateCharacterCounter);
    responseInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            handleSubmit(e);
        }
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            responseInput.value = '';
            updateCharacterCounter();
            responseInput.focus();
        }
    });

    // Initialize UI to neutral state
    currentQuestion.textContent = 'No question yet';
    progressIndicator.textContent = 'Question – / –';
    participantCount.textContent = '0 participants';
    connectionStatus.className = 'status-indicator disconnected';
    connectionStatus.innerHTML = `<div class="status-dot"></div><span class="status-text">Not Connected</span>`;
    responseInput.disabled = true;
    submitBtn.disabled = true;
    updateCharacterCounter();
    showStatus('Waiting for the session to start...', 'info');
});
