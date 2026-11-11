#!/usr/bin/env python3
"""Tests for task_tracker.py"""

import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import Mock, patch, MagicMock

# Mock neo4j before importing task_tracker
sys.modules["neo4j"] = MagicMock()
sys.path.insert(0, os.path.dirname(__file__))

# Import the module under test after mocking
import task_tracker


class TestTaskTracker(unittest.TestCase):
    """Test cases for TaskTracker."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        os.environ["NEO4J_URI"] = "bolt://localhost:7687"
        os.environ["NEO4J_USER"] = "neo4j"
        os.environ["NEO4J_PASSWORD"] = "test"

    @patch("neo4j.GraphDatabase.driver")
    def test_init_with_neo4j(self, mock_driver_class):
        """Test initialization with Neo4j available."""
        # Mock the driver and verify_connectivity
        mock_driver = MagicMock()
        mock_driver_class.return_value = mock_driver
        mock_driver.verify_connectivity.return_value = None

        tracker = task_tracker.TaskTracker()

        # Verify driver was created with correct parameters
        mock_driver_class.assert_called_once()
        call_args = mock_driver_class.call_args
        self.assertEqual(call_args[0][0], "bolt://localhost:7687")
        self.assertEqual(call_args[1]["auth"], ("neo4j", "test"))
        mock_driver.verify_connectivity.assert_called_once()
        self.assertIsNotNone(tracker.driver)

    @patch("task_tracker.GraphDatabase")
    def test_init_connection_error(self, mock_graphdb):
        """Test initialization with connection error."""
        mock_driver = MagicMock()
        mock_graphdb.driver.return_value = mock_driver
        mock_driver.verify_connectivity.side_effect = Exception("Connection failed")

        tracker = task_tracker.TaskTracker()

        # Driver should be None on connection failure
        self.assertIsNone(tracker.driver)

    @patch("task_tracker.GraphDatabase")
    def test_add_task_success(self, mock_graphdb):
        """Test adding a task successfully."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.single.return_value = {"id": 123}

        tracker = task_tracker.TaskTracker()
        task_id = tracker.add_task("Test task", tags=["test"], priority="high")

        self.assertEqual(task_id, 123)

        # Verify the query was called correctly
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        self.assertIn("CREATE", call_args[0][0])
        self.assertEqual(call_args[1]["title"], "Test task")
        self.assertEqual(call_args[1]["priority"], "high")
        self.assertEqual(call_args[1]["tags"], ["test"])

    @patch("task_tracker.GraphDatabase")
    def test_add_task_no_driver(self, mock_graphdb):
        """Test adding a task when no driver is available."""
        mock_driver = MagicMock()
        mock_driver.verify_connectivity.side_effect = Exception("Failed")
        mock_graphdb.driver.return_value = mock_driver

        tracker = task_tracker.TaskTracker()
        result = tracker.add_task("Test task")

        self.assertFalse(result)

    @patch("task_tracker.GraphDatabase")
    def test_list_tasks_empty(self, mock_graphdb):
        """Test listing tasks when none exist."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = []  # Empty result

        tracker = task_tracker.TaskTracker()
        # Capture print output
        with patch("builtins.print") as mock_print:
            tracker.list_tasks()
            # Should print "No tasks found."
            calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertIn("No tasks found.", calls)

    @patch("task_tracker.GraphDatabase")
    def test_update_task_success(self, mock_graphdb):
        """Test updating a task successfully."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_task = MagicMock()
        mock_task.element_id = "123"

        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.single.return_value = mock_task

        tracker = task_tracker.TaskTracker()
        with patch("builtins.print") as mock_print:
            tracker.update_task("123", status="done")
            # Should print success message
            calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("updated to done" in call for call in calls))

    @patch("task_tracker.GraphDatabase")
    def test_delete_task_success(self, mock_graphdb):
        """Test deleting a task successfully."""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()

        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = mock_result
        mock_result.single.return_value = {"count": 1}

        tracker = task_tracker.TaskTracker()
        with patch("builtins.print") as mock_print:
            tracker.delete_task("123")
            # Should print success message
            calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("deleted" in call for call in calls))

    @patch("task_tracker.GraphDatabase")
    def test_close(self, mock_graphdb):
        """Test closing the connection."""
        mock_driver = MagicMock()
        mock_graphdb.driver.return_value = mock_driver

        tracker = task_tracker.TaskTracker()
        tracker.close()

        mock_driver.close.assert_called_once()

    @patch("task_tracker.GraphDatabase")
    def test_list_tasks_with_filter(self, mock_graphdb):
        """Test listing tasks with status filter."""
        mock_driver = MagicMock()
        mock_session = MagicMock()

        mock_graphdb.driver.return_value = mock_driver
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value = []

        tracker = task_tracker.TaskTracker()
        tracker.list_tasks(status="todo")

        # Verify query includes status filter
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args
        self.assertIn("status: $status", call_args[0][0])
        self.assertEqual(call_args[1]["status"], "todo")


    @patch("task_tracker.TaskTracker")
    def test_version_flag(self, mock_tracker_class):
        """Test that --version prints the version and exits without a DB connection."""
        with patch.object(sys, "argv", ["task_tracker.py", "--version"]):
            stdout = StringIO()
            with redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as ctx:
                    task_tracker.main()

        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("task-tracker 0.1.0", stdout.getvalue())
        mock_tracker_class.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
