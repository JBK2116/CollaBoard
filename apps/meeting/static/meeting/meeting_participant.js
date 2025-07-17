// Used to route websocket messages received from the backend
// to the appropriate handler
const MessageTypes = Object.freeze({
    MEETING_STARTED: "meeting_started",
    NEXT_QUESTION: "next_question",
    SUBMIT_ANSWER: "submit_answer",
    MEETING_ENDED: "meeting_ended",
});


// WebSocket connection placeholder
const pathParts = window.location.pathname.split('/');
// pathParts = ["", "meeting", "access_code", "host", ""]
// Assuming url is http(s):://domainname/meeting/access_code/participant/
const access_code = pathParts[2] // Parse this from the url
const ws = new WebSocket(`ws://localhost:8000/ws/meeting/${access_code}/participant/`);

ws.onopen = function(event) {
    console.log('WebSocket connected');
    document.getElementById('meeting-status').textContent = 'Connected - Waiting for meeting to start...';
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    // Placeholder message handling
    if (data.type === MessageTypes.MEETING_STARTED) {
        handleMeetingStarted()
    }
    
    if (data.type === MessageTypes.NEXT_QUESTION) {
        handleNextQuestion()
    }
    
    if (data.type === MessageTypes.MEETING_ENDED) {
        handleMeetingEnded()
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

// Form submission
document.getElementById('answer-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const answer = document.getElementById('answer-input').value.trim();
    
    if (answer) {
        ws.send(JSON.stringify({
            'type': MessageTypes.SUBMIT_ANSWER,
            'answer': answer
        }));
        handlePostSubmission()
    }
});

function handleMeetingStarted() {
        document.getElementById('meeting-status').textContent = 'Meeting in progress';
        document.getElementById('current-question').textContent = `Question: ${data.question}`;
        document.getElementById('answer-input').value = '';
        document.getElementById('answer-input').disabled = false;
        document.getElementById('submit-btn').disabled = false;
    }

function handleNextQuestion() {
    document.getElementById('current-question').textContent = `Question: ${data.question}`;
    document.getElementById('answer-input').value = '';
    document.getElementById('answer-input').disabled = false;
    document.getElementById('submit-btn').disabled = false;
}

function handlePostSubmission() {
    document.getElementById('answer-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('submit-btn').textContent = 'Answer Submitted';
}
function handleMeetingEnded() {
    document.getElementById('meeting-status').textContent = 'Meeting ended';
    document.getElementById('answer-input').disabled = true;
    document.getElementById('submit-btn').disabled = true;
}

// Timer placeholder - will be updated via WebSocket
let duration = 0;
setInterval(() => {
    document.getElementById('duration').textContent = duration;
}, 1000);
