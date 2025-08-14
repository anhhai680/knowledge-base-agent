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
    
    def analyze_code(self, code: str, language: str, context: Optional[str] = None) -> Dict:
        """Analyze code for interaction patterns based on language and context"""
        if language == 'python':
            return self._analyze_python_code(code, context)
        elif language in ['javascript', 'typescript']:
            return self._analyze_js_ts_code(code, context)
        elif language == 'csharp':
            return self._analyze_csharp_code(code, context)
        elif language == 'markdown':
            return self._analyze_markdown_documentation(code, context)
        else:
            return {}
    
    def _analyze_python_code(self, code: str, context: Optional[str] = None) -> Dict:
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
                    interaction = self._extract_python_call(node, current_class, current_method, context)
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
    
    def _analyze_js_ts_code(self, code: str, context: Optional[str] = None) -> Dict:
        """Analyze JavaScript/TypeScript code for function calls"""
        interactions = []
        
        # Find function/method calls
        call_pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.finditer(call_pattern, code)
        
        for match in matches:
            caller = self._extract_context_from_js(code, match.start())
            callee = match.group(1)
            method = match.group(2)
            
            # Use context to make more meaningful decisions
            if context and self._is_relevant_to_context(method, context):
                interactions.append({
                    'caller': caller or 'Client',
                    'callee': callee,
                    'method': method,
                    'relevance': 'high'
                })
            else:
                interactions.append({
                    'caller': caller or 'Client',
                    'callee': callee,
                    'method': method,
                    'relevance': 'medium'
                })
        
        language = 'typescript' if '.ts' in code or 'interface ' in code else 'javascript'
        return {
            'language': language,
            'interactions': interactions
        }
    
    def _analyze_csharp_code(self, code: str, context: Optional[str] = None) -> Dict:
        """Analyze C# code for method calls"""
        interactions = []
        
        # Find method calls
        call_pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.finditer(call_pattern, code)
        
        for match in matches:
            caller = self._extract_context_from_csharp(code, match.start())
            callee = match.group(1)
            method = match.group(2)
            
            # Use context for relevance scoring
            relevance = 'high' if context and self._is_relevant_to_context(method, context) else 'medium'
            
            interactions.append({
                'caller': caller or 'Client',
                'callee': callee,
                'method': method,
                'relevance': relevance
            })
        
        return {
            'language': 'csharp',
            'interactions': interactions
        }
    
    def _extract_python_call(self, call_node, current_class, current_method, context=None):
        """Extract call information from Python AST node"""
        if hasattr(call_node.func, 'attr') and hasattr(call_node.func, 'value'):
            if hasattr(call_node.func.value, 'id'):
                callee = call_node.func.value.id
                method = call_node.func.attr
                caller = current_class or 'Client'
                
                # Use context for relevance scoring
                relevance = 'high' if context and self._is_relevant_to_context(method, context) else 'medium'
                
                return {
                    'caller': caller,
                    'callee': callee,
                    'method': method,
                    'relevance': relevance
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
    
    def _analyze_markdown_documentation(self, content: str, context: Optional[str] = None) -> Dict:
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
                        
                        # Only add interaction if both services are identified and relevant
                        if current_service and target_service:
                            # Check if this interaction is relevant to the query context
                            is_relevant = not context or self._is_interaction_relevant_to_context(
                                method, endpoint, context
                            )
                            
                            if is_relevant:
                                # Create a more meaningful method description
                                meaningful_method = self._create_meaningful_method(method.upper(), endpoint, target_service)
                                interactions.append({
                                    'caller': current_service,
                                    'callee': target_service,
                                    'method': meaningful_method,
                                    'type': 'api_call',
                                    'relevance': 'high' if is_relevant else 'medium'
                                })
            
            # Check for service interaction descriptions (only if relevant to context)
            if not context or any(term in line.lower() for term in context.lower().split()):
                for pattern in service_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        service_name = match.group(1)
                        if service_name and service_name != current_service and current_service:
                            interactions.append({
                                'caller': current_service,
                                'callee': self._normalize_service_name(service_name),
                                'method': 'integrate',
                                'type': 'service_integration',
                                'relevance': 'medium'
                            })
        
        return {
            'language': 'markdown',
            'interactions': interactions
        }
    
    def _extract_service_name_from_content(self, content: str) -> Optional[str]:
        """Extract the primary service name from documentation content"""
        # Look for service headers: # Car Listing Service
        header_match = re.search(r'^#\s+(.+?)\s*$', content, re.MULTILINE)
        if header_match:
            header_text = header_match.group(1).lower()
            if 'service' in header_text:
                # Convert "Car Listing Service" to "CarListingService"
                words = header_text.replace('service', '').strip().split()
                return ''.join(word.capitalize() for word in words) + 'Service'
            elif 'order' in header_text:
                return 'CarOrderService'
            elif 'listing' in header_text or 'car' in header_text:
                return 'CarListingService'
        
        # Look for repository/project names
        if 'car-listing' in content.lower():
            return 'CarListingService'
        elif 'car-order' in content.lower() or 'order service' in content.lower():
            return 'CarOrderService'
        elif 'car-notification' in content.lower():
            return 'CarNotificationService'
        elif 'car-web-client' in content.lower():
            return 'CarWebClient'
        
        # Return None instead of UnknownService to allow filtering
        return None
    
    def _extract_service_from_endpoint(self, endpoint: str, context: str) -> Optional[str]:
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
        
        # Return None instead of ExternalAPI to filter out unclear interactions
        return None
    
    def _normalize_service_name(self, service_name: str) -> str:
        """Normalize service names to consistent format"""
        service_name = service_name.lower()
        
        if 'listing' in service_name or 'car-listing' in service_name:
            return 'CarListingService'
        elif 'order' in service_name or 'car-order' in service_name:
            return 'CarOrderService'
        elif 'notification' in service_name or 'car-notification' in service_name:
            return 'CarNotificationService'
        elif 'web' in service_name or 'client' in service_name:
            return 'CarWebClient'
        
        # Convert kebab-case to PascalCase
        words = service_name.replace('-', ' ').replace('_', ' ').split()
        return ''.join(word.capitalize() for word in words)
    
    def _sanitize_method_call(self, method_call: str) -> str:
        """Sanitize method calls for Mermaid compatibility"""
        # Remove problematic characters that break Mermaid syntax
        sanitized = method_call.replace('`', '').replace('\\', '').replace('\n', ' ')
        # Remove extra spaces and clean up
        sanitized = ' '.join(sanitized.split())
        # Limit length to prevent overly long method names
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + '...'
        return sanitized
    
    def _create_meaningful_method(self, http_method: str, endpoint: str, target_service: str) -> str:
        """Create meaningful method descriptions for sequence diagrams"""
        # Extract the API operation from the endpoint
        operation = self._extract_operation_from_endpoint(endpoint, target_service)
        
        # Create human-readable method description
        if operation:
            return f"{http_method} {operation}"
        else:
            # Fallback to simplified endpoint
            simple_endpoint = self._simplify_endpoint(endpoint)
            return f"{http_method} {simple_endpoint}"
    
    def _extract_operation_from_endpoint(self, endpoint: str, service: str) -> Optional[str]:
        """Extract meaningful operation name from endpoint"""
        # Remove protocol and host parts, keep only the path
        path = endpoint
        if 'http' in endpoint:
            path = endpoint.split('/', 3)[-1] if '/' in endpoint else endpoint
        
        # Service-specific operation mapping
        if 'CarOrderService' in service:
            if '/order' in path.lower():
                if '<guid>' in path or '<id>' in path:
                    return 'Order'  # Order by ID
                else:
                    return 'Orders'  # Order collection
        elif 'CarListingService' in service:
            if '/car' in path.lower():
                if '<id>' in path:
                    return 'Car'  # Car by ID
                else:
                    return 'Cars'  # Car collection
        elif 'CarNotificationService' in service:
            if '/notification' in path.lower():
                return 'Notifications'
        
        # Generic operations
        if 'swagger' in path.lower():
            return 'API Documentation'
        
        return None
    
    def _simplify_endpoint(self, endpoint: str) -> str:
        """Simplify endpoint for display"""
        # Remove protocol and host, keep only meaningful path
        if 'http' in endpoint:
            parts = endpoint.split('/')
            if len(parts) > 3:
                path = '/' + '/'.join(parts[3:])
            else:
                path = endpoint
        else:
            path = endpoint
        
        # Remove IDs and GUIDs for cleaner display
        path = re.sub(r'<[^>]+>', '{id}', path)
        path = re.sub(r'/[a-f0-9-]{36}', '/{id}', path)  # GUID pattern
        
        # Limit length
        if len(path) > 20:
            path = path[:17] + '...'
            
        return path
    
    def _is_relevant_to_context(self, method: str, context: str) -> bool:
        """Check if a method is relevant to the query context"""
        if not context or not method:
            return False
            
        context_lower = context.lower()
        method_lower = method.lower()
        
        # Direct method name match
        if method_lower in context_lower:
            return True
            
        # Contextual relevance mapping
        context_keywords = {
            'login': ['login', 'authenticate', 'signin', 'auth', 'credential'],
            'order': ['order', 'purchase', 'buy', 'cart', 'checkout', 'payment'],
            'car': ['car', 'vehicle', 'listing', 'inventory', 'catalog'],
            'user': ['user', 'customer', 'profile', 'account', 'register'],
            'notification': ['notify', 'alert', 'message', 'email', 'send'],
            'search': ['search', 'find', 'query', 'filter', 'get']
        }
        
        for context_key, keywords in context_keywords.items():
            if context_key in context_lower:
                if any(keyword in method_lower for keyword in keywords):
                    return True
        
        return False
    
    def _is_interaction_relevant_to_context(self, method: str, endpoint: str, context: str) -> bool:
        """Check if an API interaction is relevant to the query context"""
        if not context:
            return True  # If no context, include all interactions
            
        context_lower = context.lower()
        
        # Check method relevance
        if self._is_relevant_to_context(method, context):
            return True
            
        # Check endpoint relevance
        endpoint_lower = endpoint.lower()
        
        # Map common query terms to endpoint patterns
        query_patterns = {
            'login': ['/auth', '/login', '/signin', '/user'],
            'order': ['/order', '/purchase', '/cart', '/payment', '/checkout'],
            'car': ['/car', '/vehicle', '/listing', '/inventory'],
            'user': ['/user', '/customer', '/profile', '/account'],
            'notification': ['/notification', '/alert', '/message'],
            'api': ['/api', '/swagger', '/docs']
        }
        
        for query_term, patterns in query_patterns.items():
            if query_term in context_lower:
                if any(pattern in endpoint_lower for pattern in patterns):
                    return True
        
        return False