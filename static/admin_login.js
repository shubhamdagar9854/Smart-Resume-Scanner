// Admin Login JavaScript

// Page load hone par
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Login page loaded');
    
    // Auto-hide flash messages after 5 seconds
    const messages = document.querySelectorAll('.message');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.transition = 'opacity 0.5s';
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
    
    // Form validation
    const loginForm = document.querySelector('form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const username = document.getElementById('username');
            const password = document.getElementById('password');
            
            // Check if fields are empty
            if (username.value.trim() === '' || password.value.trim() === '') {
                e.preventDefault();
                alert('Please fill in all fields!');
                return false;
            }
            
            // Show loading state
            const submitBtn = this.querySelector('.submit-btn');
            if (submitBtn) {
                submitBtn.textContent = 'Logging in...';
                submitBtn.style.opacity = '0.7';
                submitBtn.disabled = true;
            }
        });
    }
    
    // Auto-focus on username field
    const usernameField = document.getElementById('username');
    if (usernameField) {
        usernameField.focus();
    }
    
    // Enter key to submit form
    const passwordField = document.getElementById('password');
    if (passwordField) {
        passwordField.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loginForm.submit();
            }
        });
    }
});

