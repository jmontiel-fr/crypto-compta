"""Configuration management for Binance Tax Report Generator."""

import os
import re
from typing import Tuple
from utils.logger import get_logger


class ConfigError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class Config:
    """Manages application configuration and API credentials."""
    
    @staticmethod
    def load_binance_keys(file_path: str = "binance_keys") -> Tuple[str, str]:
        """
        Load Binance API credentials from file.
        
        The file should contain two lines in the format:
        BINANCE_API_KEY='your_api_key'
        BINANCE_SECRET_KEY='your_secret_key'
        
        Args:
            file_path: Path to the binance_keys file (default: "binance_keys")
            
        Returns:
            tuple: (api_key, secret_key)
            
        Raises:
            ConfigError: If file is missing, malformed, or keys are invalid
        """
        logger = get_logger()
        logger.info(f"Loading Binance API keys from '{file_path}'")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"Configuration file '{file_path}' not found")
            raise ConfigError(
                f"Configuration file '{file_path}' not found. "
                "Please create a binance_keys file with your API credentials."
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            logger.error(f"Failed to read configuration file '{file_path}': {e}")
            raise ConfigError(f"Failed to read configuration file '{file_path}': {e}")
        
        # Parse API key and secret key
        api_key = None
        secret_key = None
        
        # Pattern to match BINANCE_API_KEY='...' or BINANCE_API_KEY="..."
        api_key_pattern = r"BINANCE_API_KEY\s*=\s*['\"]([^'\"]+)['\"]"
        secret_key_pattern = r"BINANCE_SECRET_KEY\s*=\s*['\"]([^'\"]+)['\"]"
        
        api_key_match = re.search(api_key_pattern, content)
        secret_key_match = re.search(secret_key_pattern, content)
        
        if api_key_match:
            api_key = api_key_match.group(1).strip()
        
        if secret_key_match:
            secret_key = secret_key_match.group(1).strip()
        
        # Validate that both keys were found
        if not api_key:
            logger.error(f"BINANCE_API_KEY not found in '{file_path}'")
            raise ConfigError(
                f"BINANCE_API_KEY not found in '{file_path}'. "
                "Expected format: BINANCE_API_KEY='your_api_key'"
            )
        
        if not secret_key:
            logger.error(f"BINANCE_SECRET_KEY not found in '{file_path}'")
            raise ConfigError(
                f"BINANCE_SECRET_KEY not found in '{file_path}'. "
                "Expected format: BINANCE_SECRET_KEY='your_secret_key'"
            )
        
        # Validate that keys are not empty
        if not api_key:
            logger.error("BINANCE_API_KEY is empty")
            raise ConfigError("BINANCE_API_KEY is empty")
        
        if not secret_key:
            logger.error("BINANCE_SECRET_KEY is empty")
            raise ConfigError("BINANCE_SECRET_KEY is empty")
        
        logger.info("Binance API keys loaded successfully")
        return api_key, secret_key
