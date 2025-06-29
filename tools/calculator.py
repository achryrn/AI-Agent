# tools/calculator.py

from tools.base_tool import Tool
from sympy import sympify, SympifyError
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application

class AdvancedCalculatorTool(Tool):
    name = "advanced_calculator"
    description = "Solves complex math expressions (supports algebra, roots, powers, fractions, etc)."

    async def run(self, input: dict) -> str:
        expression = input.get("expression", "").strip()
        if not expression:
            return "[ERROR] No expression provided."

        try:
            transformations = standard_transformations + (implicit_multiplication_application,)
            result = sympify(expression, transformations=transformations)
            return f"Result: {result}"
        except SympifyError as e:
            return f"[ERROR] Invalid expression: {str(e)}"
        except Exception as e:
            return f"[ERROR] Failed to compute: {str(e)}"

    @property
    def example_usage(self) -> str:
        return '''
        {
            "expression": "sqrt(16) + 2**3 - 5/2"
        }
        '''
