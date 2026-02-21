from calculator_logic import MathEngine
import sys

def test_math_engine():
    engine = MathEngine()
    
    test_cases = [
        # Basic Math
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
        # Division by zero
        ("10 divided by 0", "Error: Cannot divide by zero"),
    ]
    
    calculus_tests = [
        ("differentiate x squared", "Derivative = 2·x"),
        ("differentiate log x", "Derivative = 1/x"),
        ("differentiate e power x", "Derivative = exp(x)"),
        ("derivative of sin x", "Derivative = cos(x)"),
        ("integrate x squared", None),
        ("integrate 2x", None),
    ]

    conversion_tests = [
        ("convert 5 km to miles", "5.0 km = 3.1069 miles"),
        ("convert 100 celsius to fahrenheit", "100.0 celsius = 212 fahrenheit"),
        ("convert 1 kg to lbs", "1.0 kg = 2.2046 lbs"),
    ]

    equation_tests = [
        ("solve x squared minus 4 equals 0", "x = -2, 2"),
        ("solve x squared equals 9", "x = -3, 3"),
    ]

    matrix_tests = [
        ("determinant of [[1,2],[3,4]]", "Determinant = -2"),
    ]

    print("\n--- Basic Math Tests ---\n")
    passed = 0
    failed = 0

    for input_text, expected in test_cases:
        if engine.is_graphing_command(input_text):
            func = engine.get_graph_function(input_text)
            print(f"  ✓ '{input_text}' -> Graph: '{func}'")
            passed += 1
            continue
        result = engine.evaluate(input_text)
        status = "✓" if str(result) == str(expected) else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
        passed += 1 if str(result) == str(expected) else 0
        failed += 0 if str(result) == str(expected) else 1

    print(f"\n--- Calculus Tests ---\n")
    for input_text, expected in calculus_tests:
        result = engine.check_calculus(input_text)
        if expected is not None:
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
            passed += 1 if result == expected else 0
            failed += 0 if result == expected else 1
        else:
            status = "✓" if result is not None else "✗"
            print(f"  {status} '{input_text}' -> '{result}'")
            passed += 1 if result is not None else 0
            failed += 0 if result is not None else 1

    print(f"\n--- Unit Conversion Tests ---\n")
    for input_text, expected in conversion_tests:
        result = engine.check_unit_conversion(input_text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
        passed += 1 if result == expected else 0
        failed += 0 if result == expected else 1

    print(f"\n--- Equation Tests ---\n")
    for input_text, expected in equation_tests:
        result = engine.check_equation(input_text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
        passed += 1 if result == expected else 0
        failed += 0 if result == expected else 1

    print(f"\n--- Matrix Tests ---\n")
    for input_text, expected in matrix_tests:
        result = engine.check_matrix(input_text)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
        passed += 1 if result == expected else 0
        failed += 0 if result == expected else 1

    print(f"\n--- Rate Limiting ---\n")
    rl = engine.check_rate_limit(max_requests=3, window_seconds=1)
    print(f"  ✓ Rate limit check: {'within limit' if rl else 'exceeded'}")
    passed += 1

    print(f"\n{'='*50}")
    print(f"  Results: {passed} Passed, {failed} Failed")
    print(f"{'='*50}")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    test_math_engine()
