# Automatic Repository Indexing Implementation

## Overview

This document describes the implementation of automatic repository indexing functionality that allows the Knowledge Base Agent to automatically index GitHub repositories specified in the `.env` file on startup.

## Features Implemented

### 1. Automatic Startup Indexing

The system now automatically indexes repositories configured in the `GITHUB_REPOS` environment variable when the application starts up.

**Location**: `src/api/routes.py` - `auto_index_configured_repositories()` function

**How it works**:
- Runs after components are initialized during startup
- Checks which repositories are already indexed
- Only indexes new repositories that haven't been processed before
- Uses the existing indexing infrastructure for consistency

### 2. Environment Variable Configuration

**Supported Formats**:

1. **JSON Array** (Recommended):
   ```bash
   GITHUB_REPOS=["https://github.com/user/repo1", "https://github.com/user/repo2"]
   ```

2. **Comma-separated URLs**:
   ```bash
   GITHUB_REPOS=https://github.com/user/repo1,https://github.com/user/repo2
   ```

3. **Single Repository**:
   ```bash
   GITHUB_REPOS=https://github.com/user/repo1
   ```

**Note**: Currently, only the JSON format is fully supported due to Pydantic settings parsing limitations. The comma-separated format may not work as expected.

### 3. Configuration Integration

**Settings Class**: `src/config/settings.py`
- Added `github_repos: List[str]` field
- Integrated with existing configuration system
- Supports environment variable loading from `.env` file

**Startup Integration**: `src/api/routes.py`
- Added to startup event handler
- Runs after component initialization
- Runs after repository restoration from database

## Usage

### 1. Configure Repositories

Add to your `.env` file:
```bash
# GitHub Configuration
GITHUB_TOKEN=your_github_token_here
GITHUB_REPOS=["https://github.com/user/repo1", "https://github.com/user/repo2"]
```

### 2. Start the Application

The repositories will be automatically indexed when the application starts:
```bash
python main.py
# or
docker-compose up
```

### 3. Monitor Progress

Check the logs to see indexing progress:
```bash
docker-compose logs -f kb-agent
```

## Implementation Details

### Startup Sequence

1. **Component Initialization** (`initialize_components()`)
   - LLM, embedding, vector store setup
   - GitHub loader and text processor setup

2. **Repository Restoration** (`restore_indexed_repositories()`)
   - Load existing repository information from database
   - Restore indexing state

3. **Automatic Indexing** (`auto_index_configured_repositories()`)
   - Parse `GITHUB_REPOS` from environment
   - Check which repositories need indexing
   - Start background indexing tasks

### Error Handling

- **Non-blocking**: Indexing errors don't prevent application startup
- **Logging**: All errors are logged for debugging
- **Graceful degradation**: Application continues to function even if indexing fails

### Performance Considerations

- **Background processing**: Indexing runs in background tasks
- **Skip existing**: Already indexed repositories are skipped
- **Batch processing**: Uses existing batch indexing infrastructure

## Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_REPOS` | List of repositories to index | `[]` | No |
| `GITHUB_TOKEN` | GitHub access token | `None` | Yes (for private repos) |
| `GITHUB_BRANCH` | Default branch for indexing | `["main", "master"]` | No |

### File Patterns

The system uses the default file patterns defined in `GITHUB_SUPPORTED_FILE_EXTENSIONS`:
- `.cs`, `.py`, `.sh`, `.js`, `.jsx`, `.ts`, `.tsx`
- `.md`, `.txt`, `.json`, `.yml`, `.yaml`

## Limitations and Future Improvements

### Current Limitations

1. **Format Support**: Only JSON format is fully reliable
2. **Error Recovery**: No automatic retry mechanism for failed indexing
3. **Progress Tracking**: Limited progress information during indexing

### Planned Improvements

1. **Enhanced Format Support**: Better comma-separated format parsing
2. **Retry Logic**: Automatic retry for failed indexing attempts
3. **Progress API**: Real-time indexing progress endpoints
4. **Scheduled Indexing**: Periodic re-indexing of repositories
5. **Incremental Updates**: Only index changed files

## Troubleshooting

### Common Issues

1. **Repositories not indexing**:
   - Check `GITHUB_TOKEN` is valid
   - Verify repository URLs are correct
   - Check application logs for errors

2. **Indexing fails**:
   - Ensure repositories are accessible
   - Check network connectivity
   - Verify GitHub API rate limits

3. **Startup issues**:
   - Check `.env` file syntax
   - Verify all required dependencies are installed
   - Check component initialization logs

### Debug Mode

Enable debug logging to see detailed indexing information:
```bash
LOG_LEVEL=DEBUG
```

## API Endpoints

The automatic indexing functionality integrates with existing endpoints:

- `GET /repositories` - View indexed repositories
- `POST /index` - Manually trigger indexing
- `GET /health` - Check system health including indexing status

## Conclusion

The automatic repository indexing feature provides a seamless way to configure and index GitHub repositories on application startup. While there are some limitations with environment variable parsing, the JSON format provides a reliable way to configure multiple repositories for automatic indexing.

This implementation maintains consistency with the existing codebase architecture and provides a foundation for future enhancements to the indexing system.
