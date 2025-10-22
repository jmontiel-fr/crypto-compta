"""
Flat Tax Calculator for French crypto taxation.

This module implements the French flat tax calculation method for cryptocurrency
gains realized through fiat withdrawals.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from dataclasses import dataclass
from utils.logger import get_logger


class TaxCalculationError(Exception):
    """Exception raised for tax calculation errors."""
    pass


@dataclass
class TaxCalculation:
    """Result of tax calculation for an operation"""
    acquisition_cost: Decimal
    taxable_gain: Decimal
    cumulative_gains: Decimal


class FlatTaxCalculator:
    """
    Calculator for French crypto flat tax.
    
    Implements the French taxation method where:
    - Deposits increase the acquisition cost
    - Withdrawals trigger taxable gain calculations based on the proportion
      of the portfolio being withdrawn
    """
    
    def __init__(self):
        """Initialize calculator with zero acquisition cost and cumulative gains"""
        self.acquisition_cost = Decimal("0")
        self.cumulative_gains = Decimal("0")
        self.logger = get_logger()
        self.logger.info("Flat tax calculator initialized")
    
    def _round_to_2_decimals(self, value: Decimal) -> Decimal:
        """
        Round a decimal value to 2 decimal places.
        
        Args:
            value: Decimal value to round
            
        Returns:
            Rounded decimal value
        """
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    def process_deposit(self, amount_eur: Decimal) -> TaxCalculation:
        """
        Process a fiat deposit operation.
        
        When depositing fiat to buy crypto, the acquisition cost increases
        by the deposit amount. No taxable gain is generated.
        
        Args:
            amount_eur: Deposit amount in EUR
            
        Returns:
            TaxCalculation with updated acquisition cost and zero taxable gain
            
        Raises:
            TaxCalculationError: If amount is invalid
        """
        self.logger.debug(f"Processing deposit: €{amount_eur}")
        
        # Validate input
        if amount_eur <= 0:
            self.logger.error(f"Invalid deposit amount: €{amount_eur}")
            raise TaxCalculationError(f"Deposit amount must be positive, got: €{amount_eur}")
        
        try:
            # Increase acquisition cost by deposit amount
            self.acquisition_cost += amount_eur
            self.acquisition_cost = self._round_to_2_decimals(self.acquisition_cost)
            
            # No taxable gain on deposits
            taxable_gain = Decimal("0")
            
            self.logger.debug(f"New acquisition cost: €{self.acquisition_cost}")
            
            return TaxCalculation(
                acquisition_cost=self.acquisition_cost,
                taxable_gain=taxable_gain,
                cumulative_gains=self.cumulative_gains
            )
        except (InvalidOperation, ValueError) as e:
            self.logger.error(f"Invalid decimal operation in deposit processing: {e}")
            raise TaxCalculationError(f"Invalid decimal value in deposit processing: {e}")
    
    def process_withdrawal(self, amount_eur: Decimal, 
                          portfolio_value_eur: Decimal) -> TaxCalculation:
        """
        Process a fiat withdrawal and calculate taxable gain.
        
        French flat tax formula:
        - Taxable Gain = Withdrawal - (Acquisition Cost × (Withdrawal / Portfolio Value))
        - New Acquisition Cost = Old Cost - (Old Cost × (Withdrawal / Portfolio Value))
        
        Args:
            amount_eur: Withdrawal amount in EUR
            portfolio_value_eur: Total portfolio value before withdrawal in EUR
            
        Returns:
            TaxCalculation with taxable gain and updated acquisition cost
            
        Raises:
            TaxCalculationError: If amounts are invalid
        """
        self.logger.debug(f"Processing withdrawal: €{amount_eur}, portfolio value: €{portfolio_value_eur}")
        
        # Validate inputs
        if amount_eur <= 0:
            self.logger.error(f"Invalid withdrawal amount: €{amount_eur}")
            raise TaxCalculationError(f"Withdrawal amount must be positive, got: €{amount_eur}")
        
        if portfolio_value_eur <= 0:
            self.logger.error(f"Invalid portfolio value: €{portfolio_value_eur}")
            raise TaxCalculationError(f"Portfolio value must be positive, got: €{portfolio_value_eur}")
        
        if amount_eur > portfolio_value_eur:
            self.logger.warning(f"Withdrawal amount (€{amount_eur}) exceeds portfolio value (€{portfolio_value_eur})")
            # This can happen due to timing or rounding, but we'll allow it with a warning
        
        try:
            # Calculate the proportion of portfolio being withdrawn
            withdrawal_ratio = amount_eur / portfolio_value_eur
            
            # Calculate the acquisition cost portion corresponding to this withdrawal
            acquisition_cost_portion = self.acquisition_cost * withdrawal_ratio
            acquisition_cost_portion = self._round_to_2_decimals(acquisition_cost_portion)
            
            # Calculate taxable gain
            taxable_gain = amount_eur - acquisition_cost_portion
            taxable_gain = self._round_to_2_decimals(taxable_gain)
            
            self.logger.debug(f"Taxable gain: €{taxable_gain}")
            
            # Update acquisition cost (reduce by the portion withdrawn)
            self.acquisition_cost -= acquisition_cost_portion
            self.acquisition_cost = self._round_to_2_decimals(self.acquisition_cost)
            
            # Ensure acquisition cost doesn't go negative due to rounding
            if self.acquisition_cost < 0:
                self.logger.warning(f"Acquisition cost went negative (€{self.acquisition_cost}), setting to 0")
                self.acquisition_cost = Decimal("0")
            
            # Update cumulative gains
            self.cumulative_gains += taxable_gain
            self.cumulative_gains = self._round_to_2_decimals(self.cumulative_gains)
            
            self.logger.debug(f"New acquisition cost: €{self.acquisition_cost}, cumulative gains: €{self.cumulative_gains}")
            
            return TaxCalculation(
                acquisition_cost=self.acquisition_cost,
                taxable_gain=taxable_gain,
                cumulative_gains=self.cumulative_gains
            )
        except (InvalidOperation, ValueError, ZeroDivisionError) as e:
            self.logger.error(f"Invalid decimal operation in withdrawal processing: {e}")
            raise TaxCalculationError(f"Invalid decimal value in withdrawal processing: {e}")
