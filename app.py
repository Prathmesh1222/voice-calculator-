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
    """Process a single command using intent parsing and return a response dict."""
    response = {
        'speech': '',
        'result': '',
        'graph': None,
        'action': None
    }

    try:
        # 1. Antigravity check
        if math_engine.check_antigravity(text):
            response['action'] = 'antigravity'
            response['speech'] = 'Activating anti gravity mode'
            response['result'] = 'Antigravity Activated 🚀'
            return response

        # 2. Parse Intent
        intent = math_engine.parse_intent(text)
        action = intent['action']
        expr_str = intent['expression']
        response['action'] = action

        # 3. Handle Actions
        if action == "PLOT_2D" or action == "PLOT_3D":
             return handle_graphing(intent, action == "PLOT_3D", response)
        
        elif action == "SOLVE":
            result = math_engine.check_equation(text)
            if result:
                response['result'] = result.get('display', '')
                response['speech'] = result.get('speech', '')
                return response

        elif action == "DERIVE" or action == "INTEGRATE":
            result = math_engine.check_calculus(text)
            if result:
                response['result'] = result.get('display', '')
                response['speech'] = result.get('speech', '')
                return response

        # Fallback to Unit Conversion or General Evaluation
        conversion = math_engine.check_unit_conversion(text)
        if conversion:
            response['result'] = conversion
            response['speech'] = conversion
            return response

        matrix = math_engine.check_matrix(text)
        if matrix:
            response['result'] = matrix
            response['speech'] = matrix
            return response

        result = math_engine.evaluate(text)
        if result:
            response['result'] = result
            response['speech'] = f"The answer is {result}"
        else:
            response['speech'] = "I didn't understand that math. Could you rephrase?"
            response['result'] = None

    except sympy.SympifyError:
        response['speech'] = "I caught the equation, but the format is a bit tricky."
        response['result'] = f"Parsing Error: Could not understand '{text}'"
    except ZeroDivisionError:
        response['speech'] = "Wait, I can't divide by zero!"
        response['result'] = "Error: Division by zero"
    except Exception as e:
        response['speech'] = "Something went wrong while calculating."
        response['result'] = f"Error: {str(e)}"

    return response

def handle_graphing(intent, is_3d, response):
    func_str = intent['expression']
    levels = intent.get('levels', [])
    try:
        x_sym, y_sym, z_sym = sympy.symbols('x y z')
        local_dict = {'x': x_sym, 'y': y_sym, 'z': z_sym,
                      'sin': sympy.sin, 'cos': sympy.cos, 'tan': sympy.tan,
                      'log': sympy.log, 'exp': sympy.exp, 'sqrt': sympy.sqrt,
                      'abs': sympy.Abs}

        # Handle implicit equations like x**2 + y**2 - 4
        is_implicit = False
        if any(token in func_str for token in ["- (", "==", "="]) or levels:
             is_implicit = True

        f = sympy.sympify(func_str, locals=local_dict)
        pretty_func = math_engine.pretty_func_name(func_str)
        
        plt.close('all')
        if is_3d:
            fig = plt.figure(figsize=(7, 5))
            ax = fig.add_subplot(111, projection='3d')
            
            x_vals = np.linspace(-5, 5, 50)
            y_vals = np.linspace(-5, 5, 50)
            X, Y = np.meshgrid(x_vals, y_vals)
            
            if levels:
                # Plot multiple layers of z = f(x,y) if z_sym not in variables
                f_lambdified = sympy.lambdify((x_sym, y_sym), f, modules=['numpy'])
                colors = plt.cm.viridis(np.linspace(0, 1, len(levels)))
                for idx, level in enumerate(levels):
                    try:
                        # If levels provided for f(x,y)=C, we plot z = f(x,y) - C ? No.
                        # Usually user says z = x+y with levels 4,5,6 meaning z=4, z=5?
                        # But user request says "x+y = 4,5,3". 
                        # If it's 3D, we'll plot surfaces of z = x+y with target levels
                        Z = f_lambdified(X, Y) + level
                        if np.isscalar(Z): Z = np.full(X.shape, Z)
                        ax.plot_surface(X, Y, Z, color=colors[idx], alpha=0.5, label=f"Level {level}")
                    except Exception: continue
            else:
                # Standard z = f(x,y)
                f_lambdified = sympy.lambdify((x_sym, y_sym), f, modules=['numpy'])
                try:
                    Z = f_lambdified(X, Y)
                    if np.isscalar(Z): Z = np.full(X.shape, Z)
                    ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.85)
                except Exception:
                    response['speech'] = "I couldn't generate a 3D surface for that."
                    response['result'] = "3D Plot Error"
                    return response

            if levels and len(levels) > 1:
                title_str = f"z = {pretty_func}\nLevels: {', '.join(map(str, levels))}"
            else:
                title_str = f"z = {pretty_func}"
            
            ax.set_title(title_str, fontsize=15, fontweight='bold', pad=20)
            ax.set_xlabel('x-axis', fontsize=12, fontweight='600')
            ax.set_ylabel('y-axis', fontsize=12, fontweight='600')
            ax.set_zlabel('z-axis', fontsize=12, fontweight='600')
        else:
            plt.figure(figsize=(6, 4))
            if is_implicit:
                x_vals = np.linspace(-10, 10, 400)
                y_vals = np.linspace(-10, 10, 400)
                X, Y = np.meshgrid(x_vals, y_vals)
                f_lambdified = sympy.lambdify((x_sym, y_sym), f, modules=['numpy'])
                Z = f_lambdified(X, Y)
                if np.isscalar(Z): Z = np.full(X.shape, Z)
                
                if levels and len(levels) > 1:
                    # Multi-level contour plot
                    cs = plt.contour(X, Y, Z, levels=levels, cmap='plasma')
                    plt.clabel(cs, inline=True, fontsize=10)
                    plt.title(f"Contours of: {pretty_func}", fontsize=15, fontweight='bold', pad=15)
                elif levels and len(levels) == 1:
                    # Single level from a list input
                    plt.contour(X, Y, Z, [levels[0]], colors=['#6366f1'])
                    plt.title(f"Plot of: {pretty_func}", fontsize=15, fontweight='bold', pad=15)
                else:
                    plt.contour(X, Y, Z, [0], colors=['#6366f1'])
                    plt.title(f"Plot of: {pretty_func}", fontsize=15, fontweight='bold', pad=15)
            else:
                f_lambdified = sympy.lambdify(x_sym, f, modules=['numpy'])
                x_vals = np.linspace(-10, 10, 400)
                y_vals = f_lambdified(x_vals)
                if np.isscalar(y_vals): y_vals = np.full(x_vals.shape, y_vals)
                plt.plot(x_vals, y_vals, color='#6366f1', linewidth=2.5)
                plt.title(f"y = {pretty_func}", fontsize=15, fontweight='bold', pad=15)

            plt.xlabel('x-axis', fontsize=12, fontweight='600')
            plt.ylabel('y-axis', fontsize=12, fontweight='600')

            plt.grid(True, alpha=0.3)
            plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight', dpi=100)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close('all')

        graph_type = "3D graph" if is_3d else "Graph"
        response['graph'] = plot_url
        response['speech'] = f"Plotting {pretty_func}"
        response['result'] = f"{graph_type} of {pretty_func}"
    except Exception as e:
        plt.close('all')
        response['speech'] = "I could not plot that function."
        response['result'] = f"Graph Error: {str(e)}"
    
    return response


@app.route('/')
def index():
    if GLOBAL_ERROR:
        return f"<html><body><h1>Deployment Error</h1><pre>{GLOBAL_ERROR}</pre></body></html>", 500
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/parse_intent', methods=['POST'])
def parse_intent_endpoint():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': 'No text provided'})
        
        intent = math_engine.parse_intent(text)
        return jsonify(intent)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
