import pytest
import threading
import time
from app.monitor.thread_monitor import ThreadMonitor

# Mock thread class for testing
class MockThread(threading.Thread):
    def __init__(self, name, active=True):
        super().__init__(name=name)
        self._active = active
        self._args = ()
        self._kwargs = {"name": name, "active": active}
        self.daemon = True
    
    def is_active(self):
        return self._active
    
    def run(self):
        while True:
            time.sleep(0.1)

class TestThreadMonitor:
    
    @pytest.fixture
    def shutdown_event(self):
        return threading.Event()
    
    @pytest.fixture
    def mock_threads(self):
        threads = []
        # Create active threads
        for i in range(3):
            thread = MockThread(f"active-{i}", active=True)
            thread.start()
            threads.append(thread)
        
        # Create inactive thread
        inactive = MockThread("inactive", active=False)
        inactive.start()
        threads.append(inactive)
        
        return threads
    
    def test_monitor_initialization(self, mock_threads, shutdown_event):
        """Test that the monitor initializes correctly."""
        monitor = ThreadMonitor(mock_threads, shutdown_event, check_interval=1, inactivity_threshold=5)
        assert monitor.name == "ThreadMonitor"
        assert monitor.threads_to_monitor == mock_threads
        assert monitor.shutdown_event == shutdown_event
        assert monitor.check_interval == 1
        assert monitor.inactivity_threshold == 5
        assert monitor.stats["total_restarts"] == 0
    
    def test_check_threads(self, mock_threads, shutdown_event):
        """Test that the monitor checks threads correctly and handles restarts."""
        monitor = ThreadMonitor(mock_threads, shutdown_event, check_interval=2, inactivity_threshold=1)
        
        # Initial check - should find the inactive thread
        monitor.check_threads()
        
        # Should have restarted the inactive thread
        assert monitor.stats["total_restarts"] == 1, "total_restarts should be 1"
        assert "inactive" in monitor.stats["restarts"], "inactive should be in restarts"
        assert monitor.stats["restarts"]["inactive"] == 1,  "inactive should have been restarted once"
        
        # The threads_to_monitor list should be the same length but contain a new thread
        assert len(monitor.threads_to_monitor) == 4
        
        # The new thread should be active
        assert all(thread.is_active() for thread in monitor.threads_to_monitor)
    
    def test_get_stats(self, mock_threads, shutdown_event):
        """Test that the monitor provides accurate statistics."""
        monitor = ThreadMonitor(mock_threads, shutdown_event)
        
        # Initialize start time
        monitor.stats["start_time"] = time.time()
        
        # Get stats
        stats = monitor.get_stats()
        
        # Check structure
        assert "restarts" in stats
        assert "last_check" in stats
        assert "total_restarts" in stats
        assert "uptime" in stats
        assert "monitored_threads" in stats
        assert "active_threads" in stats
        
        # Check values
        assert stats["total_restarts"] == 0
        assert stats["monitored_threads"] == 4
        assert stats["active_threads"] == 3  # 3 active, 1 inactive
    
    def test_monitor_run(self, mock_threads, shutdown_event):
        """Test that the monitor thread runs correctly."""
        monitor = ThreadMonitor(mock_threads, shutdown_event, check_interval=0.5, inactivity_threshold=1)
        
        # Start the monitor
        monitor.start()
        
        # Wait for a couple of checks
        time.sleep(1.5)
        
        # Should have restarted the inactive thread
        assert monitor.stats["total_restarts"] >= 1
        
        # Clean up
        shutdown_event.set()
        monitor.join(timeout=1.0)