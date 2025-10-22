"""Unit tests for flat tax calculator."""

import unittest
from decimal import Decimal
from calculators.flat_tax_calculator import FlatTaxCalculator, TaxCalculation


class TestFlatTaxCalculator(unittest.TestCase):
    """Test cases for FlatTaxCalculator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.calculator = FlatTaxCalculator()
    
    def test_deposit_increases_acquisition_cost(self):
        """Test that deposit increases acquisition cost"""
        deposit_amount = Decimal("1000.00")
        
        result = self.calculator.process_deposit(deposit_amount)
        
        self.assertEqual(result.acquisition_cost, Decimal("1000.00"))
        self.assertEqual(result.taxable_gain, Decimal("0"))
        self.assertEqual(result.cumulative_gains, Decimal("0"))
    
    def test_deposit_zero_gain(self):
        """Test that deposit generates zero taxable gain"""
        deposit_amount = Decimal("500.00")
        
        result = self.calculator.process_deposit(deposit_amount)
        
        self.assertEqual(result.taxable_gain, Decimal("0"))
    
    def test_multiple_deposits_cumulative_acquisition_cost(self):
        """Test that multiple deposits accumulate acquisition cost"""
        self.calculator.process_deposit(Decimal("1000.00"))
        result = self.calculator.process_deposit(Decimal("500.00"))
        
        self.assertEqual(result.acquisition_cost, Decimal("1500.00"))
        self.assertEqual(result.taxable_gain, Decimal("0"))
    
    def test_withdrawal_calculates_taxable_gain(self):
        """Test withdrawal processing with known values"""
        # Set up: deposit 1000 EUR
        self.calculator.process_deposit(Decimal("1000.00"))
        
        # Withdraw 500 EUR when portfolio is worth 1500 EUR
        withdrawal_amount = Decimal("500.00")
        portfolio_value = Decimal("1500.00")
        
        result = self.calculator.process_withdrawal(withdrawal_amount, portfolio_value)
        
        # Expected calculation:
        # Withdrawal ratio = 500 / 1500 = 1/3
        # Acquisition cost portion = 1000 * (1/3) = 333.33
        # Taxable gain = 500 - 333.33 = 166.67
        # New acquisition cost = 1000 - 333.33 = 666.67
        
        self.assertEqual(result.taxable_gain, Decimal("166.67"))
        self.assertEqual(result.acquisition_cost, Decimal("666.67"))
        self.assertEqual(result.cumulative_gains, Decimal("166.67"))
    
    def test_withdrawal_reduces_acquisition_cost(self):
        """Test that withdrawal reduces acquisition cost proportionally"""
        # Deposit 2000 EUR
        self.calculator.process_deposit(Decimal("2000.00"))
        
        # Withdraw 1000 EUR when portfolio is worth 3000 EUR
        result = self.calculator.process_withdrawal(Decimal("1000.00"), Decimal("3000.00"))
        
        # Withdrawal ratio = 1000 / 3000 = 1/3
        # Acquisition cost portion = 2000 * (1/3) = 666.67
        # New acquisition cost = 2000 - 666.67 = 1333.33
        
        self.assertEqual(result.acquisition_cost, Decimal("1333.33"))
    
    def test_cumulative_gains_tracking(self):
        """Test that cumulative gains are tracked across multiple withdrawals"""
        # Deposit 1000 EUR
        self.calculator.process_deposit(Decimal("1000.00"))
        
        # First withdrawal: 300 EUR from 1500 EUR portfolio
        result1 = self.calculator.process_withdrawal(Decimal("300.00"), Decimal("1500.00"))
        # Taxable gain = 300 - (1000 * 300/1500) = 300 - 200 = 100
        self.assertEqual(result1.taxable_gain, Decimal("100.00"))
        self.assertEqual(result1.cumulative_gains, Decimal("100.00"))
        
        # Second withdrawal: 200 EUR from 1200 EUR portfolio
        # Acquisition cost is now 800 (1000 - 200)
        result2 = self.calculator.process_withdrawal(Decimal("200.00"), Decimal("1200.00"))
        # Taxable gain = 200 - (800 * 200/1200) = 200 - 133.33 = 66.67
        self.assertEqual(result2.taxable_gain, Decimal("66.67"))
        self.assertEqual(result2.cumulative_gains, Decimal("166.67"))
    
    def test_decimal_precision_rounding(self):
        """Test that all calculations maintain 2 decimal precision"""
        # Deposit with odd amount
        self.calculator.process_deposit(Decimal("1234.567"))
        
        # Should be rounded to 2 decimals
        self.assertEqual(self.calculator.acquisition_cost, Decimal("1234.57"))
        
        # Withdrawal that results in repeating decimals
        result = self.calculator.process_withdrawal(Decimal("100.00"), Decimal("333.33"))
        
        # All values should have exactly 2 decimal places
        self.assertEqual(result.acquisition_cost.as_tuple().exponent, -2)
        self.assertEqual(result.taxable_gain.as_tuple().exponent, -2)
        self.assertEqual(result.cumulative_gains.as_tuple().exponent, -2)
    
    def test_withdrawal_with_no_gain(self):
        """Test withdrawal when there's no gain (loss scenario)"""
        # Deposit 1000 EUR
        self.calculator.process_deposit(Decimal("1000.00"))
        
        # Withdraw 500 EUR when portfolio is worth 1000 EUR (no gain)
        result = self.calculator.process_withdrawal(Decimal("500.00"), Decimal("1000.00"))
        
        # Taxable gain = 500 - (1000 * 500/1000) = 500 - 500 = 0
        self.assertEqual(result.taxable_gain, Decimal("0.00"))
    
    def test_complex_scenario_multiple_operations(self):
        """Test complex scenario with multiple deposits and withdrawals"""
        # Deposit 1000 EUR
        self.calculator.process_deposit(Decimal("1000.00"))
        self.assertEqual(self.calculator.acquisition_cost, Decimal("1000.00"))
        
        # Deposit another 500 EUR
        self.calculator.process_deposit(Decimal("500.00"))
        self.assertEqual(self.calculator.acquisition_cost, Decimal("1500.00"))
        
        # Withdraw 600 EUR from 2000 EUR portfolio
        result1 = self.calculator.process_withdrawal(Decimal("600.00"), Decimal("2000.00"))
        # Taxable gain = 600 - (1500 * 600/2000) = 600 - 450 = 150
        self.assertEqual(result1.taxable_gain, Decimal("150.00"))
        self.assertEqual(result1.acquisition_cost, Decimal("1050.00"))
        
        # Deposit 300 EUR
        self.calculator.process_deposit(Decimal("300.00"))
        self.assertEqual(self.calculator.acquisition_cost, Decimal("1350.00"))
        
        # Withdraw 400 EUR from 1700 EUR portfolio
        result2 = self.calculator.process_withdrawal(Decimal("400.00"), Decimal("1700.00"))
        # Taxable gain = 400 - (1350 * 400/1700) = 400 - 317.65 = 82.35
        self.assertEqual(result2.taxable_gain, Decimal("82.35"))
        self.assertEqual(result2.cumulative_gains, Decimal("232.35"))


if __name__ == '__main__':
    unittest.main()
