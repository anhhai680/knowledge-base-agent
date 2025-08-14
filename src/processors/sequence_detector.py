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
        elif language == 'markdown':
            return self._analyze_markdown_documentation(code)
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
    
    def _analyze_markdown_documentation(self, content: str) -> Dict:
        """Analyze markdown documentation for API and service interactions"""
        interactions = []
        
        # Look for API endpoint patterns
        api_patterns = [
            # REST API calls: curl -X POST http://localhost:5033/Car
            r'curl\s+-X\s+(\w+)\s+([^\s]+)',
            # HTTP requests: POST /api/cars
            r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s\n]+)',
            # Service URLs: http://localhost:5033
            r'https?://[^\s]+:(\d+)([^\s]*)',
        ]
        
        # Look for service interaction descriptions
        service_patterns = [
            # Service names: car-listing-service, car-order-service
            r'(\w+)-service',
            # API integrations: calls to, integrates with
            r'(?:calls?|integrates?|connects?)\s+(?:to\s+)?(\w+[-\w]*service|\w+[-\w]*api)',
        ]
        
        lines = content.split('\n')
        current_service = self._extract_service_name_from_content(content)
        
        for line in lines:
            line = line.strip()
            
            # Check for API endpoint patterns
            for pattern in api_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) >= 2:
                        method = match.group(1)
                        endpoint = match.group(2)
                        
                        # Extract service name from URL or endpoint
                        target_service = self._extract_service_from_endpoint(endpoint, line)
                        
                        interactions.append({
                            'caller': current_service or 'Client',
                            'callee': target_service,
                            'method': f'{method.upper()}({endpoint})',
                            'type': 'api_call'
                        })
            
            # Check for service interaction descriptions
            for pattern in service_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    service_name = match.group(1)
                    if service_name and service_name != current_service:
                        interactions.append({
                            'caller': current_service or 'Client',
                            'callee': self._normalize_service_name(service_name),
                            'method': 'integrate',
                            'type': 'service_integration'
                        })
        
        return {
            'language': 'markdown',
            'interactions': interactions
        }
    
    def _extract_service_name_from_content(self, content: str) -> str:
        """Extract the primary service name from documentation content"""
        # Look for service headers: # Car Listing Service
        header_match = re.search(r'^#\s+(.+?)\s*$', content, re.MULTILINE)
        if header_match:
            header_text = header_match.group(1).lower()
            if 'service' in header_text:
                # Convert "Car Listing Service" to "CarListingService"
                words = header_text.replace('service', '').strip().split()
                return ''.join(word.capitalize() for word in words) + 'Service'
        
        # Look for repository/project names
        if 'car-listing' in content.lower():
            return 'CarListingService'
        elif 'car-order' in content.lower():
            return 'CarOrderService'
        elif 'car-notification' in content.lower():
            return 'CarNotificationService'
        elif 'car-web-client' in content.lower():
            return 'CarWebClient'
        
        return 'UnknownService'
    
    def _extract_service_from_endpoint(self, endpoint: str, context: str) -> str:
        """Extract target service name from endpoint URL or context"""
        # Check for port numbers to identify services
        port_service_map = {
            '5033': 'CarListingService',
            '5068': 'CarOrderService', 
            '5001': 'CarNotificationService',
            '3000': 'CarWebClient'
        }
        
        # Extract port from URL
        port_match = re.search(r':(\d+)', endpoint)
        if port_match:
            port = port_match.group(1)
            if port in port_service_map:
                return port_service_map[port]
        
        # Look for service names in the endpoint path
        if '/car' in endpoint.lower():
            return 'CarListingService'
        elif '/order' in endpoint.lower():
            return 'CarOrderService'
        elif '/notification' in endpoint.lower():
            return 'CarNotificationService'
        
        # Look for service names in context
        if 'listing' in context.lower():
            return 'CarListingService'
        elif 'order' in context.lower():
            return 'CarOrderService'
        elif 'notification' in context.lower():
            return 'CarNotificationService'
        
        return 'ExternalAPI'
    
    def _normalize_service_name(self, service_name: str) -> str:
        """Normalize service names to consistent format"""
        service_name = service_name.lower()
        
        if 'listing' in service_name:
            return 'CarListingService'
        elif 'order' in service_name:
            return 'CarOrderService'
        elif 'notification' in service_name:
            return 'CarNotificationService'
        elif 'web' in service_name or 'client' in service_name:
            return 'CarWebClient'
        
        # Convert kebab-case to PascalCase
        words = service_name.replace('-', ' ').replace('_', ' ').split()
        return ''.join(word.capitalize() for word in words)