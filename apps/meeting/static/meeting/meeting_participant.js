/*
WebSocket message types - must match backend constants
*/
const MessageTypes = Object.freeze({
    START_MEETING: "start_meeting",
    END_MEETING: "end_meeting",
    NEXT_QUESTION: "next_question",
    SUBMIT_ANSWER: "submit_answer",
});
// Used when connection is rejected
let isRedirecting = false;

// Get access code from URL and establish WebSocket connection
const access_code = getAccessCode();
const ws = new WebSocket(`ws://localhost:8000/ws/meeting/${access_code}/participant/`);

// Timer state
let duration = parseInt(document.getElementById("duration").textContent);
let durationInSeconds = duration * 60;
let countdownInterval;

// Keeps track of current question
currentQuestion = null

// WebSocket event handlers
ws.onopen = function(event) {
    console.log('Participant WebSocket connected');
    updateStatus('Connected - Waiting for meeting to start...');
};

ws.onmessage = function(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('Participant received:', data);
        
        handleMessage(data);
    } catch (error) {
        console.error('Error parsing message:', error);
    }
};

ws.onclose = function(event) {
    console.log("Close event fired!");
    console.log("Close code:", event.code);
    console.log("Close reason:", event.reason);
    
    if (event.code === 4401 && !isRedirecting) {
        isRedirecting = true;
        const redirect_url = "/meeting/locked"
        console.log("Redirecting to:", redirect_url);
        window.location.replace(redirect_url);
    } else if (event.code !== 4401) {
        console.log('Participant WebSocket disconnected');
        updateStatus('Disconnected');
        pauseCountdown();
    }
};

ws.onerror = function(error) {
    console.error('Participant WebSocket error:', error);
    updateStatus('Connection error');
};

// Message handling
function handleMessage(data) {
    switch (data.type) {
        case MessageTypes.START_MEETING:
            handleMeetingStart(data);
            break;
        case MessageTypes.NEXT_QUESTION:
            handleNextQuestion(data);
            break;
        case MessageTypes.END_MEETING:
            handleMeetingEnd(data);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

function handleMeetingStart(data) {
    if (data.question) {
        currentQuestion = data.question
        updateStatus('Meeting in progress');
        updateQuestion(data.question);
        enableAnswerForm();
        startCountdown();
    }
}

function handleNextQuestion(data) {
    if (data.question) {
        currentQuestion = data.question
        updateQuestion(data.question);
        enableAnswerForm();
        resetSubmitButton();
    }
}

function handleMeetingEnd(data) {
    url = data.url
    console.log("Meeting ended")
    console.log("Redirecting to:", url);
    setTimeout(() => {
        window.location.replace(url);
    }, 200); // Delay to allow backend to finish
    window.location.replace(url);
}

// Form handling
document.getElementById('answer-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const answer = document.getElementById('answer-input').value.trim();
    if (answer) {
        submitAnswer(answer);
    }
});

function submitAnswer(answer) {
    const message = {
        type: MessageTypes.SUBMIT_ANSWER,
        answer: answer,
        question: currentQuestion
    };
    
    sendMessage(message);
    handleAnswerSubmitted();
}

function sendMessage(message) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
    } else {
        console.error('WebSocket is not open');
    }
}

// UI management functions
function updateStatus(message) {
    document.getElementById('meeting-status').textContent = message;
}

function updateQuestion(question) {
    document.getElementById('current-question').textContent = question;
}

function enableAnswerForm() {
    document.getElementById('answer-input').disabled = false;
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('answer-input').value = '';
    document.getElementById('answer-input').focus();
}

function disableAnswerForm() {
    document.getElementById('answer-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;
}

function handleAnswerSubmitted() {
    document.getElementById('answer-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('submit-btn').textContent = 'Answer Submitted';
}

function resetSubmitButton() {
    document.getElementById('submit-btn').disabled = false;
    document.getElementById('submit-btn').textContent = 'Submit Answer';
}

// Countdown timer functions
function startCountdown() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    
    countdownInterval = setInterval(() => {
        if (durationInSeconds <= 0) {
            clearInterval(countdownInterval);
            document.getElementById('duration').textContent = "Time's up!";
            return;
        }
        
        const minutes = Math.floor(durationInSeconds / 60);
        const seconds = durationInSeconds % 60;
        const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        document.getElementById('duration').textContent = timeString;
        durationInSeconds--;
    }, 1000);
}

function pauseCountdown() {
    if (countdownInterval) {
        clearInterval(countdownInterval);
        countdownInterval = null;
    }
}

// Utility functions
function getAccessCode() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[2];
}