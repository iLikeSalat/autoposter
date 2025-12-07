"""
Logging configuration for AutoPoster.
Provides structured logging with file and console output.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logger(
    name: str = "autoposter",
    log_level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """Setup and configure logger.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, logs to logs/autoposter.log
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create logs directory if needed
    if log_file is None:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"autoposter_{datetime.now().strftime('%Y%m%d')}.log"
    
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

