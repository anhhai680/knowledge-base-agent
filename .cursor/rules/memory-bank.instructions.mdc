---
alwaysApply: true
---
# Cursor Agent Instructions

## Overview

This file contains the complete set of rules, workflows, and patterns that the Cursor agent must follow to ensure 100% compatibility with GitHub Copilot. These instructions enable developers to seamlessly switch between VS Code (with GitHub Copilot) and Cursor IDE without any workflow disruption or code inconsistency.

## Core Principles

### 1. GitHub Copilot Parity
- **Exact Match**: All workflows, code patterns, and behaviors must match GitHub Copilot exactly
- **No Deviation**: Never introduce patterns that would break GitHub Copilot compatibility
- **Seamless Switching**: Developers must be able to switch between IDEs without any code changes

### 2. Memory Bank Integration
- **Full Compliance**: Follow all memory bank instructions and workflows exactly
- **Context Preservation**: Maintain complete project context across IDE switches
- **Documentation Sync**: Keep all documentation consistent between development environments

### 3. Project Intelligence
- **Pattern Recognition**: Identify and document project-specific patterns and preferences
- **Learning Integration**: Capture insights that improve development efficiency
- **Knowledge Sharing**: Ensure all team members benefit from discovered patterns

## Memory Bank Workflows

### Plan Mode Workflow
```mermaid
flowchart TD
    Start[Start] --> ReadFiles[Read Memory Bank]
    ReadFiles --> CheckFiles{Files Complete?}
    
    CheckFiles -->|No| Plan[Create Plan]
    Plan --> Document[Document in Chat]
    
    CheckFiles -->|Yes| Verify[Verify Context]
    Verify --> Strategy[Develop Strategy]
    Strategy --> Present[Present Approach]
```

**Implementation Rules:**
1. **Always start by reading ALL memory bank files** - this is mandatory, not optional
2. **Verify file completeness** before proceeding with any task
3. **Create comprehensive plans** when memory bank is incomplete
4. **Document all decisions** in the memory bank for future reference

### Act Mode Workflow
```mermaid
flowchart TD
    Start[Start] --> Context[Check Memory Bank]
    Context --> Update[Update Documentation]
    Update --> Rules[Update instructions if needed]
    Rules --> Execute[Execute Task]
    Execute --> Document[Document Changes]
```

**Implementation Rules:**
1. **Check memory bank context** before executing any task
2. **Update documentation** as work progresses
3. **Modify instructions** when new patterns are discovered
4. **Document all changes** with timestamps and reasoning

### Task Management Workflow
```mermaid
flowchart TD
    Start[New Task] --> NewFile[Create Task File in tasks/ folder]
    NewFile --> Think[Document Thought Process]
    Think --> Plan[Create Implementation Plan]
    Plan --> Index[Update task-list.md]
    
    Execute[Execute Task] --> Update[Add Progress Log Entry]
    Update --> StatusChange[Update Task Status]
    StatusChange --> IndexUpdate[Update task-list.md]
    IndexUpdate --> Complete{Completed?}
    Complete -->|Yes| Archive[Mark as Completed]
    Complete -->|No| Execute
```

**Implementation Rules:**
1. **Create dedicated task files** for each new task
2. **Document complete thought process** including reasoning and alternatives
3. **Maintain task index** with current status and completion percentages
4. **Update progress logs** with every significant change

## Code Standards and Patterns

### 1. Repository-Neutral Naming
**Rule**: Never hardcode repository names in code or function names
**Rationale**: Repository names can change, making code brittle
**Implementation**:
```python
# ✅ CORRECT - Repository-neutral naming
def process_github_repository(repo_url: str):
    pass

def create_agent_router():
    pass

# ❌ INCORRECT - Repository-specific naming
def process_knowledge_base_repository(repo_url: str):
    pass

def create_knowledge_base_agent_router():
    pass
```

### 2. AI Model Integration Compliance
**Rule**: Follow company policy for AI model connections
**Rule**: Only connect to AI models using approved project integrations and guidelines
**Rationale**: Direct connections to AI models should be avoided unless explicitly approved by project maintainers or documented in project guidelines
**Implementation**:
- **Use GitHub Copilot agent** for all AI-assisted development
- **No direct API calls** to external AI models
- **Leverage existing integrations** that have been approved
- **Document all AI usage** in memory bank for compliance tracking

### 3. Code Structure Patterns
**Rule**: Follow established project architecture patterns exactly
**Implementation**:
```python
# Factory Pattern for LLM abstraction
class LLMFactory:
    @staticmethod
    def create_llm(provider: str, model: str, **kwargs) -> BaseLLM:
        # Implementation must match existing patterns exactly
        pass

# Agent Router Pattern for dual-mode responses
class AgentRouter:
    def route_query(self, question: str) -> Dict[str, Any]:
        # Must match existing implementation exactly
        pass
```

### 4. Error Handling Patterns
**Rule**: Use consistent error handling patterns across all components
**Implementation**:
```python
# Standard error handling pattern
try:
    result = self._process_request(request)
    return {"status": "success", "data": result}
except ValidationError as e:
    logger.warning(f"Validation error: {e}")
    return {"status": "error", "message": str(e), "type": "validation"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"status": "error", "message": "Internal server error", "type": "internal"}
```

## Development Workflow Rules

### 1. Memory Bank First Approach
**Rule**: Always consult memory bank before making any changes
**Workflow**:
1. **Read projectbrief.md** to understand project scope
2. **Check activeContext.md** for current work focus
3. **Review systemPatterns.md** for architectural decisions
4. **Consult techContext.md** for technical constraints
5. **Check progress.md** for current status
6. **Review relevant task files** for specific context

### 2. Documentation-Driven Development
**Rule**: Update documentation before, during, and after code changes
**Workflow**:
1. **Document planned changes** in relevant memory bank files
2. **Update progress logs** as work progresses
3. **Record decisions and reasoning** for future reference
4. **Update task status** when milestones are reached
5. **Validate documentation accuracy** after implementation

### 3. Pattern Discovery and Documentation
**Rule**: Actively identify and document new patterns
**Workflow**:
1. **Recognize recurring patterns** during development
2. **Validate patterns** with user/team
3. **Document in systemPatterns.md** with examples
4. **Update instructions** to reflect new patterns
5. **Share insights** with team through memory bank

### 4. Testing and Validation
**Rule**: Ensure all changes maintain GitHub Copilot compatibility
**Workflow**:
1. **Test code patterns** in both VS Code and Cursor
2. **Validate memory bank** consistency across environments
3. **Verify documentation** accuracy and completeness
4. **Check for pattern conflicts** between IDEs
5. **Update instructions** if compatibility issues are found

## IDE-Specific Considerations

### 1. Cursor IDE Features
**Rule**: Leverage Cursor-specific features while maintaining compatibility
**Implementation**:
- **Use Cursor's AI capabilities** for code generation and review
- **Maintain GitHub Copilot patterns** for cross-IDE compatibility
- **Leverage Cursor's context awareness** for better suggestions
- **Use Cursor's file management** for memory bank organization

### 2. VS Code Compatibility
**Rule**: Ensure all patterns work identically in VS Code
**Implementation**:
- **Test all workflows** in VS Code environment
- **Validate memory bank** accessibility in VS Code
- **Check file path handling** for cross-platform compatibility
- **Verify documentation** rendering in VS Code

### 3. Cross-IDE Synchronization
**Rule**: Maintain perfect synchronization between development environments
**Implementation**:
- **Use Git-based synchronization** for all project files
- **Avoid IDE-specific configurations** in shared files
- **Maintain consistent file structure** across environments
- **Use relative paths** for all file references

## Memory Bank Maintenance Rules

### 1. File Update Triggers
**Rule**: Update memory bank files in specific situations
**Triggers**:
1. **After implementing significant changes** - Update relevant files immediately
2. **When discovering new patterns** - Document in systemPatterns.md
3. **When user requests "update memory bank"** - Review ALL files comprehensively
4. **When context needs clarification** - Update activeContext.md
5. **When tasks are completed** - Update progress.md and task files

### 2. Update Process Requirements
**Rule**: Follow comprehensive update process for memory bank maintenance
**Process**:
1. **Review ALL files** - No exceptions, even if some don't need updates
2. **Focus on active files** - activeContext.md, progress.md, tasks/ folder
3. **Update task-list.md** - Ensure current status accuracy
4. **Validate consistency** - Check for contradictions between files
5. **Update instructions** - Reflect any new patterns or preferences

### 3. Quality Standards
**Rule**: Maintain high quality standards for all memory bank content
**Standards**:
- **Accuracy**: All information must be current and correct
- **Completeness**: Cover all aspects of the project comprehensively
- **Clarity**: Use clear, unambiguous language
- **Consistency**: Maintain consistent formatting and structure
- **Timeliness**: Update files immediately when changes occur

## Task Management Rules

### 1. Task Creation
**Rule**: Create comprehensive task files for all new work
**Requirements**:
- **Unique Task ID** following TASK001, TASK002 pattern
- **Complete task description** with original request
- **Thought process documentation** including reasoning
- **Implementation plan** with clear steps
- **Progress tracking structure** with subtasks and status

### 2. Task Updates
**Rule**: Update tasks continuously as work progresses
**Requirements**:
- **Progress log entries** for every significant change
- **Subtask status updates** with current dates
- **Overall status updates** with completion percentages
- **Task-list.md synchronization** for status consistency

### 3. Task Commands
**Rule**: Support standard task management commands
**Commands**:
- **add task** or **create task** - Create new task with full documentation
- **update task [ID]** - Update specific task with progress and status
- **show tasks [filter]** - Display filtered task list with current status

## Compliance Verification

### 1. GitHub Copilot Compatibility Check
**Rule**: Verify all patterns work identically in GitHub Copilot
**Checklist**:
- [ ] Code generation patterns match exactly
- [ ] Memory bank access works identically
- [ ] Task management workflows are identical
- [ ] Documentation rendering is consistent
- [ ] Error handling patterns match exactly

### 2. Memory Bank Compliance Check
**Rule**: Verify complete compliance with memory bank instructions
**Checklist**:
- [ ] All required files are present and complete
- [ ] File hierarchy and relationships are correct
- [ ] Update triggers are properly implemented
- [ ] Task management follows established patterns
- [ ] Documentation quality meets established standards

### 3. Cross-IDE Compatibility Check
**Rule**: Verify seamless switching between VS Code and Cursor
**Checklist**:
- [ ] All workflows function identically
- [ ] File paths and references work correctly
- [ ] Memory bank accessibility is consistent
- [ ] Task management works seamlessly
- [ ] No IDE-specific dependencies exist

## Error Prevention Rules

### 1. Memory Reset Protection
**Rule**: Protect against memory reset issues
**Implementation**:
- **Never assume knowledge** from previous sessions
- **Always read memory bank** at session start
- **Document all decisions** immediately
- **Update progress continuously** during work
- **Validate context** before proceeding

### 2. Pattern Consistency Protection
**Rule**: Prevent pattern drift between development sessions
**Implementation**:
- **Follow established patterns** exactly
- **Document any deviations** with justification
- **Validate patterns** against memory bank
- **Update instructions** when patterns evolve
- **Maintain backward compatibility** for all changes

### 3. Documentation Drift Protection
**Rule**: Prevent documentation from becoming outdated
**Implementation**:
- **Update documentation** before code changes
- **Validate documentation** after implementation
- **Check for contradictions** between files
- **Maintain version consistency** across all files
- **Archive outdated information** appropriately

## Performance and Efficiency Rules

### 1. Memory Bank Access Optimization
**Rule**: Optimize memory bank access for efficiency
**Implementation**:
- **Read files once** at session start
- **Cache relevant information** in active context
- **Update files efficiently** with minimal overhead
- **Use structured queries** for specific information
- **Maintain file organization** for quick access

### 2. Task Management Efficiency
**Rule**: Optimize task management for productivity
**Implementation**:
- **Use consistent task structure** for quick scanning
- **Maintain current status** for immediate visibility
- **Update progress efficiently** with structured logs
- **Use task indexing** for quick status overview
- **Automate routine updates** where possible

### 3. Pattern Recognition Efficiency
**Rule**: Optimize pattern recognition and documentation
**Implementation**:
- **Identify patterns early** in development process
- **Document patterns immediately** when discovered
- **Use consistent documentation** format for quick reference
- **Maintain pattern relationships** for better understanding
- **Update instructions** efficiently when patterns evolve

## Conclusion

These instructions ensure that the Cursor agent maintains 100% compatibility with GitHub Copilot while following all memory bank workflows and rules. The key is maintaining consistency across development environments and ensuring that developers can seamlessly switch between VS Code and Cursor IDE without any workflow disruption.

**Remember**: After every memory reset, the agent begins completely fresh. The Memory Bank is the only link to previous work and must be maintained with precision and clarity. Effectiveness depends entirely on the accuracy and completeness of the memory bank documentation.
