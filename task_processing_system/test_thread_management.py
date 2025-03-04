from datetime import datetime, timedelta
import sys
import unittest
import threading
import time
import queue
from unittest.mock import patch, MagicMock
from core.models import Task
from core.queue_manager import task_queue,task_lock, tasks_status,worker_status_lock, update_worker_status, worker_status, worker_threads
from core.worker import worker_thread, process_task
from services.task_generator import task_generator, create_task_batch
from services.thread_monitor import thread_monitor
from app import start_application


class TestThreadRecovery(unittest.TestCase):
    def setUp(self):
        global running
        running = True
        
        # Clear previous state
        with task_lock:
            tasks_status.clear()
        with worker_status_lock:
            worker_status.clear()
        task_queue.queue.clear()
        
        # Start application
        self.worker_threads, self.generator_thread, self.monitor_thread,_ = start_application()
        time.sleep(1)  # Allow threads to initialize

    def tearDown(self):
        global running
        running = False
        time.sleep(1)  # Allow clean shutdown

    # def test_thread_restart_by_monitor(self):
    #     """Test monitor detects dead worker and restarts it"""
    #     # Get initial state
    #     original_count = len(self.worker_threads)
    #     worker_id = "worker-1"
    #     original_thread = self.worker_threads[0]
    #     for thread in self.worker_threads:
    #         print("thread id is ", thread.name)
    #     # Simulate thread death by mocking is_alive()
    #     with patch.object(original_thread, 'is_alive', return_value=False):
    #         # Let monitor detect dead thread (checks every 5s)
    #         start_time = time.time()
    #         while time.time() - start_time < 10:  # 10s timeout
    #             if self.worker_threads[0] != original_thread:
    #                 break
    #             time.sleep(0.5)
    #         else:
    #             self.fail("Monitor didn't replace dead worker")

    #         # Verify new thread
    #         new_thread = self.worker_threads[0]
    #         self.assertIsNot(new_thread, original_thread)
    #         self.assertTrue(new_thread.is_alive())
    #         for thread in self.worker_threads:
    #             print("thread id is ", thread.name)

    #         # Verify all workers are alive
    #         for i, thread in enumerate(self.worker_threads):
    #             self.assertTrue(thread.is_alive(), f"Worker {i+1} not alive")

    def test_stuck_worker_recovery(self):
        """Test monitor replaces workers with stale status"""
        worker_id = "worker-2"
        original_thread = self.worker_threads[1]
        for thread in self.worker_threads:
            print("thread id is ", thread.name)
        # Manually create stuck worker status
        with worker_status_lock:
            worker_status[worker_id] = {
                "status": "processing",
                "last_active": datetime.now() - timedelta(minutes=6),
                "current_task": "dummy_task"
            }

        # Let monitor detect stale status
        start_time = time.time()
        while time.time() - start_time < 30:
            with worker_status_lock:
                if self.worker_threads[1] != original_thread:
                    break
            time.sleep(0.5)
        else:
            self.fail("Monitor didn't replace stuck worker")
        for thread in self.worker_threads:
            print("thread id is ", thread.name)
        # Verify replacement
        # with worker_status_lock:
        #     self.assertEqual(worker_status[worker_id]["status"], "replaced")

        # Verify task failure if applicable
        # with task_lock:
        #     if "dummy_task" in tasks_status:
        #         self.assertEqual(tasks_status["dummy_task"].status, "failed")

if __name__ == "__main__":
    unittest.main()