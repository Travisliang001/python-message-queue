import pytest
import queue
import threading
import time
from app.consumer.task_consumer import TaskConsumer
from app.models.task import Task

class TestTaskConsumer:
    
    @pytest.fixture
    def test_queue(self):
        return queue.Queue(maxsize=10)
    
    @pytest.fixture
    def shutdown_event(self):
        return threading.Event()
    
    @pytest.fixture
    def sample_task(self):
        return Task({"type": "test", "input_value": 42, "complexity": 2})
    
    def test_consumer_initialization(self, test_queue, shutdown_event):
        """Test that the consumer initializes correctly."""
        consumer = TaskConsumer(test_queue, 1, shutdown_event)
        assert consumer.name == "TaskConsumer-1"
        assert consumer.worker_id == 1
        assert consumer.task_queue == test_queue
        assert consumer.shutdown_event == shutdown_event
        assert consumer.tasks_processed == 0
    
    def test_process_task(self, test_queue, shutdown_event, sample_task):
        """Test that the consumer processes tasks correctly."""
        consumer = TaskConsumer(test_queue, 1, shutdown_event, processing_time=(0.1, 0.1))
        
        # Process a task
        result_task = consumer.process_task(sample_task)
        
        # Check that task was processed
        assert result_task.status in ["completed", "failed"]
        if result_task.status == "completed":
            assert result_task.result is not None
            assert result_task.processed_at is not None
        else:
            assert result_task.error is not None
    
    def test_consumer_pause_resume(self, test_queue, shutdown_event, sample_task):
        """Test that the consumer can be paused and resumed."""
        consumer = TaskConsumer(test_queue, 1, shutdown_event, processing_time=(0.1, 0.1))
        
        # Start the consumer
        consumer.start()
        
        # Add a task
        test_queue.put(sample_task)
        
        # Wait a bit for the task to be processed
        time.sleep(0.3)
        
        # Pause the consumer
        consumer.pause()
        assert consumer.paused is True
        
        # Add another task
        test_queue.put(sample_task)
        
        # Wait a bit, task should not be processed
        time.sleep(0.3)
        assert test_queue.qsize() == 1
        
        # Resume the consumer
        consumer.resume()
        assert consumer.paused is False
        
        # Wait for task to be processed
        time.sleep(0.3)
        assert test_queue.empty()
        
        # Clean up
        shutdown_event.set()
        consumer.join(timeout=1.0)
    
    def test_consumer_activity_tracking(self, test_queue, shutdown_event):
        """Test that the consumer properly tracks its activity."""
        consumer = TaskConsumer(test_queue, 1, shutdown_event)
        
        # Should be active initially
        assert consumer.is_active() is True
        
        # Manually reset last activity to simulate inactivity
        consumer.last_activity = time.time() - 60
        assert consumer.is_active() is False
        
        # Update activity
        consumer.update_activity()
        assert consumer.is_active() is True
    
    def test_consumer_task_count(self, test_queue, shutdown_event, sample_task):
        """Test that the consumer correctly counts processed tasks."""
        consumer = TaskConsumer(test_queue, 1, shutdown_event, processing_time=(0.1, 0.1))
        
        # Start the consumer
        consumer.start()
        
        # Initial count should be 0
        assert consumer.tasks_processed == 0
        
        # Add multiple tasks
        for _ in range(3):
            test_queue.put(Task({"type": "test", "input_value": 42, "complexity": 2}))
        
        # Wait for tasks to be processed
        time.sleep(1.0)
        
        # Check count
        assert consumer.tasks_processed == 3
        
        # Clean up
        shutdown_event.set()
        consumer.join(timeout=1.0)