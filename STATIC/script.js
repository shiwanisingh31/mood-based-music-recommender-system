// Get the search box element
const searchBox = document.getElementById('search-box');
const resultsDiv = document.getElementById('search-results');

// All available songs (hardcoded database)
const allSongs = [
    "Happy - Pharrell Williams",
    "Good Vibrations - The Beach Boys",
    "Don't Stop Me Now - Queen",
    "Walking on Sunshine - Katrina",
    "I Gotta Feeling - Black Eyed Peas",
    "Someone Like You - Adele",
    "Hurt - Johnny Cash",
    "The Night We Met - Lord Huron",
    "Fix You - Coldplay",
    "Let Her Go - Passenger",
    "Break Stuff - Limp Bizkit",
    "Killing in the Name - RATM",
    "Enter Sandman - Metallica",
    "Bodies - Drowning Pool",
    "Smells Like Teen Spirit - Nirvana"
];

// Listen for user typing
searchBox.addEventListener('input', function() {
    const query = searchBox.value.toLowerCase();
    
    // If search box is empty, clear results
    if (query === '') {
        resultsDiv.innerHTML = '';
        return;
    }
    
    // Filter songs that match the search
    const matches = allSongs.filter(song => 
        song.toLowerCase().includes(query)
    );
    
    // Display results
    if (matches.length > 0) {
        let html = '<div style="margin-top: 20px; text-align: left;">';
        html += '<p style="color: #667eea; font-weight: bold; margin-bottom: 10px;">Search Results:</p>';
        html += '<ul class="song-list">';
        matches.forEach(song => {
            html += `<li>🎵 ${song}</li>`;
        });
        html += '</ul></div>';
        resultsDiv.innerHTML = html;
    } else {
        resultsDiv.innerHTML = '<p style="color: #999; margin-top: 15px;">No songs found 😔</p>';
    }
});

// ============= WEBCAM FUNCTIONALITY =============

const startWebcamBtn = document.getElementById('start-webcam-btn');
const stopWebcamBtn = document.getElementById('stop-webcam-btn');
const captureBtn = document.getElementById('capture-btn');
const webcamContainer = document.getElementById('webcam-container');
const video = document.getElementById('webcam');
const canvas = document.getElementById('canvas');
const emotionResult = document.getElementById('emotion-result');

let stream = null;

// Start webcam
startWebcamBtn.addEventListener('click', async function() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { width: 640, height: 480 } 
        });
        video.srcObject = stream;
        webcamContainer.style.display = 'block';
        startWebcamBtn.style.display = 'none';
        emotionResult.innerHTML = '';
    } catch (error) {
        emotionResult.innerHTML = '<p style="color: red;">❌ Camera access denied or not available</p>';
        console.error('Error accessing webcam:', error);
    }
});

// Stop webcam
stopWebcamBtn.addEventListener('click', function() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        webcamContainer.style.display = 'none';
        startWebcamBtn.style.display = 'inline-block';
        emotionResult.innerHTML = '';
    }
});

// Capture image and detect emotion
captureBtn.addEventListener('click', async function() {
    // Wait for video to have valid dimensions (must be playing)
    if (!video.videoWidth || !video.videoHeight) {
        emotionResult.innerHTML = '<p style="color: red;">❌ Please wait for the camera to start, then try again.</p>';
        return;
    }
    
    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to base64 image
   const imageData = canvas.toDataURL('image/jpeg');
    
    emotionResult.innerHTML = '<p style="color: #667eea;">🔄 Detecting emotion...<br><small>First time can take 1-2 min (loading AI). Check terminal for progress.</small></p>';
    
    try {
        const response = await fetch('/detect-emotion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData })
        });
        
        const data = await response.json().catch(() => ({}));
        
        if (!response.ok || data.error) {
            const errMsg = data.error || `Server error (${response.status})`;
            emotionResult.innerHTML = `<p style="color: red;">❌ ${errMsg}</p>`;
            console.error('Emotion detection error:', errMsg);
            return;
        }
        
        if (data.emotion && data.songs) {
            emotionResult.innerHTML = `
                <h3 style="color: #667eea;">Detected Emotion: ${data.emotion}</h3>
                <p>Recommended Songs:</p>
                <ul class="song-list">
                    ${data.songs.map(song => `<li>🎵 ${song}</li>`).join('')}
                </ul>
            `;
        } else {
            emotionResult.innerHTML = '<p style="color: red;">❌ Unexpected response from server</p>';
        }
    } catch (error) {
        emotionResult.innerHTML = `<p style="color: red;">❌ Connection error: ${error.message}. Is the server running?</p>`;
        console.error('Error:', error);
    }
});