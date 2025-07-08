# Copyright 2002-2025, OpenNebula Project, OpenNebula Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Central logging configuration for OpenNebula MCP Server.

This module provides a singleton logging setup that prevents duplicate handlers
and allows easy configuration of log levels and destinations.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


# Singleton guard to prevent duplicate handler setup
_logging_configured = False


def setup_logging(
    level: Optional[str] = None, 
    enable_file_logging: bool = True,
    log_subdirectory: Optional[str] = None
) -> None:
    """Configure logging for the OpenNebula MCP server.

    This function sets up logging with a singleton pattern to prevent duplicate
    handlers. It configures both console and optional file logging.

    Args:
        level: Log level override (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses LOG_LEVEL environment variable or defaults to INFO.
        enable_file_logging: If True, enables file logging with automatic timestamped
                           filename in ./log directory (created if doesn't exist).
        log_subdirectory: Optional subdirectory within ./log for organizing logs
                         (e.g., "tests" for test logs). If None, logs go directly in ./log.

    Note:
        This function should be called only once at application startup.
        Subsequent calls are safely ignored to prevent duplicate handlers.
    """
    global _logging_configured

    # Singleton guard - prevent duplicate setup
    if _logging_configured:
        return

    # Resolve log level with precedence: CLI arg > env var > default
    effective_level = _resolve_log_level(level)

    # Get root logger for our application
    root_logger = logging.getLogger("opennebula_mcp")
    root_logger.setLevel(effective_level)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Always add console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if file logging is enabled
    if enable_file_logging:
        log_file_path = _generate_log_file_path(log_subdirectory)
        _add_file_handler(root_logger, log_file_path, effective_level, formatter)

    # Prevent propagation to avoid duplicate messages
    root_logger.propagate = False

    # Mark as configured
    _logging_configured = True


def _generate_log_file_path(subdirectory: Optional[str] = None) -> str:
    """Generate timestamped log file path in repository's log directory.

    Creates a log file path with format: 
    - <repo_root>/log/YYYY_MM_DD_HH_MM_SS.log (if no subdirectory)
    - <repo_root>/log/<subdirectory>/YYYY_MM_DD_HH_MM_SS.log (if subdirectory provided)
    
    The log directory (and subdirectory) is created if it doesn't exist, always relative to the
    repository root regardless of current working directory.

    Args:
        subdirectory: Optional subdirectory within the log directory for organizing logs

    Returns:
        str: Full path to the log file
    """
    # Find repository root (this file is in src/, so go up two levels)
    current_file = Path(__file__).resolve()
    repo_root = current_file.parent.parent  # src/logging_config.py -> src -> repo_root

    # Create log directory relative to repository root
    log_dir = repo_root / "log"
    if subdirectory:
        log_dir = log_dir / subdirectory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamp-based filename
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    log_filename = f"{timestamp}.log"

    return str(log_dir / log_filename)


def _resolve_log_level(cli_level: Optional[str]) -> int:
    """Resolve the effective log level with proper precedence.

    Precedence order:
    1. CLI argument (highest priority)
    2. LOG_LEVEL environment variable
    3. Default INFO level (lowest priority)

    Args:
        cli_level: Log level from CLI argument

    Returns:
        int: Numeric log level for logging module
    """
    # If CLI level provided, use it (highest precedence)
    if cli_level:
        return _parse_log_level(cli_level)

    # Check environment variable
    env_level = os.getenv("LOG_LEVEL")
    if env_level:
        return _parse_log_level(env_level)

    # Default to INFO
    return logging.INFO


def _parse_log_level(level_str: str) -> int:
    """Parse string log level to logging module constant.

    Args:
        level_str: String representation of log level

    Returns:
        int: Numeric log level

    Raises:
        ValueError: If level_str is not a valid log level
    """
    level_str = level_str.upper().strip()

    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,  # Common alias
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.CRITICAL,  # Common alias
    }

    if level_str not in level_mapping:
        valid_levels = ", ".join(sorted(level_mapping.keys()))
        raise ValueError(
            f"Invalid log level '{level_str}'. Valid levels: {valid_levels}"
        )

    return level_mapping[level_str]


def _add_file_handler(
    logger: logging.Logger, log_file: str, level: int, formatter: logging.Formatter
) -> None:
    """Add rotating file handler to logger.

    Args:
        logger: Logger instance to add handler to
        log_file: Path to log file
        level: Log level for the handler
        formatter: Formatter instance for the handler
    """
    try:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler (500MB max, 10 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_path),
            maxBytes=500 * 1024 * 1024,  # 500MB
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Log the file path for user information
        console_logger = logging.getLogger("opennebula_mcp.logging_config")
        console_logger.info(f"File logging enabled: {log_file}")

    except (OSError, PermissionError) as e:
        # If file logging fails, emit warning to console but continue
        console_logger = logging.getLogger("opennebula_mcp.logging_config")
        console_logger.warning(f"Failed to setup file logging to '{log_file}': {e}")


def reset_logging_config() -> None:
    """Reset logging configuration state.

    This function is primarily intended for testing to allow reconfiguration
    of logging in test scenarios. It should not be used in production code.
    """
    global _logging_configured

    # Remove all handlers from our root logger
    root_logger = logging.getLogger("opennebula_mcp")
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Reset configuration state
    _logging_configured = False
