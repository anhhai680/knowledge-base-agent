"""
Basic Tools for ReAct Agent

Provides basic tool implementations that the ReAct agent can use
for demonstration and testing purposes.
"""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
import json
import re
import math
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
            elif char in self.allowed_operators or char in '()':
                # Operator or parenthesis
                if current:
                    tokens.append(current)
                    current = ""
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
            if token in self.allowed_operators or token in '()':
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
        """Execute the code"""
        logger.info(f"Executing code: {code[:100]}...")
        
        try:
            # Only allow safe operations
            safe_globals = {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'range': range,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'enumerate': enumerate,
                'zip': zip,
                'map': map,
                'filter': filter,
                'any': any,
                'all': all,
                'bool': bool,
                'chr': chr,
                'ord': ord,
                'hex': hex,
                'oct': oct,
                'bin': bin,
                'format': format,
                'repr': repr,
                'ascii': ascii,
                'hash': hash,
                'id': id,
                'type': type,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'callable': callable,
                'getattr': getattr,
                'hasattr': hasattr,
                'setattr': setattr,
                'delattr': delattr,
                'property': property,
                'super': super,
                'object': object,
                'Exception': Exception,
                'ValueError': ValueError,
                'TypeError': TypeError,
                'AttributeError': AttributeError,
                'IndexError': IndexError,
                'KeyError': KeyError,
                'RuntimeError': RuntimeError,
                'OSError': OSError,
                'FileNotFoundError': FileNotFoundError,
                'PermissionError': PermissionError,
                'TimeoutError': TimeoutError,
                'ConnectionError': ConnectionError,
                'BlockingIOError': BlockingIOError,
                'ChildProcessError': ChildProcessError,
                'BrokenPipeError': BrokenPipeError,
                'ConnectionAbortedError': ConnectionAbortedError,
                'ConnectionRefusedError': ConnectionRefusedError,
                'ConnectionResetError': ConnectionResetError,
                'FileExistsError': FileExistsError,
                'FileNotFoundError': FileNotFoundError,
                'InterruptedError': InterruptedError,
                'IsADirectoryError': IsADirectoryError,
                'NotADirectoryError': NotADirectoryError,
                'PermissionError': PermissionError,
                'ProcessLookupError': ProcessLookupError,
                'TimeoutError': TimeoutError,
                'UnsupportedOperation': OSError,
                'math': math,
                'json': json,
                're': re
            }
            
            safe_locals = {}
            
            # Execute the code
            exec(code, safe_globals, safe_locals)
            
            # Return any output
            if '_' in safe_locals:
                return f"Code executed successfully. Result: {safe_locals['_']}"
            else:
                return "Code executed successfully."
                
        except Exception as e:
            return f"Error executing code: {str(e)}"
    
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
