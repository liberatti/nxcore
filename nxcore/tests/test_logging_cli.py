#!/usr/bin/env python3
"""CLI test script for LoggingManager.

Demonstrates and verifies:
1. Instantiation and logger configuration completely outside of a Flask context.
2. Custom logger behavior using CustomLogger (which overrides stacklevel).
3. Logging configuration within a Flask application context.
"""

import logging
import sys
from pathlib import Path

# Add project root to path to ensure nxcore is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nxcore.middleware.logging_manager import LoggingManager, logger, CustomLogger  # noqa: E402


def test_logging_outside_flask():
    """Test LoggingManager standalone execution (completely outside Flask)."""
    print("--- Running Test: LoggingManager Standalone (Outside Flask) ---")

    # Verify CustomLogger is not yet active, or active once registered
    # Initialize LoggingManager manually with DEBUG level
    LoggingManager(loglevel="DEBUG")

    # Assert CustomLogger class is registered globally
    current_logger_class = logging.getLoggerClass()
    print(f"Current Logger Class: {current_logger_class}")
    assert issubclass(current_logger_class, CustomLogger), "CustomLogger is not registered"

    # Emit logs using the package logger
    print("\nEmitting test logs (check console output for formatting):")
    logger.debug("This is a DEBUG message from CLI standalone test")
    logger.info("This is an INFO message from CLI standalone test")
    logger.warning("This is a WARNING message from CLI standalone test")
    logger.error("This is an ERROR message from CLI standalone test")

    # Verify that the package logger propagates/handlers are set correctly
    lib_logger = logging.getLogger("nxcore")
    assert lib_logger.level == logging.DEBUG, f"Expected logger level {logging.DEBUG}, got {lib_logger.level}"
    assert len(lib_logger.handlers) > 0, "No handlers attached to the logger"

    print("\n[SUCCESS] Standalone Logging configuration and verification complete!")


def test_logging_inside_flask():
    """Test LoggingManager dynamic lookup and configuration within active Flask app context."""
    print("\n--- Running Test: LoggingManager within Flask App Context ---")
    try:
        from flask import Flask
    except ImportError:
        print("[SKIP] Flask is not installed in the environment. Skipping Flask context test.")
        return

    # Create a Flask app and configure logging level
    app = Flask("test_logging_app")
    app.config["LOGLEVEL"] = "WARNING"

    # Initialize the extension
    mgr = LoggingManager(app)

    # Use the app context to simulate an active request/context environment
    with app.app_context():
        # Retrieve the current manager dynamically from the application context
        current_mgr = LoggingManager.get_current_instance()
        assert current_mgr is mgr, "Manager instance retrieved from context mismatch"
        # Verify app logger got handler and level updated
        assert app.logger.level == logging.WARNING, "Flask logger level mismatch"

        print("Emitting flask context warning log...")
        app.logger.warning("This is a WARNING log from within Flask context")

    print("\n[SUCCESS] Flask-bound Logging configuration and verification complete!")


if __name__ == "__main__":
    try:
        test_logging_outside_flask()
        test_logging_inside_flask()
        print("\nAll Logging CLI tests passed successfully!")
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during execution: {e}", file=sys.stderr)
        sys.exit(1)
