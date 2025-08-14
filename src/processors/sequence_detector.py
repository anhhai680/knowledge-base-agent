"""
Sequence Detector for analyzing code patterns to generate sequence diagrams.
"""

import ast
import re
from typing import Dict, List, Any, Optional
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SequenceDetector:
    """Detects interaction patterns in code for sequence diagrams"""
    
    def analyze_code(self, code: str, language: str) -> Dict:
        """Analyze code for interaction patterns based on language"""
        if language == 'python':
            return self._analyze_python_code(code)
        elif language in ['javascript', 'typescript']:
            return self._analyze_js_ts_code(code)
        elif language == 'csharp':
            return self._analyze_csharp_code(code)
        else:
            return {}
    
    def _analyze_python_code(self, code: str) -> Dict:
        """Analyze Python code for method calls and class interactions"""
        try:
            tree = ast.parse(code)
            
            interactions = []
            current_class = None
            current_method = None
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    current_class = node.name
                elif isinstance(node, ast.FunctionDef):
                    current_method = node.name
                elif isinstance(node, ast.Call):
                    interaction = self._extract_python_call(node, current_class, current_method)
                    if interaction:
                        interactions.append(interaction)
            
            return {
                'language': 'python',
                'interactions': interactions
            }
            
        except SyntaxError:
            logger.debug(f"Failed to parse Python code: syntax error")
            return {'language': 'python', 'interactions': []}
        except Exception as e:
            logger.debug(f"Failed to analyze Python code: {str(e)}")
            return {'language': 'python', 'interactions': []}
    
    def _analyze_js_ts_code(self, code: str) -> Dict:
        """Analyze JavaScript/TypeScript code for function calls"""
        interactions = []
        
        # Find function/method calls
        call_pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.finditer(call_pattern, code)
        
        for match in matches:
            caller = self._extract_context_from_js(code, match.start())
            callee = match.group(1)
            method = match.group(2)
            
            interactions.append({
                'caller': caller or 'Client',
                'callee': callee,
                'method': method
            })
        
        language = 'typescript' if '.ts' in code or 'interface ' in code else 'javascript'
        return {
            'language': language,
            'interactions': interactions
        }
    
    def _analyze_csharp_code(self, code: str) -> Dict:
        """Analyze C# code for method calls"""
        interactions = []
        
        # Find method calls
        call_pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.finditer(call_pattern, code)
        
        for match in matches:
            caller = self._extract_context_from_csharp(code, match.start())
            callee = match.group(1)
            method = match.group(2)
            
            interactions.append({
                'caller': caller or 'Client',
                'callee': callee,
                'method': method
            })
        
        return {
            'language': 'csharp',
            'interactions': interactions
        }
    
    def _extract_python_call(self, call_node, current_class, current_method):
        """Extract call information from Python AST node"""
        if hasattr(call_node.func, 'attr') and hasattr(call_node.func, 'value'):
            if hasattr(call_node.func.value, 'id'):
                callee = call_node.func.value.id
                method = call_node.func.attr
                caller = current_class or 'Client'
                
                return {
                    'caller': caller,
                    'callee': callee,
                    'method': method
                }
        return None
    
    def _extract_context_from_js(self, code: str, position: int) -> str:
        """Extract calling context from JavaScript/TypeScript code"""
        # Look backwards for class/function definition
        lines = code[:position].split('\n')
        for line in reversed(lines[-10:]):  # Check last 10 lines
            if 'class ' in line or 'function ' in line:
                match = re.search(r'(class|function)\s+(\w+)', line)
                if match:
                    return match.group(2)
        return 'Client'
    
    def _extract_context_from_csharp(self, code: str, position: int) -> str:
        """Extract calling context from C# code"""
        # Look backwards for class/method definition
        lines = code[:position].split('\n')
        for line in reversed(lines[-10:]):  # Check last 10 lines
            if 'class ' in line or 'public ' in line and '(' in line:
                match = re.search(r'class\s+(\w+)|public\s+\w+\s+(\w+)\s*\(', line)
                if match:
                    return match.group(1) or match.group(2)
        return 'Client'