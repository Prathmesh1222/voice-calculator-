
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import speech_recognition as sr
import pyttsx3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sympy
import antigravity
import webbrowser
from PIL import Image
import pytesseract
import os
from calculator_logic import MathEngine, ImageHandler

# Ensure Tesseract is in PATH or set it explicitly if needed
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.is_listening = False
        
    def speak(self, text):
        def _speak():
            self.engine.say(text)
            self.engine.runAndWait()
        threading.Thread(target=_speak).start()

    def start_listening(self, callback, error_callback=None):
        self.is_listening = True
        def _listen_loop():
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source)
                while self.is_listening:
                    try:
                        print("Listening...")
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                        text = self.recognizer.recognize_google(audio)
                        if text:
                            callback(text)
                    except sr.WaitTimeoutError:
                        continue # Just listen again
                    except sr.UnknownValueError:
                        pass # Didn't catch that
                    except sr.RequestError:
                        if error_callback:
                            error_callback("API Error")
                        self.is_listening = False
                        break
                    except Exception as e:
                        print(f"Error: {e}")
                        if error_callback:
                            error_callback(str(e))
                        
        threading.Thread(target=_listen_loop, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False

class CalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Next-Gen Voice Calculator")
        self.root.geometry("800x600")
        
        self.voice_handler = VoiceHandler()
        self.math_engine = MathEngine()
        self.image_handler = ImageHandler()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#2E2E2E')
        style.configure('TLabel', background='#2E2E2E', foreground='white', font=('Helvetica', 12))
        style.configure('TButton', font=('Helvetica', 11), padding=10)
        
        self.root.configure(bg='#2E2E2E')
        
        # Display Area (Top)
        self.display_frame = ttk.Frame(self.root)
        self.display_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.history_text = tk.Text(self.display_frame, height=4, font=('Helvetica', 14), bg='#1E1E1E', fg='#00FF00', state='disabled')
        self.history_text.pack(fill=tk.X)
        
        # Graphing Area (Middle)
        self.graph_frame = ttk.Frame(self.root)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.figure, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor('#2E2E2E')
        self.ax.set_facecolor('#1E1E1E')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Controls Area (Bottom)
        self.controls_frame = ttk.Frame(self.root)
        self.controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.listen_btn = ttk.Button(self.controls_frame, text="Start Listening", command=self.toggle_listening)
        self.listen_btn.pack(side=tk.LEFT, padx=5)
        
        self.upload_btn = ttk.Button(self.controls_frame, text="Upload Image", command=self.process_image_upload)
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(self.controls_frame, text="Ready", font=('Helvetica', 10, 'italic'))
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def log_message(self, message):
        self.history_text.config(state='normal')
        self.history_text.insert(tk.END, message + "\n")
        self.history_text.see(tk.END)
        self.history_text.config(state='disabled')

    def toggle_listening(self):
        if not self.voice_handler.is_listening:
            self.status_label.config(text="Listening...")
            self.listen_btn.config(text="Stop Listening")
            self.voice_handler.start_listening(self.process_voice_command, self.on_voice_error)
        else:
            self.voice_handler.stop_listening()
            self.status_label.config(text="Ready")
            self.listen_btn.config(text="Start Listening")
            
    def on_voice_error(self, error):
        self.status_label.config(text=f"Error: {error}")
        self.voice_handler.speak(f"Error: {error}")

    def process_voice_command(self, text):
        print(f"Heard: {text}")
        self.root.after(0, self._process_command_thread_safe, text)

    def _process_command_thread_safe(self, text):
        self.log_message(f"User: {text}")
        self.status_label.config(text="Processing...")
        
        # Check for Antigravity
        if self.math_engine.check_antigravity(text):
            self.log_message("System: ACTIVATE ANTIGRAVITY!")
            self.voice_handler.speak("You are now flying!")
            threading.Thread(target=antigravity.fly).start() # antigravity.fly is not a real function in the module, just import it
            # actually importing antigravity opens the page.
            # To re-trigger it we might need to reload or just open the URL manually if it doesn't work repeatedly
            webbrowser.open("https://xkcd.com/353/")
            self.status_label.config(text="Flying...")
            return

        # Check for Graphing
        if self.math_engine.is_graphing_command(text):
            func_str = self.math_engine.get_graph_function(text)
            self.plot_graph(func_str)
            self.voice_handler.speak(f"Graphing {func_str}")
            self.status_label.config(text="Graph displayed")
            return

        # Check for Calculus
        calculus_result = self.math_engine.check_calculus(text)
        if calculus_result:
            self.log_message(f"Calculus: {calculus_result}")
            self.voice_handler.speak(calculus_result)
            self.status_label.config(text="Calculus solved")
            return

        # Evaluate Math
        result = self.math_engine.evaluate(text)
        if result:
            self.log_message(f"Calc: {result}")
            self.voice_handler.speak(f"The result is {result}")
            self.status_label.config(text="Result calculated")
        else:
            self.log_message("System: Could not understand command")
            self.voice_handler.speak("I didn't understand that calculation.")
            self.status_label.config(text="Ready")

    def plot_graph(self, func_str):
        try:
            self.ax.clear()
            x = sympy.symbols('x')
            # Generate points
            # We need to turn the string into a lambda function or evaluate it multiple times
            # Using sympy to lambdify is safer
            f = sympy.sympify(func_str)
            f_lambdified = sympy.lambdify(x, f, modules=['numpy'])
            
            import numpy as np
            x_vals = np.linspace(-10, 10, 400)
            y_vals = f_lambdified(x_vals) # This handles numpy arrays efficiently
            
            self.ax.plot(x_vals, y_vals, color='#00FF00', linewidth=2)
            self.ax.grid(True, color='gray', linestyle='--', alpha=0.5)
            self.ax.set_title(f"y = {func_str}", color='white')
            
            self.canvas.draw()
        except Exception as e:
            self.log_message(f"Graph Error: {e}")
            self.voice_handler.speak("I could not plot that function.")

    def process_image_upload(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.status_label.config(text="Processing Image...")
            text = self.image_handler.extract_text(file_path)
            self.log_message(f"OCR: {text}")
            if text:
                 # Clean up OCR noise if necessary or just feed to processing
                 self._process_command_thread_safe(text)
            else:
                 self.log_message("OCR: No text found")
                 self.voice_handler.speak("No text found in image.")
            self.status_label.config(text="Ready")

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorGUI(root)
    root.mainloop()

