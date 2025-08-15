"""
Sequence Detector for analyzing code patterns to generate sequence diagrams.
"""

import ast
import re
from typing import Dict, Optional, List
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
        
        # First, check if there are existing sequence diagrams in the content
        existing_diagrams = self._extract_existing_sequence_diagrams(content)
        if existing_diagrams:
            # If we found existing diagrams, prioritize them
            for diagram in existing_diagrams:
                interactions.append({
                    'caller': 'Documentation',
                    'callee': 'Existing Diagram',
                    'method': diagram['title'],
                    'type': 'existing_sequence_diagram',
                    'relevance': 'high',
                    'diagram_content': diagram['content']
                })
        
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
    
    def _extract_existing_sequence_diagrams(self, content: str) -> List[Dict]:
        """Extract existing sequence diagrams from markdown content"""
        diagrams = []
        
        # Look for Mermaid sequence diagrams with both 3 and 4 backticks
        mermaid_patterns = [
            r'```mermaid\s*\n(sequenceDiagram[^`]*)\n```',  # 3 backticks
            r'````mermaid\s*\n(sequenceDiagram[^`]*)\n````',  # 4 backticks
            r'```mermaid\s*\n(sequenceDiagram[^`]*)\n````',  # 3 opening, 4 closing
            r'````mermaid\s*\n(sequenceDiagram[^`]*)\n```',  # 4 opening, 3 closing
        ]
        
        for pattern in mermaid_patterns:
            mermaid_matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in mermaid_matches:
                diagram_content = match.group(1).strip()
                
                # Extract title from surrounding context
                title = self._extract_diagram_title(content, match.start())
                
                diagrams.append({
                    'title': title or 'Sequence Diagram',
                    'content': diagram_content,
                    'type': 'mermaid'
                })
        
        # Look for partial sequence diagrams (start markers without end markers)
        partial_patterns = [
            r'```mermaid\s*\n(sequenceDiagram[^`]*)',  # Start of sequence diagram
            r'````mermaid\s*\n(sequenceDiagram[^`]*)',  # Start of sequence diagram with 4 backticks
        ]
        
        for pattern in partial_patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                diagram_content = match.group(1).strip()
                
                # Extract title from surrounding context
                title = self._extract_diagram_title(content, match.start())
                
                diagrams.append({
                    'title': title or 'Partial Sequence Diagram',
                    'content': diagram_content,
                    'type': 'partial_mermaid'
                })
        
        # Look for sequence diagram descriptions in text format
        sequence_patterns = [
            r'(?:sequence|flow|interaction)\s+diagram[:\s]*([^.\n]+)',
            r'(?:shows?|displays?|illustrates?)\s+(?:the\s+)?(?:sequence|flow|interaction)\s+([^.\n]+)',
        ]
        
        for pattern in sequence_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                description = match.group(1).strip()
                if description and len(description) > 10:  # Filter out very short descriptions
                    diagrams.append({
                        'title': f'Sequence Diagram: {description}',
                        'content': description,
                        'type': 'text_description'
                    })
        
        return diagrams
    
    def reconstruct_sequence_diagram_from_chunks(self, chunks: List[str]) -> Optional[str]:
        """Reconstruct a complete sequence diagram from multiple chunks"""
        # Look for the start of a sequence diagram
        start_markers = ['```mermaid', '````mermaid']
        end_markers = ['```', '````']
        
        # Find the chunk that contains the start of a sequence diagram
        start_chunk_idx = None
        start_marker = None
        
        for i, chunk in enumerate(chunks):
            for marker in start_markers:
                if marker in chunk and 'sequenceDiagram' in chunk:
                    start_chunk_idx = i
                    start_marker = marker
                    break
            if start_chunk_idx is not None:
                break
        
        if start_chunk_idx is None:
            return None
        
        # Find the chunk that contains the end marker
        end_chunk_idx = None
        end_marker = None
        
        # Look for the end marker in subsequent chunks
        for i in range(start_chunk_idx, len(chunks)):
            chunk = chunks[i]
            for marker in end_markers:
                if marker in chunk:
                    # Check if this marker is likely the end of our sequence diagram
                    # Look for content that suggests it's the end of a sequence diagram
                    chunk_before_marker = chunk[:chunk.find(marker)]
                    if ('participant' in chunk_before_marker or 
                        'Note over' in chunk_before_marker or
                        '->>' in chunk_before_marker or
                        '-->>' in chunk_before_marker):
                        end_chunk_idx = i
                        end_marker = marker
                        break
            if end_chunk_idx is not None:
                break
        
        # If we can't find a clear end marker, try to reconstruct from what we have
        if end_chunk_idx is None:
            # Look for the last chunk that contains sequence diagram content
            for i in range(start_chunk_idx, len(chunks)):
                chunk = chunks[i]
                if ('participant' in chunk or 
                    'Note over' in chunk or
                    '->>' in chunk or
                    '-->>' in chunk):
                    end_chunk_idx = i
                    end_marker = None  # No clear end marker found
                    break
        
        # If we still can't find an end marker, use the last chunk as the end
        if end_chunk_idx is None:
            end_chunk_idx = len(chunks) - 1  # Use the last chunk
        
        # Reconstruct the complete diagram
        reconstructed_content = ""
        
        # Add content from start chunk (from the start marker)
        start_chunk = chunks[start_chunk_idx]
        start_marker_pos = start_chunk.find(start_marker)
        if start_marker_pos != -1:
            # Find the newline after the start marker
            newline_pos = start_chunk.find('\n', start_marker_pos)
            if newline_pos != -1:
                reconstructed_content = start_chunk[newline_pos + 1:]
        
        # Add content from middle chunks
        for i in range(start_chunk_idx + 1, end_chunk_idx):
            reconstructed_content += chunks[i]
        
        # Add content from end chunk (up to the end marker if found)
        end_chunk = chunks[end_chunk_idx]
        if end_marker and end_marker in end_chunk:
            end_marker_pos = end_chunk.find(end_marker)
            if end_marker_pos != -1:
                reconstructed_content += end_chunk[:end_marker_pos]
        else:
            # Add the entire end chunk if no end marker found
            reconstructed_content += end_chunk
        
        # Clean up the reconstructed content
        reconstructed_content = reconstructed_content.strip()
        
        # Validate that we have a proper sequence diagram
        if ('sequenceDiagram' in reconstructed_content and 
            'participant' in reconstructed_content and
            len(reconstructed_content) > 100):  # Ensure we have substantial content
            return reconstructed_content
        
        return None
    
    def _extract_diagram_title(self, content: str, diagram_start: int) -> str:
        """Extract a meaningful title for a diagram from surrounding context"""
        # Look for headers above the diagram
        lines_before = content[:diagram_start].split('\n')
        
        for line in reversed(lines_before[-10:]):  # Check last 10 lines before diagram
            line = line.strip()
            # Look for markdown headers
            if line.startswith('#'):
                # Remove markdown header markers and return the title
                title = re.sub(r'^#+\s*', '', line)
                if title and len(title) > 3:
                    return title
            # Look for bold text that might be a title
            elif line.startswith('**') and line.endswith('**'):
                title = line[2:-2]  # Remove ** markers
                if title and len(title) > 3:
                    return title
        
        # If no clear title found, look for context around the diagram
        context_lines = content[diagram_start:diagram_start + 200].split('\n')
        for line in context_lines[:5]:  # Check first 5 lines after diagram start
            line = line.strip()
            if line and not line.startswith('```') and len(line) > 10:
                # Clean up the line to make it a reasonable title
                title = re.sub(r'[^\w\s-]', '', line)  # Remove special characters
                title = ' '.join(title.split())  # Normalize whitespace
                if title and len(title) > 5 and len(title) < 100:
                    return title
        
        return 'Sequence Diagram'
    
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
        
        # Create business-friendly operation names based on HTTP method and endpoint
        method_upper = http_method.upper()
        endpoint_lower = endpoint.lower()
        
        # Business operation mappings
        if method_upper == 'POST':
            if 'order' in endpoint_lower:
                return 'Create Order'
            elif 'user' in endpoint_lower or 'customer' in endpoint_lower:
                return 'Create User'
            elif 'auth' in endpoint_lower or 'login' in endpoint_lower:
                return 'Authenticate User'
            elif 'payment' in endpoint_lower:
                return 'Process Payment'
            elif 'car' in endpoint_lower or 'vehicle' in endpoint_lower:
                return 'Add Vehicle'
            elif 'notification' in endpoint_lower:
                return 'Send Notification'
            else:
                operation = self._extract_operation_from_endpoint(endpoint, target_service)
                return f'Create {operation}' if operation else 'Create Resource'
                
        elif method_upper == 'GET':
            if 'swagger' in endpoint_lower or 'api' in endpoint_lower:
                return 'Get API Documentation'
            elif 'order' in endpoint_lower:
                return 'Get Order Details'
            elif 'user' in endpoint_lower or 'customer' in endpoint_lower:
                return 'Get User Info'
            elif 'car' in endpoint_lower or 'vehicle' in endpoint_lower:
                return 'Get Vehicle Details'
            elif 'notification' in endpoint_lower:
                return 'Get Notifications'
            else:
                operation = self._extract_operation_from_endpoint(endpoint, target_service)
                return f'Get {operation}' if operation else 'Get Resource'
                
        elif method_upper == 'PUT':
            if 'order' in endpoint_lower:
                return 'Update Order'
            elif 'user' in endpoint_lower or 'customer' in endpoint_lower:
                return 'Update User'
            elif 'car' in endpoint_lower or 'vehicle' in endpoint_lower:
                return 'Update Vehicle'
            elif 'notification' in endpoint_lower:
                return 'Update Notification'
            else:
                operation = self._extract_operation_from_endpoint(endpoint, target_service)
                return f'Update {operation}' if operation else 'Update Resource'
                
        elif method_upper == 'DELETE':
            if 'order' in endpoint_lower:
                return 'Cancel Order'
            elif 'user' in endpoint_lower or 'customer' in endpoint_lower:
                return 'Delete User'
            elif 'car' in endpoint_lower or 'vehicle' in endpoint_lower:
                return 'Remove Vehicle'
            elif 'notification' in endpoint_lower:
                return 'Delete Notification'
            else:
                operation = self._extract_operation_from_endpoint(endpoint, target_service)
                return f'Delete {operation}' if operation else 'Delete Resource'
        
        # Fallback logic for other methods
        method_upper = http_method.upper()
        endpoint_lower = endpoint.lower()
        
        # Fallback logic for each method type
        if method_upper in ['POST', 'GET', 'PUT', 'DELETE']:
            operation = self._extract_operation_from_endpoint(endpoint, target_service)
            if method_upper == 'POST':
                return f'Create {operation}' if operation else 'Create Resource'
            elif method_upper == 'GET':
                return f'Get {operation}' if operation else 'Get Resource'
            elif method_upper == 'PUT':
                return f'Update {operation}' if operation else 'Update Resource'
            elif method_upper == 'DELETE':
                return f'Delete {operation}' if operation else 'Delete Resource'
        
        # Fallback for other methods
        operation = self._extract_operation_from_endpoint(endpoint, target_service)
        if operation:
            return f'{method_upper.title()} {operation}'
        else:
            simple_endpoint = self._simplify_endpoint(endpoint)
            return f'{method_upper.title()} {simple_endpoint}'
    
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
        method_lower = method.lower()
        endpoint_lower = endpoint.lower()
        
        # Specific flow filtering based on user intent
        if 'creation' in context_lower or 'create' in context_lower or 'creating' in context_lower:
            # For creation flows, only include POST and related GET operations
            if method_lower in ['delete', 'remove']:
                return False
            if method_lower == 'post':
                return True
            if method_lower == 'get' and ('swagger' in endpoint_lower or 'api' in endpoint_lower):
                return True  # API documentation is relevant for creation flows
                
        elif 'deletion' in context_lower or 'delete' in context_lower or 'deleting' in context_lower:
            # For deletion flows, focus on DELETE operations
            if method_lower != 'delete':
                return False
                
        elif 'update' in context_lower or 'edit' in context_lower or 'modify' in context_lower:
            # For update flows, focus on PUT/PATCH operations
            if method_lower not in ['put', 'patch']:
                return False
        
        # Check method relevance
        if self._is_relevant_to_context(method, context):
            return True
            
        # Check endpoint relevance
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