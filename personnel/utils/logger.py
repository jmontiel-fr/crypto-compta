"""
Logging configuration for Binance Tax Report Generator.

This module provides centralized logging configuration for the application,
with support for file logging and configurable log levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(year: int, log_level: str = "INFO", log_dir: str = "logs") -> logging.Logger:
    """
    Set up and configure the application logger.
    
    Creates a logger that writes to both console and a year-specific log file.
    The log file is named tax_report_{year}.log and stored in the logs/ directory.
    
    Args:
        year: Fiscal year for the tax report (used in log filename)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory where log files should be stored (default: logs)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = setup_logger(2024, "INFO")
        >>> logger.info("Starting tax report generation")
    """
    # Create logger
    logger = logging.getLogger("binance_tax_report")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create logs directory if it doesn't exist
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)
    
    # File handler (all levels)
    log_path = log_dir_path / f"tax_report_{year}.log"
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logger initialized. Log file: {log_path}")
    
    return logger


def get_logger() -> logging.Logger:
    """
    Get the application logger instance.
    
    Returns the existing logger if already configured, otherwise returns
    a basic logger. Should be called after setup_logger() has been called.
    
    Returns:
        Logger instance
        
    Example:
        >>> logger = get_logger()
        >>> logger.debug("Debug message")
    """
    return logging.getLogger("binance_tax_report")


class LoggerMixin:
    """
    Mixin class to add logging capabilities to other classes.
    
    Classes that inherit from this mixin will have access to self.logger
    which uses the application's configured logger.
    
    Example:
        >>> class MyClass(LoggerMixin):
        ...     def process(self):
        ...         self.logger.info("Processing started")
    """
    
    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance"""
        return get_logger()
