"""
Unit tests for exchange rate service.
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime, timedelta
from pathlib import Path

from binance_fec_extractor.api.exchange_rates import (
    ExchangeRateService,
    ECBClient,
    CoinGeckoClient,
    ExchangeRate,
    ExchangeRateError,
    ECBAPIError,
    RateNotFoundError
)
from binance_fec_extractor.config.settings import Config


class TestExchangeRate:
    """Test ExchangeRate data class."""
    
    def test_exchange_rate_creation(self):
        """Test ExchangeRate creation."""
        test_date = date(2023, 12, 15)
        rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime(2023, 12, 15, 10, 30)
        )
        
        assert rate.date == test_date
        assert rate.rate == 0.92
        assert rate.source == "ECB"
        assert rate.currency_pair == "USD/EUR"
    
    def test_exchange_rate_to_dict(self):
        """Test ExchangeRate serialization."""
        test_date = date(2023, 12, 15)
        timestamp = datetime(2023, 12, 15, 10, 30)
        rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=timestamp
        )
        
        rate_dict = rate.to_dict()
        
        assert rate_dict['date'] == '2023-12-15'
        assert rate_dict['rate'] == 0.92
        assert rate_dict['source'] == "ECB"
        assert rate_dict['currency_pair'] == "USD/EUR"
        assert rate_dict['timestamp'] == timestamp.isoformat()
    
    def test_exchange_rate_from_dict(self):
        """Test ExchangeRate deserialization."""
        rate_dict = {
            'date': '2023-12-15',
            'rate': 0.92,
            'source': 'ECB',
            'currency_pair': 'USD/EUR',
            'timestamp': '2023-12-15T10:30:00'
        }
        
        rate = ExchangeRate.from_dict(rate_dict)
        
        assert rate.date == date(2023, 12, 15)
        assert rate.rate == 0.92
        assert rate.source == "ECB"
        assert rate.currency_pair == "USD/EUR"
        assert rate.timestamp == datetime(2023, 12, 15, 10, 30)


class TestECBClient:
    """Test ECB API client."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = ECBClient(timeout=30)
    
    @patch('requests.Session.get')
    def test_get_usd_eur_rate_success(self, mock_get):
        """Test successful ECB rate retrieval."""
        # Mock ECB XML response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="UTF-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
                           xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
            <message:DataSet>
                <generic:Series>
                    <generic:Obs>
                        <generic:ObsDimension id="TIME_PERIOD" value="2023-12-15"/>
                        <generic:ObsValue value="0.9234"/>
                    </generic:Obs>
                </generic:Series>
            </message:DataSet>
        </message:GenericData>'''
        mock_get.return_value = mock_response
        
        test_date = date(2023, 12, 15)
        rate = self.client.get_usd_eur_rate(test_date)
        
        assert rate is not None
        assert rate.date == test_date
        assert rate.rate == 0.9234
        assert rate.source == "ECB"
        assert rate.currency_pair == "USD/EUR"
    
    @patch('requests.Session.get')
    def test_get_usd_eur_rate_not_found(self, mock_get):
        """Test ECB rate not found."""
        # Mock empty ECB XML response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''<?xml version="1.0" encoding="UTF-8"?>
        <message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
            <message:DataSet>
            </message:DataSet>
        </message:GenericData>'''
        mock_get.return_value = mock_response
        
        test_date = date(2023, 12, 16)  # Weekend, no rate
        rate = self.client.get_usd_eur_rate(test_date)
        
        assert rate is None
    
    @patch('requests.Session.get')
    def test_get_usd_eur_rate_api_error(self, mock_get):
        """Test ECB API error handling."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection failed")
        
        test_date = date(2023, 12, 15)
        
        with pytest.raises(ECBAPIError) as exc_info:
            self.client.get_usd_eur_rate(test_date)
        
        assert "ECB API request failed" in str(exc_info.value)
    
    @patch.object(ECBClient, 'get_usd_eur_rate')
    def test_get_latest_usd_eur_rate(self, mock_get_rate):
        """Test getting latest ECB rate."""
        # Mock successful rate retrieval on second attempt
        mock_get_rate.side_effect = [None, ExchangeRate(
            date=date.today() - timedelta(days=1),
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )]
        
        rate = self.client.get_latest_usd_eur_rate()
        
        assert rate is not None
        assert rate.rate == 0.92
        assert rate.source == "ECB"


class TestCoinbaseClient:
    """Test Coinbase API client."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = CoinbaseClient(timeout=30)
    
    @patch('requests.Session.get')
    def test_get_usd_eur_rate_success(self, mock_get):
        """Test successful Coinbase rate retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "rates": {
                    "EUR": "0.92"  # EUR per USD
                }
            }
        }
        mock_get.return_value = mock_response
        
        test_date = date.today()  # Recent date
        rate = self.client.get_usd_eur_rate(test_date)
        
        assert rate is not None
        assert abs(rate.rate - (1.0 / 0.92)) < 0.001  # USD/EUR = 1 / (EUR/USD)
        assert rate.source == "Coinbase"
        assert rate.currency_pair == "USD/EUR"
    
    @patch('requests.Session.get')
    def test_get_usd_eur_rate_old_date(self, mock_get):
        """Test Coinbase rate for old date (should return None)."""
        old_date = date.today() - timedelta(days=30)
        rate = self.client.get_usd_eur_rate(old_date)
        
        assert rate is None
        mock_get.assert_not_called()


class TestCoinGeckoClient:
    """Test CoinGecko API client."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = CoinGeckoClient(timeout=30)
    
    @patch('requests.Session.get')
    def test_get_usd_eur_rate_success(self, mock_get):
        """Test successful CoinGecko rate retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "market_data": {
                "current_price": {
                    "usd": 1.0,
                    "eur": 0.92
                }
            }
        }
        mock_get.return_value = mock_response
        
        test_date = date(2023, 12, 15)
        rate = self.client.get_usd_eur_rate(test_date)
        
        assert rate is not None
        assert abs(rate.rate - (1.0 / 0.92)) < 0.001  # USD/EUR = USD_price / EUR_price
        assert rate.source == "CoinGecko"
        assert rate.currency_pair == "USD/EUR"
    
    @patch('requests.Session.get')
    def test_get_crypto_usd_price_success(self, mock_get):
        """Test successful crypto price retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "market_data": {
                "current_price": {
                    "usd": 42000.0
                }
            }
        }
        mock_get.return_value = mock_response
        
        test_date = date(2023, 12, 15)
        price = self.client.get_crypto_usd_price('BTC', test_date)
        
        assert price == 42000.0
    
    @patch('requests.Session.get')
    def test_get_crypto_usd_price_not_found(self, mock_get):
        """Test crypto price not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "market_data": {
                "current_price": {}
            }
        }
        mock_get.return_value = mock_response
        
        test_date = date(2023, 12, 15)
        price = self.client.get_crypto_usd_price('UNKNOWN', test_date)
        
        assert price is None


class TestExchangeRateService:
    """Test main exchange rate service."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create mock config
        self.mock_config = Mock(spec=Config)
        self.mock_config.exchange_rates.cache_duration = 3600
        self.mock_config.exchange_rates.fallback_sources = ["coingecko"]
        self.mock_config.api.timeout = 30
        
        # Create temporary directory for cache
        self.temp_dir = tempfile.mkdtemp()
        self.mock_config.output.directory = self.temp_dir
        
        self.service = ExchangeRateService(self.mock_config)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.object(ECBClient, 'get_usd_eur_rate')
    def test_get_usd_eur_rate_ecb_success(self, mock_ecb_get):
        """Test successful ECB rate retrieval."""
        test_date = date(2023, 12, 15)
        expected_rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        mock_ecb_get.return_value = expected_rate
        
        rate = self.service.get_usd_eur_rate(test_date)
        
        assert rate == expected_rate
        mock_ecb_get.assert_called_once_with(test_date)
    
    @patch.object(ECBClient, 'get_usd_eur_rate')
    @patch.object(CoinGeckoClient, 'get_usd_eur_rate')
    def test_get_usd_eur_rate_fallback_success(self, mock_coingecko_get, mock_ecb_get):
        """Test fallback to CoinGecko when ECB fails."""
        test_date = date(2023, 12, 15)
        
        # ECB fails
        mock_ecb_get.side_effect = ECBAPIError("ECB API failed")
        
        # CoinGecko succeeds
        fallback_rate = ExchangeRate(
            date=test_date,
            rate=0.91,
            source="CoinGecko",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        mock_coingecko_get.return_value = fallback_rate
        
        rate = self.service.get_usd_eur_rate(test_date)
        
        assert rate == fallback_rate
        mock_ecb_get.assert_called_once()
        mock_coingecko_get.assert_called_once()
    
    @patch.object(ECBClient, 'get_usd_eur_rate')
    @patch.object(ExchangeRateService, '_find_closest_ecb_rate')
    def test_get_usd_eur_rate_closest_rate(self, mock_find_closest, mock_ecb_get):
        """Test using closest ECB rate when exact date not available."""
        test_date = date(2023, 12, 16)  # Weekend
        
        # ECB fails for exact date
        mock_ecb_get.return_value = None
        
        # Closest rate found
        closest_rate = ExchangeRate(
            date=date(2023, 12, 15),  # Friday
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        mock_find_closest.return_value = closest_rate
        
        rate = self.service.get_usd_eur_rate(test_date)
        
        assert rate.rate == 0.92
        assert "ECB (from 2023-12-15)" in rate.source
    
    @patch.object(ECBClient, 'get_usd_eur_rate')
    @patch.object(ExchangeRateService, '_find_closest_ecb_rate')
    @patch.object(CoinGeckoClient, 'get_usd_eur_rate')
    def test_get_usd_eur_rate_all_fail(self, mock_coingecko_get, mock_find_closest, mock_ecb_get):
        """Test when all rate sources fail."""
        test_date = date(2023, 12, 15)
        
        # All sources fail
        mock_ecb_get.return_value = None
        mock_find_closest.return_value = None
        mock_coingecko_get.return_value = None
        
        with pytest.raises(RateNotFoundError) as exc_info:
            self.service.get_usd_eur_rate(test_date)
        
        assert "No USD/EUR rate found" in str(exc_info.value)
        assert exc_info.value.date == test_date.isoformat()
    
    def test_convert_crypto_to_usd_stablecoin(self):
        """Test converting stablecoin to USD."""
        amount = 100.0
        usd_amount, crypto_price = self.service.convert_crypto_to_usd(amount, 'USDT', date.today())
        
        assert usd_amount == 100.0
        assert crypto_price == 1.0
    
    @patch.object(CoinGeckoClient, 'get_crypto_usd_price')
    def test_convert_crypto_to_usd_success(self, mock_get_price):
        """Test converting cryptocurrency to USD."""
        mock_get_price.return_value = 42000.0
        
        amount = 0.5
        test_date = date(2023, 12, 15)
        usd_amount, crypto_price = self.service.convert_crypto_to_usd(amount, 'BTC', test_date)
        
        assert usd_amount == 21000.0  # 0.5 * 42000
        assert crypto_price == 42000.0
    
    @patch.object(CoinGeckoClient, 'get_crypto_usd_price')
    def test_convert_crypto_to_usd_not_found(self, mock_get_price):
        """Test crypto price not found."""
        mock_get_price.return_value = None
        
        with pytest.raises(RateNotFoundError):
            self.service.convert_crypto_to_usd(100.0, 'UNKNOWN', date.today())
    
    @patch.object(ExchangeRateService, 'get_usd_eur_rate')
    def test_convert_usd_to_eur(self, mock_get_rate):
        """Test converting USD to EUR."""
        test_date = date(2023, 12, 15)
        exchange_rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        mock_get_rate.return_value = exchange_rate
        
        usd_amount = 100.0
        eur_amount, rate = self.service.convert_usd_to_eur(usd_amount, test_date)
        
        assert eur_amount == 92.0  # 100 * 0.92
        assert rate == exchange_rate
    
    @patch.object(ExchangeRateService, 'convert_crypto_to_usd')
    @patch.object(ExchangeRateService, 'convert_usd_to_eur')
    def test_convert_crypto_to_eur(self, mock_usd_to_eur, mock_crypto_to_usd):
        """Test converting cryptocurrency to EUR."""
        test_date = date(2023, 12, 15)
        
        # Mock crypto to USD conversion
        mock_crypto_to_usd.return_value = (21000.0, 42000.0)
        
        # Mock USD to EUR conversion
        exchange_rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        mock_usd_to_eur.return_value = (19320.0, exchange_rate)
        
        eur_amount, usd_amount, rate = self.service.convert_crypto_to_eur(0.5, 'BTC', test_date)
        
        assert eur_amount == 19320.0
        assert usd_amount == 21000.0
        assert rate == exchange_rate
    
    def test_cache_functionality(self):
        """Test exchange rate caching."""
        test_date = date(2023, 12, 15)
        rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        
        # Cache the rate
        cache_key = f"USD/EUR_{test_date.isoformat()}"
        self.service._cache_rate(cache_key, rate)
        
        # Verify it's cached
        assert cache_key in self.service.rate_cache
        assert self.service.rate_cache[cache_key] == rate
        
        # Verify cache validity
        assert self.service._is_cache_valid(rate) is True
    
    def test_cache_persistence(self):
        """Test cache save and load."""
        test_date = date(2023, 12, 15)
        rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        
        # Cache and save
        cache_key = f"USD/EUR_{test_date.isoformat()}"
        self.service._cache_rate(cache_key, rate)
        
        # Create new service instance (should load cache)
        new_service = ExchangeRateService(self.mock_config)
        
        # Verify cache was loaded
        assert cache_key in new_service.rate_cache
        loaded_rate = new_service.rate_cache[cache_key]
        assert loaded_rate.date == rate.date
        assert loaded_rate.rate == rate.rate
        assert loaded_rate.source == rate.source
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # Add some cache entries
        test_date = date(2023, 12, 15)
        rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        cache_key = f"USD/EUR_{test_date.isoformat()}"
        self.service._cache_rate(cache_key, rate)
        
        # Verify cache has entries
        assert len(self.service.rate_cache) > 0
        
        # Clear cache
        self.service.clear_cache()
        
        # Verify cache is empty
        assert len(self.service.rate_cache) == 0
        assert not self.service.cache_file.exists()
    
    def test_get_cache_stats(self):
        """Test cache statistics."""
        # Add some cache entries
        test_date = date(2023, 12, 15)
        rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        cache_key = f"USD/EUR_{test_date.isoformat()}"
        self.service._cache_rate(cache_key, rate)
        
        stats = self.service.get_cache_stats()
        
        assert stats['total_entries'] == 1
        assert stats['valid_entries'] == 1
        assert stats['expired_entries'] == 0
        assert 'cache_file' in stats
        assert 'cache_duration' in stats
        assert 'sources' in stats
        assert stats['sources']['ECB'] == 1
    
    def test_cleanup_expired_cache(self):
        """Test cleanup of expired cache entries."""
        # Add expired cache entry
        test_date = date(2023, 12, 15)
        old_timestamp = datetime.now() - timedelta(hours=2)  # Older than cache duration
        expired_rate = ExchangeRate(
            date=test_date,
            rate=0.92,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=old_timestamp
        )
        
        cache_key = f"USD/EUR_{test_date.isoformat()}"
        self.service.rate_cache[cache_key] = expired_rate
        
        # Add valid cache entry
        valid_rate = ExchangeRate(
            date=test_date + timedelta(days=1),
            rate=0.93,
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        valid_key = f"USD/EUR_{(test_date + timedelta(days=1)).isoformat()}"
        self.service.rate_cache[valid_key] = valid_rate
        
        # Cleanup expired entries
        removed_count = self.service.cleanup_expired_cache()
        
        assert removed_count == 1
        assert cache_key not in self.service.rate_cache
        assert valid_key in self.service.rate_cache
    
    def test_validate_rate_reasonableness(self):
        """Test rate reasonableness validation."""
        test_date = date(2023, 12, 15)
        
        # Add some reference rates
        for i in range(1, 4):
            ref_date = test_date - timedelta(days=i)
            ref_rate = ExchangeRate(
                date=ref_date,
                rate=0.92,
                source="ECB",
                currency_pair="USD/EUR",
                timestamp=datetime.now()
            )
            cache_key = f"USD/EUR_{ref_date.isoformat()}"
            self.service._cache_rate(cache_key, ref_rate)
        
        # Test reasonable rate
        reasonable_rate = ExchangeRate(
            date=test_date,
            rate=0.93,  # Close to reference rates
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        assert self.service.validate_rate_reasonableness(reasonable_rate) is True
        
        # Test unreasonable rate
        unreasonable_rate = ExchangeRate(
            date=test_date,
            rate=1.5,  # Very different from reference rates
            source="ECB",
            currency_pair="USD/EUR",
            timestamp=datetime.now()
        )
        assert self.service.validate_rate_reasonableness(unreasonable_rate) is False
    
    @patch.object(ExchangeRateService, 'get_usd_eur_rate')
    def test_preload_rates_for_date_range(self, mock_get_rate):
        """Test preloading rates for date range."""
        start_date = date(2023, 12, 15)
        end_date = date(2023, 12, 17)
        
        # Mock successful rate retrieval
        def mock_rate_side_effect(target_date):
            return ExchangeRate(
                date=target_date,
                rate=0.92,
                source="ECB",
                currency_pair="USD/EUR",
                timestamp=datetime.now()
            )
        
        mock_get_rate.side_effect = mock_rate_side_effect
        
        stats = self.service.preload_rates_for_date_range(start_date, end_date)
        
        assert stats['requested_dates'] == 3  # 3 days
        assert stats['ecb_success'] == 3
        assert stats['failures'] == 0
        assert mock_get_rate.call_count == 3


class TestExceptions:
    """Test custom exception classes."""
    
    def test_exchange_rate_error(self):
        """Test ExchangeRateError exception."""
        error = ExchangeRateError("Test error", source="TestSource")
        
        assert error.message == "Test error"
        assert error.source == "TestSource"
        assert str(error) == "Exchange Rate Error (TestSource): Test error"
    
    def test_ecb_api_error(self):
        """Test ECBAPIError exception."""
        error = ECBAPIError("ECB API failed", source="ECB")
        
        assert error.message == "ECB API failed"
        assert error.source == "ECB"
    
    def test_rate_not_found_error(self):
        """Test RateNotFoundError exception."""
        error = RateNotFoundError(
            "Rate not found",
            date="2023-12-15",
            currency_pair="USD/EUR"
        )
        
        assert error.message == "Rate not found"
        assert error.date == "2023-12-15"
        assert error.currency_pair == "USD/EUR"