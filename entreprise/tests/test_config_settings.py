"""
Unit tests for configuration settings module.
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from binance_fec_extractor.config.settings import Config, load_config, APIConfig, OutputConfig, ExchangeRateConfig


class TestAPIConfig:
    """Test APIConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = APIConfig()
        assert config.base_url == "https://api.binance.com"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.rate_limit_delay == 0.1
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = APIConfig(
            base_url="https://testnet.binance.vision",
            timeout=60,
            max_retries=5,
            rate_limit_delay=0.2
        )
        assert config.base_url == "https://testnet.binance.vision"
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.rate_limit_delay == 0.2


class TestOutputConfig:
    """Test OutputConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = OutputConfig()
        assert config.directory == "./output"
        assert config.filename_template == "binance_fec_{start_date}_{end_date}.txt"
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = OutputConfig(
            directory="/custom/output",
            filename_template="custom_{start_date}.txt"
        )
        assert config.directory == "/custom/output"
        assert config.filename_template == "custom_{start_date}.txt"


class TestExchangeRateConfig:
    """Test ExchangeRateConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ExchangeRateConfig()
        assert config.primary_source == "ecb"
        assert config.fallback_sources == ["coingecko", "coinbase"]
        assert config.cache_duration == 3600
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = ExchangeRateConfig(
            primary_source="coingecko",
            fallback_sources=["ecb"],
            cache_duration=7200
        )
        assert config.primary_source == "coingecko"
        assert config.fallback_sources == ["ecb"]
        assert config.cache_duration == 7200


class TestConfig:
    """Test main Config class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Clear environment variables
        env_vars = [
            'BINANCE_API_KEY', 'BINANCE_SECRET_KEY', 'START_DATE', 'END_DATE',
            'OUTPUT_DIR', 'LOG_LEVEL', 'EXCHANGE_RATE_SOURCE', 'MAX_RETRIES', 'RATE_LIMIT_DELAY'
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]
    
    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = Config()
        assert config.api.base_url == "https://api.binance.com"
        assert config.output.directory == "./output"
        assert config.exchange_rates.primary_source == "ecb"
        assert config.log_level == "INFO"
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'test_api_key_12345',
        'BINANCE_SECRET_KEY': 'test_secret_key_12345',
        'START_DATE': '2023-01-01',
        'END_DATE': '2023-12-31',
        'OUTPUT_DIR': '/custom/output',
        'LOG_LEVEL': 'DEBUG',
        'EXCHANGE_RATE_SOURCE': 'coingecko',
        'MAX_RETRIES': '5',
        'RATE_LIMIT_DELAY': '0.5'
    })
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        config = Config()
        assert config.binance_api_key == 'test_api_key_12345'
        assert config.binance_secret_key == 'test_secret_key_12345'
        assert config.start_date == '2023-01-01'
        assert config.end_date == '2023-12-31'
        assert config.output.directory == '/custom/output'
        assert config.log_level == 'DEBUG'
        assert config.exchange_rates.primary_source == 'coingecko'
        assert config.api.max_retries == 5
        assert config.api.rate_limit_delay == 0.5
    
    def test_config_file_loading(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "api": {
                "base_url": "https://testnet.binance.vision",
                "timeout": 60,
                "max_retries": 5,
                "rate_limit_delay": 0.2
            },
            "output": {
                "directory": "/test/output",
                "filename_template": "test_{start_date}.txt"
            },
            "exchange_rates": {
                "primary_source": "coingecko",
                "fallback_sources": ["ecb"],
                "cache_duration": 7200
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = Config(config_file=config_file)
            assert config.api.base_url == "https://testnet.binance.vision"
            assert config.api.timeout == 60
            assert config.api.max_retries == 5
            assert config.api.rate_limit_delay == 0.2
            assert config.output.directory == "/test/output"
            assert config.output.filename_template == "test_{start_date}.txt"
            assert config.exchange_rates.primary_source == "coingecko"
            assert config.exchange_rates.fallback_sources == ["ecb"]
            assert config.exchange_rates.cache_duration == 7200
        finally:
            os.unlink(config_file)
    
    def test_config_file_not_found(self):
        """Test handling of missing configuration file."""
        with pytest.raises(FileNotFoundError):
            Config(config_file="nonexistent.json")
    
    def test_invalid_json_config_file(self):
        """Test handling of invalid JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_file = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                Config(config_file=config_file)
        finally:
            os.unlink(config_file)
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'test_api_key_12345',
        'BINANCE_SECRET_KEY': 'test_secret_key_12345'
    })
    def test_validate_api_credentials_valid(self):
        """Test validation of valid API credentials."""
        config = Config()
        # Should not raise any exception
        config.validate_api_credentials()
    
    def test_validate_api_credentials_missing(self):
        """Test validation of missing API credentials."""
        config = Config()
        with pytest.raises(ValueError, match="BINANCE_API_KEY is required"):
            config.validate_api_credentials()
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'short',
        'BINANCE_SECRET_KEY': 'test_secret_key_12345'
    })
    def test_validate_api_credentials_too_short(self):
        """Test validation of too short API credentials."""
        config = Config()
        with pytest.raises(ValueError, match="BINANCE_API_KEY appears to be too short"):
            config.validate_api_credentials()
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'your_api_key_here',
        'BINANCE_SECRET_KEY': 'test_secret_key_12345'
    })
    def test_validate_api_credentials_placeholder(self):
        """Test validation of placeholder API credentials."""
        config = Config()
        with pytest.raises(ValueError, match="BINANCE_API_KEY appears to be a placeholder value"):
            config.validate_api_credentials()
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'test_api_key_12345',
        'BINANCE_SECRET_KEY': 'test_secret_key_12345'
    })
    def test_get_credentials_valid(self):
        """Test getting valid credentials."""
        config = Config()
        api_key, secret_key = config.get_credentials()
        assert api_key == 'test_api_key_12345'
        assert secret_key == 'test_secret_key_12345'
    
    def test_get_credentials_missing(self):
        """Test getting credentials when not configured."""
        config = Config()
        with pytest.raises(ValueError, match="API credentials not configured"):
            config.get_credentials()
    
    def test_validation_negative_timeout(self):
        """Test validation of negative timeout."""
        config = Config()
        config.api.timeout = -1
        with pytest.raises(ValueError, match="API timeout must be positive"):
            config.validate()
    
    def test_validation_negative_max_retries(self):
        """Test validation of negative max retries."""
        config = Config()
        config.api.max_retries = -1
        with pytest.raises(ValueError, match="Max retries must be non-negative"):
            config.validate()
    
    def test_validation_invalid_exchange_rate_source(self):
        """Test validation of invalid exchange rate source."""
        config = Config()
        config.exchange_rates.primary_source = "invalid_source"
        with pytest.raises(ValueError, match="Invalid primary exchange rate source"):
            config.validate()
    
    def test_validation_invalid_fallback_source(self):
        """Test validation of invalid fallback exchange rate source."""
        config = Config()
        config.exchange_rates.fallback_sources = ["invalid_source"]
        with pytest.raises(ValueError, match="Invalid fallback exchange rate source"):
            config.validate()
    
    def test_ensure_output_directory(self):
        """Test ensuring output directory exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config()
            config.output.directory = os.path.join(temp_dir, "new_output")
            
            output_path = config.ensure_output_directory()
            assert output_path.exists()
            assert output_path.is_dir()
    
    @patch.dict(os.environ, {
        'BINANCE_API_KEY': 'test_api_key_12345',
        'BINANCE_SECRET_KEY': 'test_secret_key_12345',
        'START_DATE': '2023-01-01'
    })
    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        
        assert config_dict['api']['credentials_configured'] is True
        assert config_dict['api']['base_url'] == "https://api.binance.com"
        assert config_dict['output']['directory'] == "./output"
        assert config_dict['exchange_rates']['primary_source'] == "ecb"
        assert config_dict['log_level'] == "INFO"
        assert config_dict['start_date'] == '2023-01-01'
        
        # Ensure sensitive data is not included
        assert 'binance_api_key' not in str(config_dict)
        assert 'binance_secret_key' not in str(config_dict)


class TestLoadConfig:
    """Test load_config function."""
    
    def test_load_config_without_file(self):
        """Test loading configuration without file."""
        config = load_config()
        assert isinstance(config, Config)
        assert config.api.base_url == "https://api.binance.com"
    
    def test_load_config_with_file(self):
        """Test loading configuration with file."""
        config_data = {
            "api": {
                "base_url": "https://testnet.binance.vision"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = load_config(config_file=config_file)
            assert isinstance(config, Config)
            assert config.api.base_url == "https://testnet.binance.vision"
        finally:
            os.unlink(config_file)