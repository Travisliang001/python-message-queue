import pytest
import time
import json
import threading
import queue
from flask import Flask
from app import create_app, task_queue, shutdown_event
from app.producer.task_producer import TaskProducer
from app.consumer.task_consumer import TaskConsumer
from app.monitor.thread_monitor import ThreadMonitor
from app.models.task import Task

@pytest.fixture
def app():
    """Flask app test fixture."""
    # Use the testing configuration
    app = create_app('app.config.TestingConfig')
    
    # Add the test client
    with app.test_client() as client:
        # Set up the app context
        with app.app_context():
            yield client
    
    # Clean up
    shutdown_event.set()

@pytest.fixture
def setup_threads():
    """Set up the thread infrastructure for testing."""
    # Clear any existing tasks
    while not task_queue.empty():
        try:
            task_queue.get_nowait()
        except queue.Empty:
            break
    
    # Reset shutdown event
    shutdown_event.clear()
    
    # Start producer thread
    producer = TaskProducer(task_queue, shutdown_event, interval=0.5, demo_mode=True)
    producer.start()
    
    # Start consumer threads
    consumers = []
    for i in range(2):  # Use fewer consumers for testing
        consumer = TaskConsumer(task_queue, i+1, shutdown_event, processing_time=(0.1, 0.3))
        consumer.start()
        consumers.append(consumer)
    
    # Start monitor thread
    monitor = ThreadMonitor([producer] + consumers, shutdown_event, check_interval=1, inactivity_threshold=10)
    monitor.start()
    
    # Return the threads
    threads = {"producer": producer, "consumers": consumers, "monitor": monitor}
    yield threads
    
    # Clean up
    shutdown_event.set()
    time.sleep(0.5)

class TestAppIntegration:
    
    def test_status_endpoint(self, app):
        """Test the /status endpoint."""
        response = app.get('/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'running'
        assert 'queue_size' in data
        assert 'timestamp' in data
    
    def test_add_task_endpoint(self, app):
        """Test the /tasks POST endpoint."""
        task_data = {
            "task_data": {"type": "test", "value": 42},
            "priority": 8
        }
        response = app.post('/tasks', json=task_data)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'success'
        assert 'task_id' in data
    
    def test_get_tasks_status_endpoint(self, app):
        """Test the /tasks GET endpoint."""
        response = app.get('/tasks')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'queue_size' in data
        assert 'queue_full' in data
        assert 'queue_empty' in data
    
    def test_thread_status_endpoint(self, app, setup_threads):
        """Test the /thread-status endpoint."""
        # Wait for threads to start up
        time.sleep(1)
        
        response = app.get('/thread-status')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check structure
        assert 'producer' in data
        assert 'consumers' in data
        assert 'monitor' in data
        assert 'queue' in data
        
        # Check producer
        assert data['producer']['active'] is True
        assert data['producer']['alive'] is True
        
        # Check consumers
        assert len(data['consumers']) == 2
        for consumer in data['consumers']:
            assert consumer['active'] is True
            assert consumer['alive'] is True
            assert 'tasks_processed' in consumer
        
        # Check monitor
        assert 'total_restarts' in data['monitor']
        assert 'monitored_threads' in data['monitor']
        assert data['monitor']['monitored_threads'] == 3  # producer + 2 consumers
    
    def test_full_integration(self, app, setup_threads):
        """Test the full integration of all components."""
        # Wait for demo tasks to be generated and processed
        time.sleep(2)
        
        # Check thread status
        response = app.get('/thread-status')
        data = json.loads(response.data)
        
        # All threads should be active
        assert data['producer']['active'] is True
        assert all(consumer['active'] for consumer in data['consumers'])
        
        # Consumers should have processed some tasks
        assert any(consumer['tasks_processed'] > 0 for consumer in data['consumers'])
        
        # Add a manual task
        task_data = {
            "task_data": {"type": "manual_test", "input_value": 100, "complexity": 5},
            "priority": 10
        }
        response = app.post('/tasks', json=task_data)
        assert response.status_code == 201
        
        # Wait for task to be processed
        time.sleep(1)
        
        # Verify consumers processed more tasks
        response = app.get('/thread-status')
        new_data = json.loads(response.data)
        total_processed_before = sum(consumer['tasks_processed'] for consumer in data['consumers'])
        total_processed_after = sum(consumer['tasks_processed'] for consumer in new_data['consumers'])
        assert total_processed_after >= total_processed_before + 1