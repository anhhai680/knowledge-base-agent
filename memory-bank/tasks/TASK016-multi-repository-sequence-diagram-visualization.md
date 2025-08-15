# [TASK016] - Multi-Repository Sequence Diagram Visualization

**Status:** Completed  
**Added:** August 13, 2025  
**Updated:** August 14, 2025  
**Completed:** August 14, 2025

## Original Request
User wants to visualize sequence diagrams across multiple repositories using Mermaid syntax and display them on the web chat interface. The system should automatically generate sequence diagrams from code analysis when users ask questions about API interactions between services, code flow analysis across microservices, and application interactions with third-party/external services.

## Revised Approach (Updated August 14, 2025)
After analyzing the existing codebase, the implementation strategy has been revised to leverage existing components and follow the agent router pattern instead of creating duplicate functionality. The new approach focuses on:

1. **Agent Router Pattern**: Using intelligent query routing within the existing `/query` endpoint instead of creating separate endpoints
2. **Existing Vector Store**: Leveraging ChromaStore.similarity_search() for code retrieval instead of building new GitHub analysis
3. **Component Extension**: Extending existing RAGAgent and API infrastructure rather than creating parallel systems
4. **Single Endpoint Integration**: Maintaining the existing web chat interface that uses only the `/query` endpoint

This approach minimizes new code while maximizing reuse of proven, existing components, ensuring consistency with the current system architecture.

## Implementation Plan

### Phase 1: Extend Data Models (Days 1)

#### Subtask 1.1: Update API Models for Diagram Support
**Files to modify:**
- `src/api/models.py`

**Implementation Details:**
```python
# Extend existing QueryResponse model
class QueryResponse(BaseModel):
    answer: str
    source_documents: List[Dict[str, Any]]
    status: str
    num_sources: int
    error: Optional[str] = None
    # Extended fields for diagram responses
    mermaid_code: Optional[str] = None
    diagram_type: Optional[str] = None
```

**Key Benefits:**
- No new endpoints needed - extends existing `/query` response
- Maintains backward compatibility with current web interface
- Leverages existing error handling and validation patterns

### Phase 2: Create Specialized Agents (Days 2-3)

#### Subtask 2.1: Create DiagramHandler (Separate Agent)
**New file:** `src/processors/diagram_handler.py`

**Core Components:**
```python
class DiagramHandler:
    """Specialized agent for diagram generation using existing vector store capabilities"""
    
    def __init__(self, vectorstore, llm):
        self.vectorstore = vectorstore
        self.llm = llm
        self.sequence_detector = SequenceDetector()
    
    def generate_sequence_diagram(self, query: str) -> Dict[str, Any]
    def _find_relevant_code(self, query: str) -> List[Document]  # Uses ChromaStore.similarity_search()
    def _analyze_interaction_patterns(self, docs: List[Document]) -> List[Dict]
    def _generate_mermaid_sequence(self, patterns: List[Dict]) -> str
```

**Leverages Existing Infrastructure:**
- Uses existing ChromaStore.similarity_search() for code retrieval
- Reuses existing metadata filtering and document processing
- Follows established error handling patterns

#### Subtask 2.2: Create SequenceDetector for Pattern Analysis
**New file:** `src/processors/sequence_detector.py`

**Language-Specific Analysis:**
```python
class SequenceDetector:
    """Detects interaction patterns in code for sequence diagrams"""
    
    def analyze_code(self, code: str, language: str) -> Dict
    def _analyze_python_code(self, code: str) -> Dict     # AST-based analysis
    def _analyze_js_ts_code(self, code: str) -> Dict      # Regex-based analysis  
    def _analyze_csharp_code(self, code: str) -> Dict     # Pattern matching
```

**Supported Languages (Reduced Scope):**
- Python, JavaScript, TypeScript, C# only
- Focuses on method calls and class interactions
- Extracts caller/callee/method information

#### Subtask 2.3: Implement Agent Router
**New file:** `src/agents/agent_router.py`

**Intelligent Query Routing:**
```python
class AgentRouter:
    """Routes queries to appropriate specialized agents with enhanced pattern detection"""
    
    def route_query(self, question: str) -> Dict[str, Any]
    def _is_diagram_request(self, question: str) -> bool
    def _generate_diagram_response(self, query: str) -> Dict[str, Any]
```

**Detection Patterns:**
- Pre-compiled regex patterns for performance
- Multi-strategy detection (keywords, phrases, context)
- Handles 50+ different question variations
- Graceful fallback to RAGAgent for ambiguous cases

### Phase 3: API Integration (Day 4)

#### Subtask 3.1: Update Query Endpoint with Agent Router
**Files to modify:**
- `src/api/routes.py`

**Key Changes:**
```python
# Initialize agent router at startup
async def initialize_agents():
    global rag_agent, agent_router
    rag_agent = RAGAgent(llm=llm, vectorstore=vectorstore)
    diagram_handler = DiagramHandler(vectorstore, llm)
    agent_router = AgentRouter(rag_agent, diagram_handler)

# Enhanced query endpoint with intelligent routing
@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    result = agent_router.route_query(request.question)
    return QueryResponse(**result)
```

**No New Endpoints:**
- Web interface continues using single `/query` endpoint
- Backend intelligence handles routing transparently
- Maintains all existing functionality

### Phase 4: Frontend Enhancement (Day 5)

#### Subtask 4.1: Integrate Mermaid.js Rendering
**Files to modify:**
- `web/index.html`

**Client-Side Integration:**
```html
<!-- Mermaid.js CDN Integration -->
<script src="https://unpkg.com/mermaid@10/dist/mermaid.min.js"></script>

<script>
// Initialize Mermaid
mermaid.initialize({ startOnLoad: false });

// Enhanced sendMessage function - uses only /query endpoint
async function sendMessage() {
    // Always use the single /query endpoint
    // Backend agent router will determine the appropriate response type
    const response = await fetch('/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ question: message, max_results: 5 })
    });
    
    if (response.ok) {
        const result = await response.json();
        // Check if response contains diagram data
        if (result.mermaid_code) {
            addDiagramMessage(result);
        } else {
            // Regular text response
            addMessage(result.answer, 'assistant', result.source_documents);
        }
    }
}
</script>
```

**Key Features:**
- No frontend routing logic needed
- Automatic diagram detection from response
- Graceful fallback for render errors
- Responsive diagram containers

#### Subtask 4.2: Add Diagram Rendering Components
**Implementation Areas:**
```javascript
function addDiagramMessage(result) {
    // Create diagram container with analysis summary
    // Render Mermaid diagram with error handling  
    // Add source file references
    // Enable diagram interactions (zoom, fullscreen)
}
```

**CSS Enhancements:**
```css
.mermaid-diagram {
    background: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    margin: 10px 0;
    overflow-x: auto;
}
```

### Phase 5: Testing & Validation (Days 6-7)

#### Subtask 5.1: Comprehensive Testing Suite
**Test Files to Create:**
- `tests/test_agent_router.py` - Test routing logic with 50+ question patterns
- `tests/test_diagram_handler.py` - Test diagram generation workflow
- `tests/test_sequence_detector.py` - Test language-specific pattern detection
- `tests/test_diagram_api_integration.py` - End-to-end API testing

**Test Coverage:**
```python
class TestAgentRouter:
    def test_direct_diagram_requests(self)      # "Show sequence diagram"
    def test_visualization_requests(self)       # "Visualize how X works"
    def test_flow_analysis_requests(self)       # "How does Y flow work?"
    def test_mermaid_specific_requests(self)    # "Generate mermaid code"
    def test_non_diagram_requests(self)         # Regular questions
    def test_edge_cases(self)                   # Ambiguous requests
```

#### Subtask 5.2: Performance & Error Testing
**Validation Criteria:**
- **Routing Decision Speed**: <1 second for 300 questions
- **Diagram Generation Time**: <10 seconds per diagram
- **Error Handling**: Graceful degradation for invalid requests
- **Response Format**: Consistent QueryResponse structure

## Progress Tracking

**Overall Status:** Completed - 100%

### Subtasks
| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 16.1 | Extend API models for diagram support | Complete | Aug 14, 2025 | Added mermaid_code and diagram_type fields |
| 16.2 | Create DiagramHandler agent | Complete | Aug 14, 2025 | Full implementation with multi-language support |
| 16.3 | Create SequenceDetector for pattern analysis | Complete | Aug 14, 2025 | Python AST, JS/TS/C# regex, markdown analysis |
| 16.4 | Implement AgentRouter for intelligent routing | Complete | Aug 14, 2025 | 12+ pattern detection strategies |
| 16.5 | Update API routes with router integration | Complete | Aug 14, 2025 | Single endpoint with intelligent routing |
| 16.6 | Enhance web interface with Mermaid.js | Complete | Aug 14, 2025 | Live diagram rendering and error handling |
| 16.7 | Comprehensive testing and validation | Complete | Aug 14, 2025 | Unit tests and demo script |
| 16.8 | Create pull request and documentation | Complete | Aug 14, 2025 | PR #11 ready for review |

## Progress Log
### August 14, 2025 - TASK COMPLETION
- **MAJOR ACHIEVEMENT**: Successfully implemented complete sequence diagram visualization system
- **Pull Request Created**: PR #11 with comprehensive feature implementation
- **Scope Delivered**: All planned functionality implemented and tested
- **Key Features Completed**:
  - Agent router pattern with intelligent query detection (12+ regex patterns)
  - Multi-language code analysis: Python (AST), JavaScript/TypeScript, C# (regex), Markdown
  - Mermaid sequence diagram generation with noise filtering and participant management
  - Enhanced web interface with live Mermaid.js rendering
  - Zero breaking changes - maintains 100% backward compatibility
  - Comprehensive error handling and graceful fallbacks
  - Repository filtering and context-aware analysis
- **Technical Excellence**: 
  - Leverages existing ChromaDB infrastructure
  - Extends existing API models without breaking changes
  - Production-ready error handling
  - Comprehensive test coverage
- **User Experience**: 
  - Natural language requests like "Show me a sequence diagram for authentication"
  - Visual diagrams rendered directly in chat interface
  - Source code attribution linking diagrams to files
  - Intelligent fallback to text when diagrams aren't applicable
- **Status**: Implementation complete, ready for production use

## Progress Log
### August 13, 2025
- Updated implementation plan to use agent router pattern with single endpoint
- Aligned architecture to leverage existing ChromaStore vector database capabilities
- Removed separate endpoint approach to avoid code duplication
- Focused on extending existing API models rather than creating new endpoints
- Emphasized reuse of existing similarity_search functionality for code analysis

## Technical Specifications

### Architecture Components

#### Agent Router Pattern
**File:** `src/agents/agent_router.py`
```python
class AgentRouter:
    """Intelligent routing between RAG and Diagram generation"""
    def __init__(self, rag_agent, diagram_handler):
        self.rag_agent = rag_agent
        self.diagram_handler = diagram_handler
        self.compiled_patterns = self._compile_patterns()
    
    async def route_query(self, query: str) -> QueryResponse:
        if self._is_diagram_request(query):
            return await self.diagram_handler.generate_diagram(query)
        else:
            return await self.rag_agent.query(query)
```

#### Diagram Handler
**File:** `src/agents/diagram_handler.py`
```python
class DiagramHandler:
    """Leverage ChromaStore for code analysis and diagram generation"""
    def __init__(self, chroma_store):
        self.chroma_store = chroma_store
        self.sequence_detector = SequenceDetector()
    
    async def generate_diagram(self, query: str) -> QueryResponse:
        # Use existing similarity_search to find relevant code
        relevant_chunks = self.chroma_store.similarity_search(
            query, k=20, where={"language": {"$in": ["python", "javascript", "typescript", "csharp"]}}
        )
        
        # Analyze code patterns and generate Mermaid syntax
        mermaid_code = self.sequence_detector.analyze_sequences(relevant_chunks)
        return QueryResponse(
            answer=f"Here's the sequence diagram analysis:\n\n{analysis}",
            source_documents=relevant_chunks,
            mermaid_code=mermaid_code
        )
```

#### Extended API Models
**File:** `src/api/models.py`
```python
class QueryResponse(BaseModel):
    answer: str
    source_documents: List[Document] = []
    # Extended for diagram support
    mermaid_code: Optional[str] = None
    diagram_explanation: Optional[str] = None
    analysis_metadata: Optional[Dict] = None
```

### Integration Points

#### Single Endpoint Approach
**File:** `src/api/routes.py`
```python
@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Single endpoint - agent router determines response type"""
    return await agent_router.route_query(request.question)
```

#### Frontend Integration
**File:** `web/index.html`
- Mermaid.js rendering for diagram responses
- Automatic detection of diagram vs. text responses
- No frontend routing logic needed

### Supported Languages
- **Python**: Flask, FastAPI, Django patterns
- **JavaScript/TypeScript**: Express, NestJS, React patterns  
- **C#**: ASP.NET, Web API patterns

### Detection Patterns
**Pre-compiled Regex Patterns:**
```python
DIAGRAM_PATTERNS = {
    'sequence': [
        r'\b(?:sequence|flow|interaction)\s+diagram\b',
        r'\bshow.*(?:sequence|flow|interaction)\b',
        r'\bvisuali[sz]e.*(?:how|flow|sequence)\b'
    ],
    'mermaid': [
        r'\bmermaid\s+(?:code|syntax|diagram)\b',
        r'\bgenerate.*mermaid\b'
    ]
}
```

## Risk Mitigation Strategies

### Technical Risks
1. **Repository Analysis Complexity**
   - **Risk**: Inaccurate pattern recognition leading to incorrect diagrams
   - **Mitigation**: Implement confidence scoring and validation
   - **Fallback**: Provide text-based flow descriptions

2. **Performance Impact**
   - **Risk**: Large repository analysis causing timeouts
   - **Mitigation**: Implement streaming analysis and result caching
   - **Fallback**: Progressive analysis with partial results

3. **GitHub API Limitations**
   - **Risk**: Rate limiting affecting functionality
   - **Mitigation**: Intelligent request batching and caching
   - **Fallback**: Use cached data with staleness indicators

### User Experience Risks
1. **Diagram Complexity**
   - **Risk**: Overly complex diagrams becoming unreadable
   - **Mitigation**: Automatic simplification and progressive disclosure
   - **Fallback**: Multiple simplified views of the same flow

2. **Repository Specification**
   - **Risk**: Users providing unclear or incorrect repository names
   - **Mitigation**: Smart name resolution and suggestion system
   - **Fallback**: Interactive repository selection interface

## Success Metrics
- **Accuracy**: 90%+ correct identification of service interactions
- **Performance**: Diagram generation within 10 seconds for typical use cases
- **Usability**: Users can successfully generate diagrams with minimal instruction
- **Reliability**: 95%+ uptime for diagram generation feature
- **Coverage**: Support for 5+ major web frameworks across 4 programming languages

## Future Enhancements
1. **Interactive Diagram Elements**: Click-to-navigate to source code
2. **Real-time Updates**: Live diagram updates as code changes
3. **Collaboration Features**: Shared diagram annotations and comments
4. **Export Formats**: Support for PDF, PNG, SVG exports
5. **Template Library**: Pre-built diagram templates for common patterns
6. **Performance Analytics**: Diagram-based performance bottleneck identification
