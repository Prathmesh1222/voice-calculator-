from flask import Flask, render_template, request, jsonify
import sys
import traceback

app = Flask(__name__)

# Global Error State
GLOBAL_ERROR = None
math_engine = None
image_handler = None

try:
    # 1. Setup Environment
    import os
    os.environ['MPLCONFIGDIR'] = '/tmp'
    
    # 2. Imports
    import base64
    import io
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import sympy
    import numpy as np
    
    # 3. Logic Modules
    from calculator_logic import MathEngine, ImageHandler
    
    # 4. Initialize
    math_engine = MathEngine()
    image_handler = ImageHandler()

    # Ensure we have a static folder
    if not os.path.exists('static'):
        os.makedirs('static')
    
except Exception as e:
    GLOBAL_ERROR = f"Server Startup Error:\n{str(e)}\n\n{traceback.format_exc()}"

@app.route('/')
def index():
    if GLOBAL_ERROR:
        return f"<html><body><h1>Deployment Error</h1><pre>{GLOBAL_ERROR}</pre></body></html>", 500
    return render_template('index.html')

@app.route('/process_command', methods=['POST'])
def process_command():
    if GLOBAL_ERROR:
        return jsonify({'result': "Server Startup Error. Check Homepage.", 'speech': "Critical server error."})
        
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'result': 'No command received'})
            
        response = {
            'speech': '',
            'result': '',
            'graph': None,
            'action': None
        }
        
        # 1. Check for Antigravity
        if math_engine.check_antigravity(text):
            response['action'] = 'antigravity'
            response['speech'] = 'Activating anti gravity mode'
            response['result'] = 'Antigravity Activated 🚀'
            return jsonify(response)

        # 2. Check for Graphing
        if math_engine.is_graphing_command(text):
            func_str = math_engine.get_graph_function(text)
            try:
                # Generate graph
                plt.figure(figsize=(6, 4))
                x = sympy.symbols('x')
                f = sympy.sympify(func_str)
                f_lambdified = sympy.lambdify(x, f, modules=['numpy'])
                
                x_vals = np.linspace(-10, 10, 400)
                y_vals = f_lambdified(x_vals)
                
                plt.plot(x_vals, y_vals, color='#00FF00')
                plt.title(f"y = {func_str}", color='black')
                plt.grid(True, alpha=0.5)
                
                # Save to BytesIO
                img = io.BytesIO()
                plt.savefig(img, format='png', bbox_inches='tight')
                img.seek(0)
                plot_url = base64.b64encode(img.getvalue()).decode()
                plt.close()
                
                response['graph'] = plot_url
                response['speech'] = f"Graphing {func_str}"
                response['result'] = f"Graph of {func_str}"
            except Exception as e:
                response['speech'] = "I could not plot that function."
                response['result'] = f"Graph Error: {str(e)}"
                
            return jsonify(response)
            
        # 3. Check Calculus (Differentiation/Integration)
        calculus_result = math_engine.check_calculus(text)
        if calculus_result:
            response['result'] = calculus_result
            response['speech'] = calculus_result
            return jsonify(response)

        # 4. Evaluate Math
        result = math_engine.evaluate(text)
        if result:
            response['result'] = result
            response['speech'] = f"The answer is {result}"
        else:
            response['speech'] = "I didn't understand that."
            response['result'] = None
            
        return jsonify(response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'result': f"Server Error: {str(e)}", 'speech': "An internal error occurred."}), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'})
        
    try:
        # Save temporarily
        filepath = os.path.join('static', 'temp_upload.png')
        file.save(filepath)
        
        # OCR
        text = image_handler.extract_text(filepath)
        
        # Try to evaluate result immediately
        result = math_engine.evaluate(text)
        
        return jsonify({
            'text': text,
            'result': result,
            'speech': f"Found text: {text}. Result is {result}" if result else f"Found text: {text}"
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    import webbrowser
    from threading import Timer
    
    def open_browser():
        webbrowser.open_new('http://127.0.0.1:5000/')
        
    Timer(1.5, open_browser).start()
    app.run(debug=True)
