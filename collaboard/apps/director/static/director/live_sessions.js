// ===========================================
// LIVE SESSIONS PAGE - JOIN MEETING JS
// ===========================================

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const accessCodeForm = document.getElementById('accessCodeForm');
    const accessCodeInput = document.getElementById('accessCode');
    const codeError = document.getElementById('codeError');

    // Form Submission Handler
    accessCodeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const code = accessCodeInput.value;
        // Basic validation
        if (code.length !== 8 || !/^\d{8}$/.test(code)) {
            codeError.textContent = 'Please enter a valid 8-digit code';
            return;
        }
        // Redirect to the join meeting URL
        window.location.href = `/meeting/join/${code}/`;
    });

    // Real-time Code Validation
    accessCodeInput.addEventListener('input', function(e) {
        const code = e.target.value;
        // Only allow numbers
        e.target.value = code.replace(/\D/g, '');
        if (code.length === 8) {
            codeError.textContent = '';
        }
    });
}); 