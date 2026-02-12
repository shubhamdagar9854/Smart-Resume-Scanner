// Admin Dashboard JavaScript

// Page load hone par
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Dashboard loaded');
    
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
    
    // Filter form validation
    const filterForm = document.querySelector('.filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            const input = this.querySelector('input[name="post_type"]');
            if (input && input.value.trim() === '') {
                // If empty, show all resumes (let form submit normally)
                return true;
            }
        });
    }
    
    // Generate summary button click handler
    const generateButtons = document.querySelectorAll('.generate-btn');
    generateButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            // Show loading state
            const originalText = this.textContent;
            this.textContent = 'Generating...';
            this.style.opacity = '0.6';
            this.style.cursor = 'wait';
            
            // If user clicks again, prevent multiple requests
            if (this.dataset.processing === 'true') {
                e.preventDefault();
                return false;
            }
            
            this.dataset.processing = 'true';
        });
    });
});

