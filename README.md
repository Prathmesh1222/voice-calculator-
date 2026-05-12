# 🎙️ Voice Calculator

A next-generation voice-powered calculator that understands natural language. Speak or type commands to perform arithmetic, calculus, graphing, unit conversions, equation solving, and matrix operations.


## ✨ Features

| Category               | Examples                                                         |
| ---------------------- | ---------------------------------------------------------------- |
| **Voice & Text Input** | Speak or type commands naturally                                 |
| **Arithmetic** | "5 plus 3", "product of 4 and 5", "square root of 16"            |
| **Calculus** | "differentiate x squared", "integrate 2x", "derivative of sin x" |
| **Graphing** | "plot sin x", "graph x squared", "plot log x", "plot e power x"  |
| **Equation Solving** | "solve x squared minus 4 equals 0" → x = -2, 2                   |
| **Unit Conversion** | "convert 100 celsius to fahrenheit", "convert 5 km to miles"     |
| **Matrix Operations** | "determinant of [[1,2],[3,4]]", inverse, transpose               |
| **Image OCR** | Upload a photo of a math problem                                 |
| **Division by Zero** | Graceful error handling                                          |

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SymPy, Matplotlib, NumPy
- **Frontend:** HTML5, CSS3, JavaScript (ES6+)
- **APIs:** Web Speech API, SpeechSynthesis API
- **OCR:** Tesseract (pytesseract)
- **Deployment:** Vercel / Render
- **PWA:** Installable on mobile devices

## 🚀 Live Demo

**[voice-calculator-one.vercel.app](https://voice-calculator-one.vercel.app)**

## 📦 Installation (Local)

```bash
# Clone
git clone [https://github.com/Prathmesh1222/voice-calculator-.git](https://github.com/Prathmesh1222/voice-calculator-.git)
cd voice-calculator-

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
