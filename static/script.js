const micBtn = document.getElementById('micBtn');
const display = document.getElementById('displayHelper');
const userText = document.getElementById('userText');
const botText = document.getElementById('botText');
const graphContainer = document.getElementById('graphContainer');
const statusBar = document.getElementById('statusBar');
const imageInput = document.getElementById('imageInput');
const uploadBtn = document.getElementById('uploadBtn');

// Web Speech API Setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;
try {
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
} catch (e) {
    console.warn('SpeechRecognition not supported');
}

let isListening = false;

// --- TTS Setup (Optimized for speed) ---
const synth = window.speechSynthesis;
let preferredVoice = null;

// Pre-load voices immediately + on change
function loadVoices() {
    const voices = synth.getVoices();
    if (voices.length > 0) {
        // Prefer a local English voice (faster than network voices)
        preferredVoice = voices.find(v => v.lang.startsWith('en') && v.localService) ||
                         voices.find(v => v.lang.startsWith('en')) ||
                         voices[0];
    }
}
loadVoices();
if (synth.onvoiceschanged !== undefined) {
    synth.onvoiceschanged = loadVoices;
}

function speak(text) {
    if (!text || text === '') return;

    // Cancel any ongoing speech immediately so new result speaks fast
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.1;   // Slightly faster
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    if (preferredVoice) {
        utterance.voice = preferredVoice;
    }

    utterance.onerror = (e) => console.error('TTS error:', e);

    // Chrome bug workaround: resume synth if paused
    synth.resume();
    synth.speak(utterance);
}

// --- Microphone Interaction ---
micBtn.addEventListener('click', () => {
    if (!recognition) {
        addBotMessage("Speech recognition not supported in this browser.");
        return;
    }
    if (!isListening) {
        try {
            recognition.start();
        } catch (e) {
            // Already started
        }
    } else {
        recognition.stop();
    }
});

if (recognition) {
    recognition.onstart = () => {
        isListening = true;
        micBtn.classList.add('listening');
        statusBar.textContent = "Listening...";
    };

    recognition.onend = () => {
        isListening = false;
        micBtn.classList.remove('listening');
        statusBar.textContent = "Processing...";
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        addUserMessage(transcript);
        sendToBackend(transcript);
    };

    recognition.onerror = (event) => {
        isListening = false;
        micBtn.classList.remove('listening');
        if (event.error === 'no-speech') {
            statusBar.textContent = "No speech detected. Try again.";
        } else {
            statusBar.textContent = "Mic error: " + event.error;
        }
    };
}

// --- Image Upload ---
uploadBtn.addEventListener('click', () => {
    imageInput.click();
});

imageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadImage(e.target.files[0]);
    }
});


// --- Backend Communication ---
async function sendToBackend(text) {
    statusBar.textContent = "Calculating...";

    try {
        const response = await fetch('/process_command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();
        handleResponse(data);

    } catch (error) {
        console.error('Error:', error);
        addBotMessage("Error connecting to server.");
        speak("Error connecting to server.");
        statusBar.textContent = "Error";
    }
}

async function uploadImage(file) {
    statusBar.textContent = "Uploading & Analyzing...";
    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch('/upload_image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            addBotMessage("Error: " + data.error);
            speak("I couldn't read that image.");
        } else {
            addUserMessage("[Image Uploaded]: " + data.text);
            if (data.result) {
                addBotMessage(data.result);
                speak(data.speech || ("The result is " + data.result));
            } else {
                addBotMessage("Could not calculate result.");
                speak("I found text but couldn't calculate a result.");
            }
        }
        statusBar.textContent = "Ready";

    } catch (error) {
        console.error('Error:', error);
        addBotMessage("Upload failed.");
        statusBar.textContent = "Error";
    }
}


// --- Response Handler ---
function handleResponse(data) {
    // 1. Antigravity
    if (data.action === 'antigravity') {
        addBotMessage("Flying...");
        speak(data.speech);
        window.open('https://xkcd.com/353/', '_blank');
        statusBar.textContent = "Ready";
        return;
    }

    // 2. Graph
    if (data.graph) {
        const img = document.createElement('img');
        img.src = "data:image/png;base64," + data.graph;
        graphContainer.innerHTML = '';
        graphContainer.appendChild(img);
        addBotMessage(data.result);
        speak(data.speech);
        statusBar.textContent = "Graph Displayed";
        return;
    }

    // 3. Text Result
    if (data.result) {
        addBotMessage(data.result);
        speak(data.speech);
    } else {
        addBotMessage(data.speech || "I didn't understand that.");
        speak(data.speech);
    }
    statusBar.textContent = "Ready";
}


function addUserMessage(text) {
    userText.textContent = text;
}

function addBotMessage(text) {
    botText.textContent = text;
}
