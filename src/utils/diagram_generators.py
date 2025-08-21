"""
Diagram Generation Utilities for Multi-Diagram Type Support

This module provides pattern extraction and Mermaid diagram generation for various diagram types:
- Enhanced sequence diagrams
- Flowcharts for process flows
- Class diagrams for object-oriented structures
- Entity-Relationship diagrams for data models
- Component diagrams for system architecture
"""

import re
from typing import Dict, Any, List, Optional
from langchain.docstore.document import Document
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DiagramPatternExtractor:
    """Extract patterns from code for different diagram types"""
    
    def __init__(self):
        self.flow_keywords = [
            'if', 'else', 'elif', 'for', 'while', 'switch', 'case', 'try', 'catch', 'finally'
        ]
        self.class_keywords = [
            'class', 'extends', 'implements', 'interface', 'abstract', 'public', 'private', 'protected'
        ]
        self.entity_keywords = [
            '@entity', '@table', 'create table', 'primary key', 'foreign key', 'join', 'relationship'
        ]
        self.component_keywords = [
            '@component', '@service', '@controller', '@repository', 'module', 'import', 'require'
        ]
    
    def extract_flow_patterns(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract flow control patterns for flowchart generation"""
        flow_patterns = []
        
        for doc in code_docs:
            content = doc.page_content
            source_file = doc.metadata.get('file_path', 'unknown')
            
            # Extract function/method blocks
            functions = self._extract_functions(content)
            
            for func in functions:
                flow_data = self._analyze_function_flow(func, source_file)
                if flow_data:
                    flow_patterns.append(flow_data)
        
        return flow_patterns
    
    def extract_class_patterns(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract class structures and relationships"""
        class_patterns = []
        
        for doc in code_docs:
            content = doc.page_content
            source_file = doc.metadata.get('file_path', 'unknown')
            
            # Extract class definitions
            classes = self._extract_classes(content)
            
            for cls in classes:
                class_data = self._analyze_class_structure(cls, source_file)
                if class_data:
                    class_patterns.append(class_data)
        
        return class_patterns
    
    def extract_er_patterns(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract entity-relationship patterns from data models"""
        er_patterns = []
        
        for doc in code_docs:
            content = doc.page_content
            source_file = doc.metadata.get('file_path', 'unknown')
            
            # Look for entity/model definitions
            entities = self._extract_entities(content)
            
            for entity in entities:
                entity_data = self._analyze_entity_structure(entity, source_file)
                if entity_data:
                    er_patterns.append(entity_data)
        
        return er_patterns
    
    def extract_component_patterns(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract component and module patterns for architecture diagrams"""
        component_patterns = []
        
        for doc in code_docs:
            content = doc.page_content
            source_file = doc.metadata.get('file_path', 'unknown')
            
            # Detect language from file path
            language = self._detect_language_from_path(source_file)
            
            # Extract component/module definitions with language awareness
            components = self._extract_components(content, language)
            
            for component in components:
                component_data = self._analyze_component_structure(component, source_file)
                if component_data:
                    component_patterns.append(component_data)
        
        # Deduplicate components by name with language/type priority
        return self._dedupe_component_patterns(component_patterns)
    
    def extract_architecture_from_metadata(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Build architecture components strictly from metadata (no content parsing)."""
        patterns: List[Dict[str, Any]] = []
        seen = set()
        for doc in code_docs:
            md = getattr(doc, 'metadata', {}) or {}
            file_path = md.get('file_path', '')
            if not file_path:
                continue
            # Derive base name without extension as component name
            base = file_path.split('/')[-1]
            name = base.split('.')[0]
            # Classify by folder or name suffix
            lower_path = file_path.lower()
            comp_type = None
            if 'controller' in lower_path or name.lower().endswith('controller'):
                comp_type = 'Controller'
            elif 'service' in lower_path or name.lower().endswith('service'):
                comp_type = 'Service'
            elif 'repository' in lower_path or name.lower().endswith('repository'):
                comp_type = 'Repository'
            elif any(k in lower_path for k in ['model', 'entity', 'entities']):
                comp_type = 'Model'
            else:
                # Only include strongly signaled items to avoid noise
                continue
            key = (name, comp_type)
            if key in seen:
                continue
            seen.add(key)
            patterns.append({
                'component_name': name,
                'component_type': comp_type,
                'methods': [],
                'dependencies': [],
                'method_count': 0,
                'dependency_count': 0,
                'source_file': file_path
            })
        return patterns
    
    def _detect_language_from_path(self, file_path: str) -> str:
        """Detect programming language from file path"""
        if not file_path:
            return 'unknown'
        fp = file_path.lower()
        if fp.endswith('.py'):
            return 'python'
        if fp.endswith(('.js', '.jsx')):
            return 'javascript'
        if fp.endswith(('.ts', '.tsx')):
            return 'typescript'
        if fp.endswith('.cs'):
            return 'csharp'
        if fp.endswith('.java'):
            return 'java'
        if fp.endswith('.md'):
            return 'markdown'
        return 'unknown'
    
    def _dedupe_component_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Dedupe components by name, preferring concrete language types over generic ones"""
        if not patterns:
            return patterns
        # Priority ordering
        type_priority = {
            'csharp_component': 100,
            'spring_component': 90,
            'javascript_component': 80,
            'python_component': 70,
            'node_module': 60,
            'general': 50,
            'generic_component': 10,
        }
        best_by_name: Dict[str, Dict[str, Any]] = {}
        for p in patterns:
            name = p.get('component_name')
            t = p.get('component_type', 'general')
            priority = type_priority.get(t, 0)
            if name not in best_by_name:
                best_by_name[name] = p
            else:
                existing = best_by_name[name]
                existing_priority = type_priority.get(existing.get('component_type', 'general'), 0)
                if priority > existing_priority:
                    best_by_name[name] = p
                else:
                    # merge dependencies/methods if same component detected across files
                    if existing is not p:
                        merged_deps = list({*existing.get('dependencies', []), *p.get('dependencies', [])})[:5]
                        merged_methods = list({*existing.get('methods', []), *p.get('methods', [])})[:10]
                        existing['dependencies'] = merged_deps
                        existing['methods'] = merged_methods
        return list(best_by_name.values())
    
    def _extract_functions(self, content: str) -> List[Dict[str, str]]:
        """Extract function/method definitions"""
        functions = []
        
        # Python function patterns
        python_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        for match in re.finditer(python_pattern, content, re.MULTILINE):
            func_name = match.group(1)
            func_start = match.start()
            
            # Extract function body (simplified)
            lines = content[func_start:].split('\n')
            func_body = []
            indent_level = None
            
            for line in lines[1:]:  # Skip the def line
                if line.strip() == '':
                    continue
                
                current_indent = len(line) - len(line.lstrip())
                
                if indent_level is None and line.strip():
                    indent_level = current_indent
                
                if line.strip() and current_indent < indent_level:
                    break
                
                func_body.append(line)
                
                if len(func_body) > 50:  # Limit function size
                    break
            
            functions.append({
                'name': func_name,
                'body': '\n'.join(func_body),
                'type': 'python'
            })
        
        # JavaScript/TypeScript function patterns
        js_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(js_pattern, content, re.MULTILINE):
            func_name = match.group(1)
            func_start = match.start()
            
            # Extract function body (simplified)
            brace_count = 0
            func_body = []
            lines = content[func_start:].split('\n')
            
            for line in lines:
                func_body.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and '{' in lines[0]:
                    break
                
                if len(func_body) > 50:  # Limit function size
                    break
            
            functions.append({
                'name': func_name,
                'body': '\n'.join(func_body),
                'type': 'javascript'
            })
        
        return functions
    
    def _analyze_function_flow(self, func: Dict[str, str], source_file: str) -> Optional[Dict[str, Any]]:
        """Analyze flow control in a function"""
        body = func['body']
        
        # Find flow control statements
        flow_elements = []
        
        # Decision points
        if_count = len(re.findall(r'\bif\b', body, re.IGNORECASE))
        else_count = len(re.findall(r'\belse\b', body, re.IGNORECASE))
        
        # Loops
        for_count = len(re.findall(r'\bfor\b', body, re.IGNORECASE))
        while_count = len(re.findall(r'\bwhile\b', body, re.IGNORECASE))
        
        # Return statements
        return_count = len(re.findall(r'\breturn\b', body, re.IGNORECASE))
        
        # Only include functions with significant flow control
        total_flow = if_count + else_count + for_count + while_count + return_count
        
        if total_flow > 0:
            return {
                'function_name': func['name'],
                'source_file': source_file,
                'decisions': if_count + else_count,
                'loops': for_count + while_count,
                'returns': return_count,
                'complexity': total_flow,
                'body_preview': body[:200] + '...' if len(body) > 200 else body
            }
        
        return None
    
    def _extract_classes(self, content: str) -> List[Dict[str, str]]:
        """Extract class definitions"""
        classes = []
        
        # Python class patterns
        python_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
        for match in re.finditer(python_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            class_start = match.start()
            
            # Extract class body (simplified)
            lines = content[class_start:].split('\n')
            class_body = []
            indent_level = None
            
            for line in lines[1:]:  # Skip the class line
                if line.strip() == '':
                    continue
                
                current_indent = len(line) - len(line.lstrip())
                
                if indent_level is None and line.strip():
                    indent_level = current_indent
                
                if line.strip() and current_indent < indent_level:
                    break
                
                class_body.append(line)
                
                if len(class_body) > 100:  # Limit class size
                    break
            
            classes.append({
                'name': class_name,
                'body': '\n'.join(class_body),
                'type': 'python'
            })
        
        # JavaScript/TypeScript class patterns
        js_pattern = r'class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{'
        for match in re.finditer(js_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            class_start = match.start()
            
            # Extract class body (simplified)
            brace_count = 0
            class_body = []
            lines = content[class_start:].split('\n')
            
            for line in lines:
                class_body.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and '{' in lines[0]:
                    break
                
                if len(class_body) > 100:  # Limit class size
                    break
            
            classes.append({
                'name': class_name,
                'body': '\n'.join(class_body),
                'type': 'javascript'
            })
        
        return classes
    
    def _analyze_class_structure(self, cls: Dict[str, str], source_file: str) -> Optional[Dict[str, Any]]:
        """Analyze class structure and relationships"""
        body = cls['body']
        
        # Extract methods
        methods = []
        if cls['type'] == 'python':
            method_pattern = r'def\s+(\w+)\s*\([^)]*\):'
            methods = [match.group(1) for match in re.finditer(method_pattern, body)]
        elif cls['type'] == 'javascript':
            method_pattern = r'(\w+)\s*\([^)]*\)\s*\{'
            methods = [match.group(1) for match in re.finditer(method_pattern, body)]
        
        # Extract attributes/properties
        attributes = []
        if cls['type'] == 'python':
            attr_pattern = r'self\.(\w+)\s*='
            attributes = list(set([match.group(1) for match in re.finditer(attr_pattern, body)]))
        elif cls['type'] == 'javascript':
            attr_pattern = r'this\.(\w+)\s*='
            attributes = list(set([match.group(1) for match in re.finditer(attr_pattern, body)]))
        
        # Check for inheritance
        inheritance = []
        if 'extends' in body or 'implements' in body:
            inheritance.append('has_inheritance')
        
        if methods or attributes:
            return {
                'class_name': cls['name'],
                'source_file': source_file,
                'methods': methods[:10],  # Limit to first 10 methods
                'attributes': attributes[:10],  # Limit to first 10 attributes
                'method_count': len(methods),
                'attribute_count': len(attributes),
                'inheritance': inheritance,
                'language': cls['type']
            }
        
        return None
    
    def _extract_entities(self, content: str) -> List[Dict[str, str]]:
        """Extract entity/model definitions"""
        entities = []
        
        # Look for entity annotations
        entity_pattern = r'@Entity[^{]*class\s+(\w+)'
        for match in re.finditer(entity_pattern, content, re.MULTILINE | re.IGNORECASE):
            entity_name = match.group(1)
            entities.append({
                'name': entity_name,
                'body': content[match.start():match.start() + 500],  # Get some context
                'type': 'jpa_entity'
            })
        
        # Look for table definitions
        table_pattern = r'CREATE\s+TABLE\s+(\w+)'
        for match in re.finditer(table_pattern, content, re.MULTILINE | re.IGNORECASE):
            table_name = match.group(1)
            entities.append({
                'name': table_name,
                'body': content[match.start():match.start() + 500],
                'type': 'sql_table'
            })
        
        return entities
    
    def _analyze_entity_structure(self, entity: Dict[str, str], source_file: str) -> Optional[Dict[str, Any]]:
        """Analyze entity structure and relationships"""
        body = entity['body']
        
        # Extract fields/columns
        fields = []
        relationships = []
        
        if entity['type'] == 'jpa_entity':
            # JPA field patterns
            field_pattern = r'private\s+(\w+)\s+(\w+);'
            fields = [(match.group(1), match.group(2)) for match in re.finditer(field_pattern, body)]
            
            # JPA relationship patterns
            if '@OneToMany' in body or '@ManyToOne' in body or '@ManyToMany' in body:
                relationships.append('has_relationships')
        
        elif entity['type'] == 'sql_table':
            # SQL column patterns
            col_pattern = r'(\w+)\s+(\w+)(?:\s+(?:PRIMARY|FOREIGN)\s+KEY)?'
            fields = [(match.group(1), match.group(2)) for match in re.finditer(col_pattern, body)]
            
            # SQL relationship patterns
            if 'FOREIGN KEY' in body or 'REFERENCES' in body:
                relationships.append('has_foreign_keys')
        
        if fields:
            return {
                'entity_name': entity['name'],
                'source_file': source_file,
                'fields': fields[:10],  # Limit to first 10 fields
                'field_count': len(fields),
                'relationships': relationships,
                'entity_type': entity['type']
            }
        
        return None
    
    def _extract_components(self, content: str, language: str = 'unknown') -> List[Dict[str, str]]:
        """Extract component/module definitions"""
        components = []
        
        # Spring/Java component patterns
        if language == 'java':
            component_patterns = [
                r'@Component[^{]*class\s+(\w+)',
                r'@Service[^{]*class\s+(\w+)',
                r'@Controller[^{]*class\s+(\w+)',
                r'@Repository[^{]*class\s+(\w+)'
            ]
            for pattern in component_patterns:
                for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                    component_name = match.group(1)
                    components.append({
                        'name': component_name,
                        'body': content[match.start():match.start() + 300],
                        'type': 'spring_component'
                    })
        
        # C# component patterns
        if language == 'csharp':
            csharp_patterns = [
                r'public\s+class\s+(\w+Controller)\s*:\s*ControllerBase',
                r'public\s+class\s+(\w+Service)\s*:',
                r'public\s+class\s+(\w+Repository)\s*:',
                r'public\s+interface\s+(\w+Service)',
                r'public\s+interface\s+(\w+Repository)',
                r'public\s+class\s+(\w+Manager)\s*:',
                r'public\s+class\s+(\w+Handler)\s*:',
                r'public\s+class\s+(\w+Provider)\s*:'
            ]
            for pattern in csharp_patterns:
                for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                    component_name = match.group(1)
                    components.append({
                        'name': component_name,
                        'body': content[match.start():match.start() + 300],
                        'type': 'csharp_component'
                    })
        
        # Python component patterns
        if language == 'python':
            python_patterns = [
                r'class\s+(\w+Service)\s*:',
                r'class\s+(\w+Controller)\s*:',
                r'class\s+(\w+Repository)\s*:',
                r'class\s+(\w+Manager)\s*:',
                r'class\s+(\w+Handler)\s*:',
                r'class\s+(\w+Provider)\s*:'
            ]
            for pattern in python_patterns:
                for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                    component_name = match.group(1)
                    components.append({
                        'name': component_name,
                        'body': content[match.start():match.start() + 300],
                        'type': 'python_component'
                    })
        
        # JavaScript/TypeScript component patterns
        if language in ('javascript', 'typescript'):
            js_patterns = [
                r'class\s+(\w+Service)\s*{',
                r'class\s+(\w+Controller)\s*{',
                r'class\s+(\w+Repository)\s*{',
                r'class\s+(\w+Manager)\s*{',
                r'class\s+(\w+Handler)\s*{',
                r'class\s+(\w+Provider)\s*{',
                r'export\s+class\s+(\w+Service)',
                r'export\s+class\s+(\w+Controller)',
                r'export\s+class\s+(\w+Repository)'
            ]
            for pattern in js_patterns:
                for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                    component_name = match.group(1)
                    components.append({
                        'name': component_name,
                        'body': content[match.start():match.start() + 300],
                        'type': 'javascript_component'
                    })
        
        # Module exports (JavaScript/Node.js)
        if language in ('javascript', 'typescript'):
            module_pattern = r'module\.exports\s*=\s*(\w+)'
            for match in re.finditer(module_pattern, content, re.MULTILINE):
                module_name = match.group(1)
                components.append({
                    'name': module_name,
                    'body': content[match.start():match.start() + 300],
                    'type': 'node_module'
                })
        
        # Generic class patterns for any language (fallback)
        # Keep generic only if it ends with known role suffixes
        generic_patterns = [
            r'class\s+(\w+)(?:Controller|Service|Repository|Manager|Handler|Provider)',
            r'public\s+class\s+(\w+)(?:Controller|Service|Repository|Manager|Handler|Provider)'
        ]
        for pattern in generic_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
                component_name = match.group(1)
                # Only add if not already found
                if not any(c['name'] == component_name for c in components):
                    components.append({
                        'name': component_name,
                        'body': content[match.start():match.start() + 300],
                        'type': 'generic_component'
                    })
        
        return components
    
    def _analyze_component_structure(self, component: Dict[str, str], source_file: str) -> Optional[Dict[str, Any]]:
        """Analyze component structure and dependencies"""
        body = component['body']
        
        # Extract dependencies
        dependencies = []
        
        if component['type'] == 'spring_component':
            # Spring dependency injection patterns
            autowired_pattern = r'@Autowired[^;]*(\w+Service|\w+Repository|\w+Component)'
            dependencies = [match.group(1) for match in re.finditer(autowired_pattern, body)]
        
        elif component['type'] == 'csharp_component':
            # C# dependency injection patterns
            csharp_patterns = [
                r'private\s+readonly\s+(\w+Service|\w+Repository|\w+Manager|\w+Controller)',
                r'private\s+(\w+Service|\w+Repository|\w+Manager|\w+Controller)',
                r'public\s+(\w+Service|\w+Repository|\w+Manager|\w+Controller)',
                r'protected\s+(\w+Service|\w+Repository|\w+Manager|\w+Controller)',
                r'readonly\s+(\w+Service|\w+Repository|\w+Manager|\w+Controller)',
                r'IMongoCollection<(\w+)>',
                r'(\w+Configuration)',
                r'(\w+Client)'
            ]
            for pattern in csharp_patterns:
                deps = [match.group(1) for match in re.finditer(pattern, body, re.IGNORECASE)]
                dependencies.extend(deps)
        
        elif component['type'] == 'python_component':
            # Python dependency patterns
            python_patterns = [
                r'self\.(\w+Service|\w+Repository|\w+Manager)',
                r'(\w+Service|\w+Repository|\w+Manager)\(',
                r'from\s+(\w+)\s+import'
            ]
            for pattern in python_patterns:
                deps = [match.group(1) for match in re.finditer(pattern, body, re.IGNORECASE)]
                dependencies.extend(deps)
        
        elif component['type'] == 'javascript_component':
            # JavaScript/TypeScript dependency patterns
            js_patterns = [
                r'constructor\s*\(\s*(\w+Service|\w+Repository|\w+Manager)',
                r'this\.(\w+Service|\w+Repository|\w+Manager)',
                r'import\s+(\w+)\s+from',
                r'require\([\'"]([^\'"]+)[\'"]\)'
            ]
            for pattern in js_patterns:
                deps = [match.group(1) for match in re.finditer(pattern, body, re.IGNORECASE)]
                dependencies.extend(deps)
        
        elif component['type'] == 'node_module':
            # Node.js require/import patterns
            require_pattern = r'require\([\'"]([^\'"]+)[\'"]\)'
            dependencies = [match.group(1) for match in re.finditer(require_pattern, body)]
        
        # Extract interfaces/methods
        methods = []
        
        if component['type'] == 'spring_component':
            method_pattern = r'public\s+\w+\s+(\w+)\s*\('
            methods = [match.group(1) for match in re.finditer(method_pattern, body)]
        
        elif component['type'] == 'csharp_component':
            # C# method patterns
            csharp_method_patterns = [
                r'public\s+\w+\s+(\w+)\s*\(',
                r'private\s+\w+\s+(\w+)\s*\(',
                r'protected\s+\w+\s+(\w+)\s*\(',
                r'\[HttpGet\]\s*\w*\s*(\w+)\s*\(',
                r'\[HttpPost\]\s*\w*\s*(\w+)\s*\(',
                r'\[HttpPut\]\s*\w*\s*(\w+)\s*\(',
                r'\[HttpDelete\]\s*\w*\s*(\w+)\s*\(',
                r'\[HttpGet\("[^"]*"\)\]\s*\w*\s*(\w+)\s*\(',
                r'\[HttpPost\("[^"]*"\)\]\s*\w*\s*(\w+)\s*\(',
                r'\[HttpPut\("[^"]*"\)\]\s*\w*\s*(\w+)\s*\(',
                r'\[HttpDelete\("[^"]*"\)\]\s*\w*\s*(\w+)\s*\(',
                # More flexible patterns for HTTP methods
                r'\[HttpGet[^]]*\]\s*[^{]*?(\w+)\s*\(',
                r'\[HttpPost[^]]*\]\s*[^{]*?(\w+)\s*\(',
                r'\[HttpPut[^]]*\]\s*[^{]*?(\w+)\s*\(',
                r'\[HttpDelete[^]]*\]\s*[^{]*?(\w+)\s*\('
            ]
            for pattern in csharp_method_patterns:
                method_matches = [match.group(1) for match in re.finditer(pattern, body, re.IGNORECASE)]
                methods.extend(method_matches)
        
        elif component['type'] == 'python_component':
            # Python method patterns
            python_method_patterns = [
                r'def\s+(\w+)\s*\(',
                r'async\s+def\s+(\w+)\s*\('
            ]
            for pattern in python_method_patterns:
                method_matches = [match.group(1) for match in re.finditer(pattern, body, re.IGNORECASE)]
                methods.extend(method_matches)
        
        elif component['type'] == 'javascript_component':
            # JavaScript/TypeScript method patterns
            js_method_patterns = [
                r'(\w+)\s*\([^)]*\)\s*{',
                r'async\s+(\w+)\s*\([^)]*\)\s*{',
                r'(\w+)\s*=\s*\([^)]*\)\s*=>'
            ]
            for pattern in js_method_patterns:
                method_matches = [match.group(1) for match in re.finditer(pattern, body, re.IGNORECASE)]
                methods.extend(method_matches)
        
        # Remove duplicates and limit
        methods = list(set(methods))[:10]
        dependencies = list(set(dependencies))[:5]
        
        return {
            'component_name': component['name'],
            'source_file': source_file,
            'dependencies': dependencies,
            'methods': methods,
            'component_type': component['type'],
            'dependency_count': len(dependencies),
            'method_count': len(methods)
        }


class MermaidGenerator:
    """Generate Mermaid diagram code for different diagram types"""
    
    def __init__(self):
        self.max_nodes = 20  # Limit diagram complexity
    
    def create_flowchart_mermaid(self, flow_patterns: List[Dict[str, Any]]) -> str:
        """Create Mermaid flowchart from flow patterns"""
        if not flow_patterns:
            return "flowchart TD\n    A[No flow patterns found]"
        
        mermaid_lines = ["flowchart TD"]
        node_id = 1
        
        for pattern in flow_patterns[:self.max_nodes]:
            func_name = pattern['function_name']
            complexity = pattern['complexity']
            
            # Create start node
            start_id = f"F{node_id}"
            mermaid_lines.append(f"    {start_id}[{func_name}]")
            
            # Add decision nodes based on complexity
            if pattern['decisions'] > 0:
                decision_id = f"D{node_id}"
                mermaid_lines.append(f"    {decision_id}{{Decision Point}}")
                mermaid_lines.append(f"    {start_id} --> {decision_id}")
                
                # Add yes/no paths
                yes_id = f"Y{node_id}"
                no_id = f"N{node_id}"
                mermaid_lines.append(f"    {yes_id}[Process Yes]")
                mermaid_lines.append(f"    {no_id}[Process No]")
                mermaid_lines.append(f"    {decision_id} -->|Yes| {yes_id}")
                mermaid_lines.append(f"    {decision_id} -->|No| {no_id}")
            
            # Add loop nodes
            if pattern['loops'] > 0:
                loop_id = f"L{node_id}"
                mermaid_lines.append(f"    {loop_id}[Loop Process]")
                mermaid_lines.append(f"    {start_id} --> {loop_id}")
                mermaid_lines.append(f"    {loop_id} --> {loop_id}")
            
            # Add end node
            if pattern['returns'] > 0:
                end_id = f"E{node_id}"
                mermaid_lines.append(f"    {end_id}[Return]")
                
                # Connect to end
                if pattern['decisions'] > 0:
                    mermaid_lines.append(f"    Y{node_id} --> {end_id}")
                    mermaid_lines.append(f"    N{node_id} --> {end_id}")
                else:
                    mermaid_lines.append(f"    {start_id} --> {end_id}")
            
            node_id += 1
            
            if node_id > self.max_nodes:
                break
        
        return '\n'.join(mermaid_lines)
    
    def create_class_diagram_mermaid(self, class_patterns: List[Dict[str, Any]]) -> str:
        """Create Mermaid class diagram from class patterns"""
        if not class_patterns:
            return "classDiagram\n    class NoClassesFound"
        
        mermaid_lines = ["classDiagram"]
        
        for pattern in class_patterns[:self.max_nodes]:
            class_name = pattern['class_name']
            methods = pattern['methods']
            attributes = pattern['attributes']
            
            # Add class definition
            mermaid_lines.append(f"    class {class_name}")
            
            # Add attributes
            for attr in attributes[:5]:  # Limit attributes
                mermaid_lines.append(f"    {class_name} : +{attr}")
            
            # Add methods
            for method in methods[:5]:  # Limit methods
                mermaid_lines.append(f"    {class_name} : +{method}()")
            
            # Add inheritance relationships
            if pattern.get('inheritance'):
                mermaid_lines.append(f"    {class_name} --|> BaseClass")
        
        return '\n'.join(mermaid_lines)
    
    def create_er_diagram_mermaid(self, er_patterns: List[Dict[str, Any]]) -> str:
        """Create Mermaid ER diagram from entity patterns"""
        if not er_patterns:
            return "erDiagram\n    ENTITY ||--|| NO_ENTITIES : \"no data found\""
        
        mermaid_lines = ["erDiagram"]
        
        for pattern in er_patterns[:self.max_nodes]:
            entity_name = pattern['entity_name']
            fields = pattern['fields']
            
            # Add entity with fields
            for field_name, field_type in fields[:5]:  # Limit fields
                mermaid_lines.append(f"    {entity_name} {{")
                mermaid_lines.append(f"        {field_type} {field_name}")
                mermaid_lines.append("    }")
                break  # Only add structure once per entity
            
            # Add relationships
            if pattern.get('relationships'):
                # Simple relationship example
                mermaid_lines.append(f"    {entity_name} ||--|| RELATED_ENTITY : relationship")
        
        return '\n'.join(mermaid_lines)
    
    def create_component_diagram_mermaid(self, component_patterns: List[Dict[str, Any]]) -> str:
        """Create Mermaid component diagram from component patterns"""
        if not component_patterns:
            return "graph TB\n    subgraph NoComponents\n    A[No components found]\n    end"
        
        # Filter out non-meaningful generic components (e.g., data-only models with zero methods)
        meaningful_components: List[Dict[str, Any]] = []
        for p in component_patterns:
            comp_type = p.get('component_type', 'general')
            method_count = p.get('method_count', len(p.get('methods', [])))
            name = p.get('component_name', '')
            if comp_type == 'generic_component' and method_count == 0:
                # Treat as data node via dependency when referenced, not as a component
                continue
            meaningful_components.append(p)
        
        if not meaningful_components:
            return "graph TB\n    subgraph NoComponents\n    A[No components found]\n    end"
        
        mermaid_lines = ["graph TB"]
        
        # Group components by type
        component_groups: Dict[str, List[Dict[str, Any]]] = {}
        for pattern in meaningful_components[:self.max_nodes]:
            comp_type = pattern.get('component_type', 'general')
            if comp_type not in component_groups:
                component_groups[comp_type] = []
            component_groups[comp_type].append(pattern)
        
        # Create subgraphs for each component type
        added_nodes = set()
        for comp_type, components in component_groups.items():
            subgraph_name = comp_type.replace('_', ' ').title()
            mermaid_lines.append(f"    subgraph {subgraph_name}")
            
            for component in components:
                comp_name = component['component_name']
                if comp_name in added_nodes:
                    continue
                # Add component with type indicator
                mermaid_lines.append(f"    {comp_name}[{comp_name}]")
                added_nodes.add(comp_name)
            
            mermaid_lines.append("    end")
        
        # Helper to normalize dependency names (e.g., map Mongo primitives to MongoDB)
        def _normalize_dep(dep: str) -> str:
            d = dep.replace('.', '').replace('/', '').replace('(', '').replace(')', '')
            if not d:
                return d
            upper = d.lower()
            if 'mongoclient' in upper or 'imongocollection' in upper or 'mongodb' in upper:
                return 'MongoDB'
            if upper in {'iconfiguration'}:
                return 'IConfiguration'
            return d
        
        # Add dependencies between components
        for pattern in meaningful_components[:self.max_nodes]:
            comp_name = pattern['component_name']
            dependencies = pattern.get('dependencies', [])
            
            for dep in dependencies[:3]:  # Limit dependencies
                dep_clean = _normalize_dep(dep)
                if dep_clean and dep_clean != comp_name and len(dep_clean) > 1:
                    # Check if dependency is actually a component we know about
                    is_known_component = dep_clean in added_nodes
                    if is_known_component:
                        mermaid_lines.append(f"    {comp_name} --> {dep_clean}")
                    else:
                        # Add external dependency as a different shape
                        mermaid_lines.append(f"    {dep_clean}({dep_clean})")
                        mermaid_lines.append(f"    {comp_name} -.-> {dep_clean}")
        
        # If no dependencies found, add some basic relationships
        if len(mermaid_lines) <= len(component_groups) + 1:  # Only subgraphs defined
            mermaid_lines.append("    %% No explicit dependencies found")
            mermaid_lines.append("    %% Components are shown in their respective groups")
        
        return '\n'.join(mermaid_lines)
    
    def create_enhanced_sequence_mermaid(self, patterns: List[Dict[str, Any]]) -> str:
        """Create enhanced Mermaid sequence diagram"""
        if not patterns:
            return "sequenceDiagram\n    participant A\n    participant B\n    A->>B: No interactions found"
        
        mermaid_lines = ["sequenceDiagram"]
        participants = set()
        
        # Extract participants from patterns
        for pattern in patterns:
            interactions = pattern.get('interactions', [])
            for interaction in interactions:
                caller = interaction.get('caller', 'Unknown')
                target = interaction.get('target', 'Unknown')
                participants.add(caller)
                participants.add(target)
        
        # Add participant declarations
        for participant in sorted(list(participants))[:10]:  # Limit participants
            mermaid_lines.append(f"    participant {participant}")
        
        # Add interactions
        for pattern in patterns:
            interactions = pattern.get('interactions', [])
            for interaction in interactions[:15]:  # Limit interactions
                caller = interaction.get('caller', 'Unknown')
                target = interaction.get('target', 'Unknown')
                method = interaction.get('method', 'call')
                
                if caller in participants and target in participants:
                    mermaid_lines.append(f"    {caller}->>+{target}: {method}")
                    mermaid_lines.append(f"    {target}-->>-{caller}: response")
        
        return '\n'.join(mermaid_lines)
