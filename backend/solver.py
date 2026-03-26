import sympy as sp
import re

class GraphSolver:
    def _parse_linear_equation(self, equation_str):
        """Attempt to parse a linear equation from text into slope/intercept."""
        normalized = equation_str.replace("−", "-").replace("^", "**")

        # Look for y = expression first
        match = re.search(r"y\s*=\s*([^,;\.\n]+)", normalized, re.IGNORECASE)
        if match:
            rhs = match.group(1).strip()
            rhs = re.split(r"\bwhere\b|\bwith\b|,|;|\\n", rhs, flags=re.IGNORECASE)[0].strip()
            try:
                x = sp.symbols('x')
                expr = sp.sympify(rhs, evaluate=True)
                expr = sp.expand(expr)

                # If expression is constant y = 3, slope=0
                if expr.is_Number:
                    return 0.0, float(expr)

                m = float(expr.coeff(x, 1))
                c = float(expr.subs(x, 0))
                return m, c
            except Exception:
                pass

        # fallback: direct slope/intercept mentions
        slope_match = re.search(r"slope\s*(?:=|:)?\s*([-+]?\d*\.?\d+)", normalized, re.IGNORECASE)
        intercept_match = re.search(r"(?:y\s*-?\s*intercept|y-intercept|intercept)\s*(?:=|:)?\s*([-+]?\d*\.?\d+)", normalized, re.IGNORECASE)
        if slope_match and intercept_match:
            try:
                m = float(slope_match.group(1))
                c = float(intercept_match.group(1))
                return m, c
            except ValueError:
                pass

        return None

    def analyze(self, equation_str):
        """
        Parses the equation string from the AI and solves for mathematical properties.
        """
        parse_result = self._parse_linear_equation(equation_str)

        if parse_result is None:
            return {
                "equation": "Could not identify a specific linear equation",
                "raw_result": equation_str,
                "steps": [
                    "1. AI analyzed the visual plot.",
                    f"2. Detected description: {equation_str}",
                    "3. Failed to parse linear equation from AI text output."
                ]
            }

        m, c = parse_result

        return self.analyze_from_coefficients(m, c, raw_result=equation_str, source='parsed OCR')

    def analyze_from_coefficients(self, m, c, raw_result=None, source='coefficients'):
        x = sp.symbols('x')
        expr = m * x + c

        if m == 0:
            x_val = None
        else:
            x_val = float(sp.solve(expr, x)[0])

        steps = [
            f"1. Source: {source}.",
            f"2. Constructed equation from coefficients: y = {m}x + {c}.",
            f"3. Slope (m) = {m}, y-intercept (b) = {c}.",
            f"4. X-intercept from y=0: x = {x_val if x_val is not None else 'undefined (horizontal line)'}.",
        ]

        return {
            "equation": f"y = {m}x + {c}",
            "slope": m,
            "y_intercept": c,
            "x_intercept": x_val,
            "raw_result": raw_result or f"coefficients: m={m}, c={c}",
            "steps": steps
        }