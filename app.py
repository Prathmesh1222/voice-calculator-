from flask import Flask, render_template, request, jsonify
import sys
import traceback
import re

app = Flask(__name__)

# Global Error State
GLOBAL_ERROR = None
math_engine = None
image_handler = None
translator = None

try:
    import os
    os.environ['MPLCONFIGDIR'] = '/tmp'

    import base64
    import io
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import sympy
    import numpy as np

    from calculator_logic import MathEngine, ImageHandler

    math_engine = MathEngine()
    image_handler = ImageHandler()

    # Optional translator
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator
    except ImportError:
        translator = None

    if not os.path.exists('static'):
        os.makedirs('static')

except Exception as e:
    GLOBAL_ERROR = f"Server Startup Error:\n{str(e)}\n\n{traceback.format_exc()}"


def process_single_command(text):
    """Process a single command and return a response dict."""
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
        return response

    # 2. Unit Conversion
    conversion = math_engine.check_unit_conversion(text)
    if conversion:
        response['result'] = conversion
        response['speech'] = conversion
        return response

    # 3. Equation Solving (now returns dict with display/speech)
    equation = math_engine.check_equation(text)
    if equation:
        if isinstance(equation, dict):
            response['result'] = equation.get('display', '')
            response['speech'] = equation.get('speech', '')
        else:
            response['result'] = equation
            response['speech'] = equation
        return response

    # 4. Matrix Operations
    matrix = math_engine.check_matrix(text)
    if matrix:
        response['result'] = matrix
        response['speech'] = matrix
        return response

    # 5. Graphing (2D and 3D)
    if math_engine.is_graphing_command(text):
        is_3d = '3d' in text.lower()
        clean_text = text.lower().replace('3d', '').strip()
        func_str = math_engine.get_graph_function(clean_text)

        try:
            if is_3d:
                # 3D Surface Plot
                fig = plt.figure(figsize=(7, 5))
                ax = fig.add_subplot(111, projection='3d')

                x_sym, y_sym = sympy.symbols('x y')
                f = math_engine._parse_safe(func_str.replace(' ', ''))
                if f is None:
                    f = sympy.sympify(func_str)
                f_lambdified = sympy.lambdify((x_sym, y_sym), f, modules=['numpy'])

                x_vals = np.linspace(-5, 5, 50)
                y_vals = np.linspace(-5, 5, 50)
                X, Y = np.meshgrid(x_vals, y_vals)
                Z = f_lambdified(X, Y)

                ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.85)
                pretty_func = math_engine.pretty_func_name(func_str)
                ax.set_title(f"z = {pretty_func}", fontsize=13)
                ax.set_xlabel('x')
                ax.set_ylabel('y')
                ax.set_zlabel('z')
            else:
                # 2D Plot
                plt.figure(figsize=(6, 4))
                x = sympy.symbols('x')
                f = math_engine._parse_safe(func_str)
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
            plt.close('all')

            pretty_func = math_engine.pretty_func_name(func_str)
            graph_type = "3D graph" if is_3d else "Graph"
            response['graph'] = plot_url
            response['speech'] = f"Plotting {pretty_func}"
            response['result'] = f"{graph_type} of {pretty_func}"
        except Exception as e:
            plt.close('all')
            response['speech'] = "I could not plot that function."
            response['result'] = f"Graph Error: {str(e)}"

        return response

    # 6. Calculus (now returns dict with display/speech)
    calculus_result = math_engine.check_calculus(text)
    if calculus_result:
        if isinstance(calculus_result, dict):
            response['result'] = calculus_result.get('display', '')
            response['speech'] = calculus_result.get('speech', '')
        else:
            response['result'] = calculus_result
            response['speech'] = calculus_result
        return response

    # 7. Evaluate Math
    result = math_engine.evaluate(text)
    if result:
        response['result'] = result
        response['speech'] = f"The answer is {result}"
    else:
        response['speech'] = "I didn't understand that."
        response['result'] = None

    return response


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

    if not math_engine.check_rate_limit():
        return jsonify({'result': "Rate limit exceeded. Please slow down.", 'speech': "Too many requests."})

    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        lang = data.get('lang', 'en-US')

        if not text:
            return jsonify({'result': 'No command received'})

        # Translate if not English
        if translator and not lang.startswith('en'):
            try:
                text = translator(source='auto', target='en').translate(text)
            except Exception:
                pass  # Fall through with original text

        # Split into multiple commands by "then" / "also"
        sub_commands = re.split(r'\b(?:then|also)\b', text, flags=re.IGNORECASE)
        sub_commands = [cmd.strip() for cmd in sub_commands if cmd.strip()]

        if len(sub_commands) <= 1:
            # Single command — return directly
            response = process_single_command(text)
            return jsonify(response)

        # Multiple commands — combine results
        all_results = []
        all_speech = []
        last_graph = None
        last_action = None

        for cmd in sub_commands:
            resp = process_single_command(cmd)
            if resp.get('result'):
                all_results.append(resp['result'])
            if resp.get('speech'):
                all_speech.append(resp['speech'])
            if resp.get('graph'):
                last_graph = resp['graph']
            if resp.get('action'):
                last_action = resp['action']

        return jsonify({
            'result': ' ➜ '.join(all_results),
            'speech': '. '.join(all_speech),
            'graph': last_graph,
            'action': last_action
        })

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
