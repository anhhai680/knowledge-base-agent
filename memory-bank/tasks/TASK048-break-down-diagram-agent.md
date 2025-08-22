# TASK048: Break Down DiagramAgent - Massive Code Reduction

**Status:** Pending
**Added:** August 22, 2025
**Updated:** August 22, 2025

## Original Request
Break down the massive DiagramAgent (1,160 lines) into smaller, focused components following Single Responsibility Principle. The current DiagramAgent violates our refactoring goals by being even larger than the original files we're trying to reduce.

## Problem Analysis
The DiagramAgent has grown to 1,160 lines because it's trying to handle:
1. **Code Retrieval** (~400 lines) - Should be in retrieval layer
2. **Document Processing** (~200 lines) - Should be in processors module  
3. **Diagram Generation** (~300 lines) - Should be in diagram generators
4. **Utilities** (~200 lines) - Should be in utils or shared modules

## Target Architecture

### New Structure (Target: 200-300 lines per file):
```
src/agents/
├── diagram_agent.py (200 lines) - Main orchestration only
├── retrieval/
│   ├── enhanced_code_retriever.py (300 lines) - All search logic
│   └── repository_filter.py (150 lines) - Repository filtering
├── diagram/
│   ├── diagram_type_detector.py (200 lines) - Type detection logic
│   ├── pattern_extractor.py (250 lines) - Pattern extraction 
│   └── mermaid_generator.py (300 lines) - Mermaid generation
└── processors/
    ├── document_processor.py (200 lines) - Document filtering/ranking
    └── result_formatter.py (150 lines) - Response formatting
```

## Implementation Plan

### Phase 1: Extract Code Retrieval Logic (Target: -400 lines)
1. **Create `src/agents/retrieval/enhanced_code_retriever.py`**
   - Move `_enhanced_code_retrieval()` and all search methods
   - Move `_multi_strategy_search()`, `_strict_repository_search()`
   - Move `_search_repository_with_context()`, etc.

2. **Create `src/agents/retrieval/repository_filter.py`**
   - Move repository filtering logic
   - Move `_lenient_repository_filtering()`

### Phase 2: Extract Document Processing (Target: -200 lines)
1. **Create `src/processors/document_processor.py`**
   - Move `_filter_code_documents()`, `_deduplicate_and_rank_results()`
   - Move `_enhanced_result_processing()`

2. **Create `src/processors/result_formatter.py`**
   - Move `_format_response()`, `_format_source_docs()`
   - Move `_create_no_results_response()`, `_create_error_response()`

### Phase 3: Extract Diagram Logic (Target: -400 lines)
1. **Create `src/diagram/diagram_type_detector.py`**
   - Move `_enhanced_diagram_type_detection()`, `_suggest_diagram_type_from_code()`
   - Move `_simple_pattern_heuristic()`

2. **Enhance existing `src/utils/diagram_generators.py`**
   - Move all `_generate_*_diagram()` methods
   - Move all `_create_*_mermaid()` methods

### Phase 4: Simplify DiagramAgent (Target: 200 lines)
1. **Keep only orchestration logic**:
   - `process_query()` - main entry point
   - `can_handle_request()` - routing support
   - Initialization and dependency injection

## Target Code Reduction
- **DiagramAgent**: From 1,160 lines to ~200 lines (83% reduction)
- **Total New Files**: ~1,500 lines across 6 specialized files
- **Net Result**: Better organization, maintainability, and testability
- **Avg File Size**: ~200-300 lines (ideal for maintenance)

## Benefits
1. **Single Responsibility**: Each file has one clear purpose
2. **Testability**: Easier to unit test individual components
3. **Maintainability**: Changes affect only relevant files
4. **Reusability**: Components can be reused by other agents
5. **Performance**: Easier to optimize individual components

## Progress Tracking

**Overall Status:** Not Started - 0%

### Subtasks
| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 1.1 | Create enhanced_code_retriever.py | Not Started | 2025-08-22 | Extract all search logic |
| 1.2 | Create repository_filter.py | Not Started | 2025-08-22 | Extract repository filtering |
| 1.3 | Create document_processor.py | Not Started | 2025-08-22 | Extract document filtering/ranking |
| 1.4 | Create result_formatter.py | Not Started | 2025-08-22 | Extract response formatting |
| 1.5 | Create diagram_type_detector.py | Not Started | 2025-08-22 | Extract type detection logic |
| 1.6 | Enhance diagram_generators.py | Not Started | 2025-08-22 | Move diagram generation logic |
| 1.7 | Simplify DiagramAgent | Not Started | 2025-08-22 | Keep only orchestration logic |
| 1.8 | Update imports and tests | Not Started | 2025-08-22 | Ensure everything works |

## Progress Log

### 2025-01-27
- **Phase 1 COMPLETED**: Code retrieval extraction ✅
- Created new `src/retrieval/` module with `EnhancedCodeRetriever` (577 lines)
- Successfully extracted all code retrieval logic from DiagramAgent
- Updated DiagramAgent to use injected `EnhancedCodeRetriever` instance
- Fixed method references and removed duplicate/orphaned code
- DiagramAgent reduced from **1,160 lines to 752 lines** (35.2% reduction)
- All tests passing, imports working correctly
- **Status**: Ready for Phase 2 (Document Processing extraction)

**Current Progress**: 35.2% complete towards 83% target reduction
### 2025-08-22
- Task created to address massive DiagramAgent size (1,160 lines)
- Identified clear separation of concerns for 83% reduction
- Planned modular architecture with 6 specialized components
