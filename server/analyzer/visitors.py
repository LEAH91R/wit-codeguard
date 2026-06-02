import ast


class CodeGuardVisitor(ast.NodeVisitor):
    def __init__(self, raw_code: str):
        self.raw_code = raw_code
        self.alerts = []

        # Track variables for unused detection
        self.assigned_variables = {}  # { 'var_name': lineno }
        self.used_variables = set()  # { 'var_name1', 'var_name2' }

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # 1. Check function length
        func_length = node.end_lineno - node.lineno + 1
        if func_length > 20:
            self.alerts.append(f"Function '{node.name}' too long ({func_length} lines)")

        # 2. Check missing docstring
        docstring = ast.get_docstring(node)
        if docstring is None:
            self.alerts.append(f"Function '{node.name}' is missing a docstring")

        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        """
        Fires whenever the visitor encounters any variable name in the code.
        """
        # If the variable is being read/used
        if isinstance(node.ctx, ast.Load):
            self.used_variables.add(node.id)

        # If the variable is being assigned a value
        elif isinstance(node.ctx, ast.Store):
            self.assigned_variables[node.id] = node.lineno

            # 3. BONUS: Check for non-English (Hebrew) characters in variable name
            has_hebrew = any('\u0590' <= char <= '\u05FF' for char in node.id)
            if has_hebrew:
                self.alerts.append(f"Variable '{node.id}' at line {node.lineno} contains Hebrew characters")

        self.generic_visit(node)

    def check_unused_variables(self):
        """
        To be called after the visitor finishes walking the entire tree.
        """
        for var_name, lineno in self.assigned_variables.items():
            if var_name not in self.used_variables:
                self.alerts.append(f"Variable '{var_name}' at line {lineno} is defined but never used")