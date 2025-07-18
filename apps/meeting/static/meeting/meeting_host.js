/*
Used to route websocket messages to the appropriate handler.
Must match the defined values in `meeting_participant.js`
*/
const MessageTypes = Object.freeze({
    START_MEETING: "start_meeting",
    END_MEETING: "end_meeting",
    NEXT_QUESTION: "next_question",
    ANSWER_SUBMITTED: "answer_submitted",
    PARTICIPANT_JOINED: "participant_joined",
    PARTICIPANT_LEFT: "participant_left",
});
const COOKIE_NAME = "sessionid"
const meeting_id = getMeetingID();

// Get session ID from cookies
const sessionId = getCookie(COOKIE_NAME);

// IN PROD, DO NOT pass the sessionID via a url query
const ws = new WebSocket(`ws://localhost:8000/ws/meeting/${meeting_id}/host/?session=${sessionId}`);

// Values NEEDED for meeting functionality
let accessCode = null;
let meetingStarted = false;
let participants = [];

// Question Handling...
const meetingQuestions = [];
let totalMeetingQuestions = null;
let currentQuestionIndex = 0;

// Handle the duration countdown
let duration = parseInt(document.getElementById("duration").textContent);
let durationInSeconds = duration * 60;
let countdownInterval;


ws.onopen = function(event) {
    console.log('Host WebSocket connected');
    document.getElementById('meeting-status').textContent = 'Connected - Loading questions...';
    // Keep start button disabled until all questions are received
    document.getElementById('start-btn').disabled = true;
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Host received:', data);
    
    // Message handling
    if (data.type === MessageTypes.START_MEETING) {
        // This will be the first payload received after the first connection
        for (const question of data.questions) {
            meetingQuestions.push(question)
            console.log(question)
        }
        totalMeetingQuestions = meetingQuestions.length
        accessCode = data.access_code
        console.log(accessCode)
        initializeStartMeetingUI()
    }
    if (data.type === MessageTypes.PARTICIPANT_JOINED) {
        // This will be the second payload received after the first connection
        participants.push(data.participant);
        updateParticipantCount();
        updateParticipantsList();
    }
    
    if (data.type === MessageTypes.PARTICIPANT_LEFT) {
        // This payload can be received at random.
        participants = participants.filter(p => p.id !== data.id);
        console.log(data)
        updateParticipantCount();
        updateParticipantsList();
    }
    
    if (data.type === 'answer_submitted') {
        // This payload will be received at most, once per user per question
        console.log('Answer received:', data.answer);
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

// BUTTON EVENT LISTENERS
document.getElementById('start-btn').addEventListener('click', function() {
    if (!meetingStarted) {
        meetingStarted = true;
        currentQuestionIndex = 0;
        
        ws.send(JSON.stringify({
            'type': MessageTypes.START_MEETING,
            'question': meetingQuestions[0],
            'access_code': accessCode
        }));
        handleStartMeetingUI()
    }
});

document.getElementById('next-btn').addEventListener('click', function() {
    if (currentQuestionIndex < totalMeetingQuestions - 1) {
        currentQuestionIndex++;
        showCurrentQuestion();
        
        ws.send(JSON.stringify({
            'type': MessageTypes.NEXT_QUESTION,
            'access_code': accessCode,
            'question': meetingQuestions[currentQuestionIndex] || `Question ${currentQuestionIndex + 1}`,
            'question_number': currentQuestionIndex + 1
        }));
        
        if (currentQuestionIndex >= totalMeetingQuestions - 1) {
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

// BELOW IS THE USER AUTHENTICATION FUNCTION
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

// BELOW ARE THE PARTICIPANT HANDLING FUNCTIONS
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

// BELOW ARE GENERAL UTIL FUNCTIONS
function getMeetingID() {
    // Assuming url is http(s):://domainname/meeting/meeting_id/host/
    const pathParts = window.location.pathname.split('/');
    return pathParts[2]
}

// BELOW ARE THE UI HANDLING FUNCTIONS
function handleStartMeetingUI() {
    showCurrentQuestion();
    document.getElementById('start-btn').disabled = true;
    document.getElementById('next-btn').disabled = false;
    document.getElementById('end-btn').disabled = false;
    document.getElementById('meeting-status').textContent = 'Meeting in progress';
    startCountdown()
}

function initializeStartMeetingUI() {
    showCurrentQuestion()
    document.getElementById('start-btn').disabled = false;
    document.getElementById('meeting-status').textContent = 'Ready to start';
}

function showCurrentQuestion() {
    document.getElementById('current-question-num').textContent = currentQuestionIndex + 1;
    document.getElementById('question-text').textContent = meetingQuestions[currentQuestionIndex] || `Question ${currentQuestionIndex + 1}`;
}

function handleEndMeeting() {
    document.getElementById('start-btn').disabled = true;
    document.getElementById('next-btn').disabled = true;
    document.getElementById('end-btn').disabled = true;
    document.getElementById('meeting-status').textContent = 'Meeting ended';
    pauseCountdown()
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