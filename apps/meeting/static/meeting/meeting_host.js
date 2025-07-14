// WebSocket connection placeholder
const meetingID = None; // Parse this from the url;
const accessCode = None; //Get this from an element;
const ws = new WebSocket(`ws://localhost:8000/ws/meeting/${meetingID}/host/`);

let currentQuestionIndex = 0;
let totalQuestions = None; // Get this from an element
let meetingStarted = false;
let participants = [];

// Sample questions for testing (replace with actual data)
const questions = [
    "What is your name?",
    "How did you hear about this meeting?",
    "What are your expectations for today?"
];

ws.onopen = function(event) {
    console.log('Host WebSocket connected');
    document.getElementById('meeting-status').textContent = 'Connected - Ready to start';
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Host received:', data);
    
    // Placeholder message handling
    if (data.type === 'participant_joined') {
        participants.push(data.participant);
        updateParticipantCount();
        updateParticipantsList();
    }
    
    if (data.type === 'participant_left') {
        participants = participants.filter(p => p.id !== data.participant_id);
        updateParticipantCount();
        updateParticipantsList();
    }
    
    if (data.type === 'answer_submitted') {
        console.log('Answer received:', data.answer);
        // Update participant status in the list
        updateParticipantAnswer(data.participant_id, data.answer);
    }
};

ws.onclose = function(event) {
    console.log('Host WebSocket disconnected');
    document.getElementById('meeting-status').textContent = 'Disconnected';
};

ws.onerror = function(error) {
    console.log('Host WebSocket error:', error);
    document.getElementById('meeting-status').textContent = 'Connection error';
};

// Button event listeners
document.getElementById('start-btn').addEventListener('click', function() {
    if (!meetingStarted) {
        meetingStarted = true;
        currentQuestionIndex = 0;
        
        ws.send(JSON.stringify({
            'type': 'start_meeting',
            'access_code': accessCode
        }));
        
        showCurrentQuestion();
        
        document.getElementById('start-btn').disabled = true;
        document.getElementById('next-btn').disabled = false;
        document.getElementById('end-btn').disabled = false;
        document.getElementById('meeting-status').textContent = 'Meeting in progress';
    }
});

document.getElementById('next-btn').addEventListener('click', function() {
    if (currentQuestionIndex < totalQuestions - 1) {
        currentQuestionIndex++;
        showCurrentQuestion();
        
        ws.send(JSON.stringify({
            'type': 'next_question',
            'question': questions[currentQuestionIndex] || `Question ${currentQuestionIndex + 1}`,
            'question_number': currentQuestionIndex + 1
        }));
        
        if (currentQuestionIndex >= totalQuestions - 1) {
            document.getElementById('next-btn').disabled = true;
        }
    }
});

document.getElementById('end-btn').addEventListener('click', function() {
    ws.send(JSON.stringify({
        'type': 'end_meeting'
    }));
    
    document.getElementById('start-btn').disabled = true;
    document.getElementById('next-btn').disabled = true;
    document.getElementById('end-btn').disabled = true;
    document.getElementById('meeting-status').textContent = 'Meeting ended';
});

function showCurrentQuestion() {
    document.getElementById('current-question-num').textContent = currentQuestionIndex + 1;
    document.getElementById('question-text').textContent = questions[currentQuestionIndex] || `Question ${currentQuestionIndex + 1}`;
}

function updateParticipantCount() {
    document.getElementById('participant-count').textContent = participants.length;
}

function updateParticipantsList() {
    const listElement = document.getElementById('participants-list');
    if (participants.length === 0) {
        listElement.innerHTML = '<p class="status">No participants yet</p>';
    } else {
        listElement.innerHTML = participants.map(p => 
            `<p>Participant ${p.id} - <span class="status">${p.status || 'Waiting'}</span></p>`
        ).join('');
    }
}

function updateParticipantAnswer(participantId, answer) {
    const participant = participants.find(p => p.id === participantId);
    if (participant) {
        participant.status = 'Answered';
        updateParticipantsList();
    }
}

// Timer placeholder
let duration = 0;
setInterval(() => {
    if (meetingStarted) {
        duration++;
    }
    document.getElementById('duration').textContent = duration;
}, 1000);
