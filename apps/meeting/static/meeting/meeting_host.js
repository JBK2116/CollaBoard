/*
WebSocket message types - must match backend constants
*/
const MessageTypes = Object.freeze({
    START_MEETING: "start_meeting",
    END_MEETING: "end_meeting",
    NEXT_QUESTION: "next_question",
    SUBMIT_ANSWER: "submit_answer",
    PARTICIPANT_JOINED: "participant_joined",
    PARTICIPANT_LEFT: "participant_left",
    ANSWER_SUBMITTED: "answer_submitted", // Add this new message type
});

const COOKIE_NAME = "sessionid";
const meeting_id = getMeetingID();
const sessionId = getCookie(COOKIE_NAME);

// WebSocket connection
const ws = new WebSocket(`ws://localhost:8000/ws/meeting/${meeting_id}/host/?session=${sessionId}`);

// Meeting state
let accessCode = null;
let meetingStarted = false;
let participants = [];
let meetingQuestions = [];
let totalMeetingQuestions = 0;
let currentQuestionIndex = 0;

// Timer state
let duration = parseInt(document.getElementById("duration").textContent);
let durationInSeconds = duration * 60;
let countdownInterval;

// Handles tracking answer submission
let totalSubmissions = 0;

// WebSocket event handlers
ws.onopen = function(event) {
    console.log('Host WebSocket connected');
    updateStatus('Connected - Loading questions...');
    disableButton('start-btn', true);
};

ws.onmessage = function(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('Host received:', data);
        
        handleMessage(data);
    } catch (error) {
        console.error('Error parsing message:', error);
    }
};

ws.onclose = function(event) {
    console.log('Host WebSocket disconnected');
    updateStatus('Disconnected');
    pauseCountdown();
};

ws.onerror = function(error) {
    console.error('Host WebSocket error:', error);
    updateStatus('Connection error');
};

// Message handling
function handleMessage(data) {
    switch (data.type) {
        case MessageTypes.START_MEETING:
            handleInitialMeetingData(data);
            break;
        case MessageTypes.PARTICIPANT_JOINED:
            handleParticipantJoined(data);
            break;
        case MessageTypes.PARTICIPANT_LEFT:
            handleParticipantLeft(data);
            break;
        case MessageTypes.ANSWER_SUBMITTED:
            handleAnswerSubmitted(data);
            break;
        default:
            console.log('Unknown message type:', data.type);
    }
}

function handleInitialMeetingData(data) {
    if (data.questions && data.access_code) {
        meetingQuestions = [...data.questions];
        totalMeetingQuestions = meetingQuestions.length;
        accessCode = data.access_code;
        
        console.log(`Loaded ${totalMeetingQuestions} questions for meeting ${accessCode}`);
        
        initializeMeetingUI();
    }
}

function handleParticipantJoined(data) {
    if (data.participant) {
        participants.push(data.participant);
        updateParticipantDisplay();
        updateSubmissionTracker(); // Update tracker when participants change
        console.log('Participant joined:', data.participant.id);
    }
}

function handleParticipantLeft(data) {
    if (data.id) {
        // Find the participant and update their status instead of removing them
        const participant = participants.find(p => p.id === data.id);
        if (participant) {
            participant.status = 'Disconnected';
        }
        
        // Update participant count to only count connected participants
        const connectedCount = participants.filter(p => p.status !== 'Disconnected').length;
        document.getElementById('participant-count').textContent = connectedCount;
        
        // Update the display to show all participants with their current status
        updateParticipantDisplay();
        updateSubmissionTracker(); // Update tracker when participants change
        console.log('Participant disconnected:', data.id);
    }
}

function handleAnswerSubmitted(data) {
    totalSubmissions++;
    updateSubmissionTracker();
    console.log(`Answer submitted. Total: ${totalSubmissions}`);
}

// Button event listeners
document.getElementById('start-btn').addEventListener('click', function() {
    if (!meetingStarted && meetingQuestions.length > 0) {
        startMeeting();
    }
});

document.getElementById('next-btn').addEventListener('click', function() {
    if (currentQuestionIndex < totalMeetingQuestions - 1) {
        nextQuestion();
    }
});

document.getElementById('end-btn').addEventListener('click', function() {
    endMeeting();
});

// Meeting control functions
function startMeeting() {
    meetingStarted = true;
    currentQuestionIndex = 0;
    totalSubmissions = 0; // Reset submissions for new meeting
    
    const message = {
        type: MessageTypes.START_MEETING,
        question: meetingQuestions[0],
        access_code: accessCode
    };
    
    sendMessage(message);
    updateMeetingUI();
    updateStatus('Meeting in progress');
}

function nextQuestion() {
    currentQuestionIndex++;
    totalSubmissions = 0; // Reset submissions for new question
    
    const message = {
        type: MessageTypes.NEXT_QUESTION,
        access_code: accessCode,
        question: meetingQuestions[currentQuestionIndex],
        question_number: currentQuestionIndex + 1
    };
    
    sendMessage(message);
    updateQuestionDisplay();
    updateSubmissionTracker(); // Update tracker for new question
    
    // Disable next button if this is the last question
    if (currentQuestionIndex >= totalMeetingQuestions - 1) {
        disableButton('next-btn', true);
    }
}

function endMeeting() {
    const message = {
        type: MessageTypes.END_MEETING
    };
    
    sendMessage(message);
    handleMeetingEnd();
}

function sendMessage(message) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
    } else {
        console.error('WebSocket is not open');
    }
}

// UI management functions
function initializeMeetingUI() {
    updateQuestionDisplay();
    updateSubmissionTracker();
    disableButton('start-btn', false);
    updateStatus('Ready to start');
}

function updateMeetingUI() {
    updateQuestionDisplay();
    updateSubmissionTracker();
    disableButton('start-btn', true);
    disableButton('next-btn', false);
    disableButton('end-btn', false);
    startCountdown();
}

function handleMeetingEnd() {
    disableButton('start-btn', true);
    disableButton('next-btn', true);
    disableButton('end-btn', true);
    updateStatus('Meeting ended');
    pauseCountdown();
}

function updateQuestionDisplay() {
    const questionNum = currentQuestionIndex + 1;
    const questionText = meetingQuestions[currentQuestionIndex] || `Question ${questionNum}`;
    
    document.getElementById('current-question-num').textContent = questionNum;
    document.getElementById('question-text').textContent = questionText;
}

function updateSubmissionTracker() {
    const connectedCount = participants.filter(p => p.status !== 'Disconnected').length;
    const submissionElement = document.getElementById('submission-count');
    
    if (submissionElement) {
        submissionElement.textContent = `${totalSubmissions} / ${connectedCount}`;
        
        // Add visual feedback for completion percentage
        const percentage = connectedCount > 0 ? (totalSubmissions / connectedCount) * 100 : 0;
        const progressBar = document.getElementById('submission-progress');
        if (progressBar) {
            progressBar.style.width = `${Math.min(percentage, 100)}%`;
        }
    }
}

function updateParticipantDisplay() {
    // Count only connected participants for the main counter
    const connectedCount = participants.filter(p => p.status !== 'Disconnected').length;
    document.getElementById('participant-count').textContent = connectedCount;
    
    const listElement = document.getElementById('participants-list');
    if (participants.length === 0) {
        listElement.innerHTML = '<p class="status">No participants yet</p>';
    } else {
        listElement.innerHTML = participants.map(p => 
            `<p>
                <span class="participant-name">${p.name}</span>
                <span class="connection-status ${p.status === 'Disconnected' ? 'disconnected' : 'connected'}">${p.status || 'Connected'}</span>
            </p>`
        ).join('');
    }
}

function updateStatus(message) {
    document.getElementById('meeting-status').textContent = message;
}

function disableButton(buttonId, disabled) {
    document.getElementById(buttonId).disabled = disabled;
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

function getMeetingID() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[2];
}