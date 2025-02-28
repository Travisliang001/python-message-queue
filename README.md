# Multithreaded Flask Application

A multithreaded Flask application with a producer-consumer architecture, featuring:
- 1 producer thread for task generation
- 5 consumer worker threads for task processing
- 1 monitor thread that restarts inactive threads

## Architecture

```
┌─────────────┐     ┌───────────┐     ┌─────────────┐
│   Producer  │────▶│  Task     │────▶│  Consumers  │
│   Thread    │     │  Queue    │     │  (5 threads)│
└─────────────┘     └───────────┘     └─────────────┘
                          △
                          │
                          │
                          ▼
                    ┌─────────────┐
                    │   Monitor   │
                    │   Thread    │
                    └─────────────┘
```

## Features

- **Task Producer**: Generates simulated tasks and puts them in the queue
- **Task Consumers**: Process tasks from the queue (5 worker threads)
- **Thread Monitor**: Tracks thread activity and restarts inactive threads
- **Flask API Endpoints**: For task submission, status monitoring, and management
- **Unit & Integration Tests**: Comprehensive test coverage

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Running the Application

Basic run:
```
python run.py
```

Run with options:
```
python run.py --debug --demo --host 127.0.0.1 --port 8000
```

Options:
- `--debug`: Enable Flask debug mode
- `--demo`: Run in demo mode with auto-generated tasks
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to run on (default: 5000)
- `--config`: Config class to use (default: app.config.DevelopmentConfig)

### API Endpoints

- `GET /status`: Get API status
- `GET /tasks`: Get queue status
- `POST /tasks`: Add a task to the queue
- `GET /thread-status`: Get status of all threads

## Running Tests

Run all tests:
```
pytest
```

With coverage:
```
pytest --cov=app tests/
```

## Project Structure

```
project/
├── app/
│   ├── __init__.py          # App initialization and shared variables
│   ├── config.py            # Configuration settings
│   ├── routes.py            # API routes
│   ├── models/              # Data models
│   ├── producer/            # Task producer implementation
│   ├── consumer/            # Task consumer implementation
│   └── monitor/             # Thread monitor implementation
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── run.py                   # Application entry point
└── requirements.txt         # Project dependencies
```

## Adding New Tasks

To add a task via the API:

```bash
curl -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_data": {"type": "calculation", "input_value": 42}, "priority": 8}'
```

## Monitoring

Check the application status:
```bash
curl http://localhost:5000/status
```

Check thread status:
```bash
curl http://localhost:5000/thread-status
```

## Extending the Application

### Creating Custom Task Types

Modify the `task_consumer.py` file to handle custom task types:

```python
def process_task(self, task: Task) -> Task:
    # Extract task type
    task_type = task.data.get("type", "default")
    
    # Handle different task types
    if task_type == "calculation":
        # Process calculation task
        result = self._process_calculation(task)
    elif task_type == "validation":
        # Process validation task
        result = self._process_validation(task)
    else:
        # Default processing
        result = self._process_default(task)
    
    return task.mark_completed(result)
```

### Adding Persistent Storage

For persistent storage of tasks and results, integrate a database (e.g., SQLite, PostgreSQL) in the `models` module.
