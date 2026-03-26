from sympy import Matrix, symbols, det

class GraphSolver:
    def analyze(self, adj_matrix):
        # Convert list to SymPy Matrix
        M = Matrix(adj_matrix)
        lam = symbols('λ')
        
        # Identity Matrix
        I = Matrix.eye(M.shape[0])
        
        # Characteristic Equation: det(λI - A)
        char_matrix = lam * I - M
        char_poly = char_matrix.det()
        
        steps = [
            f"1. AI detected a graph with {M.shape[0]} nodes.",
            f"2. Constructed Adjacency Matrix A: {adj_matrix}",
            f"3. Formulated symbolic matrix [λI - A].",
            f"4. Calculated determinant to find Characteristic Polynomial."
        ]
        
        return {
            "polynomial": str(char_poly),
            "steps": steps,
            "matrix": str(adj_matrix)
        }