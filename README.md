# 🎙️ Voice Calculator

A next-generation voice-powered calculator that understands natural language. Speak or type commands to perform arithmetic, calculus, graphing, unit conversions, equation solving, and matrix operations.

> **Project Exhibition — 2**  
> B.Tech CSE • 2025-26

## 👥 Team

| Name              | Roll No.   |
| ----------------- | ---------- |
| Prathmesh Jadhav  | 24BCE10076 |
| Gayatri Kurkute   | 24BCE10094 |
| Abhijeet Patil    | 24BCE10110 |
| Shreya Mandaogade | 24BCE10614 |
| Prathviraj Chavan | 24BCE10116 |

## ✨ Features

| Category               | Examples                                                         |
| ---------------------- | ---------------------------------------------------------------- |
| **Voice & Text Input** | Speak or type commands naturally                                 |
| **Arithmetic**         | "5 plus 3", "product of 4 and 5", "square root of 16"            |
| **Calculus**           | "differentiate x squared", "integrate 2x", "derivative of sin x" |
| **Graphing**           | "plot sin x", "graph x squared", "plot log x", "plot e power x"  |
| **Equation Solving**   | "solve x squared minus 4 equals 0" → x = -2, 2                   |
| **Unit Conversion**    | "convert 100 celsius to fahrenheit", "convert 5 km to miles"     |
| **Matrix Operations**  | "determinant of \[\[1,2\],\[3,4\]\]", inverse, transpose         |
| **Image OCR**          | Upload a photo of a math problem                                 |
| **Division by Zero**   | Graceful error handling                                          |

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
git clone https://github.com/Prathmesh1222/voice-calculator-.git
cd voice-calculator-

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python app.py
```

The app will open at **http://127.0.0.1:5000** automatically.

## 📁 Project Structure

```
voice-calculator/
├── app.py                  # Flask backend (routes, graphing, API)
├── calculator_logic.py     # Math engine (NLP, calculus, equations, conversions)
├── voice_calculator.py     # Desktop GUI (Tkinter)
├── test_engine.py          # Test suite (30 tests)
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel deployment config
├── templates/
│   ├── index.html          # Main web UI
│   └── about.html          # About / Team page
├── static/
│   ├── style.css           # Light theme + responsive CSS
│   ├── script.js           # Frontend logic (voice, chat, export)
│   ├── manifest.json       # PWA manifest
│   └── sw.js               # Service worker
└── run_web.sh              # Launch script
```

## 🧪 Running Tests

```bash
python test_engine.py
```

Tests cover: arithmetic, calculus, unit conversions, equation solving, matrix operations, division by zero, and rate limiting.

## 🌐 Deployment

### Vercel

1. Push to GitHub
2. Import repo on [vercel.com](https://vercel.com)
3. Framework: **Other**, Root: `./`
4. Auto-deploys on every push

### Render

1. Push to GitHub
2. New Web Service on [render.com](https://render.com)
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn app:app`

## 📄 License

MIT License
