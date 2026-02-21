import sympy
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

    def pretty_func_name(self, func_str):
        """Clean up a function string for display in graph titles."""
        pretty = func_str.strip()
        pretty = re.sub(r'\s*\*\*\s*', '**', pretty)
        pretty = pretty.replace('**2', '²').replace('**3', '³')
        pretty = pretty.replace('**', '^')
        pretty = pretty.replace('*', '·')
        return pretty

    def _clean_calculus_input(self, text):
        """Shared NLP cleanup for calculus inputs."""
        remove_words = [
            'differentiation of', 'differentiate', 'derivative of', 'derivative',
            'derive', 'differentiation',
            'integration of', 'integral of', 'integrate', 'integral', 'integration',
            'with respect to x', 'with respect to',
            'of',
        ]
        for phrase in remove_words:
            text = text.replace(phrase, ' ')

        text = text.replace('x squared', 'x**2').replace('x cubed', 'x**3')
        text = text.replace('squared', '**2').replace('cubed', '**3')
        text = text.replace('square', '**2').replace('cube', '**3')
        text = text.replace('sqaure', '**2')
        text = text.replace('sine', 'sin').replace('cosine', 'cos').replace('tangent', 'tan')
        text = text.replace('logarithm', 'log')
        text = text.replace('exponential', 'exp')
        text = text.replace('e power x', 'exp(x)').replace('e power', 'exp')
        text = text.replace('power', '**').replace('raised to', '**')
        text = text.replace('^', '**')

        text = ' '.join(text.split())
        return text.strip()

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
        text = text.lower().strip()

        if not any(w in text for w in ['solve', 'find x', 'find the value']):
            return None

        # Remove trigger words
        for w in ['solve', 'find the value of', 'find x for', 'find x in', 'find x']:
            text = text.replace(w, '')

        # NLP cleanup
        text = text.replace('x squared', 'x**2').replace('x cubed', 'x**3')
        text = text.replace('squared', '**2').replace('cubed', '**3')
        text = text.replace('square', '**2').replace('cube', '**3')
        text = text.replace('equals', '=').replace('equal to', '=').replace('equal', '=')
        text = text.replace('minus', '-').replace('plus', '+')
        text = text.replace('times', '*').replace('divided by', '/')
        text = text.replace('^', '**')
        text = text.strip()

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
                return "No real solutions found"

            pretty_solutions = [self._pretty_result(s) for s in solutions]
            if len(pretty_solutions) == 1:
                return f"x = {pretty_solutions[0]}"
            else:
                return f"x = {', '.join(pretty_solutions)}"
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
        expression = expression.lower()

        # 1. Handle specific natural language constructs
        if 'subtraction of' in expression or 'difference of' in expression:
            expression = expression.replace('subtraction of', '').replace('difference of', '')
            expression = expression.replace('and', '-')

        elif 'product of' in expression or 'multiplication of' in expression:
            expression = expression.replace('product of', '').replace('multiplication of', '')
            expression = expression.replace('and', '*')

        elif 'division of' in expression:
            expression = expression.replace('division of', '')
            expression = expression.replace('by', '/').replace('and', '/')
        elif 'divided by' in expression:
            expression = expression.replace('divided by', '/')
        elif 'divide' in expression and 'by' in expression:
            expression = expression.replace('divide', '').replace('by', '/')

        elif 'multiply' in expression and 'by' in expression:
            expression = expression.replace('multiply', '').replace('by', '*')

        elif 'addition of' in expression or 'sum of' in expression:
            expression = expression.replace('addition of', '').replace('sum of', '')
            expression = expression.replace('and', '+')

        elif 'square root of' in expression or 'root of' in expression:
            expression = expression.replace('square root of', 'sqrt(').replace('root of', 'sqrt(')
            expression += ')'

        # 2. General Replacements
        nl_replacements = {
            'oneplus': '1 +',
            'minus': '-', 'multiply': '*', 'divide': '/',
            'plus': '+', 'times': '*', 'into': '*', 'over': '/',
            'power': '**', 'raised to': '**',
            'squared': '**2', 'cubed': '**3',
            'square': '**2', 'cube': '**3',
            'logarithm': 'log', 'log': 'log', 'ln': 'ln',
            'exponential': 'exp',
        }

        for word, symbol in nl_replacements.items():
            expression = expression.replace(word, symbol)

        # 3. Fallback "and" handling
        if re.search(r'\d+\s+and\s+\d+', expression):
            if not any(op in expression for op in ['-', '*', '/', '**']):
                expression = expression.replace('and', '+')

        expression = expression.strip()

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
        text = text.lower()

        # 1. Differentiation
        if any(w in text for w in ['differentiate', 'derivative', 'derive', 'differentiation']):
            text = self._clean_calculus_input(text)
            try:
                x = sympy.symbols('x')
                expr = self._parse_safe(text)
                if expr is None:
                    return None
                result = sympy.diff(expr, x)
                pretty = self._pretty_result(result)
                return f"Derivative = {pretty}"
            except Exception:
                return None

        # 2. Integration
        if any(w in text for w in ['integrate', 'integral', 'integration']):
            text = self._clean_calculus_input(text)
            try:
                x = sympy.symbols('x')
                expr = self._parse_safe(text)
                if expr is None:
                    return None
                result = sympy.integrate(expr, x)
                pretty = self._pretty_result(result)
                return f"Integral = {pretty} + C"
            except Exception:
                return None

        return None

    # ========== GRAPHING ==========
    def is_graphing_command(self, text):
        return text.lower().startswith(('plot', 'graph', 'draw'))

    def get_graph_function(self, text):
        for word in ['plot', 'graph', 'draw']:
            text = text.lower().replace(word, '')

        text = text.replace('sine', 'sin').replace('cosine', 'cos').replace('tangent', 'tan')
        text = text.replace('squared', '**2').replace('cubed', '**3')
        text = text.replace('square', '**2').replace('cube', '**3')
        text = text.replace('sqaure', '**2')
        text = text.replace('^', '**')
        return text.strip()

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
