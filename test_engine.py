from calculator_logic import MathEngine
import sys

def test_math_engine():
    engine = MathEngine()
    
    test_cases = [
        ("oneplus 2", "3"),
        ("1 and 2", "3"),
        ("addition of 1 and 2", "3"),
        ("sum of 5 and 3", "8"),
        ("1 + 2", "3"),
        ("multiply 5 by 2", "10"),
        ("divide 10 by 2", "5"),
        ("5 minus 2", "3"),
        ("subtraction of 5 and 2", "3"),
        ("difference of 10 and 2", "8"),
        ("5 times 5", "25"),
        ("product of 4 and 5", "20"),
        ("10 divided by 2", "5"),
        ("division of 20 by 4", "5"),
        ("2 power 3", "8"),
        ("square root of 16", "4"),
        ("10 divided by 0", "Error: Cannot divide by zero"),
    ]
    
    conversion_tests = [
        ("convert 5 km to miles", "5.0 km = 3.1069 miles"),
        ("convert 100 celsius to fahrenheit", "100.0 celsius = 212 fahrenheit"),
        ("convert 1 kg to lbs", "1.0 kg = 2.2046 lbs"),
    ]

    print("\n--- Basic Math Tests ---\n")
    passed = 0
    failed = 0

    for input_text, expected in test_cases:
        result = engine.evaluate(input_text)
        status = "✓" if str(result) == str(expected) else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
        passed += 1 if str(result) == str(expected) else 0
        failed += 0 if str(result) == str(expected) else 1

    print(f"\n--- Calculus Tests (LaTeX) ---\n")
    calculus_tests = [
        ("differentiate x squared", "display"),
        ("differentiate log x", "display"),
        ("derivative of sin x", "display"),
        ("integrate x squared", "display"),
        ("integrate 2x", "display"),
    ]
    for input_text, _ in calculus_tests:
        result = engine.check_calculus(input_text)
        if result and isinstance(result, dict) and 'display' in result and 'speech' in result:
            print(f"  ✓ '{input_text}' -> display: '{result['display'][:60]}...'")
            print(f"                   speech: '{result['speech']}'")
            passed += 1
        else:
            print(f"  ✗ '{input_text}' -> '{result}' (expected dict with display/speech)")
            failed += 1

    print(f"\n--- Equation Tests (LaTeX) ---\n")
    equation_tests = [
        "solve x squared minus 4 equals 0",
        "solve x squared equals 9",
    ]
    for input_text in equation_tests:
        result = engine.check_equation(input_text)
        if result and isinstance(result, dict) and 'display' in result:
            print(f"  ✓ '{input_text}' -> display: '{result['display']}'")
            print(f"                   speech: '{result['speech']}'")
            passed += 1
        else:
            print(f"  ✗ '{input_text}' -> '{result}'")
            failed += 1

    print(f"\n--- Unit Conversion Tests ---\n")
    for input_text, expected in conversion_tests:
        result = engine.check_unit_conversion(input_text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
        passed += 1 if result == expected else 0
        failed += 0 if result == expected else 1

    print(f"\n--- Matrix Tests ---\n")
    result = engine.check_matrix("determinant of [[1,2],[3,4]]")
    status = "✓" if result == "Determinant = -2" else "✗"
    print(f"  {status} 'determinant of [[1,2],[3,4]]' -> '{result}'")
    passed += 1 if result == "Determinant = -2" else 0
    failed += 0 if result == "Determinant = -2" else 1

    print(f"\n--- LaTeX Output ---\n")
    from sympy import symbols
    x = symbols('x')
    latex = engine._latex_result(x**2 + 3*x)
    status = "✓" if '3' in latex and 'x' in latex else "✗"
    print(f"  {status} _latex_result(x²+3x) -> '{latex}'")
    passed += 1

    print(f"\n{'='*50}")
    print(f"  Results: {passed} Passed, {failed} Failed")
    print(f"{'='*50}\n")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    test_math_engine()
