#!/usr/bin/env python3
"""
Unified logging utility for Creative Automation Pipeline.
Provides consistent console output with timestamps, levels, and emoji support.
"""
import sys
import logging
from datetime import datetime
from typing import Optional

class ConsoleFormatter(logging.Formatter):
    """Custom formatter with emoji support and clean timestamps."""
    
    # Emoji mapping for log levels
    LEVEL_EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "💥",
    }
    
    # Color mapping (optional, for terminals that support it)
    LEVEL_COLORS = {
        logging.DEBUG: "\033[36m",   # Cyan
        logging.INFO: "\033[32m",    # Green
        logging.WARNING: "\033[33m", # Yellow
        logging.ERROR: "\033[31m",   # Red
        logging.CRITICAL: "\033[35m", # Magenta
    }
    RESET_COLOR = "\033[0m"
    
    def __init__(self, use_color: bool = True):
        fmt = "%(asctime)s %(levelname)s %(message)s"
        super().__init__(fmt, datefmt="%H:%M:%S")
        self.use_color = use_color and sys.stderr.isatty()
    
    def format(self, record):
        # Add emoji before levelname
        emoji = self.LEVEL_EMOJIS.get(record.levelno, "")
        if emoji:
            record.levelname = f"{emoji} {record.levelname}"
        
        # Apply color if enabled
        if self.use_color and record.levelno in self.LEVEL_COLORS:
            color = self.LEVEL_COLORS[record.levelno]
            record.levelname = f"{color}{record.levelname}{self.RESET_COLOR}"
            record.msg = f"{color}{record.msg}{self.RESET_COLOR}"
        
        return super().format(record)

def setup_logger(name: str = "creative_pipeline", 
                level: int = logging.INFO,
                use_color: bool = True) -> logging.Logger:
    """
    Set up and return a configured logger.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_color: Enable terminal colors
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ConsoleFormatter(use_color=use_color))
    logger.addHandler(handler)
    
    return logger

def set_log_level(level: int = logging.INFO):
    """
    Set the log level for the default logger.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger.setLevel(level)
    # Update all handlers
    for handler in logger.handlers:
        handler.setLevel(level)

def get_log_level(level_str: str) -> int:
    """
    Convert string log level to logging constant.
    
    Args:
        level_str: String like "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    
    Returns:
        logging constant (defaults to logging.INFO)
    """
    level_str = level_str.upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str, logging.INFO)

# Default logger instance
logger = setup_logger()

# Convenience functions for common log types
def log_info(msg: str, *args, **kwargs):
    """Log informational message."""
    logger.info(msg, *args, **kwargs)

def log_warning(msg: str, *args, **kwargs):
    """Log warning message."""
    logger.warning(msg, *args, **kwargs)

def log_error(msg: str, *args, **kwargs):
    """Log error message."""
    logger.error(msg, *args, **kwargs)

def log_success(msg: str, *args, **kwargs):
    """Log success message with checkmark emoji."""
    logger.info(f"✅ {msg}", *args, **kwargs)

def log_failure(msg: str, *args, **kwargs):
    """Log failure message with cross emoji."""
    logger.error(f"❌ {msg}", *args, **kwargs)

def log_debug(msg: str, *args, **kwargs):
    """Log debug message."""
    logger.debug(msg, *args, **kwargs)

def log_step(step_number: int, total_steps: int, description: str):
    """Log a pipeline step with progress indicator."""
    progress = f"[{step_number}/{total_steps}]"
    logger.info(f"{progress} {description}")

if __name__ == "__main__":
    # Test the logger
    log_info("Logger initialized successfully")
    log_warning("This is a warning message")
    log_error("This is an error message")
    log_success("Operation completed successfully")
    log_failure("Operation failed")
    log_debug("Debug information (visible only if level=DEBUG)")
    log_step(1, 5, "Generating images")
    log_step(2, 5, "Applying aspect ratios")