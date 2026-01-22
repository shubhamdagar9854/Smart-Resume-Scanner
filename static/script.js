document.addEventListener('DOMContentLoaded', () => {
    const resumeForm = document.getElementById('resumeForm');
    const resumeInput = document.getElementById('resume_file');
    const fileNameDisplay = document.getElementById('fileName');

    resumeInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = 'Selected: ' + e.target.files[0].name;
        }
    });

    resumeForm.addEventListener('submit', (e) => {
        const btn = resumeForm.querySelector('button');
        btn.textContent = "Uploading... Please wait";
        
        // Button ko foran disable MAT karo, warna request block ho sakti hai
        // 100ms ka delay browser ko request bhejne mein madad karega
        setTimeout(() => {
            btn.style.opacity = "0.5";
            btn.style.cursor = "not-allowed";
        }, 100);
    });
});