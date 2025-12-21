// Show selected file name
document.getElementById('resume').addEventListener('change', (e) => {
    const fileName = document.getElementById('fileName');
    fileName.textContent = e.target.files[0] ? 'Selected: ' + e.target.files[0].name : '';
});

// Optional: client-side size check (16MB)
document.getElementById('resumeForm').addEventListener('submit', (e) => {
    const file = document.getElementById('resume').files[0];
    if (file && file.size > 16 * 1024 * 1024) {
        e.preventDefault();
        alert('File size must be 16MB or less.');
    }
});
