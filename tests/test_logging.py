#!/usr/bin/env python3
"""Test script for structured logging functionality"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.config import logger, log_with_context, get_logging_config


def test_text_logging():
    """Test standard text logging"""
    print("\n=== Testing TEXT Logging ===")
    logger.info("This is a standard info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test structured logging with context
    log_with_context('info', 'User action performed', 
                    user_id=12345, action='login', ip_address='192.168.1.1')
    
    log_with_context('warning', 'Rate limit approaching', 
                    endpoint='/api/posts', requests_count=95, limit=100)


def test_json_logging():
    """Test JSON structured logging"""
    print("\n=== Testing JSON Logging ===")
    
    # Temporarily set JSON format
    os.environ['LOG_FORMAT'] = 'JSON'
    
    # Re-import to get new logger configuration
    from importlib import reload
    import config
    reload(config)
    
    config.logger.info("This is a JSON formatted info message")
    config.logger.warning("This is a JSON formatted warning")
    
    # Test structured logging with context
    config.log_with_context('info', 'Post published successfully', 
                           post_id=456, user_id=123, platform='instagram', 
                           engagement_rate=0.85)
    
    config.log_with_context('error', 'API call failed', 
                           endpoint='https://api.instagram.com/posts', 
                           status_code=429, retry_count=3, 
                           error_type='rate_limit_exceeded')


def test_different_log_levels():
    """Test different log levels"""
    print("\n=== Testing Different Log Levels ===")
    
    # Test with DEBUG level
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    from importlib import reload
    import config
    reload(config)
    
    config.logger.debug("This is a debug message")
    config.logger.info("This is an info message")
    config.logger.warning("This is a warning message")
    config.logger.error("This is an error message")
    
    # Test with WARNING level
    os.environ['LOG_LEVEL'] = 'WARNING'
    reload(config)
    
    print("\nWith WARNING level (debug and info should not appear):")
    config.logger.debug("This debug message should NOT appear")
    config.logger.info("This info message should NOT appear")
    config.logger.warning("This warning message SHOULD appear")
    config.logger.error("This error message SHOULD appear")


def main():
    """Main test function"""
    print("Testing Enhanced Logging System")
    print("=" * 50)
    
    # Show current configuration
    config = get_logging_config()
    print(f"Current logging configuration: {config}")
    
    # Reset environment for clean testing
    os.environ.pop('LOG_FORMAT', None)
    os.environ.pop('LOG_LEVEL', None)
    
    # Test text logging
    test_text_logging()
    
    # Test JSON logging
    test_json_logging()
    
    # Test different log levels
    test_different_log_levels()
    
    print("\n=== Testing Complete ===")
    print("\nTo use JSON logging in production, set:")
    print("  LOG_FORMAT=JSON")
    print("\nTo change log level, set:")
    print("  LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL")


if __name__ == '__main__':
    main()