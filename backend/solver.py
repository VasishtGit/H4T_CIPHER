import sympy as sp
import re

class GraphSolver:
    def analyze(self, equation_str):
        """
        Parses the equation string from the AI and solves for mathematical properties.
        """
        # 1. Extract the equation using Regex (looking for y = mx + c)
        # This handles strings like "The graph shows y = 2x + 3" or just "y=2.5x-1"
        match = re.search(r"y\s*=\s*([-+]?\d*\.?\d*)x\s*([-+]\s*\d*\.?\d*)?", equation_str)
        
        if not match:
            return {
                "equation": "Could not identify a specific linear equation",
                "raw_result": equation_str,
                "steps": ["1. AI analyzed the visual plot.", f"2. Detected description: {equation_str}"]
            }

        # Parse slope (m) and intercept (c)
        m_str = match.group(1).strip()
        c_str = match.group(2).replace(" ", "") if match.group(2) else "0"

        # Handle implicit coefficients (y=x, y=-x)
        if m_str in ["", "+"]: m = 1.0
        elif m_str == "-": m = -1.0
        else: m = float(m_str)
        
        c = float(c_str)

        # 2. SymPy Analysis
        x = sp.symbols('x')
        expr = m * x + c
        
        # Calculate x-intercept (where y=0)
        x_intercept_sol = sp.solve(expr, x)
        x_val = float(x_intercept_sol[0]) if x_intercept_sol else "None"

        steps = [
            "1. AI vision model identified the linear trend in the image.",
            f"2. Extracted Equation: y = {m}x + {c}",
            f"3. Identified Slope (m) = {m} and Y-Intercept (b) = {c}.",
            f"4. Calculated X-Intercept by solving {m}x + {c} = 0."
        ]

        return {
            "equation": f"y = {m}x + {c}",
            "slope": m,
            "y_intercept": c,
            "x_intercept": x_val,
            "steps": steps
        }