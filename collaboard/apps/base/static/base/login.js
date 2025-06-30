// ===========================================
// LOGIN PAGE - JAVASCRIPT
// ===========================================

// DOM Elements
const passwordToggle = document.getElementById('passwordToggle');
const passwordInput = document.getElementById('password');
const eyeIcon = passwordToggle.querySelector('.eye-icon');
const eyeOffIcon = passwordToggle.querySelector('.eye-off-icon');
const loginForm = document.getElementById('loginForm');
const submitBtn = loginForm.querySelector('button[type="submit"]');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');
const emailInput = document.getElementById('email');

// Password Visibility Toggle
passwordToggle.addEventListener('click', function() {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    // Toggle icon visibility
    if (type === 'text') {
        eyeIcon.style.display = 'none';
        eyeOffIcon.style.display = 'block';
    } else {
        eyeIcon.style.display = 'block';
        eyeOffIcon.style.display = 'none';
    }
});

// Form Submission with Loading State
loginForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Show loading state
    submitBtn.classList.add('loading');
    btnText.style.display = 'none';
    btnLoading.style.display = 'block';
    
    // DJANGO-INTEGRATION: Submit form to Django view
    // This will be handled by Django form processing
    console.log('Form submitted - Django will handle authentication');
    
    // Simulate form submission (remove in Django implementation)
    setTimeout(() => {
        submitBtn.classList.remove('loading');
        btnText.style.display = 'block';
        btnLoading.style.display = 'none';
    }, 2000);
});

// Real-time Validation Feedback
emailInput.addEventListener('input', function() {
    const emailError = document.getElementById('emailError');
    if (this.validity.valid) {
        emailError.textContent = '';
    } else if (this.validity.typeMismatch) {
        emailError.textContent = 'Please enter a valid email address';
    }
});

passwordInput.addEventListener('input', function() {
    const passwordError = document.getElementById('passwordError');
    if (this.validity.valid) {
        passwordError.textContent = '';
    } else if (this.validity.valueMissing) {
        passwordError.textContent = 'Password is required';
    }
}); 