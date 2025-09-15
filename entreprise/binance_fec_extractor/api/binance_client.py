"""
Binance API client wrapper for FEC extractor.

This module provides a wrapper around the Binance API with proper authentication,
rate limiting, error handling, and retry logic.
"""

import time
import hmac
import hashlib
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
import logging
from dataclasses import dataclass

from ..config.settings import Config


@dataclass
class APIError(Exception):
    """Custom exception for Binance API errors."""
    code: int
    message: str
    
    def __str__(self):
        return f"Binance API Error {self.code}: {self.message}"


@dataclass
class RateLimitError(APIError):
    """Exception for rate limit errors."""
    retry_after: Optional[int] = None


@dataclass
class AuthenticationError(APIError):
    """Exception for authentication errors."""
    pass


@dataclass
class InsufficientPermissionsError(APIError):
    """Exception for insufficient API permissions."""
    pass


@dataclass
class NetworkError(APIError):
    """Exception for network-related errors."""
    pass


@dataclass
class ServerError(APIError):
    """Exception for server-side errors."""
    pass


@dataclass
class InvalidSymbolError(APIError):
    """Exception for invalid trading symbol errors."""
    symbol: Optional[str] = None


@dataclass
class InvalidParameterError(APIError):
    """Exception for invalid parameter errors."""
    parameter: Optional[str] = None


@dataclass
class OrderNotFoundError(APIError):
    """Exception for order not found errors."""
    order_id: Optional[str] = None


@dataclass
class InsufficientBalanceError(APIError):
    """Exception for insufficient balance errors."""
    asset: Optional[str] = None


class BinanceClient:
    """
    Binance API client with authentication, rate limiting, and error handling.
    """
    
    def __init__(self, config: Config):
        """
        Initialize Binance client.
        
        Args:
            config: Application configuration containing API credentials
        """
        self.config = config
        self.base_url = config.api.base_url
        self.timeout = config.api.timeout
        self.max_retries = config.api.max_retries
        self.rate_limit_delay = config.api.rate_limit_delay
        
        # Get API credentials
        try:
            self.api_key, self.secret_key = config.get_credentials()
        except ValueError as e:
            raise AuthenticationError(code=0, message=str(e))
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.request_count = 0
        self.weight_used = 0
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def _generate_signature(self, query_string: str) -> str:
        """
        Generate HMAC SHA256 signature for API request.
        
        Args:
            query_string: Query parameters as string
            
        Returns:
            HMAC signature
        """
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _should_retry_error(self, error: Exception) -> bool:
        """
        Determine if an error should be retried.
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if the error should be retried
        """
        # Always retry network errors
        if isinstance(error, (requests.exceptions.ConnectionError, 
                            requests.exceptions.Timeout,
                            requests.exceptions.HTTPError)):
            return True
        
        # Always retry rate limit errors
        if isinstance(error, RateLimitError):
            return True
        
        # Retry server errors (5xx)
        if isinstance(error, ServerError):
            return True
        
        # Don't retry authentication, permission, or parameter errors
        if isinstance(error, (AuthenticationError, InsufficientPermissionsError, 
                            InvalidParameterError, InvalidSymbolError,
                            OrderNotFoundError, InsufficientBalanceError)):
            return False
        
        # For generic API errors, check the code
        if isinstance(error, APIError):
            # Retry codes that might be temporary
            retryable_codes = {
                -1000,  # Unknown error
                -1001,  # Internal error
                -1003,  # Rate limit
                -1006,  # Unexpected response
                -1007,  # Timeout
                -1016,  # Service shutting down
            }
            return error.code in retryable_codes
        
        # Default to not retrying unknown errors
        return False
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed JSON response
            
        Raises:
            APIError: For various API errors
        """
        # Update rate limit tracking
        if 'X-MBX-USED-WEIGHT-1M' in response.headers:
            self.weight_used = int(response.headers['X-MBX-USED-WEIGHT-1M'])
        
        if response.status_code == 200:
            return response.json()
        
        # Handle error responses
        try:
            error_data = response.json()
            code = error_data.get('code', response.status_code)
            message = error_data.get('msg', response.text)
        except ValueError:
            code = response.status_code
            message = response.text
        
        # Specific error handling based on HTTP status codes
        if response.status_code == 401:
            raise AuthenticationError(code=code, message=f"Authentication failed: {message}")
        elif response.status_code == 403:
            raise InsufficientPermissionsError(code=code, message=f"Insufficient permissions: {message}")
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            retry_after = int(retry_after) if retry_after else None
            raise RateLimitError(code=code, message=f"Rate limit exceeded: {message}", retry_after=retry_after)
        elif response.status_code >= 500:
            raise ServerError(code=code, message=f"Server error: {message}")
        
        # Specific error handling based on Binance error codes
        if isinstance(code, int):
            if code == -1000:
                raise ServerError(code=code, message=f"Unknown error: {message}")
            elif code == -1001:
                raise ServerError(code=code, message=f"Internal error: {message}")
            elif code == -1002:
                raise AuthenticationError(code=code, message=f"Unauthorized: {message}")
            elif code == -1003:
                retry_after = response.headers.get('Retry-After')
                retry_after = int(retry_after) if retry_after else None
                raise RateLimitError(code=code, message=f"Rate limit exceeded: {message}", retry_after=retry_after)
            elif code == -1006:
                raise ServerError(code=code, message=f"Unexpected response: {message}")
            elif code == -1007:
                raise ServerError(code=code, message=f"Timeout: {message}")
            elif code == -1013:
                raise InvalidParameterError(code=code, message=f"Invalid quantity: {message}")
            elif code == -1014:
                raise InvalidSymbolError(code=code, message=f"Unknown order composition: {message}")
            elif code == -1015:
                raise RateLimitError(code=code, message=f"Too many orders: {message}")
            elif code == -1016:
                raise ServerError(code=code, message=f"Service shutting down: {message}")
            elif code == -1020:
                raise InvalidParameterError(code=code, message=f"Unsupported operation: {message}")
            elif code == -1021:
                raise AuthenticationError(code=code, message=f"Timestamp outside recv window: {message}")
            elif code == -1022:
                raise AuthenticationError(code=code, message=f"Invalid signature: {message}")
            elif code == -1100:
                raise InvalidParameterError(code=code, message=f"Illegal characters: {message}")
            elif code == -1101:
                raise InvalidParameterError(code=code, message=f"Too many parameters: {message}")
            elif code == -1102:
                raise InvalidParameterError(code=code, message=f"Mandatory parameter missing: {message}")
            elif code == -1103:
                raise InvalidParameterError(code=code, message=f"Unknown parameter: {message}")
            elif code == -1104:
                raise InvalidParameterError(code=code, message=f"Duplicate parameters: {message}")
            elif code == -1105:
                raise InvalidParameterError(code=code, message=f"Invalid parameter: {message}")
            elif code == -1106:
                raise InvalidParameterError(code=code, message=f"Invalid parameter combination: {message}")
            elif code == -1111:
                raise InvalidParameterError(code=code, message=f"Invalid precision: {message}")
            elif code == -1112:
                raise InvalidParameterError(code=code, message=f"No orders on book: {message}")
            elif code == -1114:
                raise InvalidParameterError(code=code, message=f"Invalid time in force: {message}")
            elif code == -1115:
                raise InvalidParameterError(code=code, message=f"Invalid order type: {message}")
            elif code == -1116:
                raise InvalidParameterError(code=code, message=f"Invalid side: {message}")
            elif code == -1117:
                raise InvalidParameterError(code=code, message=f"Invalid new client order ID: {message}")
            elif code == -1118:
                raise InvalidParameterError(code=code, message=f"Invalid original client order ID: {message}")
            elif code == -1119:
                raise InvalidParameterError(code=code, message=f"Invalid interval: {message}")
            elif code == -1120:
                raise InvalidSymbolError(code=code, message=f"Invalid symbol: {message}")
            elif code == -1121:
                raise InvalidSymbolError(code=code, message=f"Invalid listen key: {message}")
            elif code == -1125:
                raise InvalidParameterError(code=code, message=f"Invalid listen key: {message}")
            elif code == -1127:
                raise InvalidParameterError(code=code, message=f"Invalid lookup interval: {message}")
            elif code == -1128:
                raise InvalidParameterError(code=code, message=f"Combination of optional parameters invalid: {message}")
            elif code == -1130:
                raise InvalidParameterError(code=code, message=f"Invalid data sent: {message}")
            elif code == -2010:
                raise OrderNotFoundError(code=code, message=f"Order not found: {message}")
            elif code == -2011:
                raise InvalidParameterError(code=code, message=f"Order cancelled: {message}")
            elif code == -2013:
                raise OrderNotFoundError(code=code, message=f"Order does not exist: {message}")
            elif code == -2014:
                raise AuthenticationError(code=code, message=f"API key format invalid: {message}")
            elif code == -2015:
                raise InsufficientPermissionsError(code=code, message=f"Invalid API key permissions: {message}")
            elif code == -2016:
                raise ServerError(code=code, message=f"No trading window: {message}")
            elif code == -2018:
                raise InsufficientBalanceError(code=code, message=f"Balance insufficient: {message}")
            elif code == -2019:
                raise InvalidParameterError(code=code, message=f"Margin insufficient: {message}")
            elif code == -2020:
                raise InvalidParameterError(code=code, message=f"Unable to fill: {message}")
            elif code == -2021:
                raise InvalidParameterError(code=code, message=f"Order would immediately trigger: {message}")
            elif code == -2022:
                raise InvalidParameterError(code=code, message=f"Reduce only order type not supported: {message}")
            elif code == -2023:
                raise InvalidParameterError(code=code, message=f"User in liquidation mode: {message}")
            elif code == -2024:
                raise InvalidParameterError(code=code, message=f"Position side does not match: {message}")
            elif code == -2025:
                raise InvalidParameterError(code=code, message=f"Reduce only conflict: {message}")
        
        # Generic error for unhandled cases
        raise APIError(code=code, message=message)
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     signed: bool = False, retries: int = 0) -> Dict[str, Any]:
        """
        Make HTTP request to Binance API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            signed: Whether request requires signature
            retries: Current retry count
            
        Returns:
            API response data
        """
        if params is None:
            params = {}
        
        # Add timestamp for signed requests
        if signed:
            params['timestamp'] = int(time.time() * 1000)
        
        # Create query string
        query_string = urlencode(params)
        
        # Add signature for signed requests
        if signed:
            signature = self._generate_signature(query_string)
            query_string += f"&signature={signature}"
        
        # Build URL
        url = f"{self.base_url}{endpoint}"
        if query_string:
            url += f"?{query_string}"
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        try:
            self.logger.debug(f"Making {method} request to {endpoint}")
            response = self.session.request(method, url, timeout=self.timeout)
            return self._handle_response(response)
            
        except (requests.exceptions.RequestException, RateLimitError, ServerError) as e:
            if retries < self.max_retries:
                # Determine if we should retry based on error type
                should_retry = self._should_retry_error(e)
                
                if should_retry:
                    # Exponential backoff with jitter
                    wait_time = (2 ** retries) + (time.time() % 1)
                    
                    # Special handling for rate limit errors
                    if isinstance(e, RateLimitError) and e.retry_after:
                        wait_time = max(wait_time, e.retry_after)
                    
                    # Cap maximum wait time
                    wait_time = min(wait_time, 60)  # Max 60 seconds
                    
                    self.logger.warning(f"Request failed ({type(e).__name__}), retrying in {wait_time:.2f}s (attempt {retries + 1}/{self.max_retries}): {e}")
                    time.sleep(wait_time)
                    return self._make_request(method, endpoint, params, signed, retries + 1)
                else:
                    self.logger.error(f"Non-retryable error: {e}")
                    raise
            else:
                self.logger.error(f"Request failed after {self.max_retries} retries: {e}")
                raise
        except (AuthenticationError, InsufficientPermissionsError, InvalidParameterError, InvalidSymbolError) as e:
            # Don't retry these errors as they won't succeed on retry
            self.logger.error(f"Non-retryable error: {e}")
            raise
    
    def authenticate(self) -> Dict[str, Any]:
        """
        Test API authentication and return account information.
        
        Returns:
            Account information from Binance
            
        Raises:
            AuthenticationError: If authentication fails
            InsufficientPermissionsError: If API permissions are insufficient
        """
        try:
            account_info = self._make_request('GET', '/api/v3/account', signed=True)
            self.logger.info("Successfully authenticated with Binance API")
            return account_info
        except APIError:
            raise
        except Exception as e:
            raise AuthenticationError(code=0, message=f"Authentication failed: {str(e)}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Account information including balances
        """
        return self._make_request('GET', '/api/v3/account', signed=True)
    
    def verify_permissions(self) -> Tuple[bool, List[str]]:
        """
        Verify API key permissions.
        
        Returns:
            Tuple of (has_required_permissions, missing_permissions)
        """
        try:
            account_info = self.get_account_info()
            permissions = account_info.get('permissions', [])
            
            required_permissions = ['SPOT']  # We need at least SPOT trading permissions
            missing_permissions = []
            
            for perm in required_permissions:
                if perm not in permissions:
                    missing_permissions.append(perm)
            
            has_required = len(missing_permissions) == 0
            
            if has_required:
                self.logger.info("API key has all required permissions")
            else:
                self.logger.warning(f"API key missing permissions: {missing_permissions}")
            
            return has_required, missing_permissions
            
        except APIError as e:
            self.logger.error(f"Failed to verify permissions: {e}")
            return False, ["Unable to verify permissions"]
    
    def test_connectivity(self) -> bool:
        """
        Test connectivity to Binance API.
        
        Returns:
            True if connection successful
        """
        try:
            response = self._make_request('GET', '/api/v3/ping')
            return response == {}
        except Exception as e:
            self.logger.error(f"Connectivity test failed: {e}")
            return False
    
    def get_server_time(self) -> datetime:
        """
        Get Binance server time.
        
        Returns:
            Server time as datetime object
        """
        response = self._make_request('GET', '/api/v3/time')
        timestamp = response['serverTime']
        return datetime.fromtimestamp(timestamp / 1000)
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including trading rules and symbol information.
        
        Returns:
            Exchange information
        """
        return self._make_request('GET', '/api/v3/exchangeInfo')
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        return {
            'weight_used': self.weight_used,
            'request_count': self.request_count,
            'last_request_time': self.last_request_time,
            'rate_limit_delay': self.rate_limit_delay
        }
    
    def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            self.session.close()
            self.logger.debug("Binance client session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # Transaction Data Retrieval Methods
    
    def get_trades(self, symbol: Optional[str] = None, start_time: Optional[int] = None, 
                   end_time: Optional[int] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get spot trading history.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT'). If None, gets all symbols
            start_time: Start time in milliseconds
            end_time: End time in milliseconds  
            limit: Number of records to return (max 1000)
            
        Returns:
            List of trade records
        """
        if symbol:
            return self._get_trades_for_symbol(symbol, start_time, end_time, limit)
        else:
            return self._get_all_trades(start_time, end_time, limit)
    
    def _get_trades_for_symbol(self, symbol: str, start_time: Optional[int] = None,
                              end_time: Optional[int] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get trades for a specific symbol."""
        params = {
            'symbol': symbol,
            'limit': min(limit, 1000)  # Binance max is 1000
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self._make_request('GET', '/api/v3/myTrades', params=params, signed=True)
    
    def _get_all_trades(self, start_time: Optional[int] = None,
                       end_time: Optional[int] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get trades for all symbols."""
        all_trades = []
        
        # First get account info to find symbols with balances
        account_info = self.get_account_info()
        symbols_with_balance = set()
        
        for balance in account_info.get('balances', []):
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                symbols_with_balance.add(balance['asset'])
        
        # Get exchange info to find all trading pairs
        exchange_info = self.get_exchange_info()
        relevant_symbols = []
        
        for symbol_info in exchange_info.get('symbols', []):
            symbol = symbol_info['symbol']
            base_asset = symbol_info['baseAsset']
            quote_asset = symbol_info['quoteAsset']
            
            # Only get trades for symbols where we have/had balances
            if (base_asset in symbols_with_balance or 
                quote_asset in symbols_with_balance or
                symbol_info['status'] == 'TRADING'):
                relevant_symbols.append(symbol)
        
        # Get trades for each relevant symbol
        for symbol in relevant_symbols:
            try:
                symbol_trades = self._get_trades_for_symbol(symbol, start_time, end_time, limit)
                if symbol_trades:
                    all_trades.extend(symbol_trades)
                    self.logger.debug(f"Retrieved {len(symbol_trades)} trades for {symbol}")
            except InvalidSymbolError as e:
                self.logger.debug(f"Symbol {symbol} not valid for trading: {e}")
                continue
            except InvalidParameterError as e:
                if e.code == -1102:  # Mandatory parameter missing
                    self.logger.debug(f"No trades available for {symbol}")
                else:
                    self.logger.warning(f"Parameter error for {symbol}: {e}")
                continue
            except APIError as e:
                self.logger.warning(f"Failed to get trades for {symbol}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Unexpected error getting trades for {symbol}: {e}")
                continue
        
        # Sort by time and limit results
        all_trades.sort(key=lambda x: x['time'])
        return all_trades[:limit] if limit else all_trades
    
    def get_deposits(self, coin: Optional[str] = None, start_time: Optional[int] = None,
                    end_time: Optional[int] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get deposit history.
        
        Args:
            coin: Coin symbol (e.g., 'BTC'). If None, gets all coins
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of records to return (max 1000)
            
        Returns:
            List of deposit records
        """
        params = {
            'limit': min(limit, 1000)
        }
        
        if coin:
            params['coin'] = coin
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        response = self._make_request('GET', '/sapi/v1/capital/deposit/hisrec', params=params, signed=True)
        return response if isinstance(response, list) else response.get('data', [])
    
    def get_withdrawals(self, coin: Optional[str] = None, start_time: Optional[int] = None,
                       end_time: Optional[int] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get withdrawal history.
        
        Args:
            coin: Coin symbol (e.g., 'BTC'). If None, gets all coins
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of records to return (max 1000)
            
        Returns:
            List of withdrawal records
        """
        params = {
            'limit': min(limit, 1000)
        }
        
        if coin:
            params['coin'] = coin
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        response = self._make_request('GET', '/sapi/v1/capital/withdraw/history', params=params, signed=True)
        return response if isinstance(response, list) else response.get('data', [])
    
    def get_dust_log(self, start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get dust conversion history (small balance conversions to BNB).
        
        Args:
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            
        Returns:
            List of dust conversion records
        """
        params = {}
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        response = self._make_request('GET', '/sapi/v1/asset/dribblet', params=params, signed=True)
        return response.get('userAssetDribblets', [])
    
    def get_asset_dividend_record(self, asset: Optional[str] = None, start_time: Optional[int] = None,
                                 end_time: Optional[int] = None, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get asset dividend records (staking rewards, etc.).
        
        Args:
            asset: Asset symbol (e.g., 'BTC')
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of records to return (max 500)
            
        Returns:
            List of dividend records
        """
        params = {
            'limit': min(limit, 500)
        }
        
        if asset:
            params['asset'] = asset
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        response = self._make_request('GET', '/sapi/v1/asset/assetDividend', params=params, signed=True)
        return response.get('rows', [])
    
    def get_universal_transfer_history(self, transfer_type: str = 'MAIN_SPOT', 
                                     start_time: Optional[int] = None,
                                     end_time: Optional[int] = None, 
                                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get universal transfer history (transfers between different account types).
        
        Args:
            transfer_type: Type of transfer (MAIN_SPOT, SPOT_MAIN, etc.)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of records to return (max 100)
            
        Returns:
            List of transfer records
        """
        params = {
            'type': transfer_type,
            'size': min(limit, 100)
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        response = self._make_request('GET', '/sapi/v1/asset/transfer', params=params, signed=True)
        return response.get('rows', [])
    
    def get_all_transactions(self, start_time: Optional[int] = None, end_time: Optional[int] = None,
                           limit_per_type: int = 1000) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all transaction types within date range.
        
        Args:
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit_per_type: Limit per transaction type
            
        Returns:
            Dictionary with transaction types as keys and lists of transactions as values
        """
        self.logger.info("Retrieving all transaction types...")
        
        transactions = {
            'trades': [],
            'deposits': [],
            'withdrawals': [],
            'dust_conversions': [],
            'dividends': [],
            'transfers': []
        }
        
        errors = []
        
        # Get trades
        try:
            self.logger.debug("Retrieving trades...")
            transactions['trades'] = self.get_trades(start_time=start_time, end_time=end_time, limit=limit_per_type)
            self.logger.info(f"Retrieved {len(transactions['trades'])} trades")
        except Exception as e:
            error_msg = f"Failed to retrieve trades: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            transactions['trades'] = []
        
        # Get deposits
        try:
            self.logger.debug("Retrieving deposits...")
            transactions['deposits'] = self.get_deposits(start_time=start_time, end_time=end_time, limit=limit_per_type)
            self.logger.info(f"Retrieved {len(transactions['deposits'])} deposits")
        except Exception as e:
            error_msg = f"Failed to retrieve deposits: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            transactions['deposits'] = []
        
        # Get withdrawals
        try:
            self.logger.debug("Retrieving withdrawals...")
            transactions['withdrawals'] = self.get_withdrawals(start_time=start_time, end_time=end_time, limit=limit_per_type)
            self.logger.info(f"Retrieved {len(transactions['withdrawals'])} withdrawals")
        except Exception as e:
            error_msg = f"Failed to retrieve withdrawals: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            transactions['withdrawals'] = []
        
        # Get dust conversions
        try:
            self.logger.debug("Retrieving dust conversions...")
            transactions['dust_conversions'] = self.get_dust_log(start_time=start_time, end_time=end_time)
            self.logger.info(f"Retrieved {len(transactions['dust_conversions'])} dust conversions")
        except Exception as e:
            error_msg = f"Failed to retrieve dust conversions: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            transactions['dust_conversions'] = []
        
        # Get dividends/rewards
        try:
            self.logger.debug("Retrieving dividends...")
            transactions['dividends'] = self.get_asset_dividend_record(start_time=start_time, end_time=end_time, limit=limit_per_type)
            self.logger.info(f"Retrieved {len(transactions['dividends'])} dividend records")
        except Exception as e:
            error_msg = f"Failed to retrieve dividends: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            transactions['dividends'] = []
        
        # Get transfers
        try:
            self.logger.debug("Retrieving transfers...")
            transactions['transfers'] = self.get_universal_transfer_history(start_time=start_time, end_time=end_time, limit=limit_per_type)
            self.logger.info(f"Retrieved {len(transactions['transfers'])} transfer records")
        except Exception as e:
            error_msg = f"Failed to retrieve transfers: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            transactions['transfers'] = []
        
        # Log summary of errors if any
        if errors:
            self.logger.warning(f"Encountered {len(errors)} errors during transaction retrieval:")
            for error in errors:
                self.logger.warning(f"  - {error}")
        
        # If all transaction types failed, raise an exception
        total_transactions = sum(len(tx_list) for tx_list in transactions.values())
        if total_transactions == 0 and errors:
            raise APIError(code=-1000, message=f"Failed to retrieve any transactions. Errors: {'; '.join(errors)}")
        
        total_transactions = sum(len(tx_list) for tx_list in transactions.values())
        self.logger.info(f"Retrieved {total_transactions} total transactions")
        
        return transactions
    
    def get_transactions_by_date_range(self, start_date: datetime, end_date: datetime,
                                     limit_per_type: int = 1000) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all transactions within a specific date range.
        
        Args:
            start_date: Start date
            end_date: End date
            limit_per_type: Limit per transaction type
            
        Returns:
            Dictionary with transaction types and their data
        """
        # Convert dates to milliseconds
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)
        
        self.logger.info(f"Retrieving transactions from {start_date.date()} to {end_date.date()}")
        
        return self.get_all_transactions(start_time=start_time, end_time=end_time, limit_per_type=limit_per_type)