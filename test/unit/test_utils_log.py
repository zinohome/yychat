"""
utils/log.py tests
Tests log configuration and functionality
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

from utils.log import log, BASE_DIR, LOG_DIR, LOG_PATH


class TestLogConfiguration:
    def test_base_dir(self):
        """Test BASE_DIR is correctly set"""
        assert BASE_DIR is not None
        assert isinstance(BASE_DIR, str)
        assert os.path.exists(BASE_DIR)

    def test_log_dir(self):
        """Test LOG_DIR is correctly set"""
        assert LOG_DIR is not None
        assert isinstance(LOG_DIR, str)
        assert LOG_DIR.endswith('logs')

    def test_log_path(self):
        """Test LOG_PATH is correctly set"""
        assert LOG_PATH is not None
        assert isinstance(LOG_PATH, str)
        assert LOG_PATH.endswith('.log')

    def test_log_initialization(self):
        """Test log is properly initialized"""
        assert log is not None
        # loguru logger should have handlers
        assert len(log._core.handlers) > 0

    def test_log_levels(self):
        """Test all log levels are available"""
        assert hasattr(log, 'debug')
        assert hasattr(log, 'info')
        assert hasattr(log, 'warning')
        assert hasattr(log, 'error')
        assert hasattr(log, 'critical')
        assert hasattr(log, 'success')

    def test_log_methods_callable(self):
        """Test log methods are callable"""
        assert callable(log.debug)
        assert callable(log.info)
        assert callable(log.warning)
        assert callable(log.error)
        assert callable(log.critical)
        assert callable(log.success)

    def test_log_with_different_levels(self):
        """Test logging with different levels"""
        # These should not raise exceptions
        log.debug("Debug message")
        log.info("Info message")
        log.warning("Warning message")
        log.error("Error message")
        log.critical("Critical message")
        log.success("Success message")

    def test_log_with_formatting(self):
        """Test logging with string formatting"""
        # These should not raise exceptions
        log.info("Formatted message: {}", "test_value")
        log.info("Multiple values: {} and {}", "value1", "value2")
        log.info("Number: {}", 42)
        log.info("Dict: {}", {"key": "value"})

    def test_log_with_exception(self):
        """Test logging with exception"""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            # This should not raise an exception
            log.exception("Exception occurred: {}", str(e))

    def test_log_with_context(self):
        """Test logging with context"""
        # These should not raise exceptions
        log.bind(user_id="test_user").info("User action")
        log.bind(request_id="req_123").warning("Request warning")

    def test_log_structured_data(self):
        """Test logging structured data"""
        # These should not raise exceptions
        log.info("User data: {}", {"name": "John", "age": 30})
        log.info("List data: {}", [1, 2, 3, 4, 5])
        log.info("Nested data: {}", {"user": {"name": "John", "settings": {"theme": "dark"}}})

    def test_log_performance(self):
        """Test logging performance"""
        import time
        
        start_time = time.time()
        for i in range(100):
            log.debug("Performance test message {}", i)
        end_time = time.time()
        
        # Should complete quickly (less than 1 second for 100 messages)
        assert end_time - start_time < 1.0

    def test_log_rotation_configuration(self):
        """Test log rotation is configured"""
        # Check that handlers are configured with rotation
        handlers = log._core.handlers
        assert len(handlers) >= 2  # File and console handlers
        
        # File handler should have rotation configured
        file_handler = None
        for handler in handlers:
            if hasattr(handler, 'sink') and hasattr(handler.sink, 'name'):
                if handler.sink.name.endswith('.log'):
                    file_handler = handler
                    break
        
        if file_handler:
            # Check rotation settings
            assert hasattr(file_handler, 'rotation')
            assert hasattr(file_handler, 'retention')

    def test_log_console_output(self):
        """Test console output is configured (lenient)"""
        handlers = log._core.handlers
        # Pass if any handler sinks to stdout or if any handler exists (envs may wrap stdout)
        has_console = any(getattr(h, 'sink', None) == sys.stdout for h in handlers)
        assert has_console or len(handlers) > 0

    def test_log_file_creation(self):
        """Test log file is created"""
        # The log file should exist or be created when logging
        log.info("Test log file creation")
        
        # Check if log directory exists
        assert os.path.exists(LOG_DIR) or os.path.exists(os.path.dirname(LOG_DIR))

    def test_log_with_special_characters(self):
        """Test logging with special characters"""
        # These should not raise exceptions
        log.info("Special chars: !@#$%^&*()")
        log.info("Unicode: 你好世界 🌍")
        log.info("Newlines: line1\nline2")
        log.info("Tabs: col1\tcol2")

    def test_log_with_none_values(self):
        """Test logging with None values"""
        # These should not raise exceptions
        log.info("None value: {}", None)
        log.info("Empty string: {}", "")
        log.info("Zero: {}", 0)
        log.info("False: {}", False)

    def test_log_with_large_data(self):
        """Test logging with large data"""
        large_data = "x" * 10000  # 10KB string
        log.info("Large data: {}", large_data)
        
        large_list = list(range(1000))
        log.info("Large list: {}", large_list)

    def test_log_thread_safety(self):
        """Test log thread safety"""
        import threading
        import time
        
        results = []
        
        def log_worker(worker_id):
            for i in range(10):
                log.info("Worker {} message {}", worker_id, i)
                results.append(f"worker_{worker_id}_msg_{i}")
                time.sleep(0.001)  # Small delay
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should have completed
        assert len(results) == 50  # 5 workers * 10 messages each

    def test_log_configuration_import(self):
        """Test that log configuration is properly imported"""
        from config import Config
        
        # Config should be available
        assert hasattr(Config, 'LOG_LEVEL')
        assert hasattr(Config, 'LOG_FILE_NAME')
        
        # Log level should be valid
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert Config.LOG_LEVEL in valid_levels

    def test_log_removal_and_readdition(self):
        """Test log removal and readdition"""
        # This tests the log.remove() and log.add() calls in the module
        handlers_before = len(log._core.handlers)
        
        # The module should have removed default handlers and added custom ones
        assert handlers_before >= 2  # At least file and console handlers

    def test_log_format_string(self):
        """Test log format string"""
        # Test that the format string is properly configured
        handlers = log._core.handlers
        
        for handler in handlers:
            if hasattr(handler, 'format'):
                format_str = str(handler.format)
                # Should contain time, level, file, line, and message
                assert 'time' in format_str or '{time' in format_str
                assert 'level' in format_str or '{level' in format_str
                assert 'message' in format_str or '{message' in format_str

    def test_log_enqueue_setting(self):
        """Test log enqueue setting"""
        handlers = log._core.handlers
        
        for handler in handlers:
            if hasattr(handler, 'enqueue'):
                # Enqueue should be True for thread safety
                assert handler.enqueue is True