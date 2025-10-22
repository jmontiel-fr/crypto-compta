"""Unit tests for portfolio value calculator."""

import unittest
from decimal import Decimal
from calculators.portfolio_calculator import PortfolioValueCalculator


class TestPortfolioValueCalculator(unittest.TestCase):
    """Test cases for PortfolioValueCalculator class"""
    
    def test_usd_to_eur_conversion(self):
        """Test basic USD to EUR conversion"""
        portfolio_usd = Decimal("1000.00")
        exchange_rate = Decimal("0.92")
        
        result = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, exchange_rate)
        
        self.assertEqual(result, Decimal("920.00"))
    
    def test_conversion_with_different_rates(self):
        """Test conversion with various exchange rates"""
        portfolio_usd = Decimal("500.00")
        
        # Test with rate 0.85
        result1 = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, Decimal("0.85"))
        self.assertEqual(result1, Decimal("425.00"))
        
        # Test with rate 0.95
        result2 = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, Decimal("0.95"))
        self.assertEqual(result2, Decimal("475.00"))
        
        # Test with rate 1.00
        result3 = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, Decimal("1.00"))
        self.assertEqual(result3, Decimal("500.00"))
    
    def test_rounding_to_2_decimal_places(self):
        """Test that result is rounded to 2 decimal places"""
        portfolio_usd = Decimal("1234.567")
        exchange_rate = Decimal("0.876543")
        
        result = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, exchange_rate)
        
        # Expected: 1234.567 * 0.876543 = 1082.148381 -> 1082.15 (rounded)
        self.assertEqual(result, Decimal("1082.15"))
        
        # Verify it has exactly 2 decimal places
        self.assertEqual(result.as_tuple().exponent, -2)
    
    def test_rounding_half_up(self):
        """Test that rounding uses ROUND_HALF_UP method"""
        # Test case where we need to round up from .5
        portfolio_usd = Decimal("100.00")
        exchange_rate = Decimal("0.925")
        
        result = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, exchange_rate)
        
        # 100 * 0.925 = 92.5 -> should round to 92.50
        self.assertEqual(result, Decimal("92.50"))
    
    def test_large_portfolio_values(self):
        """Test conversion with large portfolio values"""
        portfolio_usd = Decimal("1000000.00")
        exchange_rate = Decimal("0.89")
        
        result = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, exchange_rate)
        
        self.assertEqual(result, Decimal("890000.00"))
    
    def test_small_portfolio_values(self):
        """Test conversion with small portfolio values"""
        portfolio_usd = Decimal("0.50")
        exchange_rate = Decimal("0.92")
        
        result = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, exchange_rate)
        
        self.assertEqual(result, Decimal("0.46"))
    
    def test_zero_portfolio_value(self):
        """Test conversion with zero portfolio value"""
        portfolio_usd = Decimal("0.00")
        exchange_rate = Decimal("0.92")
        
        result = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, exchange_rate)
        
        self.assertEqual(result, Decimal("0.00"))
    
    def test_precision_maintained(self):
        """Test that decimal precision is maintained throughout calculation"""
        # Use values that would lose precision with float arithmetic
        portfolio_usd = Decimal("333.33")
        exchange_rate = Decimal("0.909090")
        
        result = PortfolioValueCalculator.convert_usd_to_eur(portfolio_usd, exchange_rate)
        
        # Verify result is a Decimal with 2 decimal places
        self.assertIsInstance(result, Decimal)
        self.assertEqual(result.as_tuple().exponent, -2)


if __name__ == '__main__':
    unittest.main()
