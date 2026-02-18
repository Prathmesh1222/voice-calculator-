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
        
        # Graphing
        ("plot x square", None),
        ("graph x cube", None),
        ("plot x squared", None),
        
        # Calculus
        ("differentiate x squared", "Derivative is 2*x"),
        ("differentiate log x", "Derivative is 1/x"),
        ("differentiate e power x", "Derivative is exp(x)"),
        ("integrate 2x", "Integral is x**2 + C"),
        ("derivative of sin x", "Derivative is cos(x)"),
    ]
    
    print("\n--- Starting Comprehensive Tests ---\n")
    
    passed = 0
    failed = 0
    
    for input_text, expected in test_cases:
        print(f"Testing: '{input_text}'")
        
        # 1. Check Graphing
        if engine.is_graphing_command(input_text):
            func = engine.get_graph_function(input_text)
            print(f" -> Graph Function: '{func}'")
            if expected is None:
                print(" -> PASSED (Graphing detected)")
                passed += 1
            else:
                print(f" -> FAILED (Expected {expected}, got Graphing)")
                failed += 1
            continue
            
        # 2. Check Calculus
        calc_res = engine.check_calculus(input_text)
        if calc_res:
            print(f" -> Calculus Result: '{calc_res}'")
            if calc_res == expected:
                print(" -> PASSED")
                passed += 1
            else:
                print(f" -> FAILED (Expected '{expected}', got '{calc_res}')")
                failed += 1
            continue
            
        # 3. Evaluate Math
        result = engine.evaluate(input_text)
        print(f" -> Math Result: '{result}'")
        
        if str(result) == str(expected):
            print(" -> PASSED")
            passed += 1
        else:
            print(f" -> FAILED (Expected '{expected}', got '{result}')")
            failed += 1
            
    print(f"\n--- Test Summary: {passed} Passed, {failed} Failed ---")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    test_math_engine()
