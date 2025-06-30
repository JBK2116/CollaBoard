// ===========================================
// REGISTER PAGE - JAVASCRIPT
// ===========================================

// DOM Elements
const passwordToggle = document.getElementById('passwordToggle');
const passwordInput = document.getElementById('password');
const eyeIcon = passwordToggle.querySelector('.eye-icon');
const eyeOffIcon = passwordToggle.querySelector('.eye-off-icon');
const strengthProgress = document.getElementById('strengthProgress');
const strengthText = document.getElementById('strengthText');
const requirements = document.querySelectorAll('.requirement');
const registerForm = document.getElementById('registerForm');
const submitBtn = registerForm.querySelector('button[type="submit"]');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');

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

// Password Strength Indicator
function checkPasswordStrength(password) {
    let score = 0;
    const checks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password)
    };

    // Update requirement indicators
    requirements.forEach(req => {
        const requirement = req.dataset.requirement;
        const icon = req.querySelector('.requirement-icon');
        
        if (checks[requirement]) {
            req.classList.add('met');
            icon.style.display = 'block';
        } else {
            req.classList.remove('met');
            icon.style.display = 'none';
        }
    });

    // Calculate score
    Object.values(checks).forEach(check => {
        if (check) score++;
    });

    // Update strength bar and text
    const percentage = (score / 4) * 100;
    strengthProgress.style.width = percentage + '%';
    
    if (score === 0) {
        strengthProgress.className = 'strength-progress';
        strengthText.textContent = 'Password strength';
    } else if (score <= 2) {
        strengthProgress.className = 'strength-progress weak';
        strengthText.textContent = 'Weak';
    } else if (score === 3) {
        strengthProgress.className = 'strength-progress medium';
        strengthText.textContent = 'Medium';
    } else {
        strengthProgress.className = 'strength-progress strong';
        strengthText.textContent = 'Strong';
    }
}

passwordInput.addEventListener('input', function() {
    checkPasswordStrength(this.value);
});

// Form Submission with Loading State
registerForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Show loading state
    submitBtn.classList.add('loading');
    btnText.style.display = 'none';
    btnLoading.style.display = 'block';
    
    // DJANGO-INTEGRATION: Submit form to Django view
    // This will be handled by Django form processing
    console.log('Form submitted - Django will handle registration');
    
    // Simulate form submission (remove in Django implementation)
    setTimeout(() => {
        submitBtn.classList.remove('loading');
        btnText.style.display = 'block';
        btnLoading.style.display = 'none';
    }, 2000);
});

// Real-time Validation Feedback
const inputs = ['firstName', 'lastName', 'email', 'password'];

inputs.forEach(inputId => {
    const input = document.getElementById(inputId);
    const errorDiv = document.getElementById(inputId + 'Error');
    
    input.addEventListener('input', function() {
        if (this.validity.valid) {
            errorDiv.textContent = '';
        } else if (this.validity.valueMissing) {
            errorDiv.textContent = 'This field is required';
        } else if (this.validity.typeMismatch && this.type === 'email') {
            errorDiv.textContent = 'Please enter a valid email address';
        } else if (this.validity.tooShort && this.id === 'password') {
            errorDiv.textContent = 'Password must be at least 8 characters';
        }
    });
}); 