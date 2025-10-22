"""Unit tests for configuration management."""

import unittest
import os
import tempfile
from config.config import Config, ConfigError


class TestConfigManagement(unittest.TestCase):
    """Test cases for Config class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files"""
        # Clean up any temporary files created during tests
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
    
    def test_successful_key_loading(self):
        """Test successful loading of API keys from properly formatted file"""
        # Create a valid binance_keys file
        test_file = os.path.join(self.temp_dir, "binance_keys_valid")
        with open(test_file, 'w') as f:
            f.write("BINANCE_API_KEY='test_api_key_123'\n")
            f.write("BINANCE_SECRET_KEY='test_secret_key_456'\n")
        
        # Load keys
        api_key, secret_key = Config.load_binance_keys(test_file)
        
        # Verify keys are loaded correctly
        self.assertEqual(api_key, "test_api_key_123")
        self.assertEqual(secret_key, "test_secret_key_456")
    
    def test_successful_key_loading_with_double_quotes(self):
        """Test successful loading with double quotes"""
        test_file = os.path.join(self.temp_dir, "binance_keys_double_quotes")
        with open(test_file, 'w') as f:
            f.write('BINANCE_API_KEY="test_api_key_abc"\n')
            f.write('BINANCE_SECRET_KEY="test_secret_key_def"\n')
        
        api_key, secret_key = Config.load_binance_keys(test_file)
        
        self.assertEqual(api_key, "test_api_key_abc")
        self.assertEqual(secret_key, "test_secret_key_def")
    
    def test_missing_file_error(self):
        """Test error handling when configuration file is missing"""
        non_existent_file = os.path.join(self.temp_dir, "non_existent_file")
        
        with self.assertRaises(ConfigError) as context:
            Config.load_binance_keys(non_existent_file)
        
        self.assertIn("not found", str(context.exception))
    
    def test_malformed_file_missing_api_key(self):
        """Test error handling when API key is missing from file"""
        test_file = os.path.join(self.temp_dir, "binance_keys_no_api")
        with open(test_file, 'w') as f:
            f.write("BINANCE_SECRET_KEY='test_secret_key_456'\n")
        
        with self.assertRaises(ConfigError) as context:
            Config.load_binance_keys(test_file)
        
        self.assertIn("BINANCE_API_KEY not found", str(context.exception))
    
    def test_malformed_file_missing_secret_key(self):
        """Test error handling when secret key is missing from file"""
        test_file = os.path.join(self.temp_dir, "binance_keys_no_secret")
        with open(test_file, 'w') as f:
            f.write("BINANCE_API_KEY='test_api_key_123'\n")
        
        with self.assertRaises(ConfigError) as context:
            Config.load_binance_keys(test_file)
        
        self.assertIn("BINANCE_SECRET_KEY not found", str(context.exception))
    
    def test_malformed_file_wrong_format(self):
        """Test error handling when file has wrong format"""
        test_file = os.path.join(self.temp_dir, "binance_keys_wrong_format")
        with open(test_file, 'w') as f:
            f.write("API_KEY=test_api_key_123\n")
            f.write("SECRET_KEY=test_secret_key_456\n")
        
        with self.assertRaises(ConfigError):
            Config.load_binance_keys(test_file)
    
    def test_empty_file(self):
        """Test error handling when file is empty"""
        test_file = os.path.join(self.temp_dir, "binance_keys_empty")
        with open(test_file, 'w') as f:
            f.write("")
        
        with self.assertRaises(ConfigError):
            Config.load_binance_keys(test_file)


if __name__ == '__main__':
    unittest.main()
