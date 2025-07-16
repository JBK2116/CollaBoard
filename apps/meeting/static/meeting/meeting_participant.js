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
    if (data.type === 'meeting_started') {
        document.getElementById('meeting-status').textContent = 'Meeting in progress';
        document.getElementById('current-question').textContent = `Question: ${data.question}`;
        document.getElementById('answer-input').value = '';
        document.getElementById('answer-input').disabled = false;
        document.getElementById('submit-btn').disabled = false;
    }
    
    if (data.type === 'new_question') {
        document.getElementById('current-question').textContent = `Question: ${data.question}`;
        document.getElementById('answer-input').value = '';
        document.getElementById('answer-input').disabled = false;
        document.getElementById('submit-btn').disabled = false;
    }
    
    if (data.type === 'meeting_ended') {
        document.getElementById('meeting-status').textContent = 'Meeting ended';
        document.getElementById('answer-input').disabled = true;
        document.getElementById('submit-btn').disabled = true;
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
            'type': 'submit_answer',
            'answer': answer
        }));
        
        // Disable input after submission
        document.getElementById('answer-input').disabled = true;
        document.getElementById('submit-btn').disabled = true;
        document.getElementById('submit-btn').textContent = 'Answer Submitted';
    }
});

// Timer placeholder - will be updated via WebSocket
let duration = 0;
setInterval(() => {
    document.getElementById('duration').textContent = duration;
}, 1000);
