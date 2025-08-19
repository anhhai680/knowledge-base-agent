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
    
    def _run(self, expression: str) -> str:
        """Execute the calculation"""
        logger.info(f"Calculating: {expression}")
        
        try:
            # Clean the expression
            clean_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            
            # Evaluate safely
            result = eval(clean_expr)
            
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
