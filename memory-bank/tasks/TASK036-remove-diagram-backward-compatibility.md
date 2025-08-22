# [TASK036] - Remove Diagram Backward Compatibility

**Status:** Pending  
**Added:** August 22, 2025  
**Updated:** August 22, 2025

## Original Request
Phase 1, Step 1.1 of the Agents Refactoring Implementation Plan: Remove diagram backward compatibility to establish foundation for refactoring by eliminating legacy code.

## Thought Process
This is the first step in a comprehensive 4-phase refactoring plan to reduce codebase complexity from ~18,852 lines to 13,000-14,000 lines (25-30% reduction). Removing diagram backward compatibility will:

1. **Eliminate Complex Legacy Code**: Remove `src/processors/diagram_handler.py` (964 lines) entirely
2. **Simplify Agent Router**: Reduce `src/agents/agent_router.py` from 515 to ~350 lines
3. **Clean API Layer**: Reduce `src/api/routes.py` from 817 to ~700 lines  
4. **Preserve RAG Features**: Maintain Chain-of-Thought, ReAct, and query optimization capabilities
5. **Add Performance Optimization**: Implement caching for routing patterns

The target is to remove ~1,100+ lines while preserving all advanced RAG functionality and maintaining <2s response times.

## Implementation Plan
1. Remove `src/processors/diagram_handler.py` completely
2. Simplify `AgentRouter` constructor and remove diagram_handler dependency
3. Update API routes to remove diagram_handler references
4. Add caching for routing patterns
5. Validate RAG features are preserved
6. Test performance benchmarks

## Progress Tracking

**Overall Status:** Not Started - 0%

### Subtasks
| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 1.1 | Remove diagram_handler.py file | Not Started | 2025-08-22 | 964 lines to be removed |
| 1.2 | Simplify AgentRouter constructor | Not Started | 2025-08-22 | Remove diagram_handler parameter |
| 1.3 | Update agent_router.py logic | Not Started | 2025-08-22 | Reduce from 515 to ~350 lines |
| 1.4 | Update API routes.py | Not Started | 2025-08-22 | Remove diagram_handler imports and usage |
| 1.5 | Add routing cache implementation | Not Started | 2025-08-22 | Performance optimization |
| 1.6 | Validate RAG feature preservation | Not Started | 2025-08-22 | Chain-of-Thought, ReAct, query optimization |
| 1.7 | Test performance benchmarks | Not Started | 2025-08-22 | Ensure <2s response times maintained |

## Progress Log
### 2025-08-22
- Task created as part of comprehensive agents refactoring implementation plan
- Identified target files and expected line reductions
- Established success criteria for RAG feature preservation and performance
