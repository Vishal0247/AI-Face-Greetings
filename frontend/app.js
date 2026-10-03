const statusIcon = document.getElementById('statusIcon');
const statusText = document.getElementById('statusText');

const idAvatar = document.getElementById('idAvatar');
const idName = document.getElementById('idName');
const idScore = document.getElementById('idScore');

// --- Webcam and Canvas Setup ---
const videoFeed = document.getElementById('videoFeed');
const overlayCanvas = document.getElementById('overlayCanvas');
const frameCanvas = document.getElementById('frameCanvas');
const overlayCtx = overlayCanvas.getContext('2d');
const frameCtx = frameCanvas.getContext('2d');

let isStreaming = false;

// Initialize webcam
navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false })
    .then(stream => {
        videoFeed.srcObject = stream;
        videoFeed.play();
    })
    .catch(err => {
        console.error("Error accessing webcam: ", err);
        alert("Could not access webcam. Please ensure permissions are granted.");
    });

videoFeed.addEventListener('playing', () => {
    isStreaming = true;
    
    // Set internal canvas dimensions to match the video, but drastically scaled down for network speed!
    const MAX_WIDTH = 320;
    const scale = MAX_WIDTH / videoFeed.videoWidth;
    frameCanvas.width = MAX_WIDTH;
    frameCanvas.height = videoFeed.videoHeight * scale;
    
    // Set overlay canvas dimensions to match the display size
    overlayCanvas.width = videoFeed.clientWidth;
    overlayCanvas.height = videoFeed.clientHeight;
    
    // Start the frame processing loop
    processFrameLoop();
});

// Handle window resize for overlay canvas
window.addEventListener('resize', () => {
    if (isStreaming) {
        overlayCanvas.width = videoFeed.clientWidth;
        overlayCanvas.height = videoFeed.clientHeight;
    }
});

let currentVerifiedName = null;
let audioPlayer = null;

async function processFrameLoop() {
    if (!isStreaming) return;
    
    // Draw current video frame to hidden canvas
    frameCtx.drawImage(videoFeed, 0, 0, frameCanvas.width, frameCanvas.height);
    
    // Get base64 representation (Highly compressed for lightning-fast network transfer)
    const frameData = frameCanvas.toDataURL('image/jpeg', 0.5);
    
    try {
        const response = await fetch('/process_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: frameData })
        });
        
        const data = await response.json();
        
        // Update Status Card
        statusText.textContent = data.status_text;
        
        if (data.is_valid) {
            statusIcon.className = "status-icon good";
            statusIcon.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#00ff66" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
        } else {
            statusIcon.className = "status-icon bad";
            statusIcon.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ff3366" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
        }
        
        // Update Identity / Enrollment Card
        const personalizedText = document.getElementById('personalizedText');
        
        if (data.is_enrolling) {
            idName.textContent = "Enrolling: " + data.enroll_name;
            idScore.textContent = data.extra_status;
            idAvatar.textContent = "E";
            idAvatar.className = "id-avatar";
            currentVerifiedName = null;
            personalizedText.style.display = "none";
        } else {
            if (data.verified_name) {
                idName.textContent = data.verified_name;
                idScore.textContent = "Identity Confirmed";
                idAvatar.textContent = data.verified_name.charAt(0).toUpperCase();
                idAvatar.className = "id-avatar verified";
                
                // Show personalized text
                personalizedText.style.display = "block";
                personalizedText.textContent = `Welcome back, ${data.verified_name}! Great to see you today.`;
                
                // Audio Playback Logic
                if (currentVerifiedName !== data.verified_name) {
                    currentVerifiedName = data.verified_name;
                    if (audioPlayer) {
                        audioPlayer.pause();
                        audioPlayer.currentTime = 0;
                    }
                    audioPlayer = new Audio(`/audio/${data.verified_name}`);
                    audioPlayer.play().catch(e => console.error("Audio play failed:", e));
                }
            } else {
                currentVerifiedName = null;
                personalizedText.style.display = "none";
                
                // Immediately stop the audio if they leave the circle
                if (audioPlayer) {
                    audioPlayer.pause();
                    audioPlayer.currentTime = 0;
                    audioPlayer = null;
                }
                
                if (data.extra_status) {
                    idName.textContent = "Unknown";
                    idScore.textContent = data.extra_status;
                    idAvatar.textContent = "?";
                    idAvatar.className = "id-avatar";
                } else {
                    idName.textContent = "Scanning...";
                    idScore.textContent = "Waiting for face";
                    idAvatar.textContent = "?";
                    idAvatar.className = "id-avatar";
                }
            }
        }
        
        // Draw UI overlay
        drawOverlay(data);
        
    } catch (err) {
        console.error("Error processing frame:", err);
    }
    
    // Call next frame
    setTimeout(processFrameLoop, 150); // ~7 FPS to reduce server load
}

function drawOverlay(data) {
    overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    
    const centerX = overlayCanvas.width / 2;
    const centerY = overlayCanvas.height / 2;
    const radius = Math.min(overlayCanvas.width, overlayCanvas.height) * 0.35;
    
    // Determine color
    let color = '#ff3366'; // Danger
    if (data.verified_name) {
        color = '#00f0ff'; // Cyan
    } else if (data.is_valid) {
        color = '#00ff66'; // Success
    }
    
    // Draw guide circle
    overlayCtx.beginPath();
    overlayCtx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    overlayCtx.strokeStyle = color;
    overlayCtx.lineWidth = 4;
    overlayCtx.stroke();
    
    // We could draw face bounding boxes if the server returned them, but we simplified it to just the guide circle for now.
}
