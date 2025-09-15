"""
Exchange rate service for FEC extractor with ECB API integration.

This module provides exchange rate retrieval from multiple sources with ECB as primary,
caching, and fallback mechanisms for reliable USD/EUR conversion.
"""

import time
import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass
from pathlib import Path
import logging
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

from ..config.settings import Config


@dataclass
class ExchangeRateError(Exception):
    """Base exception for exchange rate errors."""
    message: str
    source: Optional[str] = None
    
    def __str__(self):
        return f"Exchange Rate Error ({self.source}): {self.message}"


@dataclass
class ECBAPIError(ExchangeRateError):
    """Exception for ECB API errors."""
    pass


@dataclass
class RateNotFoundError(ExchangeRateError):
    """Exception when exchange rate is not found."""
    date: Optional[str] = None
    currency_pair: Optional[str] = None


@dataclass
class ExchangeRate:
    """Exchange rate data structure."""
    date: date
    rate: float
    source: str
    currency_pair: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'date': self.date.isoformat(),
            'rate': self.rate,
            'source': self.source,
            'currency_pair': self.currency_pair,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExchangeRate':
        """Create from dictionary."""
        return cls(
            date=datetime.fromisoformat(data['date']).date(),
            rate=float(data['rate']),
            source=data['source'],
            currency_pair=data['currency_pair'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class ECBClient:
    """European Central Bank API client for official USD/EUR exchange rates."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize ECB client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.base_url = "https://sdw-wsrest.ecb.europa.eu/service/data/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/vnd.sdmx.data+xml;version=2.1',
            'User-Agent': 'Binance-FEC-Extractor/1.0'
        })
        self.logger = logging.getLogger(__name__)
    
    def get_usd_eur_rate(self, target_date: date) -> Optional[ExchangeRate]:
        """
        Get USD/EUR exchange rate from ECB for specific date.
        
        Args:
            target_date: Date for which to get the rate
            
        Returns:
            ExchangeRate object or None if not found
            
        Raises:
            ECBAPIError: If API request fails
        """
        try:
            # Format date for ECB API (YYYY-MM-DD)
            date_str = target_date.strftime('%Y-%m-%d')
            
            # ECB API endpoint for USD/EUR daily rates
            # EXR = Exchange Rates, D = Daily, USD = US Dollar, EUR = Euro, SP00 = Spot, A = Average
            endpoint = f"EXR/D.USD.EUR.SP00.A?startPeriod={date_str}&endPeriod={date_str}"
            url = urljoin(self.base_url, endpoint)
            
            self.logger.debug(f"Requesting ECB rate for {date_str}: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse XML response
            rate = self._parse_ecb_xml_response(response.text, target_date)
            
            if rate:
                self.logger.debug(f"Retrieved ECB rate for {date_str}: {rate.rate}")
                return rate
            else:
                self.logger.debug(f"No ECB rate found for {date_str}")
                return None
                
        except requests.exceptions.RequestException as e:
            raise ECBAPIError(f"ECB API request failed: {e}", source="ECB")
        except Exception as e:
            raise ECBAPIError(f"Error parsing ECB response: {e}", source="ECB")
    
    def _parse_ecb_xml_response(self, xml_content: str, target_date: date) -> Optional[ExchangeRate]:
        """
        Parse ECB XML response to extract exchange rate.
        
        Args:
            xml_content: XML response content
            target_date: Target date for the rate
            
        Returns:
            ExchangeRate object or None if not found
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Define namespaces used in ECB XML
            namespaces = {
                'message': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
                'generic': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic'
            }
            
            # Find observation data
            observations = root.findall('.//generic:Obs', namespaces)
            
            for obs in observations:
                # Get time period
                time_elem = obs.find('.//generic:ObsDimension[@id="TIME_PERIOD"]', namespaces)
                if time_elem is None:
                    continue
                
                obs_date_str = time_elem.get('value')
                if not obs_date_str:
                    continue
                
                # Parse date
                try:
                    obs_date = datetime.strptime(obs_date_str, '%Y-%m-%d').date()
                except ValueError:
                    continue
                
                # Check if this is the date we want
                if obs_date != target_date:
                    continue
                
                # Get exchange rate value
                value_elem = obs.find('.//generic:ObsValue', namespaces)
                if value_elem is None:
                    continue
                
                rate_str = value_elem.get('value')
                if not rate_str:
                    continue
                
                try:
                    rate_value = float(rate_str)
                    return ExchangeRate(
                        date=target_date,
                        rate=rate_value,
                        source="ECB",
                        currency_pair="USD/EUR",
                        timestamp=datetime.now()
                    )
                except ValueError:
                    continue
            
            return None
            
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse ECB XML response: {e}")
            return None
    
    def get_latest_usd_eur_rate(self) -> Optional[ExchangeRate]:
        """
        Get the latest available USD/EUR rate from ECB.
        
        Returns:
            Latest ExchangeRate or None if not found
        """
        # Try the last 10 business days to find the latest rate
        current_date = date.today()
        
        for i in range(10):
            check_date = current_date - timedelta(days=i)
            
            # Skip weekends (ECB doesn't publish rates on weekends)
            if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
            
            try:
                rate = self.get_usd_eur_rate(check_date)
                if rate:
                    return rate
            except ECBAPIError:
                continue
        
        return None


class ExchangeRateAPIClient:
    """Free ExchangeRate-API client with no request limits."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize ExchangeRate-API client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.base_url = "https://api.exchangerate-api.com/v4/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Binance-FEC-Extractor/1.0'
        })
        self.logger = logging.getLogger(__name__)
    
    def get_usd_eur_rate(self, target_date: date) -> Optional[ExchangeRate]:
        """
        Get USD/EUR rate from ExchangeRate-API for specific date.
        
        Args:
            target_date: Date for which to get the rate
            
        Returns:
            ExchangeRate object or None if not found
        """
        try:
            # For historical data, use the historical endpoint
            date_str = target_date.strftime('%Y-%m-%d')
            endpoint = f"history/USD/{date_str}"
            url = urljoin(self.base_url, endpoint)
            
            self.logger.debug(f"Requesting ExchangeRate-API rate for {date_str}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            eur_rate = rates.get('EUR')
            
            if eur_rate:
                # ExchangeRate-API gives EUR per USD, we need USD per EUR
                usd_eur_rate = 1.0 / float(eur_rate)
                
                return ExchangeRate(
                    date=target_date,
                    rate=usd_eur_rate,
                    source="ExchangeRate-API",
                    currency_pair="USD/EUR",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"ExchangeRate-API error: {e}")
            return None
    
    def get_latest_usd_eur_rate(self) -> Optional[ExchangeRate]:
        """
        Get latest USD/EUR rate from ExchangeRate-API.
        
        Returns:
            Latest ExchangeRate or None if not found
        """
        try:
            endpoint = "latest/USD"
            url = urljoin(self.base_url, endpoint)
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('rates', {})
            eur_rate = rates.get('EUR')
            
            if eur_rate:
                usd_eur_rate = 1.0 / float(eur_rate)
                
                return ExchangeRate(
                    date=date.today(),
                    rate=usd_eur_rate,
                    source="ExchangeRate-API",
                    currency_pair="USD/EUR",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"ExchangeRate-API latest rate error: {e}")
            return None


class FreeCurrencyAPIClient:
    """Free FreeCurrencyAPI client with no request limits."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize FreeCurrencyAPI client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.base_url = "https://api.freecurrencyapi.com/v1/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Binance-FEC-Extractor/1.0'
        })
        self.logger = logging.getLogger(__name__)
    
    def get_usd_eur_rate(self, target_date: date) -> Optional[ExchangeRate]:
        """
        Get USD/EUR rate from FreeCurrencyAPI for specific date.
        
        Args:
            target_date: Date for which to get the rate
            
        Returns:
            ExchangeRate object or None if not found
        """
        try:
            # FreeCurrencyAPI historical endpoint
            date_str = target_date.strftime('%Y-%m-%d')
            endpoint = f"historical?apikey=fca_live_free&date={date_str}&base_currency=USD&currencies=EUR"
            url = urljoin(self.base_url, endpoint)
            
            self.logger.debug(f"Requesting FreeCurrencyAPI rate for {date_str}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('data', {}).get(date_str, {})
            eur_rate = rates.get('EUR')
            
            if eur_rate:
                # FreeCurrencyAPI gives EUR per USD, we need USD per EUR
                usd_eur_rate = 1.0 / float(eur_rate)
                
                return ExchangeRate(
                    date=target_date,
                    rate=usd_eur_rate,
                    source="FreeCurrencyAPI",
                    currency_pair="USD/EUR",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"FreeCurrencyAPI error: {e}")
            return None


class CoinbaseClient:
    """Coinbase API client for exchange rates (no rate limits on public endpoints)."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize Coinbase client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.base_url = "https://api.coinbase.com/v2/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Binance-FEC-Extractor/1.0'
        })
        self.logger = logging.getLogger(__name__)
    
    def get_usd_eur_rate(self, target_date: date) -> Optional[ExchangeRate]:
        """
        Get USD/EUR rate from Coinbase for specific date.
        
        Args:
            target_date: Date for which to get the rate
            
        Returns:
            ExchangeRate object or None if not found
        """
        try:
            # Coinbase doesn't have historical data for fiat pairs in free API
            # Use current rate as approximation for recent dates
            if (date.today() - target_date).days > 7:
                return None
            
            endpoint = "exchange-rates?currency=USD"
            url = urljoin(self.base_url, endpoint)
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            rates = data.get('data', {}).get('rates', {})
            eur_rate = rates.get('EUR')
            
            if eur_rate:
                # Coinbase gives EUR per USD, we need USD per EUR
                usd_eur_rate = 1.0 / float(eur_rate)
                
                return ExchangeRate(
                    date=target_date,
                    rate=usd_eur_rate,
                    source="Coinbase",
                    currency_pair="USD/EUR",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Coinbase API error: {e}")
            return None


class CoinGeckoClient:
    """CoinGecko API client for cryptocurrency prices (used sparingly as last resort)."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize CoinGecko client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.base_url = "https://api.coingecko.com/api/v3/"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Binance-FEC-Extractor/1.0'
        })
        self.logger = logging.getLogger(__name__)
    
    def get_usd_eur_rate(self, target_date: date) -> Optional[ExchangeRate]:
        """
        Get USD/EUR rate from CoinGecko for specific date (used sparingly).
        
        Args:
            target_date: Date for which to get the rate
            
        Returns:
            ExchangeRate object or None if not found
        """
        # Only use CoinGecko for very recent dates to minimize API usage
        if (date.today() - target_date).days > 3:
            return None
            
        try:
            # Use simple price endpoint instead of historical to reduce API calls
            endpoint = "simple/price?ids=tether&vs_currencies=usd,eur"
            url = urljoin(self.base_url, endpoint)
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            tether_data = data.get('tether', {})
            
            usd_price = tether_data.get('usd', 1.0)
            eur_price = tether_data.get('eur')
            
            if eur_price and eur_price > 0:
                usd_eur_rate = usd_price / eur_price
                
                return ExchangeRate(
                    date=target_date,
                    rate=usd_eur_rate,
                    source="CoinGecko",
                    currency_pair="USD/EUR",
                    timestamp=datetime.now()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"CoinGecko API error: {e}")
            return None
    
    def get_crypto_usd_price(self, symbol: str, target_date: date) -> Optional[float]:
        """
        Get cryptocurrency price in USD for specific date.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'bitcoin', 'ethereum')
            target_date: Date for which to get the price
            
        Returns:
            Price in USD or None if not found
        """
        try:
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'BNB': 'binancecoin',
                'ADA': 'cardano',
                'DOT': 'polkadot',
                'LINK': 'chainlink',
                'LTC': 'litecoin',
                'XRP': 'ripple',
                'SOL': 'solana',
                'MATIC': 'matic-network',
                'AVAX': 'avalanche-2',
                'ATOM': 'cosmos',
                'UNI': 'uniswap',
                'AAVE': 'aave'
            }
            
            coin_id = symbol_map.get(symbol.upper(), symbol.lower())
            date_str = target_date.strftime('%d-%m-%Y')
            
            endpoint = f"coins/{coin_id}/history?date={date_str}"
            url = urljoin(self.base_url, endpoint)
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            market_data = data.get('market_data', {})
            current_price = market_data.get('current_price', {})
            
            return current_price.get('usd')
            
        except Exception as e:
            self.logger.error(f"Error getting {symbol} price from CoinGecko: {e}")
            return None


class ExchangeRateService:
    """
    Main exchange rate service with ECB primary source and fallback mechanisms.
    """
    
    def __init__(self, config: Config):
        """
        Initialize exchange rate service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.cache_duration = config.exchange_rates.cache_duration
        self.max_rate_age_days = getattr(config.exchange_rates, 'max_rate_age_days', 5)
        
        # Initialize clients
        self.ecb_client = ECBClient(timeout=config.api.timeout)
        self.exchangerate_api_client = ExchangeRateAPIClient(timeout=config.api.timeout)
        self.freecurrency_api_client = FreeCurrencyAPIClient(timeout=config.api.timeout)
        self.coinbase_client = CoinbaseClient(timeout=config.api.timeout)
        self.coingecko_client = CoinGeckoClient(timeout=config.api.timeout)  # Last resort
        
        # Cache setup
        self.cache_file = Path(config.output.directory) / "exchange_rate_cache.json"
        self.rate_cache: Dict[str, ExchangeRate] = {}
        self.load_cache()
        
        self.logger = logging.getLogger(__name__)
    
    def get_usd_eur_rate(self, target_date: date) -> ExchangeRate:
        """
        Get USD/EUR exchange rate for specific date with fallback logic.
        
        Args:
            target_date: Date for which to get the rate
            
        Returns:
            ExchangeRate object
            
        Raises:
            RateNotFoundError: If no rate can be found
        """
        cache_key = f"USD/EUR_{target_date.isoformat()}"
        
        # Check cache first
        if cache_key in self.rate_cache:
            cached_rate = self.rate_cache[cache_key]
            if self._is_cache_valid(cached_rate):
                self.logger.debug(f"Using cached USD/EUR rate for {target_date}")
                return cached_rate
        
        # Try ECB first (primary source)
        try:
            rate = self.ecb_client.get_usd_eur_rate(target_date)
            if rate:
                self._cache_rate(cache_key, rate)
                return rate
        except ECBAPIError as e:
            self.logger.warning(f"ECB API failed for {target_date}: {e}")
        
        # Try to find closest ECB rate within max_rate_age_days
        closest_rate = self._find_closest_ecb_rate(target_date)
        if closest_rate:
            self.logger.info(f"Using closest ECB rate from {closest_rate.date} for {target_date}")
            # Cache with original date for future lookups
            self._cache_rate(cache_key, ExchangeRate(
                date=target_date,
                rate=closest_rate.rate,
                source=f"ECB (from {closest_rate.date})",
                currency_pair="USD/EUR",
                timestamp=datetime.now()
            ))
            return closest_rate
        
        # Try free fallback sources (no rate limits)
        free_sources = [
            ('exchangerate-api', self.exchangerate_api_client),
            ('freecurrency-api', self.freecurrency_api_client),
            ('coinbase', self.coinbase_client),
        ]
        
        for source_name, client in free_sources:
            try:
                rate = client.get_usd_eur_rate(target_date)
                if rate:
                    self.logger.info(f"Using free fallback source {source_name} for {target_date}")
                    self._cache_rate(cache_key, rate)
                    return rate
            except Exception as e:
                self.logger.warning(f"Free fallback source {source_name} failed for {target_date}: {e}")
        
        # Try configured fallback sources
        for source in self.config.exchange_rates.fallback_sources:
            try:
                rate = None
                
                if source.lower() == 'exchangerate-api':
                    rate = self.exchangerate_api_client.get_usd_eur_rate(target_date)
                elif source.lower() == 'freecurrency-api':
                    rate = self.freecurrency_api_client.get_usd_eur_rate(target_date)
                elif source.lower() == 'coinbase':
                    rate = self.coinbase_client.get_usd_eur_rate(target_date)
                elif source.lower() == 'coingecko':
                    # Use CoinGecko sparingly as last resort
                    rate = self.coingecko_client.get_usd_eur_rate(target_date)
                else:
                    self.logger.warning(f"Unknown fallback source: {source}")
                    continue
                
                if rate:
                    self.logger.info(f"Using configured fallback source {source} for {target_date}")
                    self._cache_rate(cache_key, rate)
                    return rate
                    
            except Exception as e:
                self.logger.warning(f"Configured fallback source {source} failed for {target_date}: {e}")
        
        # If all else fails, raise error
        raise RateNotFoundError(
            f"No USD/EUR rate found for {target_date}",
            date=target_date.isoformat(),
            currency_pair="USD/EUR"
        )
    
    def _find_closest_ecb_rate(self, target_date: date) -> Optional[ExchangeRate]:
        """
        Find the closest available ECB rate within max_rate_age_days.
        
        Args:
            target_date: Target date
            
        Returns:
            Closest ExchangeRate or None
        """
        # Try dates before and after the target date
        for days_offset in range(1, self.max_rate_age_days + 1):
            # Try earlier dates first (more recent rates are preferred)
            for date_offset in [-days_offset, days_offset]:
                check_date = target_date + timedelta(days=date_offset)
                
                # Don't check future dates beyond today
                if check_date > date.today():
                    continue
                
                # Skip weekends for ECB
                if check_date.weekday() >= 5:
                    continue
                
                try:
                    rate = self.ecb_client.get_usd_eur_rate(check_date)
                    if rate:
                        return rate
                except ECBAPIError:
                    continue
        
        return None
    
    def convert_crypto_to_usd(self, amount: float, crypto_symbol: str, 
                            transaction_date: date) -> Tuple[float, float]:
        """
        Convert cryptocurrency amount to USD.
        
        Args:
            amount: Amount in cryptocurrency
            crypto_symbol: Cryptocurrency symbol
            transaction_date: Date of transaction
            
        Returns:
            Tuple of (usd_amount, crypto_usd_price)
            
        Raises:
            RateNotFoundError: If crypto price cannot be found
        """
        # For stablecoins, assume 1:1 with USD
        stablecoins = {'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'FDUSD', 'USDP'}
        if crypto_symbol.upper() in stablecoins:
            return amount, 1.0
        
        # Try to get crypto price from free sources first
        crypto_usd_price = None
        
        # For major cryptocurrencies, try to use the USD/EUR rate as approximation
        # This is a simplified approach for free solution
        major_cryptos = {
            'BTC': 50000.0,   # Approximate BTC price (will be updated with real data)
            'ETH': 3000.0,    # Approximate ETH price
            'BNB': 300.0,     # Approximate BNB price
        }
        
        if crypto_symbol.upper() in major_cryptos:
            # Use approximate price - in a real implementation, you'd want to
            # get this from Binance API or cache recent prices
            crypto_usd_price = major_cryptos[crypto_symbol.upper()]
            self.logger.warning(f"Using approximate price for {crypto_symbol}: ${crypto_usd_price}")
        else:
            # For other cryptos, try CoinGecko as last resort
            try:
                crypto_usd_price = self.coingecko_client.get_crypto_usd_price(crypto_symbol, transaction_date)
            except Exception as e:
                self.logger.error(f"Failed to get {crypto_symbol} price from CoinGecko: {e}")
        
        if crypto_usd_price is None:
            # Fallback: ask for manual input
            self.logger.warning(f"No automatic price found for {crypto_symbol} on {transaction_date}")
            try:
                price_input = input(f"Please enter USD price for {crypto_symbol} on {transaction_date}: ").strip()
                if price_input:
                    crypto_usd_price = float(price_input)
                    self.logger.info(f"Manual price entered for {crypto_symbol}: ${crypto_usd_price}")
            except (ValueError, KeyboardInterrupt):
                pass
        
        if crypto_usd_price is None:
            raise RateNotFoundError(
                f"No USD price found for {crypto_symbol} on {transaction_date}",
                date=transaction_date.isoformat(),
                currency_pair=f"{crypto_symbol}/USD"
            )
        
        usd_amount = amount * crypto_usd_price
        return usd_amount, crypto_usd_price
    
    def convert_usd_to_eur(self, usd_amount: float, transaction_date: date) -> Tuple[float, ExchangeRate]:
        """
        Convert USD amount to EUR using ECB rates.
        
        Args:
            usd_amount: Amount in USD
            transaction_date: Date of transaction
            
        Returns:
            Tuple of (eur_amount, exchange_rate)
        """
        exchange_rate = self.get_usd_eur_rate(transaction_date)
        eur_amount = usd_amount * exchange_rate.rate
        return eur_amount, exchange_rate
    
    def convert_crypto_to_eur(self, amount: float, crypto_symbol: str, 
                            transaction_date: date) -> Tuple[float, float, ExchangeRate]:
        """
        Convert cryptocurrency amount to EUR via USD.
        
        Args:
            amount: Amount in cryptocurrency
            crypto_symbol: Cryptocurrency symbol
            transaction_date: Date of transaction
            
        Returns:
            Tuple of (eur_amount, usd_amount, exchange_rate)
        """
        # Step 1: Convert crypto to USD
        usd_amount, crypto_usd_price = self.convert_crypto_to_usd(amount, crypto_symbol, transaction_date)
        
        # Step 2: Convert USD to EUR
        eur_amount, exchange_rate = self.convert_usd_to_eur(usd_amount, transaction_date)
        
        return eur_amount, usd_amount, exchange_rate
    
    def _is_cache_valid(self, rate: ExchangeRate) -> bool:
        """Check if cached rate is still valid."""
        age = datetime.now() - rate.timestamp
        return age.total_seconds() < self.cache_duration
    
    def _cache_rate(self, key: str, rate: ExchangeRate) -> None:
        """Cache exchange rate."""
        self.rate_cache[key] = rate
        self.save_cache()
    
    def load_cache(self) -> None:
        """Load exchange rate cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                for key, rate_data in cache_data.items():
                    try:
                        self.rate_cache[key] = ExchangeRate.from_dict(rate_data)
                    except Exception as e:
                        self.logger.warning(f"Failed to load cached rate {key}: {e}")
                
                self.logger.debug(f"Loaded {len(self.rate_cache)} cached exchange rates")
        except Exception as e:
            self.logger.warning(f"Failed to load exchange rate cache: {e}")
            self.rate_cache = {}
    
    def save_cache(self) -> None:
        """Save exchange rate cache to file."""
        try:
            # Ensure output directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert cache to serializable format
            cache_data = {
                key: rate.to_dict() 
                for key, rate in self.rate_cache.items()
                if self._is_cache_valid(rate)  # Only save valid cache entries
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            self.logger.debug(f"Saved {len(cache_data)} exchange rates to cache")
        except Exception as e:
            self.logger.error(f"Failed to save exchange rate cache: {e}")
    
    def clear_cache(self) -> None:
        """Clear exchange rate cache."""
        self.rate_cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        self.logger.info("Exchange rate cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        valid_entries = sum(1 for rate in self.rate_cache.values() if self._is_cache_valid(rate))
        
        # Calculate cache hit statistics
        cache_sources = {}
        for rate in self.rate_cache.values():
            source = rate.source
            cache_sources[source] = cache_sources.get(source, 0) + 1
        
        return {
            'total_entries': len(self.rate_cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.rate_cache) - valid_entries,
            'cache_file': str(self.cache_file),
            'cache_duration': self.cache_duration,
            'sources': cache_sources,
            'cache_file_size': self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }
    
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, rate in self.rate_cache.items()
            if not self._is_cache_valid(rate)
        ]
        
        for key in expired_keys:
            del self.rate_cache[key]
        
        if expired_keys:
            self.save_cache()
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def preload_rates_for_date_range(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Preload exchange rates for a date range to improve performance.
        
        Args:
            start_date: Start date for preloading
            end_date: End date for preloading
            
        Returns:
            Dictionary with preloading statistics
        """
        self.logger.info(f"Preloading exchange rates from {start_date} to {end_date}")
        
        stats = {
            'requested_dates': 0,
            'cache_hits': 0,
            'ecb_success': 0,
            'fallback_success': 0,
            'failures': 0,
            'errors': []
        }
        
        current_date = start_date
        while current_date <= end_date:
            stats['requested_dates'] += 1
            
            try:
                cache_key = f"USD/EUR_{current_date.isoformat()}"
                
                # Check if already cached
                if cache_key in self.rate_cache and self._is_cache_valid(self.rate_cache[cache_key]):
                    stats['cache_hits'] += 1
                else:
                    # Try to get rate
                    rate = self.get_usd_eur_rate(current_date)
                    if rate.source.startswith("ECB"):
                        stats['ecb_success'] += 1
                    else:
                        stats['fallback_success'] += 1
                        
            except RateNotFoundError as e:
                stats['failures'] += 1
                stats['errors'].append(f"{current_date}: {e.message}")
                self.logger.warning(f"Failed to preload rate for {current_date}: {e}")
            except Exception as e:
                stats['failures'] += 1
                stats['errors'].append(f"{current_date}: {str(e)}")
                self.logger.error(f"Error preloading rate for {current_date}: {e}")
            
            current_date += timedelta(days=1)
        
        self.logger.info(f"Preloading complete: {stats['ecb_success']} ECB, {stats['fallback_success']} fallback, {stats['cache_hits']} cached, {stats['failures']} failed")
        return stats
    
    def get_manual_rate_input(self, target_date: date, currency_pair: str = "USD/EUR") -> Optional[ExchangeRate]:
        """
        Get manual rate input from user when automatic retrieval fails.
        
        Args:
            target_date: Date for the rate
            currency_pair: Currency pair (default: USD/EUR)
            
        Returns:
            ExchangeRate with manual input or None if cancelled
        """
        try:
            print(f"\nAutomatic exchange rate retrieval failed for {target_date}")
            print(f"Please provide manual {currency_pair} exchange rate for {target_date}")
            print("(Press Enter to skip this rate)")
            
            rate_input = input(f"{currency_pair} rate for {target_date}: ").strip()
            
            if not rate_input:
                return None
            
            try:
                rate_value = float(rate_input)
                if rate_value <= 0:
                    print("Error: Exchange rate must be positive")
                    return None
                
                manual_rate = ExchangeRate(
                    date=target_date,
                    rate=rate_value,
                    source="Manual Input",
                    currency_pair=currency_pair,
                    timestamp=datetime.now()
                )
                
                # Cache the manual rate
                cache_key = f"{currency_pair}_{target_date.isoformat()}"
                self._cache_rate(cache_key, manual_rate)
                
                self.logger.info(f"Manual rate entered: {rate_value} for {target_date}")
                return manual_rate
                
            except ValueError:
                print("Error: Invalid number format")
                return None
                
        except KeyboardInterrupt:
            print("\nManual input cancelled")
            return None
        except Exception as e:
            self.logger.error(f"Error in manual rate input: {e}")
            return None
    
    def validate_rate_reasonableness(self, rate: ExchangeRate, tolerance: float = 0.2) -> bool:
        """
        Validate that an exchange rate is reasonable compared to recent rates.
        
        Args:
            rate: Exchange rate to validate
            tolerance: Tolerance for rate variation (default: 20%)
            
        Returns:
            True if rate seems reasonable
        """
        try:
            # Get recent rates for comparison
            recent_rates = []
            check_date = rate.date
            
            for i in range(1, 8):  # Check last 7 days
                check_date = rate.date - timedelta(days=i)
                cache_key = f"{rate.currency_pair}_{check_date.isoformat()}"
                
                if cache_key in self.rate_cache:
                    cached_rate = self.rate_cache[cache_key]
                    if self._is_cache_valid(cached_rate):
                        recent_rates.append(cached_rate.rate)
                
                if len(recent_rates) >= 3:  # Enough data points
                    break
            
            if not recent_rates:
                # No recent data, assume reasonable
                return True
            
            avg_rate = sum(recent_rates) / len(recent_rates)
            variation = abs(rate.rate - avg_rate) / avg_rate
            
            is_reasonable = variation <= tolerance
            
            if not is_reasonable:
                self.logger.warning(
                    f"Rate {rate.rate} for {rate.date} seems unreasonable "
                    f"(avg recent: {avg_rate:.4f}, variation: {variation:.2%})"
                )
            
            return is_reasonable
            
        except Exception as e:
            self.logger.error(f"Error validating rate reasonableness: {e}")
            return True  # Assume reasonable if validation fails
    
    def get_rate_with_validation(self, target_date: date, allow_manual: bool = False) -> ExchangeRate:
        """
        Get exchange rate with validation and optional manual fallback.
        
        Args:
            target_date: Date for the rate
            allow_manual: Whether to allow manual input if automatic fails
            
        Returns:
            Validated ExchangeRate
            
        Raises:
            RateNotFoundError: If no rate can be obtained
        """
        try:
            # Try automatic retrieval
            rate = self.get_usd_eur_rate(target_date)
            
            # Validate reasonableness
            if not self.validate_rate_reasonableness(rate):
                self.logger.warning(f"Rate validation failed for {target_date}, but proceeding")
            
            return rate
            
        except RateNotFoundError:
            if allow_manual:
                manual_rate = self.get_manual_rate_input(target_date)
                if manual_rate:
                    return manual_rate
            
            # Re-raise the original error
            raise