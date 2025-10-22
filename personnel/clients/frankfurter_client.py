"""Frankfurter API client for retrieving historical exchange rates."""

import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

import requests
from utils.logger import get_logger


class FrankfurterAPIError(Exception):
    """Exception raised for Frankfurter API-related errors."""
    pass


class FrankfurterNetworkError(FrankfurterAPIError):
    """Exception raised for network-related errors."""
    pass


class FrankfurterClient:
    """Client for Frankfurter exchange rate API."""
    
    BASE_URL = "https://api.frankfurter.app"
    
    def __init__(self, timeout: int = 10):
        """
        Initialize Frankfurter client.
        
        Args:
            timeout: Request timeout in seconds (default: 10)
        """
        self.timeout = timeout
        self.logger = get_logger()
        self.logger.info("Frankfurter API client initialized")
    
    def get_exchange_rate(self, target_date: date, from_currency: str = "USD", 
                         to_currency: str = "EUR") -> Decimal:
        """
        Get historical exchange rate for a specific date.
        
        If the exact date is unavailable (e.g., weekend or holiday), the method
        will try the nearest dates within 7 days before and after.
        
        Args:
            target_date: Date for exchange rate
            from_currency: Source currency (default: USD)
            to_currency: Target currency (default: EUR)
            
        Returns:
            Exchange rate (e.g., 0.92 means 1 USD = 0.92 EUR)
            
        Raises:
            FrankfurterAPIError: If exchange rate cannot be retrieved
        """
        self.logger.debug(f"Fetching exchange rate for {from_currency}/{to_currency} on {target_date}")
        
        # Try exact date first
        rate = self._fetch_rate_for_date(target_date, from_currency, to_currency)
        if rate is not None:
            self.logger.debug(f"Exchange rate found: {rate}")
            return rate
        
        self.logger.warning(f"Exchange rate not available for {target_date}, trying nearby dates")
        
        # If exact date fails, try nearest dates within 7 days
        for days_offset in range(1, 8):
            # Try earlier date
            earlier_date = target_date - timedelta(days=days_offset)
            rate = self._fetch_rate_for_date(earlier_date, from_currency, to_currency)
            if rate is not None:
                self.logger.warning(f"Using exchange rate from {earlier_date} (±{days_offset} days): {rate}")
                return rate
            
            # Try later date
            later_date = target_date + timedelta(days=days_offset)
            rate = self._fetch_rate_for_date(later_date, from_currency, to_currency)
            if rate is not None:
                self.logger.warning(f"Using exchange rate from {later_date} (±{days_offset} days): {rate}")
                return rate
        
        # If all attempts fail, raise error
        self.logger.error(f"Failed to retrieve exchange rate for {from_currency}/{to_currency} around {target_date}")
        raise FrankfurterAPIError(
            f"Failed to retrieve exchange rate for {from_currency}/{to_currency} "
            f"around date {target_date} (tried ±7 days)"
        )
    
    def _fetch_rate_for_date(self, target_date: date, from_currency: str, 
                            to_currency: str, max_retries: int = 3) -> Optional[Decimal]:
        """
        Fetch exchange rate for a specific date with retry logic.
        
        Args:
            target_date: Date for exchange rate
            from_currency: Source currency
            to_currency: Target currency
            max_retries: Maximum number of retry attempts
            
        Returns:
            Exchange rate as Decimal, or None if date is unavailable
            
        Raises:
            FrankfurterAPIError: If API call fails after retries
        """
        date_str = target_date.strftime("%Y-%m-%d")
        url = f"{self.BASE_URL}/{date_str}"
        
        params = {
            "from": from_currency,
            "to": to_currency
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                
                # If date is not available (404), return None to try another date
                if response.status_code == 404:
                    return None
                
                # Raise exception for other error status codes
                response.raise_for_status()
                
                data = response.json()
                
                # Extract the exchange rate
                if 'rates' in data and to_currency in data['rates']:
                    rate = Decimal(str(data['rates'][to_currency]))
                    return rate
                else:
                    raise FrankfurterAPIError(
                        f"Exchange rate for {to_currency} not found in API response"
                    )
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.warning(f"Request timeout for {date_str} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request timeout after {max_retries} attempts for date {date_str}")
                    raise FrankfurterNetworkError(
                        f"Request to Frankfurter API timed out after {max_retries} attempts. "
                        "Please check your internet connection and try again."
                    )
            
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Connection error for {date_str} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Connection error after {max_retries} attempts: {e}")
                    raise FrankfurterNetworkError(
                        "Unable to connect to Frankfurter API. Please check your internet connection."
                    )
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.warning(f"Request failed for {date_str} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Failed to retrieve exchange rate after {max_retries} attempts: {e}")
                    raise FrankfurterNetworkError(
                        f"Failed to retrieve exchange rate after {max_retries} attempts. "
                        "Please check your internet connection."
                    )
            
            except (ValueError, KeyError) as e:
                self.logger.error(f"Failed to parse API response: {e}")
                raise FrankfurterAPIError(f"Failed to parse API response: {e}")
        
        return None
