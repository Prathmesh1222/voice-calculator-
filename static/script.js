// ===== DOM Elements =====
const micBtn = document.getElementById('micBtn');
const chatArea = document.getElementById('chatArea');
const graphContainer = document.getElementById('graphContainer');
const statusBar = document.getElementById('statusBar');
const imageInput = document.getElementById('imageInput');
const uploadBtn = document.getElementById('uploadBtn');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const loader = document.getElementById('loader');
const exportBtn = document.getElementById('exportBtn');


// ===== Chat History =====
let chatHistory = [];
let welcomeRemoved = false;

function removeWelcome() {
    if (!welcomeRemoved) {
        const welcome = chatArea.querySelector('.chat-welcome');
        if (welcome) welcome.remove();
        welcomeRemoved = true;
    }
}

function addMessage(text, sender) {
    removeWelcome();
    chatHistory.push({ text, sender, time: new Date().toLocaleTimeString() });

    const msg = document.createElement('div');
    msg.className = `chat-msg ${sender}`;

    const label = document.createElement('div');
    label.className = 'msg-label';
    label.textContent = sender === 'user' ? 'You' : 'Calculator';

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;

    // Copy button (for bot messages)
    if (sender === 'bot') {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
        copyBtn.title = 'Copy';
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(text).then(() => {
                copyBtn.innerHTML = '<i class="fas fa-check"></i>';
                copyBtn.classList.add('copied');
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
                    copyBtn.classList.remove('copied');
                }, 1500);
            });
        };
        bubble.appendChild(copyBtn);
    }

    msg.appendChild(label);
    msg.appendChild(bubble);
    chatArea.appendChild(msg);

    // Auto scroll
    chatArea.scrollTop = chatArea.scrollHeight;
}

// ===== Speech Recognition =====
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

// ===== TTS (Optimized) =====
const synth = window.speechSynthesis;
let preferredVoice = null;

function loadVoices() {
    const voices = synth.getVoices();
    if (voices.length > 0) {
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
    if (!text) return;
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.1;
    utterance.pitch = 1.0;
    if (preferredVoice) utterance.voice = preferredVoice;

    synth.resume();
    synth.speak(utterance);
}



// ===== Microphone =====
micBtn.addEventListener('click', () => {
    if (!recognition) {
        addMessage("Speech recognition not supported in this browser.", 'bot');
        return;
    }
    if (!isListening) {
        try { recognition.start(); } catch (e) {}
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
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        addMessage(transcript, 'user');
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

// ===== Text Input =====
textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && textInput.value.trim()) {
        const text = textInput.value.trim();
        addMessage(text, 'user');
        sendToBackend(text);
        textInput.value = '';
    }
});

sendBtn.addEventListener('click', () => {
    if (textInput.value.trim()) {
        const text = textInput.value.trim();
        addMessage(text, 'user');
        sendToBackend(text);
        textInput.value = '';
    }
});

// ===== Example Commands =====
document.querySelectorAll('.example-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        const cmd = chip.getAttribute('data-cmd');
        addMessage(cmd, 'user');
        sendToBackend(cmd);
    });
});

// ===== Image Upload =====
uploadBtn.addEventListener('click', () => imageInput.click());

imageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadImage(e.target.files[0]);
        imageInput.value = '';
    }
});

// ===== Export History =====
exportBtn.addEventListener('click', () => {
    if (chatHistory.length === 0) {
        addMessage("No history to export.", 'bot');
        return;
    }

    let content = "Voice Calculator — Chat History\n";
    content += "Exported: " + new Date().toLocaleString() + "\n";
    content += "=".repeat(40) + "\n\n";

    chatHistory.forEach(entry => {
        const label = entry.sender === 'user' ? 'You' : 'Calculator';
        content += `[${entry.time}] ${label}: ${entry.text}\n`;
    });

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'calculator_history.txt';
    a.click();
    URL.revokeObjectURL(url);

    statusBar.textContent = "History exported!";
});

// ===== Backend Communication =====
function showLoader() {
    loader.style.display = 'flex';
    statusBar.textContent = "Calculating...";
}

function hideLoader() {
    loader.style.display = 'none';
}

async function sendToBackend(text) {
    showLoader();

    try {
        const response = await fetch('/process_command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();
        hideLoader();
        handleResponse(data);

    } catch (error) {
        hideLoader();
        addMessage("Error connecting to server.", 'bot');
        speak("Error connecting to server.");
        statusBar.textContent = "Error";
    }
}

async function uploadImage(file) {
    showLoader();
    statusBar.textContent = "Uploading & Analyzing...";
    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch('/upload_image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        hideLoader();

        if (data.error) {
            addMessage("Error: " + data.error, 'bot');
            speak("I couldn't read that image.");
        } else {
            addMessage("[Image]: " + data.text, 'user');
            if (data.result) {
                playDing();
                addMessage(data.result, 'bot');
                speak(data.speech || "The result is " + data.result);
            } else {
                addMessage("Could not calculate result.", 'bot');
                speak("I found text but couldn't calculate a result.");
            }
        }
        statusBar.textContent = "Ready";

    } catch (error) {
        hideLoader();
        addMessage("Upload failed.", 'bot');
        statusBar.textContent = "Error";
    }
}

// ===== Response Handler =====
function handleResponse(data) {
    // 1. Antigravity
    if (data.action === 'antigravity') {
        addMessage("🚀 Antigravity Activated!", 'bot');
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

        // Download button
        const dlBtn = document.createElement('button');
        dlBtn.className = 'graph-download-btn';
        dlBtn.innerHTML = '<i class="fas fa-download"></i> Download Graph';
        dlBtn.onclick = () => {
            const a = document.createElement('a');
            a.href = img.src;
            a.download = 'graph.png';
            a.click();
        };
        graphContainer.appendChild(dlBtn);

        addMessage(data.result, 'bot');
        speak(data.speech);
        statusBar.textContent = "Graph Displayed";
        return;
    }

    // 3. Text Result
    if (data.result) {
        addMessage(data.result, 'bot');
        speak(data.speech);
    } else {
        addMessage(data.speech || "I didn't understand that.", 'bot');
        speak(data.speech);
    }
    statusBar.textContent = "Ready";
}

// ===== PWA Service Worker =====
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js').catch(() => {});
}
