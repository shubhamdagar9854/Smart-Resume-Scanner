document.addEventListener('DOMContentLoaded', () => {
    const resumeForm = document.getElementById('resumeForm');
    const resumeInput = document.getElementById('resume_file');
    const fileNameDisplay = document.getElementById('fileName');

    // Sirf file ka naam dikhane ke liye
    resumeInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = 'Selected: ' + e.target.files[0].name;
        }
    });

    // Submit par koi e.preventDefault() NAHI hona chahiye
    resumeForm.addEventListener('submit', () => {
        // Sirf button ka text badlein feedback ke liye
        const btn = resumeForm.querySelector('button');
        btn.textContent = "Uploading...";
        btn.disabled = true; 
        
        // Form apne aap submit hoga aur page refresh hoga
    });
});