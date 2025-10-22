"""
Portfolio Value Calculator for converting USD portfolio values to EUR.

This module handles the conversion of portfolio values from USD to EUR
using historical exchange rates.
"""

from decimal import Decimal, ROUND_HALF_UP


class PortfolioValueCalculator:
    """
    Calculator for converting portfolio values from USD to EUR.
    
    Handles currency conversion with proper rounding to 2 decimal places
    as required for financial reporting.
    """
    
    @staticmethod
    def _round_to_2_decimals(value: Decimal) -> Decimal:
        """
        Round a decimal value to 2 decimal places.
        
        Args:
            value: Decimal value to round
            
        Returns:
            Rounded decimal value
        """
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def convert_usd_to_eur(portfolio_value_usd: Decimal, 
                          exchange_rate: Decimal) -> Decimal:
        """
        Convert USD portfolio value to EUR using the given exchange rate.
        
        Args:
            portfolio_value_usd: Portfolio value in USD
            exchange_rate: USD to EUR exchange rate (e.g., 0.92 means 1 USD = 0.92 EUR)
            
        Returns:
            Portfolio value in EUR, rounded to 2 decimal places
            
        Example:
            >>> calc = PortfolioValueCalculator()
            >>> calc.convert_usd_to_eur(Decimal("1000.00"), Decimal("0.92"))
            Decimal('920.00')
        """
        # Convert USD to EUR
        portfolio_value_eur = portfolio_value_usd * exchange_rate
        
        # Round to 2 decimal places
        return PortfolioValueCalculator._round_to_2_decimals(portfolio_value_eur)
