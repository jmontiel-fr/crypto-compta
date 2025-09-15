"""
Unit tests for FEC account mapping system.
"""

import pytest
from binance_fec_extractor.config.accounts import (
    SystemAccount,
    CRYPTO_ACCOUNTS,
    DEFAULT_CRYPTO_ACCOUNT,
    get_crypto_account,
    get_system_account,
    is_stablecoin,
    is_major_cryptocurrency,
    get_account_category,
    add_crypto_account,
    get_all_crypto_accounts,
    get_all_system_accounts,
    validate_account_number,
    format_account_description,
    get_conversion_account
)


class TestSystemAccount:
    """Test SystemAccount enum."""
    
    def test_system_account_values(self):
        """Test system account enum values."""
        assert SystemAccount.INTERNAL_TRANSFER.account_number == "580"
        assert SystemAccount.INTERNAL_TRANSFER.description == "Mouvement intra-bancaire"
        
        assert SystemAccount.COMMISSIONS.account_number == "6278"
        assert SystemAccount.COMMISSIONS.description == "Commissions"
        
        assert SystemAccount.CONVERSION_GAINS.account_number == "767004"
        assert SystemAccount.CONVERSION_GAINS.description == "Produits nets sur cessions de jeton"
        
        assert SystemAccount.CONVERSION_LOSSES.account_number == "667004"
        assert SystemAccount.CONVERSION_LOSSES.description == "Charges nettes sur cessions de jetons"


class TestCryptoAccounts:
    """Test cryptocurrency account mappings."""
    
    def test_major_stablecoins(self):
        """Test major stablecoin account mappings."""
        assert "USDC" in CRYPTO_ACCOUNTS
        assert "USDT" in CRYPTO_ACCOUNTS
        assert "BUSD" in CRYPTO_ACCOUNTS
        assert "DAI" in CRYPTO_ACCOUNTS
        
        usdc_account, usdc_desc = CRYPTO_ACCOUNTS["USDC"]
        assert usdc_account == "5220011005"
        assert "USDC" in usdc_desc
        assert "VOXOMA" in usdc_desc
    
    def test_major_cryptocurrencies(self):
        """Test major cryptocurrency account mappings."""
        assert "BTC" in CRYPTO_ACCOUNTS
        assert "ETH" in CRYPTO_ACCOUNTS
        assert "BNB" in CRYPTO_ACCOUNTS
        
        btc_account, btc_desc = CRYPTO_ACCOUNTS["BTC"]
        assert btc_account == "5220020188"
        assert "Bitcoin" in btc_desc
        assert "BTC" in btc_desc
    
    def test_altcoins(self):
        """Test altcoin account mappings."""
        assert "ADA" in CRYPTO_ACCOUNTS
        assert "DOT" in CRYPTO_ACCOUNTS
        assert "LINK" in CRYPTO_ACCOUNTS
        assert "SEI" in CRYPTO_ACCOUNTS
        
        sei_account, sei_desc = CRYPTO_ACCOUNTS["SEI"]
        assert sei_account == "5220012289"  # From example FEC file
        assert "Sei" in sei_desc


class TestGetCryptoAccount:
    """Test get_crypto_account function."""
    
    def test_known_cryptocurrency(self):
        """Test getting account for known cryptocurrency."""
        account_num, description = get_crypto_account("BTC")
        assert account_num == "5220020188"
        assert "Bitcoin" in description
        assert "BTC" in description
    
    def test_case_insensitive(self):
        """Test case insensitive symbol lookup."""
        account_num1, desc1 = get_crypto_account("btc")
        account_num2, desc2 = get_crypto_account("BTC")
        account_num3, desc3 = get_crypto_account("Btc")
        
        assert account_num1 == account_num2 == account_num3
        assert desc1 == desc2 == desc3
    
    def test_whitespace_handling(self):
        """Test whitespace handling in symbol."""
        account_num, description = get_crypto_account("  BTC  ")
        assert account_num == "5220020188"
        assert "Bitcoin" in description
    
    def test_unknown_cryptocurrency(self):
        """Test getting account for unknown cryptocurrency."""
        account_num, description = get_crypto_account("UNKNOWN")
        assert account_num == DEFAULT_CRYPTO_ACCOUNT[0]
        assert "UNKNOWN" in description
    
    def test_empty_symbol(self):
        """Test handling of empty symbol."""
        account_num, description = get_crypto_account("")
        assert account_num == DEFAULT_CRYPTO_ACCOUNT[0]


class TestGetSystemAccount:
    """Test get_system_account function."""
    
    def test_internal_transfer_account(self):
        """Test getting internal transfer account."""
        account_num, description = get_system_account(SystemAccount.INTERNAL_TRANSFER)
        assert account_num == "580"
        assert description == "Mouvement intra-bancaire"
    
    def test_commissions_account(self):
        """Test getting commissions account."""
        account_num, description = get_system_account(SystemAccount.COMMISSIONS)
        assert account_num == "6278"
        assert description == "Commissions"
    
    def test_conversion_gains_account(self):
        """Test getting conversion gains account."""
        account_num, description = get_system_account(SystemAccount.CONVERSION_GAINS)
        assert account_num == "767004"
        assert description == "Produits nets sur cessions de jeton"
    
    def test_conversion_losses_account(self):
        """Test getting conversion losses account."""
        account_num, description = get_system_account(SystemAccount.CONVERSION_LOSSES)
        assert account_num == "667004"
        assert description == "Charges nettes sur cessions de jetons"


class TestCryptoCategorization:
    """Test cryptocurrency categorization functions."""
    
    def test_is_stablecoin(self):
        """Test stablecoin identification."""
        assert is_stablecoin("USDC") is True
        assert is_stablecoin("USDT") is True
        assert is_stablecoin("DAI") is True
        assert is_stablecoin("BUSD") is True
        
        assert is_stablecoin("BTC") is False
        assert is_stablecoin("ETH") is False
        assert is_stablecoin("UNKNOWN") is False
    
    def test_is_stablecoin_case_insensitive(self):
        """Test stablecoin identification is case insensitive."""
        assert is_stablecoin("usdc") is True
        assert is_stablecoin("Usdt") is True
        assert is_stablecoin("  USDC  ") is True
    
    def test_is_major_cryptocurrency(self):
        """Test major cryptocurrency identification."""
        assert is_major_cryptocurrency("BTC") is True
        assert is_major_cryptocurrency("ETH") is True
        assert is_major_cryptocurrency("BNB") is True
        
        assert is_major_cryptocurrency("USDC") is False
        assert is_major_cryptocurrency("ADA") is False
        assert is_major_cryptocurrency("UNKNOWN") is False
    
    def test_is_major_cryptocurrency_case_insensitive(self):
        """Test major cryptocurrency identification is case insensitive."""
        assert is_major_cryptocurrency("btc") is True
        assert is_major_cryptocurrency("Eth") is True
        assert is_major_cryptocurrency("  BNB  ") is True
    
    def test_get_account_category(self):
        """Test account category determination."""
        assert get_account_category("USDC") == "stablecoins"
        assert get_account_category("USDT") == "stablecoins"
        
        assert get_account_category("BTC") == "major_crypto"
        assert get_account_category("ETH") == "major_crypto"
        
        assert get_account_category("ADA") == "altcoins"
        assert get_account_category("LINK") == "altcoins"
        assert get_account_category("UNKNOWN") == "altcoins"


class TestAccountManagement:
    """Test account management functions."""
    
    def test_add_crypto_account(self):
        """Test adding new cryptocurrency account."""
        original_accounts = get_all_crypto_accounts()
        
        # Add new account
        add_crypto_account("TEST", "5220099999", "Test Token")
        
        # Verify it was added
        account_num, description = get_crypto_account("TEST")
        assert account_num == "5220099999"
        assert description == "Test Token"
        
        # Clean up - restore original accounts
        CRYPTO_ACCOUNTS.clear()
        CRYPTO_ACCOUNTS.update(original_accounts)
    
    def test_add_crypto_account_case_handling(self):
        """Test adding cryptocurrency account with case handling."""
        original_accounts = get_all_crypto_accounts()
        
        # Add account with lowercase symbol
        add_crypto_account("test", "5220099999", "Test Token")
        
        # Verify it can be retrieved with different cases
        account_num1, desc1 = get_crypto_account("TEST")
        account_num2, desc2 = get_crypto_account("test")
        
        assert account_num1 == account_num2 == "5220099999"
        assert desc1 == desc2 == "Test Token"
        
        # Clean up
        CRYPTO_ACCOUNTS.clear()
        CRYPTO_ACCOUNTS.update(original_accounts)
    
    def test_get_all_crypto_accounts(self):
        """Test getting all cryptocurrency accounts."""
        all_accounts = get_all_crypto_accounts()
        
        assert isinstance(all_accounts, dict)
        assert "BTC" in all_accounts
        assert "USDC" in all_accounts
        assert len(all_accounts) > 0
        
        # Verify it's a copy (modifying it doesn't affect original)
        original_count = len(CRYPTO_ACCOUNTS)
        all_accounts["NEW_TOKEN"] = ("123", "New Token")
        assert len(CRYPTO_ACCOUNTS) == original_count
    
    def test_get_all_system_accounts(self):
        """Test getting all system accounts."""
        all_accounts = get_all_system_accounts()
        
        assert isinstance(all_accounts, dict)
        assert "INTERNAL_TRANSFER" in all_accounts
        assert "COMMISSIONS" in all_accounts
        assert "CONVERSION_GAINS" in all_accounts
        assert "CONVERSION_LOSSES" in all_accounts
        
        # Verify values
        assert all_accounts["INTERNAL_TRANSFER"] == ("580", "Mouvement intra-bancaire")
        assert all_accounts["COMMISSIONS"] == ("6278", "Commissions")


class TestAccountValidation:
    """Test account validation functions."""
    
    def test_validate_account_number_valid(self):
        """Test validation of valid account numbers."""
        assert validate_account_number("580") is True
        assert validate_account_number("6278") is True
        assert validate_account_number("5220011005") is True
        assert validate_account_number("767004") is True
    
    def test_validate_account_number_invalid(self):
        """Test validation of invalid account numbers."""
        assert validate_account_number("") is False
        assert validate_account_number(None) is False
        assert validate_account_number("12") is False  # Too short
        assert validate_account_number("12345678901") is False  # Too long
        assert validate_account_number("ABC123") is False  # Non-numeric
        assert validate_account_number("123.45") is False  # Contains decimal
        assert validate_account_number("123 456") is False  # Contains space
    
    def test_validate_account_number_whitespace(self):
        """Test validation handles whitespace."""
        assert validate_account_number("  580  ") is True
        assert validate_account_number("\t6278\n") is True


class TestAccountFormatting:
    """Test account formatting functions."""
    
    def test_format_account_description_known_crypto(self):
        """Test formatting description for known cryptocurrency."""
        description = format_account_description("BTC")
        assert "Bitcoin" in description
        assert "BTC" in description
        assert "VOXOMA" in description
        
        description = format_account_description("USDC")
        assert "Usd Coin" in description
        assert "USDC" in description
    
    def test_format_account_description_unknown_crypto(self):
        """Test formatting description for unknown cryptocurrency."""
        description = format_account_description("UNKNOWN")
        assert "UNKNOWN" in description
        assert "VOXOMA" in description
    
    def test_format_account_description_custom_account_name(self):
        """Test formatting description with custom account name."""
        description = format_account_description("BTC", "CUSTOM_ACCOUNT")
        assert "Bitcoin" in description
        assert "BTC" in description
        assert "CUSTOM_ACCOUNT" in description
        assert "VOXOMA" not in description
    
    def test_format_account_description_case_handling(self):
        """Test formatting description handles case properly."""
        description1 = format_account_description("btc")
        description2 = format_account_description("BTC")
        
        assert description1 == description2
        assert "Bitcoin" in description1
        assert "BTC" in description1


class TestConversionAccounts:
    """Test conversion account functions."""
    
    def test_get_conversion_account_gains(self):
        """Test getting conversion account for gains."""
        account_num, description = get_conversion_account(is_gain=True)
        assert account_num == "767004"
        assert description == "Produits nets sur cessions de jeton"
    
    def test_get_conversion_account_losses(self):
        """Test getting conversion account for losses."""
        account_num, description = get_conversion_account(is_gain=False)
        assert account_num == "667004"
        assert description == "Charges nettes sur cessions de jetons"