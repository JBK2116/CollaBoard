/*
Used to route websocket messages to the appropriate handler.
Must match the defined values in `meeting_host.js`
*/

const MessageTypes = Object.freeze({
    START_MEETING: "start_meeting",
    END_MEETING: "end_meeting",
    NEXT_QUESTION: "next_question",
    SUBMIT_ANSWER: "submit_answer",
});

// Handle the duration countdown
let duration = parseInt(document.getElementById("duration").textContent);
let durationInSeconds = duration * 60;
let countdownInterval;

// Access code passed and received during websocket connections
const access_code = getAccessCode()
const ws = new WebSocket(`ws://localhost:8000/ws/meeting/${access_code}/participant/`);

ws.onopen = function(event) {
    console.log('WebSocket connected');
    document.getElementById('meeting-status').textContent = 'Connected - Waiting for meeting to start...';
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    // Placeholder message handling
    if (data.type === MessageTypes.START_MEETING) {
        initializeStartMeetingUI(data)
    }
    
    if (data.type === MessageTypes.NEXT_QUESTION) {
        handleNextQuestionUI(data)
    }
    
    if (data.type === MessageTypes.END_MEETING) {
        handleMeetingEndedUI()
    }
};

ws.onclose = function(event) {
    console.log('WebSocket disconnected');
    document.getElementById('meeting-status').textContent = 'Disconnected';
};

ws.onerror = function(error) {
    console.log('WebSocket error:', error);
    document.getElementById('meeting-status').textContent = 'Connection error';
};

// Form submission for answering questions
document.getElementById('answer-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const answer = document.getElementById('answer-input').value.trim();
    
    if (answer) {
        ws.send(JSON.stringify({
            'type': MessageTypes.SUBMIT_ANSWER,
            'answer': answer
        }));
        handlePostSubmissionUI()
    }
});

// BELOW ARE THE UI HANDLING FUNCTIONS
function initializeStartMeetingUI(data) {
        document.getElementById('meeting-status').textContent = 'Meeting in progress';
        document.getElementById('current-question').textContent = `Question: ${data.question}`;
        document.getElementById('answer-input').value = '';
        document.getElementById('answer-input').disabled = false;
        document.getElementById('submit-btn').disabled = false;
        startCountdown()
    }

function handleNextQuestionUI(data) {
    document.getElementById('current-question').textContent = `Question: ${data.question}`;
    document.getElementById('answer-input').value = '';
    document.getElementById('answer-input').disabled = false;
    document.getElementById('submit-btn').disabled = false;
}

function handlePostSubmissionUI() {
    document.getElementById('answer-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('submit-btn').textContent = 'Answer Submitted';
}
function handleMeetingEndedUI() {
    document.getElementById('meeting-status').textContent = 'Meeting ended';
    document.getElementById('answer-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;
    pauseCountdown()
}

// BELOW ARE THE UTIL FUNCTIONS
function getAccessCode() {
    // Assuming url is http(s):://domainname/meeting/access_code/participant/
    const pathParts = window.location.pathname.split('/');
    const access_code = pathParts[2]
    return access_code
}

// THESE SET OF FUNCTIONS HANDLE COUNTDOWN FORMATTING
function startCountdown() {
    // Clear any existing interval first
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    
    countdownInterval = setInterval(() => {
        if (durationInSeconds <= 0) {
            // Time's up!
            clearInterval(countdownInterval);
            document.getElementById('duration').textContent = "Time's up!";
            return;
        }
        
        // Calculate minutes and seconds remaining
        const minutes = Math.floor(durationInSeconds / 60);
        const seconds = durationInSeconds % 60;
        
        // Format as MM:SS
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

function resumeCountdown() {
    startCountdown();
}


