from flask import Flask, render_template, request, jsonify
import sys
import traceback

app = Flask(__name__)

# Global Error State
GLOBAL_ERROR = None
math_engine = None
image_handler = None

try:
    import os
    os.environ['MPLCONFIGDIR'] = '/tmp'

    import base64
    import io
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import sympy
    import numpy as np

    from calculator_logic import MathEngine, ImageHandler

    math_engine = MathEngine()
    image_handler = ImageHandler()

    if not os.path.exists('static'):
        os.makedirs('static')

except Exception as e:
    GLOBAL_ERROR = f"Server Startup Error:\n{str(e)}\n\n{traceback.format_exc()}"

@app.route('/')
def index():
    if GLOBAL_ERROR:
        return f"<html><body><h1>Deployment Error</h1><pre>{GLOBAL_ERROR}</pre></body></html>", 500
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/process_command', methods=['POST'])
def process_command():
    if GLOBAL_ERROR:
        return jsonify({'result': "Server Error. Check homepage.", 'speech': "Server error."})

    # Rate limiting
    if not math_engine.check_rate_limit():
        return jsonify({'result': "Rate limit exceeded. Please slow down.", 'speech': "Too many requests."})

    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'result': 'No command received'})

        response = {
            'speech': '',
            'result': '',
            'graph': None,
            'action': None
        }

        # 1. Antigravity
        if math_engine.check_antigravity(text):
            response['action'] = 'antigravity'
            response['speech'] = 'Activating anti gravity mode'
            response['result'] = 'Antigravity Activated 🚀'
            return jsonify(response)

        # 2. Unit Conversion
        conversion = math_engine.check_unit_conversion(text)
        if conversion:
            response['result'] = conversion
            response['speech'] = conversion
            return jsonify(response)

        # 3. Equation Solving
        equation = math_engine.check_equation(text)
        if equation:
            response['result'] = equation
            response['speech'] = equation
            return jsonify(response)

        # 4. Matrix Operations
        matrix = math_engine.check_matrix(text)
        if matrix:
            response['result'] = matrix
            response['speech'] = matrix
            return jsonify(response)

        # 5. Graphing
        if math_engine.is_graphing_command(text):
            func_str = math_engine.get_graph_function(text)
            try:
                plt.figure(figsize=(6, 4))
                x = sympy.symbols('x')
                f = sympy.sympify(func_str)
                f_lambdified = sympy.lambdify(x, f, modules=['numpy'])

                x_vals = np.linspace(-10, 10, 400)
                y_vals = f_lambdified(x_vals)

                pretty_func = math_engine.pretty_func_name(func_str)

                plt.plot(x_vals, y_vals, color='#6366f1', linewidth=2)
                plt.title(f"y = {pretty_func}", fontsize=14)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                img = io.BytesIO()
                plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
                img.seek(0)
                plot_url = base64.b64encode(img.getvalue()).decode()
                plt.close()

                response['graph'] = plot_url
                response['speech'] = f"Graphing {pretty_func}"
                response['result'] = f"Graph of {pretty_func}"
            except Exception as e:
                response['speech'] = "I could not plot that function."
                response['result'] = f"Graph Error: {str(e)}"

            return jsonify(response)

        # 6. Calculus
        calculus_result = math_engine.check_calculus(text)
        if calculus_result:
            response['result'] = calculus_result
            response['speech'] = calculus_result
            return jsonify(response)

        # 7. Evaluate Math
        result = math_engine.evaluate(text)
        if result:
            response['result'] = result
            response['speech'] = f"The answer is {result}"
        else:
            response['speech'] = "I didn't understand that."
            response['result'] = None

        return jsonify(response)
    except Exception as e:
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
        filepath = os.path.join('static', 'temp_upload.png')
        file.save(filepath)

        text = image_handler.extract_text(filepath)
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
