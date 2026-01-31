"""
logger.py - Log manager
Log manager responsible for message formatting and queue management for user interface logging system.
"""

from datetime import datetime
from queue import Queue


class LogManager:
    """Log manager - Responsible for formatting and queue management"""
    
    def __init__(self):
        self.log_queue = Queue()
    
    def log(self, message, level='INFO'):
        """Add log message to queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_queue.put((log_message, level))
    
    def get_log_queue(self):
        """Get log queue"""
        return self.log_queue
    
    def clear_queue(self):
        """Clear log queue"""
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except:
                break
