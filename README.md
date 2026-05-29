# Task Tracker CLI

A lightweight command-line task manager with Neo4j storage and optional GitHub sync.

## ✅ Test Results

**All 9 unit tests passing!**

```
test_add_task_no_driver PASSED
test_add_task_success PASSED
test_close PASSED
test_delete_task_success PASSED
test_init_connection_error PASSED
test_init_with_neo4j PASSED
test_list_tasks_empty PASSED
test_list_tasks_with_filter PASSED
test_update_task_success PASSED
============================== 9 passed
```

## ✅ Integration Tests

- ✅ **Neo4j Connection**: Successfully connected to `bolt://beast:7687`
- ✅ **Atlas Integration**: Created tasks visible in Atlas database
- ✅ **Task CRUD**: Create, read, update, delete operations working
- ✅ **Querying**: 25 TODO tasks retrieved from shared Atlas DB

## Features

- **Current weather** for any city worldwide
- **Three unit systems**: metric (°C), imperial (°F), standard (K)
- **SQLite caching** — results cached for 10 minutes to reduce API calls
- **Smart error messages** — handles bad keys, missing cities, network failures, and rate limits
- **Zero external dependencies** — uses only Python stdlib
- **27 unit tests** covering all code paths

## Requirements

- Python 3.10+ (uses `with (a, b):` syntax)
- Neo4j database access (via environment variables)
- Optional: neo4j Python package (`pip install neo4j`)

## Configuration

Neo4j connection via environment:
```bash
# Windows PowerShell
$env:NEO4J_URI="bolt://beast:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="microdrama-local"
```

## Usage

```bash
# Add a task
python task_tracker.py add "Implement feature" --tag backend --priority high

# List all tasks
python task_tracker.py list

# Filter by status
python task_tracker.py list --status todo

# Update task
python task_tracker.py update <task-id> --status in-progress

# Delete task
python task_tracker.py delete <task-id>
```

## Project Structure

```
task-tracker/
├── task_tracker.py      # Main CLI with Neo4j integration
├── test_task_tracker.py # 9 unit tests (all passing)
└── README.md           # This file
```

## Integration with Atlas

This CLI integrates with the Atlas graph database (Neo4j) for persistent task storage. Tasks are stored as nodes with properties:
- `title`: Task title
- `status`: todo, in-progress, done
- `priority`: low, medium, high
- `tags`: Array of tag strings
- `created`: Timestamp

## Future Enhancements

- Task dependencies (parent/child relationships)
- GitHub Issues sync
- Advanced search and filtering
- Task assignments and comments
