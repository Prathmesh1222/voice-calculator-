# Next-Gen Voice Calculator 🎙️➕

A powerful AI-driven calculator that supports voice commands, natural language processing, graphing, and calculus operations. Built with Python (Flask & Tkinter).

## Features 🚀

- **Voice Control**: Speak natural commands like "Calculate 5 plus 5" or "Plot x squared".
- **Advanced Math**: Supports basic arithmetic, power, roots, logarithms (`log`, `ln`), and exponential functions.
- **Calculus**: Perform differentiation and integration (e.g., "Differentiate x squared", "Integrate 2x").
- **Graphing**: Visualizes mathematical functions instantly.
- **Image Upload**: Upload images of math problems for OCR-based solving.
- **Dual Interface**: 
    - **Web App**: Modern, responsive UI with dark mode and glassmorphism.
    - **Desktop App**: Classic Tkinter-based GUI for offline use.

## Installation 🛠️

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/voice-calculator.git
   cd voice-calculator
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: You may need to install system dependencies for PyAudio and Tkinter based on your OS)*

## Usage ▶️

### Web Application (Recommended)
Run the helper script:
```bash
./run_web.sh
```
The app will automatically open in your browser at `http://127.0.0.1:5000`.

### Desktop Application
Run the desktop GUI:
```bash
python voice_calculator.py
```

## Technologies Used 💻
- **Python**: Core logic.
- **Flask**: Web backend.
- **Tkinter**: Desktop GUI.
- **SymPy**: Symbolic mathematics (Calculus, Algebra).
- **Matplotlib**: Graph plotting.
- **SpeechRecognition**: Voice to text.
- **PyTesseract**: OCR for images.

## License 📄
MIT License
