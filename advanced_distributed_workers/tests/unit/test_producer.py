import pytest
import queue
import threading
import time
import sys
import os

# Add the root directory of the project to the Python path
from app.producer.task_producer import TaskProducer
from app.models.task import Task

class TestTaskProducer:
    
    @pytest.fixture
    def test_queue(self):
        
        return queue.Queue(maxsize=10)
    
    @pytest.fixture
    def shutdown_event(self):
        return threading.Event()
    
    def test_producer_initialization(self, test_queue, shutdown_event):
        """Test that the producer initializes correctly."""
        producer = TaskProducer(test_queue, shutdown_event, interval=0.1)
        assert producer.name == "TaskProducer"
        assert producer.task_queue == test_queue
        assert producer.shutdown_event == shutdown_event
        assert producer.interval == 0.1
        assert producer.demo_mode is False
    
    def test_producer_demo_mode(self, test_queue, shutdown_event):
        """Test that the producer generates tasks in demo mode."""
        producer = TaskProducer(test_queue, shutdown_event, interval=0.1, demo_mode=True)
        
        # Start the producer
        producer.start()
        
        # Wait for tasks to be generated
        time.sleep(0.5)
        
        # Stop the producer
        shutdown_event.set()
        producer.join(timeout=1.0)
        
        # Check that tasks were generated
        assert not test_queue.empty()
        
        # Check task structure
        task = test_queue.get()
        assert isinstance(task, Task)
        assert "type" in task.data
        assert "complexity" in task.data
        assert "input_value" in task.data
    
    def test_producer_pause_resume(self, test_queue, shutdown_event):
        """Test that the producer can be paused and resumed."""
        producer = TaskProducer(test_queue, shutdown_event, interval=0.1, demo_mode=True)
        
        # Start the producer
        producer.start()
        
        # Let it generate some tasks
        time.sleep(0.5)
        
        # Pause the producer
        producer.pause()
        assert producer.paused is True
        
        # Get the current queue size
        size_before = test_queue.qsize()
        
        # Wait a bit, no new tasks should be generated
        time.sleep(0.5)
        assert test_queue.qsize() == size_before
        
        # Resume the producer
        producer.resume()
        assert producer.paused is False
        
        # Wait for more tasks to be generated
        time.sleep(0.5)
        assert test_queue.qsize() > size_before
        
        # Clean up
        shutdown_event.set()
        producer.join(timeout=1.0)
    
    def test_producer_activity_tracking(self, test_queue, shutdown_event):
        """Test that the producer properly tracks its activity."""
        producer = TaskProducer(test_queue, shutdown_event)
        
        # Should be active initially
        assert producer.is_active() is True
        
        # Manually reset last activity to simulate inactivity
        producer.last_activity = time.time() - 80
        assert producer.is_active() is False
        
        # Update activity
        producer.update_activity()
        assert producer.is_active() is True
    
    def test_generate_demo_task(self, test_queue, shutdown_event):
        """Test that demo tasks are generated correctly."""
        producer = TaskProducer(test_queue, shutdown_event)
        
        # Generate multiple tasks to test randomness
        tasks = [producer.generate_demo_task() for _ in range(10)]
        
        # Check common properties
        for task in tasks:
            assert isinstance(task, Task)
            assert isinstance(task.data, dict)
            assert task.data["type"] in ["calculation", "processing", "validation", "analysis"]
            assert 1 <= task.data["complexity"] <= 10
            assert 1 <= task.data["input_value"] <= 100
            assert 1 <= task.priority <= 10