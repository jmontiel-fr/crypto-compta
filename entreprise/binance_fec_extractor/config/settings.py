"""
Configuration management module for Binance FEC Extractor.

This module handles application settings, environment variable loading,
and configuration validation.
"""

import os
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class APIConfig:
    """API configuration settings."""
    base_url: str = "https://api.binance.com"
    timeout: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 0.1


@dataclass
class OutputConfig:
    """Output configuration settings."""
    directory: str = "./output"
    filename_template: str = "binance_fec_{start_date}_{end_date}.txt"


@dataclass
class ExchangeRateConfig:
    """Exchange rate service configuration."""
    primary_source: str = "ecb"
    fallback_sources: list = None
    cache_duration: int = 3600
    
    def __post_init__(self):
        if self.fallback_sources is None:
            self.fallback_sources = ["exchangerate-api", "freecurrency-api", "coinbase"]


class Config:
    """Main configuration class for the Binance FEC Extractor application."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Optional path to configuration file
        """
        self.api = APIConfig()
        self.output = OutputConfig()
        self.exchange_rates = ExchangeRateConfig()
        
        # Load configuration from file if provided
        if config_file:
            self.load_from_file(config_file)
        
        # Load environment variables (overrides file config)
        self.load_from_environment()
        
        # Validate configuration
        self.validate()
    
    def load_from_file(self, config_file: str) -> None:
        """
        Load configuration from JSON file.
        
        Args:
            config_file: Path to configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Update API configuration
            if 'api' in config_data:
                api_config = config_data['api']
                self.api.base_url = api_config.get('base_url', self.api.base_url)
                self.api.timeout = api_config.get('timeout', self.api.timeout)
                self.api.max_retries = api_config.get('max_retries', self.api.max_retries)
                self.api.rate_limit_delay = api_config.get('rate_limit_delay', self.api.rate_limit_delay)
            
            # Update output configuration
            if 'output' in config_data:
                output_config = config_data['output']
                self.output.directory = output_config.get('directory', self.output.directory)
                self.output.filename_template = output_config.get('filename_template', self.output.filename_template)
            
            # Update exchange rate configuration
            if 'exchange_rates' in config_data:
                er_config = config_data['exchange_rates']
                self.exchange_rates.primary_source = er_config.get('primary_source', self.exchange_rates.primary_source)
                self.exchange_rates.fallback_sources = er_config.get('fallback_sources', self.exchange_rates.fallback_sources)
                self.exchange_rates.cache_duration = er_config.get('cache_duration', self.exchange_rates.cache_duration)
                
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in configuration file: {e}")
    
    def load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # API credentials (required)
        self.binance_api_key = os.getenv('BINANCE_API_KEY')
        self.binance_secret_key = os.getenv('BINANCE_SECRET_KEY')
        
        # Date range (optional, can be provided via CLI)
        self.start_date = os.getenv('START_DATE')
        self.end_date = os.getenv('END_DATE')
        
        # Optional configuration overrides
        if os.getenv('OUTPUT_DIR'):
            self.output.directory = os.getenv('OUTPUT_DIR')
        
        if os.getenv('LOG_LEVEL'):
            self.log_level = os.getenv('LOG_LEVEL')
        else:
            self.log_level = 'INFO'
        
        if os.getenv('EXCHANGE_RATE_SOURCE'):
            self.exchange_rates.primary_source = os.getenv('EXCHANGE_RATE_SOURCE')
        
        if os.getenv('MAX_RETRIES'):
            try:
                self.api.max_retries = int(os.getenv('MAX_RETRIES'))
            except ValueError:
                pass  # Keep default value
        
        if os.getenv('RATE_LIMIT_DELAY'):
            try:
                self.api.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY'))
            except ValueError:
                pass  # Keep default value
    
    def validate(self) -> None:
        """
        Validate configuration settings.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate API credentials format (basic validation)
        if self.binance_api_key:
            self.validate_api_credentials()
        
        # Validate output directory
        if self.output.directory:
            output_path = Path(self.output.directory)
            if output_path.exists() and not output_path.is_dir():
                raise ValueError(f"Output path exists but is not a directory: {self.output.directory}")
        
        # Validate numeric values
        if self.api.timeout <= 0:
            raise ValueError("API timeout must be positive")
        
        if self.api.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        
        if self.api.rate_limit_delay < 0:
            raise ValueError("Rate limit delay must be non-negative")
        
        if self.exchange_rates.cache_duration < 0:
            raise ValueError("Exchange rate cache duration must be non-negative")
        
        # Validate exchange rate sources
        valid_sources = ["ecb", "coingecko", "coinbase"]
        if self.exchange_rates.primary_source not in valid_sources:
            raise ValueError(f"Invalid primary exchange rate source: {self.exchange_rates.primary_source}")
        
        for source in self.exchange_rates.fallback_sources:
            if source not in valid_sources:
                raise ValueError(f"Invalid fallback exchange rate source: {source}")
    
    def validate_api_credentials(self) -> None:
        """
        Validate Binance API credentials format.
        
        Raises:
            ValueError: If credentials are invalid
        """
        if not self.binance_api_key:
            raise ValueError("BINANCE_API_KEY is required")
        
        if not self.binance_secret_key:
            raise ValueError("BINANCE_SECRET_KEY is required")
        
        # Basic format validation
        if len(self.binance_api_key) < 10:
            raise ValueError("BINANCE_API_KEY appears to be too short")
        
        if len(self.binance_secret_key) < 10:
            raise ValueError("BINANCE_SECRET_KEY appears to be too short")
        
        # Check for common mistakes
        if self.binance_api_key.startswith('your_api_key') or self.binance_api_key == 'REPLACE_ME':
            raise ValueError("BINANCE_API_KEY appears to be a placeholder value")
        
        if self.binance_secret_key.startswith('your_secret_key') or self.binance_secret_key == 'REPLACE_ME':
            raise ValueError("BINANCE_SECRET_KEY appears to be a placeholder value")
    
    def get_credentials(self) -> tuple[str, str]:
        """
        Get API credentials.
        
        Returns:
            Tuple of (api_key, secret_key)
            
        Raises:
            ValueError: If credentials are not configured
        """
        if not self.binance_api_key or not self.binance_secret_key:
            raise ValueError("API credentials not configured. Set BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables.")
        
        return self.binance_api_key, self.binance_secret_key
    
    def ensure_output_directory(self) -> Path:
        """
        Ensure output directory exists and return Path object.
        
        Returns:
            Path object for output directory
        """
        output_path = Path(self.output.directory)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary (excluding sensitive data).
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            'api': {
                'base_url': self.api.base_url,
                'timeout': self.api.timeout,
                'max_retries': self.api.max_retries,
                'rate_limit_delay': self.api.rate_limit_delay,
                'credentials_configured': bool(self.binance_api_key and self.binance_secret_key)
            },
            'output': {
                'directory': self.output.directory,
                'filename_template': self.output.filename_template
            },
            'exchange_rates': {
                'primary_source': self.exchange_rates.primary_source,
                'fallback_sources': self.exchange_rates.fallback_sources,
                'cache_duration': self.exchange_rates.cache_duration
            },
            'log_level': getattr(self, 'log_level', 'INFO'),
            'start_date': getattr(self, 'start_date', None),
            'end_date': getattr(self, 'end_date', None)
        }


def load_config(config_file: Optional[str] = None) -> Config:
    """
    Load application configuration.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Configured Config instance
    """
    return Config(config_file)