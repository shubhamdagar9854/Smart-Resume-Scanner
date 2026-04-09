// Load jobs when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadJobs();
});

document.getElementById('addJobForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const title = document.getElementById('jobTitle').value;
    const requirements = document.getElementById('jobRequirements').value;

    fetch('/api/add_job', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title, requirements: requirements })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            // ✅ Alert ke baad seedhe matches dikhayenge
            alert('✅ Job post added! Searching for candidates...');
            
            // Yahan hum nayi banyi hui Job ka ID use karke viewMatches call karenge
            // Note: Backend se 'job_id' aana zaroori hai
            if(data.job_id) {
                viewMatches(data.job_id, title);
            }
            
            document.getElementById('addJobForm').reset();
        } else {
            alert('❌ Error adding job post');
        }
    })
    .catch(error => console.error('Error:', error));
});

// loadJobs() function ko delete kar sakte hain kyunki ab humein list nahi chahiye
// Load all jobs
function loadJobs() {
    fetch('/api/get_jobs')
    .then(response => response.json())
    .then(data => {
        const container = document.getElementById('jobsContainer');
        
        if(data.jobs && data.jobs.length > 0) {
            container.innerHTML = '';
            data.jobs.forEach(job => {
                container.innerHTML += createJobCard(job);
            });
        } else {
            container.innerHTML = '<div class="no-matches">No job posts available. Add one above!</div>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('jobsContainer').innerHTML = '<div class="no-matches">❌ Error loading jobs</div>';
    });
}

// Create job card (WITHOUT matches inside)
function createJobCard(job) {
    return `<div class="job-item">
        <div class="job-header">
            <div class="job-title">${job.title}</div>
            <button class="btn btn-success" onclick="viewMatches(${job.id}, '${job.title}')">
                👥 View Matches
            </button>
        </div>
        <div class="job-requirements">
            <strong>Requirements:</strong> ${job.requirements}
        </div>
    </div>`;
}

// 🔥 IS FUNCTION KO UPDATE KAREIN
function viewMatches(jobId, jobTitle) {
    const matchesSection = document.getElementById('matchesSection');
    const matchesContainer = document.getElementById('matchesContainer');
    const matchesTitle = document.getElementById('matchesTitle');

    matchesSection.style.display = 'block'; // Ensure it's visible
    matchesSection.classList.add('active');
    matchesTitle.textContent = `🎯 Matches for "${jobTitle}"`;
    matchesContainer.innerHTML = '<div class="loading">⏳ Searching candidates...</div>';

    fetch(`/api/get_matches/${jobId}`)
        .then(res => {
            if (res.status === 401) throw new Error("Please login again!");
            return res.json();
        })
        .then(data => {
            matchesContainer.innerHTML = '';
            if (!data || data.length === 0) {
                matchesContainer.innerHTML = '<div class="no-matches">No candidates match these requirements.</div>';
                return;
            }
            // Data dikhane ke liye cards banayein
            data.forEach(candidate => {
                matchesContainer.innerHTML += createCandidateCard(candidate);
            });
        })
        .catch(err => {
            matchesContainer.innerHTML = `<div class="no-matches">❌ Error: ${err.message}</div>`;
        });
}

// Create candidate card with match percentage
function createCandidateCard(candidate) {
    // Determine badge color based on match percentage
    let badgeClass = 'match-low';
    if(candidate.match_percent >= 70) {
        badgeClass = 'match-high';
    } else if(candidate.match_percent >= 40) {
        badgeClass = 'match-medium';
    }

    return `<div class="candidate-card">
        <div class="candidate-header">
            <div class="candidate-name">👤 ${candidate.name}</div>
            <div class="match-badge ${badgeClass}">
                ${candidate.match_percent}% Match
            </div>
        </div>
        <div class="candidate-email">
            📧 Email: ${candidate.email}
        </div>
        <div class="candidate-summary">
            <strong>📄 Resume Summary:</strong><br>
            ${candidate.summary || 'No summary available'}
        </div>
    </div>`;
}