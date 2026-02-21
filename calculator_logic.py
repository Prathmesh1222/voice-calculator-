import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
try:
    import pytesseract
except ImportError:
    pytesseract = None
from PIL import Image
import re


class MathEngine:
    def __init__(self):
        self.transformations = (standard_transformations + (implicit_multiplication_application,))

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
        # Make output readable
        result = result.replace('**2', '²').replace('**3', '³')
        result = result.replace('**', '^')
        result = result.replace('*', '·')
        result = result.replace('sqrt', '√')
        return result

    def pretty_func_name(self, func_str):
        """Clean up a function string for display in graph titles."""
        pretty = func_str.strip()
        # Collapse spaces before ** so 'x **2' becomes 'x**2'
        pretty = re.sub(r'\s*\*\*\s*', '**', pretty)
        pretty = pretty.replace('**2', '²').replace('**3', '³')
        pretty = pretty.replace('**', '^')
        pretty = pretty.replace('*', '·')
        return pretty

    def _clean_calculus_input(self, text):
        """Shared NLP cleanup for calculus inputs."""
        # Remove all known trigger/filler words
        remove_words = [
            'differentiation of', 'differentiate', 'derivative of', 'derivative',
            'derive', 'differentiation',
            'integration of', 'integral of', 'integrate', 'integral', 'integration',
            'with respect to x', 'with respect to',
            'of',  # catch any remaining "of"
        ]
        for phrase in remove_words:
            text = text.replace(phrase, ' ')

        # NLP -> Math symbol replacements
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

        # Collapse whitespace
        text = ' '.join(text.split())
        return text.strip()

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

            result = self._parse_safe(expression).evalf()
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
            try:
                if any(w in expression.split() for w in ['and', 'or', 'not', 'is']):
                    return None
                return str(eval(expression))
            except Exception:
                return None

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
