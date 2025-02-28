import unittest
import sys
import os
import time
import json
import queue
import threading
from unittest.mock import patch, MagicMock, call
from flask import Flask
from contextlib import contextmanager

# Add project root to path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import application modules
from worker.queue_manager import start_workers, start_producer, stop_producer, cleanup, task_queue
from worker.worker import handle_request
from worker.producer import producer
from utils.thread_monitor import health_monitor
from app import app as flask_app
from config import DEFAULT_WORKER_COUNT

class TestWorkerThread(unittest.TestCase):
    """Tests for the worker thread functionality."""
    
    def setUp(self):
        self.test_queue = queue.Queue()
        self.thread_lock = threading.Lock()
        self.thread_health = {}
    
    @patch('worker.worker.requests.get')
    def test_worker_successful_request(self, mock_get):
        """Test worker processes a URL successfully."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Add test URL to queue
        test_url = "https://jsonplaceholder.typicode.com/posts/1"
        self.test_queue.put(test_url)
        
        # Set up worker to run only once
        def stop_after_one():
            time.sleep(0.1)  # Give worker time to process
            global workers_running
            workers_running = False
            
        stopper = threading.Thread(target=stop_after_one)
        stopper.daemon = True
        stopper.start()
        
        # Run worker function
        with patch('worker.worker.workers_running', True):
            handle_request(self.test_queue, self.thread_lock, self.thread_health)
        
        # Check if URL was processed
        mock_get.assert_called_once_with(test_url, timeout=10)
        self.assertTrue(self.test_queue.empty())
    
    @patch('worker.worker.requests.get')
    def test_worker_request_failure(self, mock_get):
        """Test worker handles request failure gracefully."""
        # Setup mock to raise an exception
        mock_get.side_effect = Exception("Connection error")
        
        # Add test URL to queue
        test_url = "https://jsonplaceholder.typicode.com/posts/1"
        self.test_queue.put(test_url)
        
        # Set up worker to run only once
        def stop_after_one():
            time.sleep(0.1)  # Give worker time to process
            global workers_running
            workers_running = False
            
        stopper = threading.Thread(target=stop_after_one)
        stopper.daemon = True
        stopper.start()
        
        # Run worker function
        with patch('worker.worker.workers_running', True):
            handle_request(self.test_queue, self.thread_lock, self.thread_health)
        
        # Verify error was handled and health status was updated
        thread_id = threading.get_ident()
        self.assertIn(thread_id, self.thread_health)
        # Queue should be empty as the task was processed (even with error)
        self.assertTrue(self.test_queue.empty())
    
    def test_worker_empty_queue(self):
        """Test worker handles empty queue without errors."""
        # Start with empty queue
        self.assertTrue(self.test_queue.empty())
        
        # Run worker for short time
        with patch('worker.worker.workers_running', True):
            worker_thread = threading.Thread(
                target=handle_request,
                args=(self.test_queue, self.thread_lock, self.thread_health)
            )
            worker_thread.daemon = True
            worker_thread.start()
            
            # Let it run briefly
            time.sleep(0.1)
        
        # Stop the worker
        with patch('worker.worker.workers_running', False):
            # Add None to unblock the queue.get if it's blocked
            self.test_queue.put(None)
            worker_thread.join(timeout=1)
        
        # Verify thread updates health correctly
        thread_id = worker_thread.ident
        self.assertIn(thread_id, self.thread_health)


class TestProducerThread(unittest.TestCase):
    """Tests for the producer thread functionality."""
    
    def setUp(self):
        self.test_queue = queue.Queue()
        self.thread_lock = threading.Lock()
        self.thread_health = {}
        self.producer_running = True
    
    def test_producer_adds_urls_to_queue(self):
        """Test producer adds URLs to the queue at specified interval."""
        test_urls = ["https://jsonplaceholder.typicode.com/posts/1", "https://jsonplaceholder.typicode.com/posts/2"]
        test_interval = 0.1  # Fast interval for testing
        
        # Start producer thread
        producer_thread = threading.Thread(
            target=producer,
            args=(self.test_queue, self.producer_running, self.thread_lock, self.thread_health, test_interval, test_urls)
        )
        producer_thread.daemon = True
        producer_thread.start()
        
        # Let it run for enough time to add both URLs
        time.sleep(0.3)
        
        # Stop producer
        self.producer_running = False
        producer_thread.join(timeout=1)
        
        # Check if URLs were added to queue
        # Should have at least 2 items in queue
        self.assertGreaterEqual(self.test_queue.qsize(), 2)
        
        # Get items from queue and verify
        urls_from_queue = []
        while not self.test_queue.empty():
            urls_from_queue.append(self.test_queue.get())
            
        # Check all our test URLs are in what was produced
        for url in test_urls:
            self.assertIn(url, urls_from_queue)
    
    def test_producer_respects_interval(self):
        """Test producer respects the interval between adding tasks."""
        test_url = ["https://jsonplaceholder.typicode.com/posts/1"]
        test_interval = 0.5  # Half second interval
        
        # Start producer
        producer_thread = threading.Thread(
            target=producer,
            args=(self.test_queue, self.producer_running, self.thread_lock, self.thread_health, test_interval, test_url)
        )
        producer_thread.daemon = True
        producer_thread.start()
        
        # Let it run briefly
        time.sleep(0.1)
        
        # Should have 1 item
        self.assertEqual(self.test_queue.qsize(), 1)
        
        # Wait just under the interval
        time.sleep(0.3)
        
        # Should still have just 1 item
        self.assertEqual(self.test_queue.qsize(), 1)
        
        # Wait for full interval
        time.sleep(0.2)
        
        # Now should have 2 items
        self.assertEqual(self.test_queue.qsize(), 2)
        
        # Stop producer
        self.producer_running = False
        producer_thread.join(timeout=1)


class TestQueueManager(unittest.TestCase):
    """Tests for the queue manager functionality."""
    
    def setUp(self):
        # Reset the task queue
        while not task_queue.empty():
            task_queue.get()
    
    @patch('worker.queue_manager.producer')
    @patch('worker.queue_manager.threading.Thread')
    def test_start_producer(self, mock_thread, mock_producer):
        """Test starting the producer thread."""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        test_interval = 10
        test_urls = ["https://jsonplaceholder.typicode.com/posts/1"]
        
        # Call start_producer
        result = start_producer(test_interval, test_urls)
        
        # Verify thread was created with correct args
        mock_thread.assert_called_once()
        thread_args = mock_thread.call_args[1]['args']
        self.assertEqual(thread_args[3], test_interval)
        self.assertEqual(thread_args[4], test_urls)
        
        # Verify thread was started
        mock_thread_instance.start.assert_called_once()
        
        # Verify correct result
        self.assertEqual(result["interval"], test_interval)
        self.assertEqual(result["urls_count"], len(test_urls))
    
    @patch('worker.queue_manager.producer')
    @patch('worker.queue_manager.threading.Thread')
    def test_stop_producer(self, mock_thread, mock_producer):
        """Test stopping the producer thread."""
        # Set up a mock producer thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        mock_thread_instance.is_alive.return_value = True
        
        # Start producer
        start_producer()
        
        # Reset the mock to test stop_producer
        mock_thread.reset_mock()
        
        # Stop producer
        result = stop_producer()
        
        # Verify producer_running flag was set to False
        self.assertFalse(producer_running)
        
        # Verify result
        self.assertEqual(result["status"], "Producer stopped")
    
    @patch('worker.queue_manager.handle_request')
    @patch('worker.queue_manager.threading.Thread')
    def test_start_workers(self, mock_thread, mock_handler):
        """Test starting worker threads."""
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Start workers
        worker_count = 5
        result = start_workers(worker_count)
        
        # Verify correct number of threads created
        self.assertEqual(mock_thread.call_count, worker_count + 1)  # +1 for health monitor
        
        # Verify all threads started
        self.assertEqual(mock_thread_instance.start.call_count, worker_count + 1)
        
        # Verify result
        self.assertEqual(len(result), worker_count)


class TestFlaskAPI(unittest.TestCase):
    """Tests for the Flask API endpoints."""
    
    def setUp(self):
        flask_app.testing = True
        self.app = flask_app.test_client()
        
        # Reset the task queue
        while not task_queue.empty():
            task_queue.get()
    
    def test_index_route(self):
        """Test the root endpoint."""
        response = self.app.get('/')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "running")
        self.assertIn("endpoints", data)
    
    def test_add_task_endpoint(self):
        """Test adding a single task."""
        # Send request
        response = self.app.post('/api/add_task', json={'url': 'https://jsonplaceholder.typicode.com/posts/1'})
        data = json.loads(response.data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn('Task added', data['message'])
        self.assertEqual(data['queue_size'], 1)
        
        # Verify task was added to queue
        self.assertEqual(task_queue.qsize(), 1)
    
    def test_add_task_missing_url(self):
        """Test adding a task without providing a URL."""
        # Send request with missing URL
        response = self.app.post('/api/add_task', json={})
        data = json.loads(response.data)
        
        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
        
        # Verify queue is still empty
        self.assertEqual(task_queue.qsize(), 0)
    
    def test_add_multiple_endpoint(self):
        """Test adding multiple tasks."""
        test_urls = ['https://jsonplaceholder.typicode.com/posts/1', 'https://jsonplaceholder.typicode.com/posts/2']
        
        # Send request
        response = self.app.post('/api/add_multiple', json={'urls': test_urls})
        data = json.loads(response.data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertIn('Added', data['message'])
        self.assertEqual(data['queue_size'], 2)
        
        # Verify tasks were added to queue
        self.assertEqual(task_queue.qsize(), 2)
    
    def test_queue_status_endpoint(self):
        """Test getting queue status."""
        # Add a task to the queue
        task_queue.put('https://jsonplaceholder.typicode.com/posts/1')
        
        # Get status
        response = self.app.get('/api/queue_status')
        data = json.loads(response.data)
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['queue_size'], 1)
        self.assertIn('workers_running', data)
        self.assertIn('producer_running', data)


class TestHealthMonitoring(unittest.TestCase):
    """Tests for the health monitoring functionality."""
    
    def setUp(self):
        self.thread_lock = threading.Lock()
        self.thread_health = {}
        self.consumer_threads = []
        self.producer_thread = None
        self.workers_running = True
        self.producer_running = False
    
    @patch('utils.thread_monitor.time.sleep')
    def test_health_monitor_detects_dead_threads(self, mock_sleep):
        """Test health monitor detects dead worker threads."""
        # Create a mock thread that appears to be dead
        dead_thread = MagicMock()
        dead_thread.is_alive.return_value = False
        
        # Add to consumer threads list
        self.consumer_threads.append(dead_thread)
        
        # Mock handle_request to avoid actually starting threads
        with patch('worker.worker.handle_request'):
            # Mock Thread to track if new thread was created
            with patch('threading.Thread') as mock_thread:
                mock_thread_instance = MagicMock()
                mock_thread.return_value = mock_thread_instance
                
                # Run monitor for one iteration
                mock_sleep.side_effect = lambda _: setattr(self, 'workers_running', False)
                
                # Run health monitor
                health_monitor(
                    self.thread_lock, 
                    self.thread_health, 
                    self.consumer_threads,
                    self.producer_thread,
                    self.workers_running,
                    self.producer_running
                )
                
                # Verify new thread was created to replace dead one
                mock_thread.assert_called()
                mock_thread_instance.start.assert_called_once()
    
    @patch('utils.thread_monitor.time.sleep')
    def test_health_monitor_detects_dead_producer(self, mock_sleep):
        """Test health monitor detects dead producer thread."""
        # Set producer as running but thread as dead
        self.producer_running = True
        self.producer_thread = MagicMock()
        self.producer_thread.is_alive.return_value = False
        
        # Mock producer to avoid actually starting thread
        with patch('worker.producer.producer'):
            # Mock Thread to track if new thread was created
            with patch('threading.Thread') as mock_thread:
                mock_thread_instance = MagicMock()
                mock_thread.return_value = mock_thread_instance
                
                # Run monitor for one iteration
                mock_sleep.side_effect = lambda _: setattr(self, 'workers_running', False)
                
                # Run health monitor
                health_monitor(
                    self.thread_lock, 
                    self.thread_health, 
                    self.consumer_threads,
                    self.producer_thread,
                    self.workers_running,
                    self.producer_running
                )
                
                # Verify new thread was created to replace dead producer
                mock_thread.assert_called()
                mock_thread_instance.start.assert_called_once()


class TestIntegration(unittest.TestCase):
    """Integration tests for the application."""
    
    def setUp(self):
        # Use test client
        flask_app.testing = True
        self.app = flask_app.test_client()
        
        # Reset the queue
        while not task_queue.empty():
            task_queue.get()
    
    @patch('worker.worker.requests.get')
    def test_add_task_and_process(self, mock_get):
        """Test adding a task and having it processed by a worker."""
        # Setup mock for request
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Start a worker
        worker_thread = threading.Thread(
            target=handle_request,
            args=(task_queue, threading.Lock(), {})
        )
        worker_thread.daemon = True
        worker_thread.start()
        
        # Add a task via API
        test_url = 'https://jsonplaceholder.typicode.com/posts/1'
        response = self.app.post('/api/add_task', json={'url': test_url})
        
        # Verify task was added
        self.assertEqual(response.status_code, 200)
        
        # Wait for worker to process
        time.sleep(0.5)
        
        # Verify request was made
        mock_get.assert_called_with(test_url, timeout=10)
        
        # Verify queue is now empty
        self.assertEqual(task_queue.qsize(), 0)
    
    def test_producer_integration(self):
        """Test producer adds tasks and workers process them."""
        with patch('worker.worker.requests.get') as mock_get:
            # Setup mock for request
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # Start worker
            worker_thread = threading.Thread(
                target=handle_request,
                args=(task_queue, threading.Lock(), {})
            )
            worker_thread.daemon = True
            worker_thread.start()
            
            # Start producer with fast interval
            test_urls = ['https://jsonplaceholder.typicode.com/posts/1']
            producer_running = True
            producer_thread = threading.Thread(
                target=producer,
                args=(task_queue, producer_running, threading.Lock(), {}, 0.1, test_urls)
            )
            producer_thread.daemon = True
            producer_thread.start()
            
            # Wait for producer to add tasks and worker to process
            time.sleep(0.5)
            
            # Stop producer
            producer_running = False
            
            # Verify at least one request was made
            mock_get.assert_called()
            
            # Verify URL was called
            url_called = mock_get.call_args[0][0]
            self.assertEqual(url_called, test_urls[0])


# Run tests
if __name__ == '__main__':
    unittest.main()