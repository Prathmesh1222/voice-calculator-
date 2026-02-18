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
const recognition = new SpeechRecognition();
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.maxAlternatives = 1;

let isListening = false;

// TTS Setup
const synth = window.speechSynthesis;

function speak(text) {
    if (synth.speaking) {
        console.error('speechSynthesis.speaking');
        return;
    }
    if (text !== '') {
        const utterThis = new SpeechSynthesisUtterance(text);
        utterThis.onend = function (event) {
            console.log('SpeechSynthesisUtterance.onend');
        }
        utterThis.onerror = function (event) {
            console.error('SpeechSynthesisUtterance.onerror');
        }
        synth.speak(utterThis);
    }
}

// Microphone Interaction
micBtn.addEventListener('click', () => {
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

// Image Upload
uploadBtn.addEventListener('click', () => {
    imageInput.click();
});

imageInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadImage(e.target.files[0]);
    }
});


// Backend Communication
async function sendToBackend(text) {
    statusBar.textContent = "Calculating...";

    try {
        const response = await fetch('/process_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
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
        graphContainer.innerHTML = ''; // Clear previous
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
        statusBar.textContent = "Ready";
    } else {
        addBotMessage(data.speech);
        speak(data.speech);
        statusBar.textContent = "Ready";
    }
}


function addUserMessage(text) {
    userText.textContent = text;
    // userText.scrollIntoView({ behavior: "smooth" });
}

function addBotMessage(text) {
    botText.textContent = text;
    // botText.scrollIntoView({ behavior: "smooth" });
}
