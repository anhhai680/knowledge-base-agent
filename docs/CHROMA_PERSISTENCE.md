# Chroma Data Persistence Configuration

This document outlines the configuration changes made to fix the Chroma data loss issue.

## Problem Analysis

The original configuration had several issues:
1. **Volume mapping mismatch**: Chroma service used named volumes while the application used bind mounts
2. **Inconsistent storage paths**: Different services stored data in different locations
3. **Named volume limitations**: Docker named volumes don't persist across `docker-compose down`

## Solution Implemented

### 1. Docker Compose Changes

**Before:**
```yaml
chroma:
  volumes:
    - chroma_data:/chroma/chroma  # Named volume - gets recreated
    
knowledge-base-agent:
  volumes:
    - ./chroma_db:/app/chroma_db  # Bind mount - different location

volumes:
  chroma_data:  # Named volume declaration
```

**After:**
```yaml
chroma:
  volumes:
    - ./chroma_db:/chroma/chroma        # Same directory as application

knowledge-base-agent:
  volumes:
    - ./chroma_db:/app/chroma_db        # Same directory as Chroma service

# Removed all named volumes for chroma
```

### 2. Key Benefits

1. **Unified Storage**: Both HTTP service and persistent client use the same directory
2. **True Persistence**: Bind mounts ensure data survives all container operations
3. **Seamless Fallback**: When HTTP client fails, persistent client accesses same data
4. **Consistent State**: No data synchronization issues between storage methods

### 3. Directory Structure

```
project-root/
├── chroma_db/       # Unified Chroma database storage
└── logs/           # Application logs
```

### 4. Usage Instructions

1. **Setup**: Run `./setup_chroma_persistence.sh` to create proper directory structure
2. **Start**: Use `docker-compose up -d` to start services
3. **Data persists**: Data will survive container restarts, rebuilds, and `docker-compose down`
4. **Clean up**: Use `docker-compose down -v` followed by manual directory cleanup if needed

### 5. Application Configuration

The application now uses:
- **Primary**: HTTP client connecting to Chroma service (`chroma:8000`)
- **Fallback**: Persistent client using local storage (`./chroma_db`)
- **Shared persistence**: Both mechanisms can access the same data

### 6. Verification

To verify data persistence:
1. Add some documents to the knowledge base
2. Run `docker-compose down`
3. Run `docker-compose up -d`
4. Check that documents are still available

## Troubleshooting

- **Permission issues**: Run `sudo chown -R $USER:$USER ./chroma_data ./chroma_db` if needed
- **Data corruption**: Delete contents of both directories and restart
- **Connection issues**: Check that Chroma service is running on port 8001
