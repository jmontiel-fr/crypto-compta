"""
Unit tests for Binance API client.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime

from binance_fec_extractor.api.binance_client import (
    BinanceClient,
    APIError,
    RateLimitError,
    AuthenticationError,
    InsufficientPermissionsError
)
from binance_fec_extractor.config.settings import Config


class TestBinanceClient:
    """Test BinanceClient class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create mock config
        self.mock_config = Mock(spec=Config)
        self.mock_config.api.base_url = "https://api.binance.com"
        self.mock_config.api.timeout = 30
        self.mock_config.api.max_retries = 3
        self.mock_config.api.rate_limit_delay = 0.1
        self.mock_config.get_credentials.return_value = ("test_api_key", "test_secret_key")
    
    def test_initialization_success(self):
        """Test successful client initialization."""
        client = BinanceClient(self.mock_config)
        
        assert client.base_url == "https://api.binance.com"
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.rate_limit_delay == 0.1
        assert client.api_key == "test_api_key"
        assert client.secret_key == "test_secret_key"
        assert 'X-MBX-APIKEY' in client.session.headers
    
    def test_initialization_missing_credentials(self):
        """Test initialization with missing credentials."""
        self.mock_config.get_credentials.side_effect = ValueError("API credentials not configured")
        
        with pytest.raises(AuthenticationError) as exc_info:
            BinanceClient(self.mock_config)
        
        assert "API credentials not configured" in str(exc_info.value)
    
    def test_generate_signature(self):
        """Test HMAC signature generation."""
        client = BinanceClient(self.mock_config)
        
        query_string = "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559"
        signature = client._generate_signature(query_string)
        
        # Signature should be a 64-character hex string
        assert len(signature) == 64
        assert all(c in '0123456789abcdef' for c in signature)
    
    @patch('time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test rate limiting functionality."""
        client = BinanceClient(self.mock_config)
        
        # First request should not sleep
        client._apply_rate_limit()
        mock_sleep.assert_not_called()
        
        # Second request immediately after should sleep
        client._apply_rate_limit()
        mock_sleep.assert_called_once()
        
        # Verify sleep time is appropriate
        sleep_time = mock_sleep.call_args[0][0]
        assert 0 < sleep_time <= client.rate_limit_delay
    
    def test_handle_response_success(self):
        """Test successful response handling."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {'X-MBX-USED-WEIGHT-1M': '10'}
        
        result = client._handle_response(mock_response)
        
        assert result == {"success": True}
        assert client.weight_used == 10
    
    def test_handle_response_authentication_error(self):
        """Test authentication error handling."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"code": -2014, "msg": "API-key format invalid."}
        mock_response.headers = {}
        
        with pytest.raises(AuthenticationError) as exc_info:
            client._handle_response(mock_response)
        
        assert exc_info.value.code == -2014
        assert "API-key format invalid" in str(exc_info.value)
    
    def test_handle_response_insufficient_permissions(self):
        """Test insufficient permissions error handling."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"code": -2015, "msg": "Invalid API-key, IP, or permissions for action."}
        mock_response.headers = {}
        
        with pytest.raises(InsufficientPermissionsError) as exc_info:
            client._handle_response(mock_response)
        
        assert exc_info.value.code == -2015
        assert "Invalid API-key" in str(exc_info.value)
    
    def test_handle_response_rate_limit_error(self):
        """Test rate limit error handling."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"code": -1003, "msg": "Too many requests."}
        mock_response.headers = {'Retry-After': '60'}
        
        with pytest.raises(RateLimitError) as exc_info:
            client._handle_response(mock_response)
        
        assert exc_info.value.code == -1003
        assert exc_info.value.retry_after == 60
    
    def test_handle_response_generic_error(self):
        """Test generic API error handling."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"code": -1000, "msg": "Unknown error occurred."}
        mock_response.headers = {}
        
        with pytest.raises(APIError) as exc_info:
            client._handle_response(mock_response)
        
        assert exc_info.value.code == -1000
        assert "Unknown error occurred" in str(exc_info.value)
    
    @patch('binance_fec_extractor.api.binance_client.time.time')
    @patch('requests.Session.request')
    def test_make_request_success(self, mock_request, mock_time):
        """Test successful API request."""
        client = BinanceClient(self.mock_config)
        
        # Mock time for timestamp
        mock_time.return_value = 1499827319.559
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = client._make_request('GET', '/api/v3/ping')
        
        assert result == {"success": True}
        mock_request.assert_called_once()
    
    @patch('binance_fec_extractor.api.binance_client.time.time')
    @patch('requests.Session.request')
    def test_make_request_signed(self, mock_request, mock_time):
        """Test signed API request."""
        client = BinanceClient(self.mock_config)
        
        # Mock time for timestamp
        mock_time.return_value = 1499827319.559
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = client._make_request('GET', '/api/v3/account', signed=True)
        
        assert result == {"success": True}
        
        # Verify signature was added to URL
        called_url = mock_request.call_args[1]['url'] if 'url' in mock_request.call_args[1] else mock_request.call_args[0][1]
        assert 'signature=' in called_url
        assert 'timestamp=' in called_url
    
    @patch('binance_fec_extractor.api.binance_client.time.sleep')
    @patch('requests.Session.request')
    def test_make_request_retry_logic(self, mock_request, mock_sleep):
        """Test retry logic for failed requests."""
        client = BinanceClient(self.mock_config)
        
        # Mock failed responses followed by success
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.json.return_value = {"code": -1000, "msg": "Internal error"}
        mock_response_fail.headers = {}
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}
        mock_response_success.headers = {}
        
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            mock_response_success
        ]
        
        result = client._make_request('GET', '/api/v3/ping')
        
        assert result == {"success": True}
        assert mock_request.call_count == 2
        mock_sleep.assert_called_once()
    
    @patch('requests.Session.request')
    def test_authenticate_success(self, mock_request):
        """Test successful authentication."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "makerCommission": 15,
            "takerCommission": 15,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": 123456789,
            "accountType": "SPOT",
            "balances": []
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = client.authenticate()
        
        assert result["canTrade"] is True
        assert result["accountType"] == "SPOT"
    
    @patch('requests.Session.request')
    def test_authenticate_failure(self, mock_request):
        """Test authentication failure."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"code": -2014, "msg": "API-key format invalid."}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        with pytest.raises(AuthenticationError):
            client.authenticate()
    
    @patch('requests.Session.request')
    def test_verify_permissions_success(self, mock_request):
        """Test successful permission verification."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "permissions": ["SPOT", "MARGIN"],
            "canTrade": True
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        has_permissions, missing = client.verify_permissions()
        
        assert has_permissions is True
        assert missing == []
    
    @patch('requests.Session.request')
    def test_verify_permissions_missing(self, mock_request):
        """Test permission verification with missing permissions."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "permissions": ["MARGIN"],  # Missing SPOT
            "canTrade": True
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        has_permissions, missing = client.verify_permissions()
        
        assert has_permissions is False
        assert "SPOT" in missing
    
    @patch('requests.Session.request')
    def test_test_connectivity_success(self, mock_request):
        """Test successful connectivity test."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = client.test_connectivity()
        
        assert result is True
    
    @patch('requests.Session.request')
    def test_test_connectivity_failure(self, mock_request):
        """Test connectivity test failure."""
        client = BinanceClient(self.mock_config)
        
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = client.test_connectivity()
        
        assert result is False
    
    @patch('requests.Session.request')
    def test_get_server_time(self, mock_request):
        """Test getting server time."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"serverTime": 1499827319559}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        server_time = client.get_server_time()
        
        assert isinstance(server_time, datetime)
        assert server_time.year == 2017  # 1499827319559 is in 2017
    
    @patch('requests.Session.request')
    def test_get_exchange_info(self, mock_request):
        """Test getting exchange information."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "timezone": "UTC",
            "serverTime": 1499827319559,
            "symbols": []
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        exchange_info = client.get_exchange_info()
        
        assert exchange_info["timezone"] == "UTC"
        assert "symbols" in exchange_info
    
    def test_get_rate_limit_status(self):
        """Test getting rate limit status."""
        client = BinanceClient(self.mock_config)
        client.weight_used = 50
        client.request_count = 10
        
        status = client.get_rate_limit_status()
        
        assert status["weight_used"] == 50
        assert status["request_count"] == 10
        assert "last_request_time" in status
        assert "rate_limit_delay" in status
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with patch.object(BinanceClient, 'close') as mock_close:
            with BinanceClient(self.mock_config) as client:
                assert isinstance(client, BinanceClient)
            
            mock_close.assert_called_once()
    
    def test_close(self):
        """Test client cleanup."""
        client = BinanceClient(self.mock_config)
        mock_session = Mock()
        client.session = mock_session
        
        client.close()
        
        mock_session.close.assert_called_once()
    
    @patch('requests.Session.request')
    def test_get_trades_for_symbol(self, mock_request):
        """Test getting trades for specific symbol."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "symbol": "BTCUSDT",
                "id": 28457,
                "orderId": 100234,
                "price": "4000.00000000",
                "qty": "12.00000000",
                "commission": "10.10000000",
                "commissionAsset": "BNB",
                "time": 1499865549590,
                "isBuyer": True,
                "isMaker": False,
                "isBestMatch": True
            }
        ]
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        trades = client.get_trades(symbol="BTCUSDT", limit=100)
        
        assert len(trades) == 1
        assert trades[0]["symbol"] == "BTCUSDT"
        assert trades[0]["price"] == "4000.00000000"
    
    @patch('requests.Session.request')
    def test_get_deposits(self, mock_request):
        """Test getting deposit history."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "amount": "0.00999800",
                "coin": "PAXG",
                "network": "ETH",
                "status": 1,
                "address": "0x788cabe9236ce061e5a892e1a59395a81fc8d62c",
                "addressTag": "",
                "txId": "0xaad4654a3234aa6118af9b4b335f5ae81c360b2394721c019b5d1e75328b09f3",
                "insertTime": 1599621997000,
                "transferType": 0,
                "confirmTimes": "12/12"
            }
        ]
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        deposits = client.get_deposits(coin="PAXG", limit=100)
        
        assert len(deposits) == 1
        assert deposits[0]["coin"] == "PAXG"
        assert deposits[0]["amount"] == "0.00999800"
    
    @patch('requests.Session.request')
    def test_get_withdrawals(self, mock_request):
        """Test getting withdrawal history."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "address": "0x94df8b352de7f46f64b01d3666bf6e936e44ce60",
                "amount": "8.91000000",
                "applyTime": "2019-10-12 11:12:02",
                "coin": "USDT",
                "id": "b6ae22b3aa844210a7041aee7589b68a",
                "withdrawOrderId": "WITHDRAWtest123",
                "network": "ETH",
                "transferType": 0,
                "status": 6,
                "txId": "0xb5ef8c13b968a406cc62a93a8bd80f9e9a906ef1b3fcf20a2e48573c17659268"
            }
        ]
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        withdrawals = client.get_withdrawals(coin="USDT", limit=100)
        
        assert len(withdrawals) == 1
        assert withdrawals[0]["coin"] == "USDT"
        assert withdrawals[0]["amount"] == "8.91000000"
    
    @patch('requests.Session.request')
    def test_get_dust_log(self, mock_request):
        """Test getting dust conversion history."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": 8,
            "userAssetDribblets": [
                {
                    "operateTime": 1615985535000,
                    "totalTransferedAmount": "0.00132256",
                    "totalServiceChargeAmount": "0.00002699",
                    "transId": 45178372831,
                    "userAssetDribbletDetails": [
                        {
                            "transId": 4359321,
                            "serviceChargeAmount": "0.000009",
                            "amount": "0.0009",
                            "operateTime": 1615985535000,
                            "transferedAmount": "0.000441",
                            "fromAsset": "USDT"
                        }
                    ]
                }
            ]
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        dust_log = client.get_dust_log()
        
        assert len(dust_log) == 1
        assert dust_log[0]["totalTransferedAmount"] == "0.00132256"
    
    @patch('requests.Session.request')
    def test_get_asset_dividend_record(self, mock_request):
        """Test getting asset dividend records."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [
                {
                    "amount": "10.00000000",
                    "asset": "BHFT",
                    "divTime": 1563189166000,
                    "enInfo": "BHFT distribution",
                    "tranId": 2968885920
                }
            ],
            "total": 1
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        dividends = client.get_asset_dividend_record(asset="BHFT")
        
        assert len(dividends) == 1
        assert dividends[0]["asset"] == "BHFT"
        assert dividends[0]["amount"] == "10.00000000"
    
    @patch('requests.Session.request')
    def test_get_universal_transfer_history(self, mock_request):
        """Test getting universal transfer history."""
        client = BinanceClient(self.mock_config)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total": 1,
            "rows": [
                {
                    "asset": "USDT",
                    "amount": "1000.00000000",
                    "type": "MAIN_SPOT",
                    "status": "CONFIRMED",
                    "tranId": 13526853623,
                    "timestamp": 1544433325000
                }
            ]
        }
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        transfers = client.get_universal_transfer_history()
        
        assert len(transfers) == 1
        assert transfers[0]["asset"] == "USDT"
        assert transfers[0]["amount"] == "1000.00000000"
    
    @patch.object(BinanceClient, 'get_trades')
    @patch.object(BinanceClient, 'get_deposits')
    @patch.object(BinanceClient, 'get_withdrawals')
    @patch.object(BinanceClient, 'get_dust_log')
    @patch.object(BinanceClient, 'get_asset_dividend_record')
    @patch.object(BinanceClient, 'get_universal_transfer_history')
    def test_get_all_transactions(self, mock_transfers, mock_dividends, mock_dust, 
                                 mock_withdrawals, mock_deposits, mock_trades):
        """Test getting all transaction types."""
        client = BinanceClient(self.mock_config)
        
        # Mock return values
        mock_trades.return_value = [{"type": "trade"}]
        mock_deposits.return_value = [{"type": "deposit"}]
        mock_withdrawals.return_value = [{"type": "withdrawal"}]
        mock_dust.return_value = [{"type": "dust"}]
        mock_dividends.return_value = [{"type": "dividend"}]
        mock_transfers.return_value = [{"type": "transfer"}]
        
        transactions = client.get_all_transactions()
        
        assert len(transactions) == 6
        assert len(transactions['trades']) == 1
        assert len(transactions['deposits']) == 1
        assert len(transactions['withdrawals']) == 1
        assert len(transactions['dust_conversions']) == 1
        assert len(transactions['dividends']) == 1
        assert len(transactions['transfers']) == 1
    
    @patch.object(BinanceClient, 'get_all_transactions')
    def test_get_transactions_by_date_range(self, mock_get_all):
        """Test getting transactions by date range."""
        client = BinanceClient(self.mock_config)
        
        mock_get_all.return_value = {"trades": [{"type": "trade"}]}
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        transactions = client.get_transactions_by_date_range(start_date, end_date)
        
        assert "trades" in transactions
        mock_get_all.assert_called_once()
        
        # Verify timestamps were converted correctly
        call_args = mock_get_all.call_args[1]
        assert 'start_time' in call_args
        assert 'end_time' in call_args


class TestAPIExceptions:
    """Test custom API exception classes."""
    
    def test_api_error(self):
        """Test APIError exception."""
        error = APIError(code=-1000, message="Unknown error")
        
        assert error.code == -1000
        assert error.message == "Unknown error"
        assert str(error) == "Binance API Error -1000: Unknown error"
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        error = RateLimitError(code=-1003, message="Too many requests", retry_after=60)
        
        assert error.code == -1003
        assert error.message == "Too many requests"
        assert error.retry_after == 60
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        error = AuthenticationError(code=-2014, message="API-key format invalid")
        
        assert error.code == -2014
        assert error.message == "API-key format invalid"
    
    def test_insufficient_permissions_error(self):
        """Test InsufficientPermissionsError exception."""
        error = InsufficientPermissionsError(code=-2015, message="Invalid permissions")
        
        assert error.code == -2015
        assert error.message == "Invalid permissions"
    
    def test_network_error(self):
        """Test NetworkError exception."""
        from binance_fec_extractor.api.binance_client import NetworkError
        error = NetworkError(code=0, message="Connection failed")
        
        assert error.code == 0
        assert error.message == "Connection failed"
    
    def test_server_error(self):
        """Test ServerError exception."""
        from binance_fec_extractor.api.binance_client import ServerError
        error = ServerError(code=500, message="Internal server error")
        
        assert error.code == 500
        assert error.message == "Internal server error"
    
    def test_invalid_symbol_error(self):
        """Test InvalidSymbolError exception."""
        from binance_fec_extractor.api.binance_client import InvalidSymbolError
        error = InvalidSymbolError(code=-1120, message="Invalid symbol", symbol="INVALID")
        
        assert error.code == -1120
        assert error.message == "Invalid symbol"
        assert error.symbol == "INVALID"
    
    def test_invalid_parameter_error(self):
        """Test InvalidParameterError exception."""
        from binance_fec_extractor.api.binance_client import InvalidParameterError
        error = InvalidParameterError(code=-1102, message="Missing parameter", parameter="symbol")
        
        assert error.code == -1102
        assert error.message == "Missing parameter"
        assert error.parameter == "symbol"
    
    def test_order_not_found_error(self):
        """Test OrderNotFoundError exception."""
        from binance_fec_extractor.api.binance_client import OrderNotFoundError
        error = OrderNotFoundError(code=-2013, message="Order not found", order_id="12345")
        
        assert error.code == -2013
        assert error.message == "Order not found"
        assert error.order_id == "12345"
    
    def test_insufficient_balance_error(self):
        """Test InsufficientBalanceError exception."""
        from binance_fec_extractor.api.binance_client import InsufficientBalanceError
        error = InsufficientBalanceError(code=-2018, message="Insufficient balance", asset="BTC")
        
        assert error.code == -2018
        assert error.message == "Insufficient balance"
        assert error.asset == "BTC"


class TestErrorHandling:
    """Test enhanced error handling functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.mock_config = Mock(spec=Config)
        self.mock_config.api.base_url = "https://api.binance.com"
        self.mock_config.api.timeout = 30
        self.mock_config.api.max_retries = 3
        self.mock_config.api.rate_limit_delay = 0.1
        self.mock_config.get_credentials.return_value = ("test_api_key", "test_secret_key")
    
    def test_should_retry_error_network_errors(self):
        """Test retry logic for network errors."""
        client = BinanceClient(self.mock_config)
        
        # Network errors should be retried
        assert client._should_retry_error(requests.exceptions.ConnectionError()) is True
        assert client._should_retry_error(requests.exceptions.Timeout()) is True
        assert client._should_retry_error(requests.exceptions.HTTPError()) is True
    
    def test_should_retry_error_rate_limit(self):
        """Test retry logic for rate limit errors."""
        client = BinanceClient(self.mock_config)
        
        rate_error = RateLimitError(code=-1003, message="Rate limit")
        assert client._should_retry_error(rate_error) is True
    
    def test_should_retry_error_server_errors(self):
        """Test retry logic for server errors."""
        from binance_fec_extractor.api.binance_client import ServerError
        client = BinanceClient(self.mock_config)
        
        server_error = ServerError(code=500, message="Internal server error")
        assert client._should_retry_error(server_error) is True
    
    def test_should_not_retry_error_auth_errors(self):
        """Test retry logic for authentication errors."""
        client = BinanceClient(self.mock_config)
        
        auth_error = AuthenticationError(code=-2014, message="Invalid API key")
        assert client._should_retry_error(auth_error) is False
        
        perm_error = InsufficientPermissionsError(code=-2015, message="Invalid permissions")
        assert client._should_retry_error(perm_error) is False
    
    def test_should_not_retry_error_parameter_errors(self):
        """Test retry logic for parameter errors."""
        from binance_fec_extractor.api.binance_client import InvalidParameterError, InvalidSymbolError
        client = BinanceClient(self.mock_config)
        
        param_error = InvalidParameterError(code=-1102, message="Missing parameter")
        assert client._should_retry_error(param_error) is False
        
        symbol_error = InvalidSymbolError(code=-1120, message="Invalid symbol")
        assert client._should_retry_error(symbol_error) is False
    
    def test_should_retry_error_retryable_codes(self):
        """Test retry logic for specific retryable error codes."""
        client = BinanceClient(self.mock_config)
        
        # These codes should be retried
        retryable_codes = [-1000, -1001, -1003, -1006, -1007, -1016]
        
        for code in retryable_codes:
            error = APIError(code=code, message="Test error")
            assert client._should_retry_error(error) is True, f"Code {code} should be retryable"
    
    def test_enhanced_error_code_handling(self):
        """Test enhanced error code handling in _handle_response."""
        from binance_fec_extractor.api.binance_client import (
            ServerError, InvalidParameterError, InvalidSymbolError, 
            OrderNotFoundError, InsufficientBalanceError
        )
        
        client = BinanceClient(self.mock_config)
        
        # Test server error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"code": -1000, "msg": "Unknown error"}
        mock_response.headers = {}
        
        with pytest.raises(ServerError) as exc_info:
            client._handle_response(mock_response)
        assert exc_info.value.code == -1000
        
        # Test invalid parameter error
        mock_response.json.return_value = {"code": -1102, "msg": "Mandatory parameter missing"}
        with pytest.raises(InvalidParameterError) as exc_info:
            client._handle_response(mock_response)
        assert exc_info.value.code == -1102
        
        # Test invalid symbol error
        mock_response.json.return_value = {"code": -1120, "msg": "Invalid symbol"}
        with pytest.raises(InvalidSymbolError) as exc_info:
            client._handle_response(mock_response)
        assert exc_info.value.code == -1120
        
        # Test order not found error
        mock_response.json.return_value = {"code": -2013, "msg": "Order does not exist"}
        with pytest.raises(OrderNotFoundError) as exc_info:
            client._handle_response(mock_response)
        assert exc_info.value.code == -2013
        
        # Test insufficient balance error
        mock_response.json.return_value = {"code": -2018, "msg": "Balance insufficient"}
        with pytest.raises(InsufficientBalanceError) as exc_info:
            client._handle_response(mock_response)
        assert exc_info.value.code == -2018