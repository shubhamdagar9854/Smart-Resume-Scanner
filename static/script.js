document.addEventListener('DOMContentLoaded', () => {
    const resumeForm = document.getElementById('resumeForm');
    const resumeInput = document.getElementById('resume_file');
    const fileNameDisplay = document.getElementById('fileName');

    resumeInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = 'Selected: ' + e.target.files[0].name;
        }
    });

    resumeForm.addEventListener('submit', () => {
        const btn = resumeForm.querySelector('button');
        btn.textContent = "Uploading... Please wait";
        
        // YE LINE HATA DO: btn.disabled = true; 
        // Iski jagah sirf opacity kam kar do taaki click na ho
        btn.style.pointerEvents = "none"; 
        btn.style.opacity = "0.7";
    });
});