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
        
        # Graphing (expected = None means graphing)
        ("plot x square", None),
        ("graph x cube", None),
        ("plot x squared", None),
    ]
    
    # Calculus tests (tested separately via check_calculus)
    calculus_tests = [
        ("differentiate x squared", "Derivative = 2·x"),
        ("differentiate log x", "Derivative = 1/x"),
        ("differentiate e power x", "Derivative = exp(x)"),
        ("derivative of sin x", "Derivative = cos(x)"),
        ("integration of log x", None),   # Should give x·log(x) - x + C (just check not None)
        ("integrate x squared", None),    # Should give x³/3 + C
        ("integrate 2x", None),           # Should give x² + C
        ("integration of x cubed", None), # Should give x^4/4 + C
    ]
    
    print("\n--- Math & Graphing Tests ---\n")
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        # Graphing
        if engine.is_graphing_command(input_text):
            func = engine.get_graph_function(input_text)
            print(f"  ✓ '{input_text}' -> Graph: '{func}'")
            if expected is None:
                passed += 1
            else:
                failed += 1
            continue
            
        # Math
        result = engine.evaluate(input_text)
        status = "✓" if str(result) == str(expected) else "✗"
        print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
        if str(result) == str(expected):
            passed += 1
        else:
            failed += 1
    
    print(f"\n--- Calculus Tests ---\n")
    
    for input_text, expected in calculus_tests:
        result = engine.check_calculus(input_text)
        
        if expected is not None:
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{input_text}' -> '{result}' (expected '{expected}')")
            if result == expected:
                passed += 1
            else:
                failed += 1
        else:
            # Just check it returned something (not None)
            status = "✓" if result is not None else "✗"
            print(f"  {status} '{input_text}' -> '{result}'")
            if result is not None:
                passed += 1
            else:
                failed += 1
            
    print(f"\n{'='*50}")
    print(f"  Results: {passed} Passed, {failed} Failed")
    print(f"{'='*50}")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    test_math_engine()
