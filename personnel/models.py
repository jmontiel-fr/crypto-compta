"""Data models for the Binance Tax Report Generator."""

from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal


@dataclass
class FiatOperation:
    """Represents a fiat deposit or withdrawal operation."""
    date: datetime
    operation_type: str  # "Dépôt" or "Retrait"
    amount_eur: Decimal
    timestamp: int  # Unix timestamp in milliseconds


@dataclass
class TaxCalculation:
    """Result of tax calculation for an operation."""
    acquisition_cost: Decimal
    taxable_gain: Decimal
    cumulative_gains: Decimal


@dataclass
class TaxReportRow:
    """Complete row for Excel report."""
    date: date
    operation_type: str
    amount_eur: Decimal
    portfolio_value_usd: Decimal
    exchange_rate: Decimal
    portfolio_value_eur: Decimal | None  # None for deposits
    acquisition_cost: Decimal
    taxable_gain: Decimal
    cumulative_gains: Decimal
