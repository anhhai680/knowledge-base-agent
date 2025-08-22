# [TASK041] - API Layer Simplification

**Status:** Pending  
**Added:** August 22, 2025  
**Updated:** August 22, 2025

## Original Request
Phase 2, Step 2.3 of the Agents Refactoring Implementation Plan: Reduce routes.py complexity and implement service layer to separate business logic from API routing.

## Thought Process
This task addresses the API layer complexity:

**Current Issue:**
- `routes.py` is 817 lines with mixed concerns (routing + business logic)
- No separation between API routing and business logic
- Difficult to test and maintain

**New Architecture:**
- Separate routes/ directory with focused endpoint files
- Service layer for business logic separation
- Middleware for cross-cutting concerns (CORS, auth, logging)
- Dependency injection for better testing
- Each route file focused on specific domain (health, query, repository, config, diagram)

Target: Reduce routes.py from 817 to ~400 total lines across multiple focused files.

## Implementation Plan
1. Create new API structure with routes/, services/, middleware/, dependencies/
2. Break down routes.py into domain-specific route files
3. Implement service layer for business logic
4. Add middleware for common functionality
5. Implement dependency injection system

## Progress Tracking

**Overall Status:** Not Started - 0%

### Subtasks
| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 6.1 | Create new src/api/ structure | Not Started | 2025-08-22 | routes/, services/, middleware/, dependencies/ |
| 6.2 | Create health routes (50 lines) | Not Started | 2025-08-22 | Health check endpoints |
| 6.3 | Create query routes (100 lines) | Not Started | 2025-08-22 | Query processing endpoints |
| 6.4 | Create repository routes (100 lines) | Not Started | 2025-08-22 | Repository management endpoints |
| 6.5 | Create config routes (80 lines) | Not Started | 2025-08-22 | Configuration endpoints |
| 6.6 | Create diagram routes (70 lines) | Not Started | 2025-08-22 | Diagram-specific endpoints |
| 6.7 | Implement query service | Not Started | 2025-08-22 | Query processing business logic |
| 6.8 | Implement repository service | Not Started | 2025-08-22 | Repository management logic |
| 6.9 | Create middleware components | Not Started | 2025-08-22 | CORS, auth, rate limiting, logging |
| 6.10 | Implement dependency injection | Not Started | 2025-08-22 | Agent, config, database dependencies |
| 6.11 | Test API layer integration | Not Started | 2025-08-22 | Validate service layer functionality |

## Progress Log
### 2025-08-22
- Task created as part of comprehensive agents refactoring implementation plan
- Designed service layer architecture for business logic separation
- Planned focused route files for better maintainability
- Established middleware and dependency injection patterns
