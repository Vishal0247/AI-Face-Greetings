const loginScreen = document.getElementById('loginScreen');
const dashboardContent = document.getElementById('dashboardContent');

// --- Global Functions ---
window.deletePerson = async (name) => {
    if (!confirm('Are you sure you want to delete ' + name + ' and all their data?')) return;
    try {
        const res = await fetch('/api/people/' + name, { method: 'DELETE' });
        if (!res.ok) throw new Error("Backend failed to delete");
        loadPeople();
        loadLogs();
    } catch (e) {
        console.error(e);
        alert('Error deleting person. Please try again.');
    }
};

window.deleteLog = async (filename) => {
    if (!confirm('Delete this video log?')) return;
    try {
        const res = await fetch('/api/logs/' + filename, { method: 'DELETE' });
        if (!res.ok) throw new Error("Failed");
        loadLogs();
    } catch (e) {
        console.error(e);
    }
};

window.uploadAudioForPerson = async (name, inputEl) => {
    if (!inputEl.files.length) return;
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('file', inputEl.files[0]);
    
    try {
        const res = await fetch('/upload_audio', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            alert(`✅ Custom audio saved for ${name}!`);
            loadPeople(); // Refresh to update the audio player
        } else {
            alert('❌ ' + (data.message || 'Error uploading audio'));
        }
    } catch (e) {
        console.error(e);
        alert('❌ Error uploading audio');
    }
};

// Store which log folders are collapsed (since they are open by default now)
const openFolders = new Set();
window.toggleLogFolder = (name) => {
    const closedKey = name + "_closed";
    if (openFolders.has(closedKey)) {
        openFolders.delete(closedKey);
    } else {
        openFolders.add(closedKey);
    }
    
    // Force immediate UI update without waiting for next poll
    const folder = document.getElementById(`log-folder-${name}`);
    const arrow = document.getElementById(`log-arrow-${name}`);
    if (folder && arrow) {
        const isClosed = openFolders.has(closedKey);
        folder.style.display = isClosed ? 'none' : 'flex';
        arrow.textContent = isClosed ? '▼ Open' : '▲ Close';
    }
};

window.enlargeVideo = (src) => {
    const modal = document.getElementById('videoModal');
    const modalImg = document.getElementById('modalVideo');
    modalImg.src = src;
    modal.style.display = 'flex';
};

window.closeModal = () => {
    const modal = document.getElementById('videoModal');
    const modalImg = document.getElementById('modalVideo');
    modal.style.display = 'none';
    modalImg.src = '';
};

document.getElementById('clearLogsBtn')?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete ALL recent scan videos?')) return;
    try {
        await fetch('/api/logs_all', { method: 'DELETE' });
        loadLogs();
    } catch (e) {
        console.error(e);
    }
});
const adminPassword = document.getElementById('adminPassword');
const loginBtn = document.getElementById('loginBtn');
const loginError = document.getElementById('loginError');

const peopleGrid = document.getElementById('peopleGrid');
const newPersonName = document.getElementById('newPersonName');
const newPersonPhoto = document.getElementById('newPersonPhoto');
const uploadNewBtn = document.getElementById('uploadNewBtn');
const uploadStatus = document.getElementById('uploadStatus');

// Login Logic
loginBtn.addEventListener('click', async () => {
    // Server-side authentication
    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: adminPassword.value })
        });
        const data = await res.json();
        
        if (data.success) {
            loginScreen.style.display = 'none';
            dashboardContent.style.display = 'block';
            loadPeople();
            loadLogs();
            loadStats();
            // Auto refresh logs every 5 seconds
            setInterval(() => {
                loadLogs();
                loadStats();
            }, 5000);
        } else {
            loginError.style.display = 'block';
        }
    } catch (e) {
        console.error('Login error:', e);
        loginError.textContent = 'Error connecting to server.';
        loginError.style.display = 'block';
    }
});

adminPassword.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') loginBtn.click();
});

// Fetch Stats
async function loadStats() {
    try {
        const response = await fetch('/api/stats?t=' + new Date().getTime());
        const stats = await response.json();
        
        const analyticsRibbon = document.getElementById('analyticsRibbon');
        if (analyticsRibbon) {
            analyticsRibbon.innerHTML = `
                <div class="stat-card">
                    <h3>Total Enrolled</h3>
                    <p class="stat-value">${stats.total_enrolled}</p>
                </div>
                <div class="stat-card">
                    <h3>Scans Today</h3>
                    <p class="stat-value">${stats.scans_today}</p>
                </div>
                <div class="stat-card">
                    <h3>Most Active</h3>
                    <p class="stat-value">${stats.top_user}</p>
                </div>
                <div class="stat-card">
                    <h3>Storage Used</h3>
                    <p class="stat-value">${stats.storage_used}</p>
                </div>
            `;
        }
    } catch (e) {
        console.error("Failed to load stats:", e);
    }
}

// Fetch Enrolled People
async function loadPeople() {
    try {
        const response = await fetch('/api/people?t=' + new Date().getTime());
        const people = await response.json();
        
        if (people.length === 0) {
            peopleGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 40px;">No identities enrolled yet.</div>`;
            return;
        }

        peopleGrid.innerHTML = '';
        people.forEach(person => {
            const card = document.createElement('div');
            card.className = 'person-card';
            
            // Generate a random timestamp to bypass browser image caching when updating
            const rand = new Date().getTime();
            const audioInputId = `audioFile_${person.name.replace(/\s+/g, '_')}`;
            
            card.innerHTML = `
                <div class="person-photo" style="position: relative; background: #111;">
                    <button onclick="deletePerson('${person.name}')" style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.6); border: none; color: var(--danger); cursor: pointer; font-size: 1.2rem; border-radius: 50%; width: 30px; height: 30px; display: flex; justify-content: center; align-items: center; z-index: 10;">&times;</button>
                    <img src="/api/people/${person.name}/photo?t=${rand}" alt="${person.name}" onerror="this.style.opacity='0'; this.parentElement.style.background='#222';">
                </div>
                <div class="person-details">
                    <h3>${person.name}</h3>
                    <p>${person.samples} Training Samples</p>
                    <div class="audio-player-mini">
                        <audio controls style="width: 100%; height: 30px;">
                            <source src="/audio/${person.name}?t=${rand}">
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                    <div style="display: flex; gap: 5px; margin-top: 8px; align-items: center;">
                        <label for="${audioInputId}" class="btn" style="padding: 4px 10px; font-size: 0.75rem; cursor: pointer; border-color: #666; color: #aaa; flex: 1; text-align: center;">🎵 Change Audio</label>
                        <input type="file" id="${audioInputId}" accept="audio/*" style="display: none;" onchange="uploadAudioForPerson('${person.name}', this)">
                    </div>
                </div>
            `;
            peopleGrid.appendChild(card);
        });
    } catch (e) {
        console.error("Failed to load people:", e);
        peopleGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--danger); padding: 40px;">Error loading data from server.</div>`;
    }
}
// --- Enrollment & Upload Logic ---
const startEnrollBtn = document.getElementById('startEnrollBtn');
const photoUpload = document.getElementById('photoUpload');
const uploadPhotoBtn = document.getElementById('uploadPhotoBtn');
const enrollStatus = document.getElementById('enrollStatus');

function showStatus(msg, type) {
    if (!enrollStatus) return;
    enrollStatus.style.display = 'block';
    enrollStatus.textContent = msg;
    if (type === 'success') {
        enrollStatus.style.background = 'rgba(0, 255, 102, 0.15)';
        enrollStatus.style.color = '#00ff66';
        enrollStatus.style.border = '1px solid rgba(0, 255, 102, 0.3)';
    } else if (type === 'error') {
        enrollStatus.style.background = 'rgba(255, 51, 102, 0.15)';
        enrollStatus.style.color = '#ff3366';
        enrollStatus.style.border = '1px solid rgba(255, 51, 102, 0.3)';
    } else {
        enrollStatus.style.background = 'rgba(0, 170, 255, 0.15)';
        enrollStatus.style.color = '#00aaff';
        enrollStatus.style.border = '1px solid rgba(0, 170, 255, 0.3)';
    }
    // Auto-hide after 8 seconds
    setTimeout(() => { enrollStatus.style.display = 'none'; }, 8000);
}

// Live Enroll Button
if (startEnrollBtn) {
    startEnrollBtn.addEventListener('click', async () => {
        const name = newPersonName.value.trim();
        if (!name) {
            showStatus('⚠ Please enter a name first!', 'error');
            return;
        }
        try {
            showStatus(`⏳ Starting enrollment for "${name}"...`, 'info');
            const res = await fetch('/start_enrollment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            const data = await res.json();
            if (data.success) {
                showStatus(`✅ Enrollment started for "${name}"! Redirecting to scanner...`, 'success');
                newPersonName.value = '';
                // Redirect to scanner after 1.5 seconds so user can look at camera
                setTimeout(() => { window.location.href = '/'; }, 1500);
            } else {
                showStatus(data.message || 'Error starting enrollment', 'error');
            }
        } catch(e) {
            console.error(e);
            showStatus('❌ Error connecting to server', 'error');
        }
    });
}

// Photo Upload — show upload button when file is selected
if (photoUpload) {
    photoUpload.addEventListener('change', () => {
        if (photoUpload.files.length > 0) {
            uploadPhotoBtn.style.display = 'inline-block';
            uploadPhotoBtn.textContent = `⬆ Upload "${photoUpload.files[0].name}"`;
        } else {
            uploadPhotoBtn.style.display = 'none';
        }
    });
}

if (uploadPhotoBtn) {
    uploadPhotoBtn.addEventListener('click', async () => {
        const name = newPersonName.value.trim();
        if (!name) {
            showStatus('⚠ Please enter a name first!', 'error');
            return;
        }
        if (!photoUpload.files.length) {
            showStatus('⚠ Please select a photo first!', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', name);
        formData.append('file', photoUpload.files[0]);
        
        try {
            showStatus(`⏳ Uploading photo for "${name}"...`, 'info');
            uploadPhotoBtn.disabled = true;
            
            const res = await fetch('/upload_photo', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            
            if (data.success) {
                showStatus(`✅ ${data.message}`, 'success');
                newPersonName.value = '';
                photoUpload.value = '';
                uploadPhotoBtn.style.display = 'none';
                // Reload the people list to show the new person
                loadPeople();
                loadStats();
            } else {
                showStatus(`❌ ${data.message}`, 'error');
            }
        } catch(e) {
            console.error(e);
            showStatus('❌ Error uploading photo', 'error');
        } finally {
            uploadPhotoBtn.disabled = false;
        }
    });
}

// Fetch Recent Logs
async function loadLogs() {
    const logsGrid = document.getElementById('logsGrid');
    try {
        const response = await fetch('/api/logs?t=' + new Date().getTime());
        const logs = await response.json();
        
        if (logs.length === 0) {
            if (logsGrid.innerHTML.includes("No recent scans found")) return; // skip update
            logsGrid.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 40px;">No recent scans found. Wait for someone to use the camera!</div>`;
            return;
        }

        logsGrid.innerHTML = '';
        
        // Group logs by person
        const groupedLogs = {};
        logs.forEach(log => {
            if (!groupedLogs[log.name]) groupedLogs[log.name] = [];
            groupedLogs[log.name].push(log);
        });

        // Create horizontal rows for each person
        Object.keys(groupedLogs).forEach(name => {
            const rowContainer = document.createElement('div');
            rowContainer.className = 'log-person-group';
            
            const safeName = name.replace(/[^a-zA-Z0-9]/g, '-');
            // Default to open if they haven't explicitly interacted with it
            const isOpen = !openFolders.has(safeName + "_closed");
            
            rowContainer.innerHTML = `
                <h3 onclick="toggleLogFolder('${safeName}')" style="margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; color: var(--primary); font-size: 1.1rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
                    <span>${name} <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal; margin-left: 10px;">(${groupedLogs[name].length} scans)</span></span>
                    <span id="log-arrow-${safeName}" style="font-size: 0.8rem; color: var(--text-muted);">${isOpen ? '▲ Close' : '▼ Open'}</span>
                </h3>
                <div id="log-folder-${safeName}" class="horizontal-scroll" style="display: ${isOpen ? 'flex' : 'none'}; gap: 15px; overflow-x: auto; padding-bottom: 15px;"></div>
            `;
            
            const scrollContainer = rowContainer.querySelector('.horizontal-scroll');
            
            groupedLogs[name].forEach(log => {
                const card = document.createElement('div');
                card.className = 'person-card';
                card.style.minWidth = '220px'; // Fixed width for horizontal scroll
                card.style.flexShrink = '0'; // Prevent squishing
                
                card.innerHTML = `
                    <div class="person-photo" style="background: #000; height: 160px; position: relative;">
                        <button onclick="deleteLog('${log.filename}')" style="position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.6); border: none; color: var(--danger); cursor: pointer; font-size: 1.1rem; border-radius: 50%; width: 25px; height: 25px; display: flex; justify-content: center; align-items: center; z-index: 10;">&times;</button>
                        <img src="/api/logs/${log.filename}" onclick="enlargeVideo(this.src)" alt="Recent Scan" style="width: 100%; height: 100%; object-fit: contain; filter: none; cursor: pointer;">
                    </div>
                    <div class="person-details" style="padding: 12px; display: flex; justify-content: center;">
                        <p style="color: var(--text-muted); margin: 0; font-size: 0.85rem; font-weight: 500;">${log.timestamp}</p>
                    </div>
                `;
                scrollContainer.appendChild(card);
            });
            
            logsGrid.appendChild(rowContainer);
        });
        
    } catch (e) {
        console.error("Failed to load logs:", e);
    }
}
