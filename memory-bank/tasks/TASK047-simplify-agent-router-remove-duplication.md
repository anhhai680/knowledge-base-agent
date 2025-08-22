# TASK047: Simplify AgentRouter - Remove Diagram Logic Duplication

**Status:** Pending
**Added:** August 22, 2025
**Updated:** August 22, 2025

## Original Request
Remove duplication between AgentRouter and DiagramAgent diagram detection logic. The AgentRouter should only route requests, not process them. Currently there's significant duplication in diagram detection patterns and processing logic.

## Thought Process
The AgentRouter violates Single Responsibility Principle by:

1. **Duplicate Pattern Detection**: Both `_compile_diagram_patterns()` and `DiagramAgent.diagram_type_keywords` detect diagram requests
2. **Processing Logic in Router**: `_generate_diagram_response()`, `_enhance_mermaid_response()`, `_is_mermaid_specific_request()` should be in DiagramAgent
3. **Complex Routing Logic**: 100+ lines of diagram detection code when simple keyword matching would suffice for routing

## Current Duplication Issues

### AgentRouter (Should Remove):
- `_compile_diagram_patterns()` - 20+ regex patterns
- `_is_diagram_request()` - 50+ lines of detection logic  
- `_generate_diagram_response()` - 30+ lines of processing
- `_is_mermaid_specific_request()` - Mermaid detection
- `_enhance_mermaid_response()` - Mermaid enhancement

### DiagramAgent (Should Keep):
- `diagram_type_keywords` - Diagram type mapping
- `_enhanced_diagram_type_detection()` - Advanced detection
- `process_query()` - All diagram processing logic

## Implementation Plan

### Phase 1: Simplify AgentRouter (Target: 50% line reduction)
1. **Replace `_compile_diagram_patterns()` with simple keyword list**
2. **Simplify `_is_diagram_request()` to basic keyword matching**
3. **Replace `_generate_diagram_response()` with simple delegation**
4. **Remove `_is_mermaid_specific_request()` and `_enhance_mermaid_response()`**
5. **Move repository info logic to RAG agent or separate handler**

### Phase 2: Enhance DiagramAgent
1. **Add `can_handle_request()` method for better routing**
2. **Move all mermaid enhancement logic to DiagramAgent**
3. **Enhance `process_query()` to handle all diagram processing**

### Phase 3: Clean Architecture
1. **Router becomes thin routing layer (< 100 lines total)**
2. **DiagramAgent becomes thick processing layer**
3. **Clear separation of concerns**

## Target Code Reduction
- **AgentRouter**: From 359 lines to ~150 lines (58% reduction)
- **Removed Duplication**: ~100 lines of duplicate logic
- **Cleaner Architecture**: Single responsibility principle followed

## Progress Tracking

**Overall Status:** In Progress - 85%

### Subtasks
| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 1.1 | Remove _compile_diagram_patterns() | Complete | 2025-08-22 | Replaced with simple keyword list |
| 1.2 | Simplify _is_diagram_request() | Complete | 2025-08-22 | Basic keyword matching + DiagramAgent capability check |
| 1.3 | Replace _generate_diagram_response() | Complete | 2025-08-22 | Simple delegation to DiagramAgent |
| 1.4 | Remove mermaid-specific methods | Complete | 2025-08-22 | Moved to DiagramAgent (already had capabilities) |
| 1.5 | Move repository info logic | Complete | 2025-08-22 | Fixed variable scoping bug |
| 1.6 | Add DiagramAgent.can_handle_request() | Complete | 2025-08-22 | Better routing decision support implemented |
| 1.7 | Test simplified routing | In Progress | 2025-08-22 | Syntax validated, integration testing needed |

## Progress Log
### 2025-08-22
- **MAJOR PROGRESS**: Completed 85% of simplification
- **Code Reduction**: AgentRouter reduced from 359 to 199 lines (45% reduction)
- **Removed Duplication**: 
  - `_compile_diagram_patterns()` - 20+ regex patterns removed
  - `_is_diagram_request()` - 50+ lines of complex detection logic simplified to 10 lines
  - `_generate_diagram_response()` - 30+ lines replaced with simple delegation
  - `_is_mermaid_specific_request()` and `_enhance_mermaid_response()` - removed entirely
- **Enhanced DiagramAgent**: Added `can_handle_request()` method for intelligent routing
- **Fixed Bug**: Resolved variable scoping issue in repository info generation
- **Architecture Improvement**: Clear separation of concerns - Router routes, DiagramAgent processes
- **Next**: Integration testing to ensure all functionality preserved
