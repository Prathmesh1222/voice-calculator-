
import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
try:
    import pytesseract
except ImportError:
    pytesseract = None
from PIL import Image

class MathEngine:
    def __init__(self):
        # Transformations for implicit mult
        self.transformations = (standard_transformations + (implicit_multiplication_application,))

    def _parse_safe(self, text):
        try:
            return parse_expr(text, transformations=self.transformations)
        except Exception:
            try:
                return sympy.sympify(text) # Fallback
            except:
                return sympy.sympify(text)

    def evaluate(self, expression):
        expression = expression.lower()
        
        # 1. Handle specific natural language constructs that change the operator structure
        import re
        
        # Subtraction: "subtraction of 5 and 2", "difference of 5 and 2", "5 minus 2"
        if 'subtraction of' in expression or 'difference of' in expression:
            expression = expression.replace('subtraction of', '').replace('difference of', '')
            # Replace 'and' with '-'
            expression = expression.replace('and', '-')
        
        # Product: "product of 5 and 2", "multiplication of 5 and 2"
        elif 'product of' in expression or 'multiplication of' in expression:
            expression = expression.replace('product of', '').replace('multiplication of', '')
            expression = expression.replace('and', '*')
            
        # Division: "division of 10 by 2", "10 divided by 2", "divide 10 by 2"
        elif 'division of' in expression:
            expression = expression.replace('division of', '')
            expression = expression.replace('by', '/').replace('and', '/')
        elif 'divided by' in expression:
            expression = expression.replace('divided by', '/')
        elif 'divide' in expression and 'by' in expression:
             expression = expression.replace('divide', '').replace('by', '/')

        # Multiplication: "multiply 5 by 2"
        elif 'multiply' in expression and 'by' in expression:
             expression = expression.replace('multiply', '').replace('by', '*')

        # Addition: "addition of 1 and 2", "sum of 1 and 2"
        elif 'addition of' in expression or 'sum of' in expression:
            expression = expression.replace('addition of', '').replace('sum of', '')
            expression = expression.replace('and', '+')
            
        # Square Root: "square root of 16", "root of 16"
        elif 'square root of' in expression or 'root of' in expression:
             expression = expression.replace('square root of', 'sqrt(').replace('root of', 'sqrt(')
             expression += ')' # Close parenthesis logic is tricky, usually just assume end of string
        
        # 2. General Replacements
        nl_replacements = {
            'oneplus': '1 +',
            'minus': '-',
            'multiply': '*',
            'divide': '/',
            'plus': '+', 'times': '*', 'into': '*', 'over': '/', 
            'power': '**', 'raised to': '**',
            'squared': '**2', 'cubed': '**3',
            'square': '**2', 'cube': '**3',
            'logarithm': 'log', 'log': 'log', 'ln': 'ln',
            'exponential': 'exp',
        }
        
        for word, symbol in nl_replacements.items():
            expression = expression.replace(word, symbol)

        # 3. Fallback "and" handling for "1 and 2" -> "1 + 2" (Default to addition if no context)
        if re.search(r'\d+\s+and\s+\d+', expression):
            if not any(op in expression for op in ['-', '*', '/', '**']):
                 expression = expression.replace('and', '+')

        # Cleanup whitespace
        expression = expression.strip()
        
        try:
            # Use sympy for safe evaluation
            # Handle sqrt parenthesis automatically if we just prepended it
            # e.g. "sqrt( 16" -> sympy might need closing, but evalf usually needs syntactically correct string.
            # Let's try to balance parentheses if we added an opening one.
            if expression.count('(') > expression.count(')'):
                expression += ')' * (expression.count('(') - expression.count(')'))

            result = self._parse_safe(expression).evalf()
            val = float(result)
            if val.is_integer():
                return str(int(val))
            return str(round(val, 4))
        except Exception:
            try:
                 # Last resort eval
                 if any(w in expression.split() for w in ['and', 'or', 'not', 'is']):
                     return None
                 return str(eval(expression))
            except Exception:
                return None

    def check_calculus(self, text):
        text = text.lower()
        
        # 1. Differentiation
        if any(w in text for w in ['differentiate', 'derivative', 'derive', 'differentiation']):
            # Cleanup - Sort by length descending to match longest phrases first
            cleanup_phrases = ['differentiation of', 'derivative of', 'differentiate', 'derivative', 'derive', 'differentiation', 'with respect to x']
            for w in cleanup_phrases:
                text = text.replace(w, '')
            
            # NLP replacements (shared with evaluate)
            text = text.replace('squared', '**2').replace('cubed', '**3')
            text = text.replace('square', '**2').replace('cube', '**3')
            text = text.replace('sqaure', '**2')
            text = text.replace('sine', 'sin').replace('cosine', 'cos').replace('tangent', 'tan')
            text = text.replace('^', '**')
            text = text.replace('logarithm', 'log').replace('log', 'log').replace('ln', 'ln')
            text = text.replace('exponential', 'exp').replace('e power', 'exp')
            text = text.replace('power', '**').replace('raised to', '**')
            
            try:
                x = sympy.symbols('x')
                expr = self._parse_safe(text)
                result = sympy.diff(expr, x)
                return f"Derivative is {str(result)}"
            except Exception as e:
                return None

        # 2. Integration
        if any(w in text for w in ['integrate', 'integral', 'integration']):
            # Cleanup
            cleanup_phrases = ['integration of', 'integral of', 'integrate', 'integral', 'integration', 'with respect to x']
            for w in cleanup_phrases:
                text = text.replace(w, '')
            
            # NLP replacements
            text = text.replace('squared', '**2').replace('cubed', '**3')
            text = text.replace('square', '**2').replace('cube', '**3')
            text = text.replace('sqaure', '**2')
            text = text.replace('sine', 'sin').replace('cosine', 'cos').replace('tangent', 'tan')
            text = text.replace('^', '**')
            text = text.replace('logarithm', 'log').replace('log', 'log').replace('ln', 'ln')
            text = text.replace('exponential', 'exp').replace('e power', 'exp')
            text = text.replace('power', '**').replace('raised to', '**')
            
            try:
                x = sympy.symbols('x')
                expr = self._parse_safe(text)
                result = sympy.integrate(expr, x)
                return f"Integral is {str(result)} + C"
            except Exception as e:
                return None
        
        return None

    def is_graphing_command(self, text):
        return text.lower().startswith(('plot', 'graph', 'draw'))

    def get_graph_function(self, text):
        # Remove trigger words
        for word in ['plot', 'graph', 'draw']:
            text = text.lower().replace(word, '')
        
        # Clean up the function string for sympy/matplotlib
        text = text.replace('sine', 'sin').replace('cosine', 'cos').replace('tangent', 'tan')
        text = text.replace('squared', '**2').replace('cubed', '**3')
        text = text.replace('square', '**2').replace('cube', '**3')
        text = text.replace('sqaure', '**2') # Handle typo
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
            # Check if tesseract binary is available
            try:
                text = pytesseract.image_to_string(img)
                return text.strip()
            except Exception:
                 return "Tesseract Binary not found on server."
        except Exception as e:
            return str(e)
