// Used to route websocket messages received from the backend
// to the appropriate handler
const MessageTypes = Object.freeze({
    START_MEETING: "start_meeting",
    END_MEETING: "end_meeting",
    ANSWER_SUBMITTED: "answer_submitted",
    NEXT_QUESTION: "next_question",
    PARTICIPANT_JOINED: "participant_joined",
    PARTICIPANT_LEFT: "participant_left",
    MEETING_ENDED: "meeting_ended",
});
const pathParts = window.location.pathname.split('/');
// pathParts = ["", "meeting", "meeting_id", "host", ""]
// Assuming url is http(s):://domainname/meeting/meeting_id/host/
const meeting_id = pathParts[2];

// Function to get cookie value by name
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

// Get session ID from cookies
const sessionId = getCookie('sessionid');

// Create WebSocket with session as query parameter (most reliable method)
const ws = new WebSocket(`ws://localhost:8000/ws/meeting/${meeting_id}/host/?session=${sessionId}`);
// IN PROD, DO NOT pass the sessionID via a url query

const accessCode = null; // To be 
let currentQuestionIndex = 0;
let totalQuestions = null; // Get this from an element
let meetingStarted = false;
let participants = [];

// Meeting questions: will be filled with info from websocket
const questions = [];

ws.onopen = function(event) {
    console.log('Host WebSocket connected');
    document.getElementById('meeting-status').textContent = 'Connected - Ready to start';
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Host received:', data);
    
    // Message handling
    if (data.type === MessageTypes.START_MEETING) {
        // This will be the first payload received after the first connection
        for (const question of data.questions) {
            questions.push(question)
            console.log(question)
        }
        totalQuestions = questions.length
        accessCode = data.access_code
        console.log(accessCode)
        showCurrentQuestion()
    }
    if (data.type === MessageTypes.PARTICIPANT_JOINED) {
        // This will be the second payload received after the first connection
        participants.push(data.participant);
        updateParticipantCount();
        updateParticipantsList();
    }
    
    if (data.type === MessageTypes.PARTICIPANT_LEFT) {
        // This payload can be received at random.
        // Most of it though will be handled at the end of the meeting
        participants = participants.filter(p => p.id !== data.participant_id);
        updateParticipantCount();
        updateParticipantsList();
    }
    
    if (data.type === 'answer_submitted') {
        // This payload will be received at most, once per user per question
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
            'type': MessageTypes.START_MEETING,
            'question': questions[0],
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
            'type': MessageTypes.NEXT_QUESTION,
            'access_code': accessCode,
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
        'type': MessageTypes.END_MEETING
        // Add more info
    }));
    handleEndMeeting()
});

function handleStartMeeting() {

}

function handleEndMeeting() {
    document.getElementById('start-btn').disabled = true;
    document.getElementById('next-btn').disabled = true;
    document.getElementById('end-btn').disabled = true;
    document.getElementById('meeting-status').textContent = 'Meeting ended';
}

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
            `<p>Participant ${p.name} - <span class="status">${p.status || 'Waiting'}</span></p>`
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
