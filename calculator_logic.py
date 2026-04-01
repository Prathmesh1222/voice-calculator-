import sympy
from sympy import latex as sympy_latex
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
try:
    import pytesseract
except ImportError:
    pytesseract = None
from PIL import Image
import re
import time


class MathEngine:
    def __init__(self):
        self.transformations = (standard_transformations + (implicit_multiplication_application,))
        self._request_times = []  # For rate limiting

    def _parse_safe(self, text):
        """Parse text into a SymPy expression, handling implicit multiplication."""
        text = text.strip()
        if not text:
            return None
        try:
            return parse_expr(text, transformations=self.transformations)
        except Exception:
            try:
                return sympy.sympify(text)
            except Exception:
                return None

    def _pretty_result(self, expr):
        """Convert SymPy expression to clean, human-readable string."""
        result = str(expr)
        result = result.replace('**2', '²').replace('**3', '³')
        result = result.replace('**', '^')
        result = result.replace('*', '·')
        result = result.replace('sqrt', '√')
        return result

    def _latex_result(self, expr):
        """Convert SymPy expression to LaTeX string for KaTeX rendering."""
        return sympy_latex(expr)

    def pretty_func_name(self, func_str):
        """Clean up a function string for display in graph titles."""
        pretty = func_str.strip()
        pretty = re.sub(r'\s*\*\*\s*', '**', pretty)
        pretty = pretty.replace('**2', '²').replace('**3', '³')
        pretty = pretty.replace('**', '^')
        pretty = pretty.replace('*', '·')
        return pretty

    def clean_voice_text(self, text):
        """Regex-based pre-processor to convert natural language to math syntax."""
        text = text.lower().strip()
        
        # 0. Strip filler words from the beginning
        text = re.sub(r'^(?:lord|hey|hi|calculator|please|ok|okay)\s*', '', text)

        # Word numbers to digits
        word_numbers = {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
            'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
            'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
            'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
            'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
            'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
            'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '1000',
            'million': '1000000',
        }
        for word, digit in word_numbers.items():
            text = re.sub(r'\b' + word + r'\b', digit, text)

        # 2. Specific constructs "X of Y and Z" or "Op X by Y"
        # We use word boundaries to avoid partial matches (e.g., 'divide' matching 'divided')
        constructs = {
            "sum of": "+",
            "addition of": "+",
            "difference of": "-",
            "subtraction of": "-",
            "product of": "*",
            "multiplication of": "*",
            "division of": "/",
            "multiply": "*",
            "divide": "/",
        }
        for word, op in constructs.items():
            pattern = r'\b' + word + r'\b'
            if re.search(pattern, text):
                text = re.sub(pattern, "", text)
                if "and" in text:
                    text = text.replace("and", op)
                elif "by" in text:
                    text = text.replace("by", op)

        # Basic math symbols
        replacements = {
            "of": "",
            "plus": "+",
            "minus": "-",
            "times": "*",
            "multiplied by": "*",
            "divided by": "/",
            "over": "/",
            "into": "*",
            "equal to": "=",
            "equals": "=",
            "equal": "=",
            "is": "=",
            "square": "**2",
            "squared": "**2",
            "cube": "**3",
            "cubed": "**3",
            "square root of": "sqrt(",
            "root of": "sqrt(",
            "power": "**",
            "raised to": "**",
            "^": "**",
            "sine": "sin",
            "cosine": "cos",
            "tangent": "tan",
            "logarithm": "log",
            "exponential": "exp",
            "oneplus": "1+",
            "and": "+", # Fallback for "1 and 2"
        }
        
        # Sort replacements by length descending
        sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
        
        for word in sorted_keys:
            if word in ["and"] and any(op in text for op in ["+", "-", "*", "/"]):
                 continue # Skip fallback 'and' if we already have an operator
            text = text.replace(word, replacements[word])

        # Clean parentheses
        if "sqrt(" in text and ")" not in text:
            text += ")"

        # Special: remove spaces around operators for cleaner parsing
        text = re.sub(r'\s*(\*\*|\+|\-|\*|/|=)\s*', r'\1', text)
        
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Special for lists: convert '1, 2, 3' or '1 2 3' after '=' to space-separated values
        # If there's an '=' and the RHS looks like a list
        if "=" in text:
            lhs, rhs = text.split("=", 1)
            # If RHS contains commas between digits, keep them but normalize spaces
            rhs = re.sub(r'(\d+)\s*,\s*(\d+)', r'\1,\2', rhs)
            text = f"{lhs}={rhs}"

        return text.strip()

    def parse_intent(self, text):
        """Analyze voice text and return structured JSON with action + expression."""
        clean_text = self.clean_voice_text(text)
        action = "CALCULATE"
        
        lower_text = text.lower()
        if "3d" in lower_text:
            action = "PLOT_3D"
        elif any(w in lower_text for w in ["plot", "graph", "draw"]):
            action = "PLOT_2D"
        elif any(w in lower_text for w in ["solve", "find x", "find the value"]):
            action = "SOLVE"
        elif any(w in lower_text for w in ["differentiate", "derivative", "derive"]):
            action = "DERIVE"
        elif any(w in lower_text for w in ["integrate", "integral"]):
            action = "INTEGRATE"

        # Special check for plot action: if 'y' is in expression, auto-detect 3D
        if action == "PLOT_2D" and "y" in clean_text and "=" not in clean_text:
             action = "PLOT_3D"

        # Strip action keywords from the expressions
        expr = clean_text
        keywords = ["plot", "graph", "draw", "3d", "solve", "find x", "find the value of", 
                    "differentiate", "derivative of", "derivative", "derive", 
                    "integrate", "integral of", "integral", "calculate"]
        for k in keywords:
            cleaned_k = self.clean_voice_text(k)
            # Remove from start of text primarily to avoid stripping math content
            if expr.startswith(cleaned_k):
                expr = expr[len(cleaned_k):].strip()
            else:
                expr = expr.replace(cleaned_k, "").strip()

        # Handle implicit equations: x + y = 4 -> x + y - 4
        # NEW: Handle multiple RHS values (levels)
        levels = []
        if "=" in expr and action not in ["SOLVE"]:
            parts = expr.split("=")
            if len(parts) == 2:
                lhs = parts[0].strip()
                rhs = parts[1].strip()
                # Check for list in RHS: '4,5,6' or '4 5 6'
                # Use split by comma or space if it looks like a list of numbers
                val_strings = re.split(r'[,\s]+', rhs)
                try:
                    # Only treat as levels if all are numeric
                    levels = [float(v) for v in val_strings if v.strip()]
                    if len(levels) > 1:
                        # Limit to 5 levels for performance
                        levels = levels[:5]
                        expr = lhs # The base function to plot against the levels
                    elif len(levels) == 1:
                        expr = f"({lhs})-({rhs})" # Standard implicit Eq
                    else:
                        expr = f"({lhs})-({rhs})"
                except ValueError:
                    # Not a numeric list, treat as normal implicit Eq
                    expr = f"({lhs})-({rhs})"

        # Identify variables
        vars = []
        if "x" in expr: vars.append("x")
        if "y" in expr: vars.append("y")
        if "z" in expr: vars.append("z")
        
        return {
            "action": action,
            "expression": expr,
            "levels": levels,
            "variables": vars if vars else ["x"]
        }

    def _clean_calculus_input(self, text):
        """Refactored to use central cleaner."""
        return self.clean_voice_text(text)

    # ========== RATE LIMITING ==========
    def check_rate_limit(self, max_requests=30, window_seconds=60):
        """Returns True if within rate limit, False if exceeded."""
        now = time.time()
        self._request_times = [t for t in self._request_times if now - t < window_seconds]
        if len(self._request_times) >= max_requests:
            return False
        self._request_times.append(now)
        return True

    # ========== UNIT CONVERSIONS ==========
    def check_unit_conversion(self, text):
        """Handle unit conversion commands."""
        text = text.lower().strip()

        # Match patterns like "convert 5 km to miles"
        pattern = r'(?:convert\s+)?([\d.]+)\s*([a-zA-Z°]+)\s+(?:to|in)\s+([a-zA-Z°]+)'
        match = re.search(pattern, text)
        if not match:
            return None

        value = float(match.group(1))
        from_unit = match.group(2).lower().strip()
        to_unit = match.group(3).lower().strip()

        conversions = {
            # Length
            ('km', 'miles'): lambda v: v * 0.621371,
            ('miles', 'km'): lambda v: v * 1.60934,
            ('m', 'feet'): lambda v: v * 3.28084,
            ('m', 'ft'): lambda v: v * 3.28084,
            ('feet', 'm'): lambda v: v / 3.28084,
            ('ft', 'm'): lambda v: v / 3.28084,
            ('cm', 'inches'): lambda v: v / 2.54,
            ('cm', 'inch'): lambda v: v / 2.54,
            ('inches', 'cm'): lambda v: v * 2.54,
            ('inch', 'cm'): lambda v: v * 2.54,
            ('m', 'cm'): lambda v: v * 100,
            ('cm', 'm'): lambda v: v / 100,
            ('km', 'm'): lambda v: v * 1000,
            ('m', 'km'): lambda v: v / 1000,

            # Weight
            ('kg', 'lbs'): lambda v: v * 2.20462,
            ('kg', 'pounds'): lambda v: v * 2.20462,
            ('lbs', 'kg'): lambda v: v / 2.20462,
            ('pounds', 'kg'): lambda v: v / 2.20462,
            ('g', 'kg'): lambda v: v / 1000,
            ('kg', 'g'): lambda v: v * 1000,

            # Temperature
            ('celsius', 'fahrenheit'): lambda v: v * 9/5 + 32,
            ('c', 'f'): lambda v: v * 9/5 + 32,
            ('°c', '°f'): lambda v: v * 9/5 + 32,
            ('fahrenheit', 'celsius'): lambda v: (v - 32) * 5/9,
            ('f', 'c'): lambda v: (v - 32) * 5/9,
            ('°f', '°c'): lambda v: (v - 32) * 5/9,
            ('celsius', 'kelvin'): lambda v: v + 273.15,
            ('c', 'k'): lambda v: v + 273.15,
            ('kelvin', 'celsius'): lambda v: v - 273.15,
            ('k', 'c'): lambda v: v - 273.15,

            # Speed
            ('kmph', 'mph'): lambda v: v * 0.621371,
            ('mph', 'kmph'): lambda v: v * 1.60934,

            # Data
            ('gb', 'mb'): lambda v: v * 1024,
            ('mb', 'gb'): lambda v: v / 1024,
            ('mb', 'kb'): lambda v: v * 1024,
            ('kb', 'mb'): lambda v: v / 1024,
        }

        key = (from_unit, to_unit)
        if key in conversions:
            result = conversions[key](value)
            if result == int(result):
                result = int(result)
            else:
                result = round(result, 4)
            return f"{value} {from_unit} = {result} {to_unit}"

        return None

    # ========== EQUATION SOLVING ==========
    def check_equation(self, text):
        """Handle equation solving commands like 'solve x squared minus 4 equals 0'."""
        text = self.clean_voice_text(text)
        if not any(w in text for w in ['solve', 'find x', 'find the value']):
            return None

        intent = self.parse_intent(text)
        text = intent['expression']

        try:
            x = sympy.symbols('x')
            if '=' in text:
                parts = text.split('=')
                lhs = self._parse_safe(parts[0].strip())
                rhs = self._parse_safe(parts[1].strip())
                if lhs is None or rhs is None:
                    return None
                equation = sympy.Eq(lhs, rhs)
            else:
                # Assume equals 0
                expr = self._parse_safe(text)
                if expr is None:
                    return None
                equation = sympy.Eq(expr, 0)

            solutions = sympy.solve(equation, x)
            if not solutions:
                return {'display': 'No real solutions found', 'speech': 'No real solutions found'}

            pretty_solutions = [self._pretty_result(s) for s in solutions]
            latex_solutions = [self._latex_result(s) for s in solutions]
            speech = f"x equals {', '.join(pretty_solutions)}"
            display = f"$$x = {', \\;'.join(latex_solutions)}$$"
            return {'display': display, 'speech': speech}
        except Exception:
            return None

    # ========== MATRIX OPERATIONS ==========
    def check_matrix(self, text):
        """Handle matrix operations like 'determinant of [[1,2],[3,4]]'."""
        text = text.lower().strip()

        if 'determinant' in text:
            # Extract matrix
            matrix_match = re.search(r'\[\[.*?\]\]', text)
            if not matrix_match:
                return None
            try:
                import ast
                matrix_data = ast.literal_eval(matrix_match.group())
                m = sympy.Matrix(matrix_data)
                det = m.det()
                return f"Determinant = {self._pretty_result(det)}"
            except Exception:
                return None

        if 'inverse' in text:
            matrix_match = re.search(r'\[\[.*?\]\]', text)
            if not matrix_match:
                return None
            try:
                import ast
                matrix_data = ast.literal_eval(matrix_match.group())
                m = sympy.Matrix(matrix_data)
                inv = m.inv()
                return f"Inverse = {str(inv.tolist())}"
            except Exception:
                return "Matrix is not invertible"

        if 'transpose' in text:
            matrix_match = re.search(r'\[\[.*?\]\]', text)
            if not matrix_match:
                return None
            try:
                import ast
                matrix_data = ast.literal_eval(matrix_match.group())
                m = sympy.Matrix(matrix_data)
                t = m.T
                return f"Transpose = {str(t.tolist())}"
            except Exception:
                return None

        return None

    # ========== EVALUATE (Math) ==========
    def evaluate(self, expression):
        expression = self.clean_voice_text(expression)
        
        if not expression:
            return None

        # Division by zero check
        if re.search(r'/\s*0(\.0*)?\s*$', expression) or re.search(r'/\s*0(\.0*)?\s*[^.]', expression):
            return "Error: Cannot divide by zero"

        try:
            if expression.count('(') > expression.count(')'):
                expression += ')' * (expression.count('(') - expression.count(')'))

            result = self._parse_safe(expression)
            if result is None:
                return None
            result = result.evalf()
            val = float(result)
            if val == float('inf') or val == float('-inf'):
                return "Error: Cannot divide by zero"
            if val != val:  # NaN check
                return "Error: Undefined result"
            if val.is_integer():
                return str(int(val))
            return str(round(val, 4))
        except ZeroDivisionError:
            return "Error: Cannot divide by zero"
        except Exception:
            return None

    # ========== CALCULUS ==========
    def check_calculus(self, text):
        text_lower = text.lower()

        # 1. Differentiation
        if any(w in text_lower for w in ['differentiate', 'derivative', 'derive', 'differentiation']):
            intent = self.parse_intent(text)
            expr_str = intent['expression']
            try:
                x = sympy.symbols('x')
                expr = self._parse_safe(expr_str)
                if expr is None:
                    return None
                result = sympy.diff(expr, x)
                pretty = self._pretty_result(result)
                latex_str = self._latex_result(result)
                return {
                    'display': f"Derivative: $$\\frac{{d}}{{dx}} {self._latex_result(expr)} = {latex_str}$$",
                    'speech': f"Derivative is {pretty}"
                }
            except Exception:
                return None

        # 2. Integration
        if any(w in text_lower for w in ['integrate', 'integral', 'integration']):
            intent = self.parse_intent(text)
            expr_str = intent['expression']
            try:
                x = sympy.symbols('x')
                expr = self._parse_safe(expr_str)
                if expr is None:
                    return None
                result = sympy.integrate(expr, x)
                pretty = self._pretty_result(result)
                latex_str = self._latex_result(result)
                return {
                    'display': f"Integral: $$\\int {self._latex_result(expr)} \\, dx = {latex_str} + C$$",
                    'speech': f"Integral is {pretty} plus C"
                }
            except Exception:
                return None

        return None

    # ========== GRAPHING ==========
    def is_graphing_command(self, text):
        return text.lower().startswith(('plot', 'graph', 'draw'))

    def get_graph_function(self, text):
        intent = self.parse_intent(text)
        return intent['expression']

    def check_antigravity(self, text):
        keywords = ['activate antigravity', 'python fly', 'fly python']
        for k in keywords:
            if k in text.lower():
                return True
        return False


class ImageHandler:
    def extract_text(self, image_path):
        if pytesseract is None:
            return "OCR Library not installed on server."
        try:
            img = Image.open(image_path)
            try:
                text = pytesseract.image_to_string(img)
                return text.strip()
            except Exception:
                return "Tesseract Binary not found on server."
        except Exception as e:
            return str(e)
