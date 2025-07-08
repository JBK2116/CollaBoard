    // DOM Elements
    const currentQuestionText = document.getElementById('currentQuestionText');
    const questionProgress = document.getElementById('questionProgress');
    const progressFill = document.getElementById('progressFill');
    const bottomProgressFill = document.getElementById('bottomProgressFill');
    const bottomProgressText = document.getElementById('bottomProgressText');
    const questionJumpSelect = document.getElementById('questionJumpSelect');
    const responseFeed = document.getElementById('responseFeed');
    const liveResponseCount = document.getElementById('liveResponseCount');
    const participantCount = document.getElementById('participantCount');
    const responseCount = document.getElementById('responseCount');
    const activeParticipants = document.getElementById('activeParticipants');
    const sessionDuration = document.getElementById('sessionDuration');
    const accessCode = document.getElementById('accessCode');
    const connectionStatus = document.getElementById('connectionStatus');
    const nextQuestionBtn = document.getElementById('nextQuestionBtn');
    const prevQuestionBtn = document.getElementById('prevQuestionBtn');
    const skipQuestionBtn = document.getElementById('skipQuestionBtn');
    const endMeetingBtn = document.getElementById('endMeetingBtn');
    const pauseSessionBtn = document.getElementById('pauseSessionBtn');
    const copyCodeBtn = document.getElementById('copyCodeBtn');
    const refreshResponsesBtn = document.getElementById('refreshResponsesBtn');
    const clearResponsesBtn = document.getElementById('clearResponsesBtn');
    const startMeetingBtn = document.getElementById('startMeetingBtn');

    // Meeting State
    let currentQuestionIndex = -1;
    let totalQuestions = 0;
    let responseCountValue = 0;
    let participantCountValue = 0;
    let sessionStartTime = null;
    let isPaused = false;
    let isConnected = false;

    // No questions or responses at start
    const questions = [];

    // WebSocket Simulation (replace with actual Django Channels)
    let wsConnection = null;

    function initializeWebSocket() {
        // DJANGO-INTEGRATION: Replace with actual WebSocket connection
        // wsConnection = new WebSocket(`ws://${window.location.host}/ws/meeting/${meetingId}/`);
        
        console.log('WebSocket connection initialized (simulated)');
    }

    // Question Navigation
    function nextQuestion() {
        if (currentQuestionIndex < totalQuestions - 1) {
            currentQuestionIndex++;
            updateQuestionDisplay();
            clearResponses();
            // DJANGO-INTEGRATION: Send WebSocket message to participants
            // wsConnection.send(JSON.stringify({type: 'next_question', question_index: currentQuestionIndex}));
        } else {
            // Last question - show completion state
            nextQuestionBtn.innerHTML = `
                <span class="btn-text">Complete Meeting</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                    <polyline points="22,4 12,14.01 9,11.01"/>
                </svg>
            `;
            nextQuestionBtn.classList.remove('btn-primary');
            nextQuestionBtn.classList.add('btn-success');
        }
    }

    function previousQuestion() {
        if (currentQuestionIndex > 0) {
            currentQuestionIndex--;
            updateQuestionDisplay();
            clearResponses();
            // DJANGO-INTEGRATION: Send WebSocket message to participants
            // wsConnection.send(JSON.stringify({type: 'previous_question', question_index: currentQuestionIndex}));
        }
    }

    function jumpToQuestion(questionIndex) {
        currentQuestionIndex = parseInt(questionIndex);
        updateQuestionDisplay();
        clearResponses();
        // DJANGO-INTEGRATION: Send WebSocket message to participants
        // wsConnection.send(JSON.stringify({type: 'jump_question', question_index: currentQuestionIndex}));
    }

    function updateQuestionDisplay() {
        currentQuestionText.textContent = questions[currentQuestionIndex];
        questionProgress.textContent = `Question ${currentQuestionIndex + 1} of ${totalQuestions}`;
        
        const progressPercentage = ((currentQuestionIndex + 1) / totalQuestions) * 100;
        progressFill.style.width = `${progressPercentage}%`;
        bottomProgressFill.style.width = `${progressPercentage}%`;
        bottomProgressText.textContent = `${currentQuestionIndex + 1} of ${totalQuestions} questions`;
        
        // Update question jump select
        questionJumpSelect.value = currentQuestionIndex;
        
        // Update button states
        prevQuestionBtn.disabled = currentQuestionIndex === 0;
        nextQuestionBtn.disabled = currentQuestionIndex === totalQuestions - 1;
    }

    // Response Management
    function addNewResponse(participantId, responseText) {
        const responseCard = document.createElement('div');
        responseCard.className = 'response-card new-response';
        responseCard.innerHTML = `
            <div class="response-header">
                <span class="participant-id">${participantId}</span>
                <span class="response-time">Just now</span>
            </div>
            <div class="response-text">
                ${responseText}
            </div>
        `;
        
        responseFeed.insertBefore(responseCard, responseFeed.firstChild);
        
        // Animate in
        setTimeout(() => {
            responseCard.classList.remove('new-response');
        }, 100);
        
        // Auto-scroll to top
        responseFeed.scrollTop = 0;
        
        // Remove old responses if too many
        const responses = responseFeed.querySelectorAll('.response-card');
        if (responses.length > 50) {
            responses[responses.length - 1].remove();
        }
    }

    function clearResponses() {
        responseFeed.innerHTML = '';
        responseCountValue = 0;
        updateResponseCount();
    }

    function updateResponseCount() {
        responseCountValue++;
        responseCount.textContent = `${responseCountValue} responses`;
        liveResponseCount.textContent = `${responseCountValue} responses`;
    }

    function updateParticipantDisplay() {
        participantCount.textContent = `${participantCountValue} participants`;
        activeParticipants.textContent = `${participantCountValue} active`;
    }

    // Session Timer
    function updateSessionTimer() {
        if (!sessionStartTime || isNaN(sessionStartTime.getTime())) {
            sessionDuration.textContent = '00:00';
            return;
        }
        const now = new Date();
        const elapsed = now - sessionStartTime;
        const hours = Math.floor(elapsed / (1000 * 60 * 60));
        const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((elapsed % (1000 * 60)) / 1000);
        sessionDuration.textContent =
            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    // Copy Access Code
    function copyAccessCode() {
        navigator.clipboard.writeText(accessCode.textContent).then(() => {
            copyCodeBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20,6 9,17 4,12"/>
                </svg>
            `;
            copyCodeBtn.style.color = 'var(--accent-success)';
            
            setTimeout(() => {
                copyCodeBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                `;
                copyCodeBtn.style.color = '';
            }, 2000);
        });
    }

    // Pause/Resume Session
    function togglePause() {
        isPaused = !isPaused;
        
        if (isPaused) {
            pauseSessionBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="5,3 19,12 5,21 5,3"/>
                </svg>
                Resume
            `;
            pauseSessionBtn.classList.remove('btn-secondary');
            pauseSessionBtn.classList.add('btn-warning');
        } else {
            pauseSessionBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="6" y="4" width="4" height="16"/>
                    <rect x="14" y="4" width="4" height="16"/>
                </svg>
                Pause
            `;
            pauseSessionBtn.classList.remove('btn-warning');
            pauseSessionBtn.classList.add('btn-secondary');
        }
        
        // DJANGO-INTEGRATION: Send pause/resume message to participants
        // wsConnection.send(JSON.stringify({type: 'session_pause', paused: isPaused}));
    }

    // End Meeting
    let timerInterval = null;

    function endMeeting() {
        if (confirm('Are you sure you want to end this meeting? This action cannot be undone.')) {
            // Stop all intervals
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            // Disable controls
            prevQuestionBtn.disabled = true;
            nextQuestionBtn.disabled = true;
            skipQuestionBtn.disabled = true;
            endMeetingBtn.disabled = true;
            pauseSessionBtn.disabled = true;
            // Update session status
            document.querySelector('.session-status .status-text').textContent = 'Session Ended';
            // Optionally, show a message or redirect
            alert('Meeting ended successfully');
        }
    }

    // Skip Question
    function skipQuestion() {
        if (confirm('Skip this question and move to the next one?')) {
            nextQuestion();
        }
    }

    // Event Listeners
    nextQuestionBtn.addEventListener('click', nextQuestion);
    prevQuestionBtn.addEventListener('click', previousQuestion);
    skipQuestionBtn.addEventListener('click', skipQuestion);
    endMeetingBtn.addEventListener('click', endMeeting);
    pauseSessionBtn.addEventListener('click', togglePause);
    copyCodeBtn.addEventListener('click', copyAccessCode);
    refreshResponsesBtn.addEventListener('click', () => {
        // DJANGO-INTEGRATION: Refresh responses from server
        console.log('Refreshing responses...');
    });
    clearResponsesBtn.addEventListener('click', clearResponses);
    questionJumpSelect.addEventListener('change', (e) => {
        jumpToQuestion(e.target.value);
    });

    // Initialize
    initializeWebSocket();
    updateQuestionDisplay();
    updateParticipantDisplay();
    
    // Start timer
    timerInterval = setInterval(updateSessionTimer, 1000);
    
    // DJANGO-INTEGRATION: Load initial meeting data
    // meeting = {{ meeting|safe }};
    // currentQuestionIndex = {{ current_question_index }};
    // totalQuestions = {{ total_questions }};
    // questions = {{ questions|safe }};

    function initializeUIForNotStarted() {
        currentQuestionText.textContent = 'No questions yet';
        questionProgress.textContent = 'Question – / –';
        progressFill.style.width = '0%';
        bottomProgressFill.style.width = '0%';
        bottomProgressText.textContent = '0 of 0 questions';
        questionJumpSelect.innerHTML = '<option>No questions</option>';
        questionJumpSelect.disabled = true;
        responseFeed.innerHTML = '<!-- No responses yet -->';
        responseCount.textContent = '0 responses';
        liveResponseCount.textContent = '0 responses';
        participantCount.textContent = '0 participants';
        activeParticipants.textContent = '0 active';
        sessionDuration.textContent = '00:00';
        connectionStatus.classList.remove('connected');
        connectionStatus.classList.add('disconnected');
        connectionStatus.querySelector('.status-text').textContent = 'Not Connected';
        prevQuestionBtn.disabled = true;
        nextQuestionBtn.disabled = true;
        skipQuestionBtn.disabled = true;
        endMeetingBtn.disabled = true;
        pauseSessionBtn.disabled = true;
    }

    document.addEventListener('DOMContentLoaded', () => {
        initializeUIForNotStarted();
    });

    function startMeeting() {
        // Set the session start time
        sessionStartTime = new Date();
        isConnected = true;
        // Enable controls
        prevQuestionBtn.disabled = false;
        nextQuestionBtn.disabled = false;
        skipQuestionBtn.disabled = false;
        endMeetingBtn.disabled = false;
        pauseSessionBtn.disabled = false;
        // Update connection status
        connectionStatus.classList.remove('disconnected');
        connectionStatus.classList.add('connected');
        connectionStatus.querySelector('.status-text').textContent = 'Connected';
        // Hide the start button
        startMeetingBtn.style.display = 'none';
        // Change session status text
        document.querySelector('.session-status .status-text').textContent = 'Session Active';
        // Optionally, initialize first question, etc.
        // DJANGO-CHANNELS: Here you will broadcast meeting started event
    }

    if (startMeetingBtn) {
        startMeetingBtn.addEventListener('click', startMeeting);
    }
