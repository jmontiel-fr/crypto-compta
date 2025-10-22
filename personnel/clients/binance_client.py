"""Binance API client for retrieving fiat operations and portfolio values."""

import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
import requests
from utils.logger import get_logger


class BinanceAPIError(Exception):
    """Exception raised for Binance API-related errors."""
    pass


class BinanceRateLimitError(BinanceAPIError):
    """Exception raised when Binance API rate limit is exceeded."""
    pass


class BinanceNetworkError(BinanceAPIError):
    """Exception raised for network-related errors."""
    pass


class FiatOperation:
    """Represents a fiat deposit or withdrawal operation."""
    
    def __init__(self, date: datetime, operation_type: str, amount_eur: Decimal, timestamp: int):
        """
        Initialize a FiatOperation.
        
        Args:
            date: Operation datetime
            operation_type: "Dépôt" or "Retrait"
            amount_eur: Amount in EUR
            timestamp: Unix timestamp in milliseconds
        """
        self.date = date
        self.operation_type = operation_type
        self.amount_eur = amount_eur
        self.timestamp = timestamp
    
    def __repr__(self):
        return f"FiatOperation(date={self.date}, type={self.operation_type}, amount={self.amount_eur})"


class BinanceClient:
    """Client for Binance API operations."""
    
    def __init__(self, api_key: str, secret_key: str, request_timeout: int = 30):
        """
        Initialize Binance client with API credentials.
        
        Args:
            api_key: Binance API key
            secret_key: Binance secret key
            request_timeout: Request timeout in seconds (default: 30)
        """
        self.logger = get_logger()
        self.logger.info("Initializing Binance API client")
        self.request_timeout = request_timeout
        
        try:
            # Initialize client with timeout configuration
            self.client = Client(api_key, secret_key, requests_params={'timeout': request_timeout})
            # Test authentication
            self.client.get_account_status()
            self.logger.info("Binance API client initialized successfully")
        except BinanceAPIException as e:
            self.logger.error(f"Binance API authentication failed: {e.message}")
            if e.code == -2015:
                raise BinanceAPIError(
                    "Invalid API key or secret. Please check your binance_keys file. "
                    "Ensure your API keys have the correct permissions (read-only is sufficient)."
                )
            elif e.code == -1021:
                raise BinanceAPIError(
                    "Timestamp synchronization error. Please check your system clock is synchronized."
                )
            else:
                raise BinanceAPIError(f"Binance API authentication failed: {e.message}")
        except BinanceRequestException as e:
            self.logger.error(f"Binance API request failed: {e}")
            raise BinanceNetworkError(
                f"Failed to connect to Binance API. Please check your internet connection. Error: {e}"
            )
        except requests.exceptions.Timeout:
            self.logger.error("Binance API request timeout during initialization")
            raise BinanceNetworkError(
                f"Connection to Binance API timed out after {request_timeout} seconds. "
                "Please check your internet connection and try again."
            )
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Network connection error: {e}")
            raise BinanceNetworkError(
                "Unable to connect to Binance API. Please check your internet connection."
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Binance client: {e}")
            raise BinanceAPIError(f"Failed to initialize Binance client: {e}")
    
    def get_fiat_operations(self, year: int, currency: str = "EUR") -> List[FiatOperation]:
        """
        Retrieve all fiat deposit/withdrawal operations for a year.
        
        Args:
            year: Fiscal year (e.g., 2024)
            currency: Fiat currency code (default: EUR)
            
        Returns:
            List of FiatOperation objects sorted by date
            
        Raises:
            BinanceAPIError: If API call fails after retries
        """
        self.logger.info(f"Retrieving {currency} fiat operations for year {year}")
        
        # Calculate start and end timestamps for the year
        start_date = datetime(year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)
        
        operations = []
        
        # Get deposits
        deposits = self._get_fiat_deposits_with_retry(currency, start_timestamp, end_timestamp)
        self.logger.info(f"Found {len(deposits)} deposit(s)")
        for deposit in deposits:
            operations.append(FiatOperation(
                date=datetime.fromtimestamp(deposit['updateTime'] / 1000, tz=timezone.utc),
                operation_type="Dépôt",
                amount_eur=Decimal(str(deposit['amount'])),
                timestamp=deposit['updateTime']
            ))
        
        # Get withdrawals
        withdrawals = self._get_fiat_withdrawals_with_retry(currency, start_timestamp, end_timestamp)
        self.logger.info(f"Found {len(withdrawals)} withdrawal(s)")
        for withdrawal in withdrawals:
            operations.append(FiatOperation(
                date=datetime.fromtimestamp(withdrawal['updateTime'] / 1000, tz=timezone.utc),
                operation_type="Retrait",
                amount_eur=Decimal(str(withdrawal['amount'])),
                timestamp=withdrawal['updateTime']
            ))
        
        # Sort by timestamp
        operations.sort(key=lambda op: op.timestamp)
        
        self.logger.info(f"Total operations retrieved: {len(operations)}")
        return operations
    
    def get_portfolio_value_usd(self, timestamp: int) -> Decimal:
        """
        Get total portfolio value in USD at a specific timestamp.
        
        Args:
            timestamp: Unix timestamp in milliseconds
            
        Returns:
            Total portfolio value in USD
            
        Raises:
            BinanceAPIError: If API call fails after retries
        """
        self.logger.debug(f"Retrieving portfolio value for timestamp {timestamp}")
        value = self._get_portfolio_value_with_retry(timestamp)
        self.logger.debug(f"Portfolio value: ${value} USD")
        return value
    
    def _get_fiat_deposits_with_retry(self, currency: str, start_time: int, end_time: int, 
                                      max_retries: int = 3) -> List[dict]:
        """
        Get fiat deposits with retry logic.
        
        Args:
            currency: Fiat currency code
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of deposit records
            
        Raises:
            BinanceAPIError: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                # Get fiat deposit history
                response = self.client.get_fiat_deposit_withdraw_history(
                    transactionType=0,  # 0 for deposit
                    beginTime=start_time,
                    endTime=end_time
                )
                
                # Filter by currency and successful status
                deposits = [
                    d for d in response.get('data', [])
                    if d.get('fiatCurrency') == currency and d.get('status') == 'Successful'
                ]
                
                return deposits
                
            except BinanceAPIException as e:
                # Handle rate limiting specifically
                if e.code == -1003 or e.code == 429:
                    wait_time = 60  # Wait 60 seconds for rate limit
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise BinanceRateLimitError(
                            "Binance API rate limit exceeded. Please wait a few minutes and try again."
                        )
                else:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        self.logger.warning(f"Failed to retrieve fiat deposits (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Failed to retrieve fiat deposits after {max_retries} attempts: {e}")
                        raise BinanceAPIError(f"Failed to retrieve fiat deposits: {e.message}")
            
            except BinanceRequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Network error retrieving deposits (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Network error after {max_retries} attempts: {e}")
                    raise BinanceNetworkError(f"Network error retrieving fiat deposits: {e}")
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request timeout after {max_retries} attempts")
                    raise BinanceNetworkError(
                        f"Request timed out after {max_retries} attempts. Please check your internet connection."
                    )
            
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Connection error after {max_retries} attempts")
                    raise BinanceNetworkError(
                        "Unable to connect to Binance API. Please check your internet connection."
                    )
            
            except Exception as e:
                self.logger.error(f"Unexpected error retrieving fiat deposits: {e}")
                raise BinanceAPIError(f"Unexpected error retrieving fiat deposits: {e}")
        
        return []
    
    def _get_fiat_withdrawals_with_retry(self, currency: str, start_time: int, end_time: int,
                                         max_retries: int = 3) -> List[dict]:
        """
        Get fiat withdrawals with retry logic.
        
        Args:
            currency: Fiat currency code
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of withdrawal records
            
        Raises:
            BinanceAPIError: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                # Get fiat withdrawal history
                response = self.client.get_fiat_deposit_withdraw_history(
                    transactionType=1,  # 1 for withdrawal
                    beginTime=start_time,
                    endTime=end_time
                )
                
                # Filter by currency and successful status
                withdrawals = [
                    w for w in response.get('data', [])
                    if w.get('fiatCurrency') == currency and w.get('status') == 'Successful'
                ]
                
                return withdrawals
                
            except BinanceAPIException as e:
                # Handle rate limiting specifically
                if e.code == -1003 or e.code == 429:
                    wait_time = 60  # Wait 60 seconds for rate limit
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise BinanceRateLimitError(
                            "Binance API rate limit exceeded. Please wait a few minutes and try again."
                        )
                else:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        self.logger.warning(f"Failed to retrieve fiat withdrawals (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Failed to retrieve fiat withdrawals after {max_retries} attempts: {e}")
                        raise BinanceAPIError(f"Failed to retrieve fiat withdrawals: {e.message}")
            
            except BinanceRequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Network error retrieving withdrawals (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Network error after {max_retries} attempts: {e}")
                    raise BinanceNetworkError(f"Network error retrieving fiat withdrawals: {e}")
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request timeout after {max_retries} attempts")
                    raise BinanceNetworkError(
                        f"Request timed out after {max_retries} attempts. Please check your internet connection."
                    )
            
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Connection error after {max_retries} attempts")
                    raise BinanceNetworkError(
                        "Unable to connect to Binance API. Please check your internet connection."
                    )
            
            except Exception as e:
                self.logger.error(f"Unexpected error retrieving fiat withdrawals: {e}")
                raise BinanceAPIError(f"Unexpected error retrieving fiat withdrawals: {e}")
        
        return []
    
    def _get_portfolio_value_with_retry(self, timestamp: int, max_retries: int = 3) -> Decimal:
        """
        Get portfolio value with retry logic.
        
        Args:
            timestamp: Unix timestamp in milliseconds
            max_retries: Maximum number of retry attempts
            
        Returns:
            Total portfolio value in USD
            
        Raises:
            BinanceAPIError: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                # Try to get account snapshot for the specific date
                # Note: Binance only keeps snapshots for the last 30 days
                from datetime import datetime
                snapshot_date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
                
                try:
                    # Try to get daily account snapshot (SPOT account)
                    snapshot = self.client.get_account_snapshot(
                        type='SPOT',
                        startTime=timestamp,
                        endTime=timestamp + 86400000,  # +24 hours
                        limit=1
                    )
                    
                    if snapshot.get('code') == 200 and snapshot.get('snapshotVos'):
                        # Use snapshot data
                        snapshot_data = snapshot['snapshotVos'][0]['data']
                        total_value_usd = Decimal("0")
                        
                        for balance in snapshot_data.get('balances', []):
                            asset = balance['asset']
                            free = Decimal(balance['free'])
                            locked = Decimal(balance['locked'])
                            total = free + locked
                            
                            if total > 0:
                                # Get historical price for this asset at the snapshot time
                                if asset == 'USDT' or asset == 'USDC' or asset == 'BUSD':
                                    # Stablecoins are 1:1 with USD
                                    total_value_usd += total
                                elif asset == 'EUR':
                                    # EUR fiat balance - convert to USD using historical rate
                                    try:
                                        from clients.frankfurter_client import FrankfurterClient
                                        fx_client = FrankfurterClient()
                                        snapshot_date_obj = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).date()
                                        eur_to_usd_rate = fx_client.get_exchange_rate(snapshot_date_obj, "EUR", "USD")
                                        total_value_usd += total * eur_to_usd_rate
                                        self.logger.debug(f"EUR fiat: {total} × {eur_to_usd_rate} = ${total * eur_to_usd_rate}")
                                    except Exception as e:
                                        self.logger.warning(f"Could not convert EUR to USD: {e}")
                                else:
                                    try:
                                        symbol = f"{asset}USDT"
                                        # Get kline (candlestick) data for the specific timestamp
                                        klines = self.client.get_historical_klines(
                                            symbol, 
                                            self.client.KLINE_INTERVAL_1HOUR,
                                            timestamp,
                                            timestamp + 3600000,  # +1 hour
                                            limit=1
                                        )
                                        if klines:
                                            # Use close price
                                            price = Decimal(klines[0][4])
                                            total_value_usd += total * price
                                    except:
                                        pass
                        
                        self.logger.info(f"Using snapshot data for {snapshot_date}: ${total_value_usd} USD")
                        return total_value_usd
                except Exception as e:
                    self.logger.warning(f"Could not get snapshot for {snapshot_date}: {e}")
                
                # Fallback: Use current account balance with historical prices
                self.logger.info(f"Using current balances with historical prices for {snapshot_date}")
                account_info = self.client.get_account()
                
                total_value_usd = Decimal("0")
                
                # Get all balances
                for balance in account_info['balances']:
                    asset = balance['asset']
                    free = Decimal(balance['free'])
                    locked = Decimal(balance['locked'])
                    total = free + locked
                    
                    if total > 0:
                        # Convert to USD using historical price
                        if asset == 'USDT' or asset == 'USDC' or asset == 'BUSD':
                            # Stablecoins are 1:1 with USD
                            total_value_usd += total
                        elif asset == 'EUR':
                            # EUR fiat balance - convert to USD using historical rate
                            try:
                                from clients.frankfurter_client import FrankfurterClient
                                fx_client = FrankfurterClient()
                                snapshot_date_obj = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).date()
                                eur_to_usd_rate = fx_client.get_exchange_rate(snapshot_date_obj, "EUR", "USD")
                                total_value_usd += total * eur_to_usd_rate
                                self.logger.debug(f"EUR fiat: {total} × {eur_to_usd_rate} = ${total * eur_to_usd_rate}")
                            except Exception as e:
                                self.logger.warning(f"Could not convert EUR to USD: {e}")
                        else:
                            # Get historical price at the timestamp
                            try:
                                symbol = f"{asset}USDT"
                                # Get kline data for the specific timestamp
                                klines = self.client.get_historical_klines(
                                    symbol, 
                                    self.client.KLINE_INTERVAL_1HOUR,
                                    timestamp,
                                    timestamp + 3600000,  # +1 hour
                                    limit=1
                                )
                                if klines:
                                    # Use close price
                                    price = Decimal(klines[0][4])
                                    total_value_usd += total * price
                                    self.logger.debug(f"{asset}: {total} × ${price} = ${total * price}")
                            except Exception as e:
                                self.logger.warning(f"Could not get historical price for {asset}: {e}")
                                # Skip assets we can't price
                                pass
                
                return total_value_usd
                
            except BinanceAPIException as e:
                # Handle rate limiting specifically
                if e.code == -1003 or e.code == 429:
                    wait_time = 60  # Wait 60 seconds for rate limit
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Rate limit exceeded (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise BinanceRateLimitError(
                            "Binance API rate limit exceeded. Please wait a few minutes and try again."
                        )
                else:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        self.logger.warning(f"Failed to retrieve portfolio value (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"Failed to retrieve portfolio value after {max_retries} attempts: {e}")
                        raise BinanceAPIError(f"Failed to retrieve portfolio value: {e.message}")
            
            except BinanceRequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Network error retrieving portfolio value (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Network error after {max_retries} attempts: {e}")
                    raise BinanceNetworkError(f"Network error retrieving portfolio value: {e}")
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request timeout after {max_retries} attempts")
                    raise BinanceNetworkError(
                        f"Request timed out after {max_retries} attempts. Please check your internet connection."
                    )
            
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Connection error after {max_retries} attempts")
                    raise BinanceNetworkError(
                        "Unable to connect to Binance API. Please check your internet connection."
                    )
            
            except Exception as e:
                self.logger.error(f"Unexpected error retrieving portfolio value: {e}")
                raise BinanceAPIError(f"Unexpected error retrieving portfolio value: {e}")
        
        return Decimal("0")
