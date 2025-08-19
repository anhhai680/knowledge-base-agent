"""
Basic Tools for ReAct Agent

Provides basic tool implementations that the ReAct agent can use
for demonstration and testing purposes.
"""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
import re
import math
import ast
from ..utils.logging import get_logger

logger = get_logger(__name__)

class SafeMathEvaluator:
    """Safe mathematical expression evaluator that only allows mathematical operations"""
    
    def __init__(self):
        # Define allowed mathematical operators and functions
        self.allowed_operators = {'+', '-', '*', '/', '**', '//', '%'}
        self.allowed_functions = {
            'abs', 'round', 'min', 'max', 'sum', 'pow', 'sqrt',
            'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
            'sinh', 'cosh', 'tanh', 'asinh', 'acosh', 'atanh',
            'log', 'log10', 'exp', 'floor', 'ceil', 'trunc',
            'factorial', 'gcd', 'lcm'
        }
    
    def _tokenize(self, expression: str) -> List[str]:
        """Tokenize the mathematical expression"""
        # Remove all whitespace
        expr = ''.join(expression.split())
        
        # Split into tokens
        tokens = []
        current = ""
        i = 0
        
        while i < len(expr):
            char = expr[i]
            
            if char.isdigit() or char == '.':
                # Number
                current += char
            elif char in '()':
                # Parenthesis
                if current:
                    tokens.append(current)
                    current = ""
                tokens.append(char)
            elif char == ',':
                # Argument separator
                if current:
                    tokens.append(current)
                    current = ""
                tokens.append(',')
            elif char in '+-*/%':
                # Operator (handle multi-char operators ** and //)
                if current:
                    tokens.append(current)
                    current = ""
                # Peek next char for multi-character operators
                if i + 1 < len(expr) and ((char == '*' and expr[i+1] == '*') or (char == '/' and expr[i+1] == '/')):
                    tokens.append(char + expr[i+1])
                    i += 1
                else:
                    tokens.append(char)
            elif char.isalpha():
                # Function name or variable
                current += char
            else:
                # Invalid character
                raise ValueError(f"Invalid character in expression: {char}")
            
            i += 1
        
        if current:
            tokens.append(current)
        
        return tokens
    
    def _validate_tokens(self, tokens: List[str]) -> bool:
        """Validate that tokens only contain safe mathematical operations"""
        for token in tokens:
            if token in self.allowed_operators or token in '()' or token == ',':
                continue
            elif token.replace('.', '').isdigit():
                continue
            elif token in self.allowed_functions:
                continue
            else:
                raise ValueError(f"Invalid token in expression: {token}")
        return True
    
    def _evaluate_tokens(self, tokens: List[str]) -> float:
        """Evaluate the mathematical expression from tokens"""
        # Convert to postfix notation and evaluate
        def precedence(op):
            if op in {'+', '-'}:
                return 1
            elif op in {'*', '/', '//', '%'}:
                return 2
            elif op == '**':
                return 3
            return 0
        
        def apply_operator(a, b, op):
            if op == '+':
                return a + b
            elif op == '-':
                return a - b
            elif op == '*':
                return a * b
            elif op == '/':
                if b == 0:
                    raise ValueError("Division by zero")
                return a / b
            elif op == '//':
                if b == 0:
                    raise ValueError("Division by zero")
                return a // b
            elif op == '%':
                if b == 0:
                    raise ValueError("Modulo by zero")
                return a % b
            elif op == '**':
                return a ** b
        
        def apply_function(func, args):
            if func == 'abs':
                return abs(args[0])
            elif func == 'round':
                return round(args[0])
            elif func == 'min':
                return min(args)
            elif func == 'max':
                return max(args)
            elif func == 'sum':
                return sum(args)
            elif func == 'pow':
                return pow(args[0], args[1])
            elif func == 'sqrt':
                return math.sqrt(args[0])
            elif func == 'sin':
                return math.sin(args[0])
            elif func == 'cos':
                return math.cos(args[0])
            elif func == 'tan':
                return math.tan(args[0])
            elif func == 'asin':
                return math.asin(args[0])
            elif func == 'acos':
                return math.acos(args[0])
            elif func == 'atan':
                return math.atan(args[0])
            elif func == 'sinh':
                return math.sinh(args[0])
            elif func == 'cosh':
                return math.cosh(args[0])
            elif func == 'tanh':
                return math.tanh(args[0])
            elif func == 'asinh':
                return math.asinh(args[0])
            elif func == 'acosh':
                return math.acosh(args[0])
            elif func == 'atanh':
                return math.atanh(args[0])
            elif func == 'log':
                return math.log(args[0])
            elif func == 'log10':
                return math.log10(args[0])
            elif func == 'exp':
                return math.exp(args[0])
            elif func == 'floor':
                return math.floor(args[0])
            elif func == 'ceil':
                return math.ceil(args[0])
            elif func == 'trunc':
                return math.trunc(args[0])
            elif func == 'factorial':
                return math.factorial(int(args[0]))
            elif func == 'gcd':
                return math.gcd(int(args[0]), int(args[1]))
            elif func == 'lcm':
                return math.lcm(int(args[0]), int(args[1]))
            else:
                raise ValueError(f"Unknown function: {func}")
        
        # Convert to postfix notation
        output = []
        operators = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if token.replace('.', '').isdigit():
                output.append(float(token))
            elif token in self.allowed_functions:
                # Function call
                func = token
                i += 1
                if i >= len(tokens) or tokens[i] != '(':
                    raise ValueError(f"Expected '(' after function {func}")
                
                # Parse function arguments
                args = []
                paren_count = 1
                arg_start = i + 1
                i += 1
                
                while i < len(tokens) and paren_count > 0:
                    if tokens[i] == '(':
                        paren_count += 1
                    elif tokens[i] == ')':
                        paren_count -= 1
                    elif tokens[i] == ',' and paren_count == 1:
                        # End of argument
                        arg_tokens = tokens[arg_start:i]
                        if arg_tokens:
                            args.append(self._evaluate_tokens(arg_tokens))
                        arg_start = i + 1
                    i += 1
                
                # Add last argument
                if arg_start < i - 1:
                    arg_tokens = tokens[arg_start:i-1]
                    if arg_tokens:
                        args.append(self._evaluate_tokens(arg_tokens))
                
                if paren_count != 0:
                    raise ValueError(f"Mismatched parentheses in function {func}")
                
                output.append(apply_function(func, args))
                continue
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    op = operators.pop()
                    b = output.pop()
                    a = output.pop()
                    output.append(apply_operator(a, b, op))
                if operators and operators[-1] == '(':
                    operators.pop()
                else:
                    raise ValueError("Mismatched parentheses")
            elif token in self.allowed_operators:
                while (operators and operators[-1] != '(' and 
                       precedence(operators[-1]) >= precedence(token)):
                    op = operators.pop()
                    b = output.pop()
                    a = output.pop()
                    output.append(apply_operator(a, b, op))
                operators.append(token)
            
            i += 1
        
        # Process remaining operators
        while operators:
            op = operators.pop()
            if op == '(':
                raise ValueError("Mismatched parentheses")
            b = output.pop()
            a = output.pop()
            output.append(apply_operator(a, b, op))
        
        if len(output) != 1:
            raise ValueError("Invalid expression")
        
        return output[0]
    
    def evaluate(self, expression: str) -> float:
        """Safely evaluate a mathematical expression"""
        try:
            # Clean the expression - only allow safe characters
            clean_expr = re.sub(r'[^0-9+\-*/().\s\w]', '', expression)
            
            # Tokenize and validate
            tokens = self._tokenize(clean_expr)
            self._validate_tokens(tokens)
            
            # Evaluate
            return self._evaluate_tokens(tokens)
            
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {str(e)}")

class SafePythonEvaluator(ast.NodeVisitor):
    """Safely evaluate a restricted subset of Python expressions.

    Supported:
    - Numeric operations (+, -, *, /, //, %, **)
    - Parentheses and unary +/-
    - Function calls to whitelisted names only (no attributes)
    - Constants: numbers, strings, booleans, None
    - Names that exist in the provided allowed names

    Not supported:
    - Attribute access (obj.attr)
    - Subscripts (obj[idx]) and slicing
    - Comprehensions, lambdas, generators
    - Assignments, imports, control flow, statements
    - Keyword arguments and starargs/kwargs
    """

    def __init__(self, allowed_names: Optional[Dict[str, Any]] = None) -> None:
        self.allowed_names: Dict[str, Any] = allowed_names or {}

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    # Python <3.8 compatibility (Num, Str, NameConstant) is not required here

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.allowed_names:
            return self.allowed_names[node.id]
        raise ValueError(f"Use of name '{node.id}' is not allowed")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError("Unsupported unary operator")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise ValueError("Division by zero")
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise ValueError("Division by zero")
            return left // right
        if isinstance(node.op, ast.Mod):
            if right == 0:
                raise ValueError("Modulo by zero")
            return left % right
        if isinstance(node.op, ast.Pow):
            return left ** right
        raise ValueError("Unsupported binary operator")

    def visit_Call(self, node: ast.Call) -> Any:
        # Disallow attribute-based calls like module.func
        if isinstance(node.func, ast.Attribute):
            raise ValueError("Attribute access is not allowed")
        func_obj = self.visit(node.func)
        if not callable(func_obj):
            raise ValueError("Attempted to call a non-callable object")
        if node.keywords:
            raise ValueError("Keyword arguments are not allowed")
        if any(isinstance(arg, (ast.Starred)) for arg in node.args):
            raise ValueError("Starred arguments are not allowed")
        args = [self.visit(arg) for arg in node.args]
        return func_obj(*args)

    # Explicitly forbid everything else
    def generic_visit(self, node: ast.AST) -> Any:
        forbidden_nodes = (
            ast.Attribute,
            ast.Subscript,
            ast.Slice,
            ast.IfExp,
            ast.ListComp,
            ast.DictComp,
            ast.SetComp,
            ast.GeneratorExp,
            ast.Lambda,
            ast.List,
            ast.Tuple,
            ast.Dict,
            ast.Set,
            ast.Compare,
            ast.BoolOp,
            ast.Assign,
            ast.AugAssign,
            ast.AnnAssign,
            ast.NamedExpr,
            ast.Import,
            ast.ImportFrom,
            ast.For,
            ast.While,
            ast.If,
            ast.With,
            ast.Try,
            ast.FunctionDef,
            ast.ClassDef,
            ast.Return,
            ast.Delete,
            ast.Global,
            ast.Nonlocal,
            ast.Yield,
            ast.YieldFrom,
            ast.Raise,
            ast.Module,
            ast.Expr,
        )
        if isinstance(node, forbidden_nodes):
            raise ValueError("This Python construct is not allowed")
        return super().generic_visit(node)

    @staticmethod
    def evaluate(expression: str, allowed_names: Optional[Dict[str, Any]] = None) -> Any:
        # Only allow a single expression, reject statements or multiple lines
        code = expression.strip()
        if "\n" in code or ";" in code:
            raise ValueError("Only single expressions are allowed")
        try:
            parsed = ast.parse(code, mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Invalid expression: {exc.msg}")
        evaluator = SafePythonEvaluator(allowed_names)
        return evaluator.visit(parsed)

class SearchTool(BaseTool):
    """Basic search tool for demonstration"""
    
    name: str = "web_search"
    description: str = "Search for information on the web"
    
    def _run(self, query: str) -> str:
        """Execute the search"""
        logger.info(f"Searching for: {query}")
        
        # Simulate search results
        results = [
            f"Search result 1 for '{query}': This is a simulated search result that would contain information about {query}.",
            f"Search result 2 for '{query}': Additional simulated information about {query} from another source.",
            f"Search result 3 for '{query}': More detailed simulated content related to {query}."
        ]
        
        return "\n\n".join(results)
    
    def _arun(self, query: str) -> str:
        """Async version of the search"""
        return self._run(query)

class CalculatorTool(BaseTool):
    """Basic calculator tool for mathematical operations"""
    
    name: str = "calculator"
    description: str = "Perform mathematical calculations"
    
    def __init__(self):
        super().__init__()
        self.math_evaluator = SafeMathEvaluator()
    
    def _run(self, expression: str) -> str:
        """Execute the calculation"""
        logger.info(f"Calculating: {expression}")
        
        try:
            # Use safe mathematical evaluator instead of eval()
            result = self.math_evaluator.evaluate(expression)
            
            return f"Result of {expression} = {result}"
            
        except Exception as e:
            return f"Error calculating {expression}: {str(e)}"
    
    def _arun(self, expression: str) -> str:
        """Async version of the calculation"""
        return self._run(expression)

class CodeExecutionTool(BaseTool):
    """Basic code execution tool for simple Python code"""
    
    name: str = "code_executor"
    description: str = "Execute simple Python code safely"
    
    def _run(self, code: str) -> str:
        """Safely evaluate a restricted Python expression (no exec)."""
        logger.info(f"Executing code expression: {code[:100]}...")
        try:
            allowed: Dict[str, Any] = {
                # Builtins
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
                'sum': sum,
                'pow': pow,
                'True': True,
                'False': False,
                'None': None,
                # Math constants and functions
                'pi': math.pi,
                'e': math.e,
                'tau': getattr(math, 'tau', 6.283185307179586),
                'inf': math.inf,
                'nan': math.nan,
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'asin': math.asin,
                'acos': math.acos,
                'atan': math.atan,
                'sinh': math.sinh,
                'cosh': math.cosh,
                'tanh': math.tanh,
                'asinh': math.asinh,
                'acosh': math.acosh,
                'atanh': math.atanh,
                'log': math.log,
                'log10': math.log10,
                'exp': math.exp,
                'floor': math.floor,
                'ceil': math.ceil,
                'trunc': math.trunc,
                'factorial': math.factorial,
                'gcd': math.gcd,
                'lcm': getattr(math, 'lcm', lambda a, b: (a*b)//math.gcd(a,b) if a and b else 0),
            }

            result = SafePythonEvaluator.evaluate(code, allowed)
            return f"Result: {result}"
        except Exception as e:
            return f"Error executing expression: {str(e)}"
    
    def _arun(self, code: str) -> str:
        """Async version of the code execution"""
        return self._run(code)

class FileOperationTool(BaseTool):
    """Basic file operation tool for demonstration"""
    
    name: str = "file_operations"
    description: str = "Perform basic file operations (read, write, list)"
    
    def _run(self, operation: str, path: str = "", content: str = "") -> str:
        """Execute the file operation"""
        logger.info(f"File operation: {operation} on {path}")
        
        try:
            if operation.lower() == "list":
                # Simulate listing files
                return f"Files in current directory: file1.txt, file2.py, folder1/, file3.json"
            
            elif operation.lower() == "read":
                # Simulate reading a file
                if path:
                    return f"Content of {path}:\nThis is simulated content for {path}. In a real implementation, this would read the actual file."
                else:
                    return "Error: No file path specified for read operation"
            
            elif operation.lower() == "write":
                # Simulate writing to a file
                if path and content:
                    return f"Successfully wrote content to {path}. Content length: {len(content)} characters."
                else:
                    return "Error: Both file path and content are required for write operation"
            
            elif operation.lower() == "exists":
                # Simulate checking if file exists
                if path:
                    return f"File {path} exists: True (simulated)"
                else:
                    return "Error: No file path specified for exists operation"
            
            else:
                return f"Unknown operation: {operation}. Supported operations: list, read, write, exists"
                
        except Exception as e:
            return f"Error in file operation: {str(e)}"
    
    def _arun(self, operation: str, path: str = "", content: str = "") -> str:
        """Async version of the file operation"""
        return self._run(operation, path, content)

class APICallTool(BaseTool):
    """Basic API call tool for demonstration"""
    
    name: str = "api_caller"
    description: str = "Make HTTP API calls to external services"
    
    def _run(self, url: str, method: str = "GET", data: str = "") -> str:
        """Execute the API call"""
        logger.info(f"API call: {method} {url}")
        
        try:
            # Simulate API response
            if method.upper() == "GET":
                return f"GET {url} - Simulated response: {{'status': 'success', 'data': 'This is simulated API data from {url}'}}"
            
            elif method.upper() == "POST":
                return f"POST {url} - Simulated response: {{'status': 'success', 'data': 'Posted data: {data}', 'message': 'Data received successfully'}}"
            
            elif method.upper() == "PUT":
                return f"PUT {url} - Simulated response: {{'status': 'success', 'data': 'Updated data: {data}', 'message': 'Resource updated successfully'}}"
            
            elif method.upper() == "DELETE":
                return f"DELETE {url} - Simulated response: {{'status': 'success', 'message': 'Resource deleted successfully'}}"
            
            else:
                return f"Unsupported HTTP method: {method}. Supported methods: GET, POST, PUT, DELETE"
                
        except Exception as e:
            return f"Error in API call: {str(e)}"
    
    def _arun(self, url: str, method: str = "GET", data: str = "") -> str:
        """Async version of the API call"""
        return self._run(url, method, data)

def get_default_tools() -> List[BaseTool]:
    """Get a list of default tools for the ReAct agent"""
    return [
        SearchTool(),
        CalculatorTool(),
        CodeExecutionTool(),
        FileOperationTool(),
        APICallTool()
    ]

def get_tool_by_name(tools: List[BaseTool], name: str) -> Optional[BaseTool]:
    """Get a tool by name from a list of tools"""
    for tool in tools:
        if tool.name == name:
            return tool
    return None

def validate_tool_parameters(tool: BaseTool, parameters: Dict[str, Any]) -> bool:
    """Validate tool parameters before execution"""
    try:
        # Basic validation - check if required parameters are present
        # In a real implementation, you'd have more sophisticated validation
        return True
    except Exception:
        return False
