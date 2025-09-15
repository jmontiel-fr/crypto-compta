"""
FEC account mapping system for Binance FEC Extractor.

This module defines the mapping between cryptocurrencies and French FEC account numbers,
as well as system accounts used for different transaction types.
"""

from typing import Dict, Optional, Tuple
from enum import Enum


class SystemAccount(Enum):
    """System account definitions for FEC entries."""
    
    # Account 580: Mouvement intra-bancaire (Internal bank movements)
    INTERNAL_TRANSFER = ("580", "Mouvement intra-bancaire")
    
    # Account 6278: Commissions (Transaction fees)
    COMMISSIONS = ("6278", "Commissions")
    
    # Account 767004: Produits nets sur cessions de jeton (Net gains on token sales)
    CONVERSION_GAINS = ("767004", "Produits nets sur cessions de jeton")
    
    # Account 667004: Charges nettes sur cessions de jetons (Net losses on token sales)
    CONVERSION_LOSSES = ("667004", "Charges nettes sur cessions de jetons")
    
    def __init__(self, account_number: str, description: str):
        self.account_number = account_number
        self.description = description


# Cryptocurrency to FEC account mapping
# Based on the example FEC file and French accounting standards
CRYPTO_ACCOUNTS: Dict[str, Tuple[str, str]] = {
    # Major stablecoins
    "USDC": ("5220011005", "Jetons detenus en Usd Coin (USDC) du compte VOXOMA"),
    "USDT": ("5220011011", "Jetons detenus en Tether (USDT) du compte VOXOMA"),
    "BUSD": ("5220011012", "Jetons detenus en Binance USD (BUSD) du compte VOXOMA"),
    "DAI": ("5220011013", "Jetons detenus en Dai (DAI) du compte VOXOMA"),
    "TUSD": ("5220011014", "Jetons detenus en TrueUSD (TUSD) du compte VOXOMA"),
    
    # Major cryptocurrencies
    "BTC": ("5220020188", "Jetons detenus en Bitcoin (BTC) du compte Voxoma"),
    "ETH": ("5220020189", "Jetons detenus en Ethereum (ETH) du compte VOXOMA"),
    "BNB": ("5220020190", "Jetons detenus en Binance Coin (BNB) du compte VOXOMA"),
    
    # Popular altcoins (using generic token account pattern)
    "ADA": ("5220012001", "Jetons detenus en Cardano (ADA) du compte VOXOMA"),
    "DOT": ("5220012002", "Jetons detenus en Polkadot (DOT) du compte VOXOMA"),
    "LINK": ("5220012003", "Jetons detenus en Chainlink (LINK) du compte VOXOMA"),
    "LTC": ("5220012004", "Jetons detenus en Litecoin (LTC) du compte VOXOMA"),
    "XRP": ("5220012005", "Jetons detenus en Ripple (XRP) du compte VOXOMA"),
    "SOL": ("5220012006", "Jetons detenus en Solana (SOL) du compte VOXOMA"),
    "MATIC": ("5220012007", "Jetons detenus en Polygon (MATIC) du compte VOXOMA"),
    "AVAX": ("5220012008", "Jetons detenus en Avalanche (AVAX) du compte VOXOMA"),
    "ATOM": ("5220012009", "Jetons detenus en Cosmos (ATOM) du compte VOXOMA"),
    "NEAR": ("5220012010", "Jetons detenus en Near Protocol (NEAR) du compte VOXOMA"),
    
    # DeFi tokens
    "UNI": ("5220012020", "Jetons detenus en Uniswap (UNI) du compte VOXOMA"),
    "AAVE": ("5220012021", "Jetons detenus en Aave (AAVE) du compte VOXOMA"),
    "COMP": ("5220012022", "Jetons detenus en Compound (COMP) du compte VOXOMA"),
    "MKR": ("5220012023", "Jetons detenus en Maker (MKR) du compte VOXOMA"),
    "SNX": ("5220012024", "Jetons detenus en Synthetix (SNX) du compte VOXOMA"),
    
    # Layer 2 and scaling solutions
    "ARB": ("5220012030", "Jetons detenus en Arbitrum (ARB) du compte VOXOMA"),
    "OP": ("5220012031", "Jetons detenus en Optimism (OP) du compte VOXOMA"),
    
    # Meme coins and others
    "DOGE": ("5220012040", "Jetons detenus en Dogecoin (DOGE) du compte VOXOMA"),
    "SHIB": ("5220012041", "Jetons detenus en Shiba Inu (SHIB) du compte VOXOMA"),
    
    # Example from the FEC file
    "SEI": ("5220012289", "Jetons detenus en Sei (SEI) du compte VOXOMA"),
}

# Default account for unknown cryptocurrencies
DEFAULT_CRYPTO_ACCOUNT = ("5220012999", "Jetons detenus en crypto-monnaie du compte VOXOMA")

# Account number ranges for different crypto categories
ACCOUNT_RANGES = {
    "stablecoins": (5220011000, 5220011999),
    "major_crypto": (5220020000, 5220020999),
    "altcoins": (5220012000, 5220012999),
}


def get_crypto_account(symbol: str) -> Tuple[str, str]:
    """
    Get FEC account number and description for a cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'USDC')
        
    Returns:
        Tuple of (account_number, account_description)
    """
    symbol = symbol.upper().strip()
    
    if symbol in CRYPTO_ACCOUNTS:
        return CRYPTO_ACCOUNTS[symbol]
    
    # Return default account for unknown cryptocurrencies
    account_number, base_description = DEFAULT_CRYPTO_ACCOUNT
    description = base_description.replace("crypto-monnaie", f"{symbol}")
    return account_number, description


def get_system_account(account_type: SystemAccount) -> Tuple[str, str]:
    """
    Get system account number and description.
    
    Args:
        account_type: SystemAccount enum value
        
    Returns:
        Tuple of (account_number, account_description)
    """
    return account_type.account_number, account_type.description


def is_stablecoin(symbol: str) -> bool:
    """
    Check if a cryptocurrency is a stablecoin.
    
    Args:
        symbol: Cryptocurrency symbol
        
    Returns:
        True if the symbol is a known stablecoin
    """
    stablecoins = {"USDC", "USDT", "BUSD", "DAI", "TUSD", "FDUSD", "USDP"}
    return symbol.upper().strip() in stablecoins


def is_major_cryptocurrency(symbol: str) -> bool:
    """
    Check if a cryptocurrency is a major cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol
        
    Returns:
        True if the symbol is a major cryptocurrency
    """
    major_cryptos = {"BTC", "ETH", "BNB"}
    return symbol.upper().strip() in major_cryptos


def get_account_category(symbol: str) -> str:
    """
    Get the account category for a cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol
        
    Returns:
        Account category ('stablecoins', 'major_crypto', or 'altcoins')
    """
    if is_stablecoin(symbol):
        return "stablecoins"
    elif is_major_cryptocurrency(symbol):
        return "major_crypto"
    else:
        return "altcoins"


def add_crypto_account(symbol: str, account_number: str, description: str) -> None:
    """
    Add a new cryptocurrency account mapping.
    
    Args:
        symbol: Cryptocurrency symbol
        account_number: FEC account number
        description: Account description
    """
    symbol = symbol.upper().strip()
    CRYPTO_ACCOUNTS[symbol] = (account_number, description)


def get_all_crypto_accounts() -> Dict[str, Tuple[str, str]]:
    """
    Get all cryptocurrency account mappings.
    
    Returns:
        Dictionary of symbol -> (account_number, description) mappings
    """
    return CRYPTO_ACCOUNTS.copy()


def get_all_system_accounts() -> Dict[str, Tuple[str, str]]:
    """
    Get all system account mappings.
    
    Returns:
        Dictionary of account_type -> (account_number, description) mappings
    """
    return {
        account.name: (account.account_number, account.description)
        for account in SystemAccount
    }


def validate_account_number(account_number: str) -> bool:
    """
    Validate that an account number follows French FEC format.
    
    Args:
        account_number: Account number to validate
        
    Returns:
        True if the account number is valid
    """
    if not account_number or not isinstance(account_number, str):
        return False
    
    # Remove any whitespace
    account_number = account_number.strip()
    
    # Check if it's numeric and has appropriate length
    if not account_number.isdigit():
        return False
    
    # French account numbers are typically 3-10 digits
    if len(account_number) < 3 or len(account_number) > 10:
        return False
    
    return True


def format_account_description(symbol: str, account_name: str = "VOXOMA") -> str:
    """
    Format account description for a cryptocurrency.
    
    Args:
        symbol: Cryptocurrency symbol
        account_name: Account name (default: VOXOMA)
        
    Returns:
        Formatted account description
    """
    symbol = symbol.upper().strip()
    
    # Get full name mapping for common cryptocurrencies
    full_names = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "BNB": "Binance Coin",
        "USDC": "Usd Coin",
        "USDT": "Tether",
        "BUSD": "Binance USD",
        "DAI": "Dai",
        "ADA": "Cardano",
        "DOT": "Polkadot",
        "LINK": "Chainlink",
        "LTC": "Litecoin",
        "XRP": "Ripple",
        "SOL": "Solana",
        "MATIC": "Polygon",
        "AVAX": "Avalanche",
        "ATOM": "Cosmos",
        "UNI": "Uniswap",
        "AAVE": "Aave",
        "SEI": "Sei",
    }
    
    full_name = full_names.get(symbol, symbol)
    return f"Jetons detenus en {full_name} ({symbol}) du compte {account_name}"


def get_conversion_account(is_gain: bool) -> Tuple[str, str]:
    """
    Get the appropriate conversion account for gains or losses.
    
    Args:
        is_gain: True for gains, False for losses
        
    Returns:
        Tuple of (account_number, account_description)
    """
    if is_gain:
        return get_system_account(SystemAccount.CONVERSION_GAINS)
    else:
        return get_system_account(SystemAccount.CONVERSION_LOSSES)