"""
Transaction SQLAlchemy models for the Binance FEC Extractor.

This module defines the transaction models including the base Transaction class
and specialized classes for different transaction types (Trade, Deposit, Withdrawal).
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Numeric, ForeignKey, 
    Index, CheckConstraint, Text
)
from sqlalchemy.orm import relationship, validates
from .database import Base


class Transaction(Base):
    """
    Base transaction model representing all types of Binance transactions.
    
    This is the parent class for all transaction types and contains
    common fields shared across trades, deposits, and withdrawals.
    """
    
    __tablename__ = 'transactions'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Binance-specific identifiers
    binance_id = Column(String(100), unique=True, nullable=False, index=True)
    order_id = Column(String(100), nullable=True, index=True)
    
    # Transaction timing
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Asset information
    symbol = Column(String(20), nullable=False, index=True)
    base_asset = Column(String(10), nullable=True)
    quote_asset = Column(String(10), nullable=True)
    
    # Transaction details
    side = Column(String(10), nullable=True)  # BUY/SELL for trades
    quantity = Column(Numeric(precision=18, scale=8), nullable=False)
    price = Column(Numeric(precision=18, scale=8), nullable=True)
    quote_quantity = Column(Numeric(precision=18, scale=8), nullable=True)
    
    # Commission/Fee information
    commission = Column(Numeric(precision=18, scale=8), nullable=True, default=0)
    commission_asset = Column(String(10), nullable=True)
    
    # Transaction type and status
    transaction_type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=True, default='COMPLETED')
    
    # Network information (for deposits/withdrawals)
    network = Column(String(50), nullable=True)
    address = Column(String(200), nullable=True)
    address_tag = Column(String(50), nullable=True)
    tx_id = Column(String(200), nullable=True)
    
    # Additional metadata
    raw_data = Column(Text, nullable=True)  # Store original API response
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'transaction',
        'polymorphic_on': transaction_type,
        'with_polymorphic': '*'
    }
    
    # Relationships
    fec_entries = relationship("FECEntry", back_populates="transaction", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity > 0', name='positive_quantity'),
        CheckConstraint('price IS NULL OR price > 0', name='positive_price'),
        CheckConstraint('commission IS NULL OR commission >= 0', name='non_negative_commission'),
        Index('idx_transaction_timestamp_type', 'timestamp', 'transaction_type'),
        Index('idx_transaction_symbol_timestamp', 'symbol', 'timestamp'),
    )
    
    @validates('transaction_type')
    def validate_transaction_type(self, key, transaction_type):
        """Validate transaction type values."""
        valid_types = ['TRADE', 'DEPOSIT', 'WITHDRAWAL', 'FEE', 'TRANSFER']
        if transaction_type not in valid_types:
            raise ValueError(f"Invalid transaction type: {transaction_type}")
        return transaction_type
    
    @validates('side')
    def validate_side(self, key, side):
        """Validate side values for trades."""
        if side is not None:
            valid_sides = ['BUY', 'SELL']
            if side not in valid_sides:
                raise ValueError(f"Invalid side: {side}")
        return side
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status values."""
        if status is not None:
            valid_statuses = ['COMPLETED', 'PENDING', 'FAILED', 'CANCELLED']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status: {status}")
        return status
    
    def __repr__(self):
        return (f"<Transaction(id={self.id}, binance_id='{self.binance_id}', "
                f"type='{self.transaction_type}', symbol='{self.symbol}', "
                f"quantity={self.quantity}, timestamp='{self.timestamp}')>")


class Trade(Transaction):
    """
    Trade transaction model for spot trading transactions.
    
    Inherits from Transaction and adds trade-specific fields.
    """
    
    __tablename__ = 'trades'
    
    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    
    # Trade-specific fields
    is_buyer = Column(String(10), nullable=True)  # true/false from API
    is_maker = Column(String(10), nullable=True)  # true/false from API
    is_best_match = Column(String(10), nullable=True)  # true/false from API
    
    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'TRADE'
    }
    
    @validates('is_buyer', 'is_maker', 'is_best_match')
    def validate_boolean_strings(self, key, value):
        """Validate boolean string values from Binance API."""
        if value is not None and value not in ['true', 'false']:
            raise ValueError(f"Invalid boolean string for {key}: {value}")
        return value
    
    def __repr__(self):
        return (f"<Trade(id={self.id}, binance_id='{self.binance_id}', "
                f"symbol='{self.symbol}', side='{self.side}', "
                f"quantity={self.quantity}, price={self.price})>")


class Deposit(Transaction):
    """
    Deposit transaction model for cryptocurrency deposits.
    
    Inherits from Transaction and adds deposit-specific fields.
    """
    
    __tablename__ = 'deposits'
    
    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    
    # Deposit-specific fields
    confirm_times = Column(String(50), nullable=True)  # Network confirmation info
    unlock_confirm = Column(Integer, nullable=True)
    wallet_type = Column(String(20), nullable=True)  # 0=spot, 1=funding
    
    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'DEPOSIT'
    }
    
    def __repr__(self):
        return (f"<Deposit(id={self.id}, binance_id='{self.binance_id}', "
                f"symbol='{self.symbol}', quantity={self.quantity}, "
                f"network='{self.network}', address='{self.address}')>")


class Withdrawal(Transaction):
    """
    Withdrawal transaction model for cryptocurrency withdrawals.
    
    Inherits from Transaction and adds withdrawal-specific fields.
    """
    
    __tablename__ = 'withdrawals'
    
    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    
    # Withdrawal-specific fields
    withdraw_order_id = Column(String(100), nullable=True)
    transaction_fee = Column(Numeric(precision=18, scale=8), nullable=True)
    confirm_no = Column(Integer, nullable=True)
    wallet_type = Column(String(20), nullable=True)  # 0=spot, 1=funding
    
    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'WITHDRAWAL'
    }
    
    @validates('transaction_fee')
    def validate_transaction_fee(self, key, transaction_fee):
        """Validate transaction fee is non-negative."""
        if transaction_fee is not None and transaction_fee < 0:
            raise ValueError("Transaction fee cannot be negative")
        return transaction_fee
    
    def __repr__(self):
        return (f"<Withdrawal(id={self.id}, binance_id='{self.binance_id}', "
                f"symbol='{self.symbol}', quantity={self.quantity}, "
                f"network='{self.network}', address='{self.address}')>")


class Fee(Transaction):
    """
    Fee transaction model for standalone fee transactions.
    
    Inherits from Transaction and represents fee-only transactions
    that are not part of trades.
    """
    
    __tablename__ = 'fees'
    
    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    
    # Fee-specific fields
    fee_type = Column(String(50), nullable=True)  # Type of fee (trading, withdrawal, etc.)
    related_transaction_id = Column(String(100), nullable=True)  # Reference to related transaction
    
    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'FEE'
    }
    
    def __repr__(self):
        return (f"<Fee(id={self.id}, binance_id='{self.binance_id}', "
                f"symbol='{self.symbol}', quantity={self.commission}, "
                f"fee_type='{self.fee_type}')>")


class Transfer(Transaction):
    """
    Transfer transaction model for internal transfers between accounts.
    
    Inherits from Transaction and represents transfers between
    different Binance account types (spot, margin, futures, etc.).
    """
    
    __tablename__ = 'transfers'
    
    id = Column(Integer, ForeignKey('transactions.id'), primary_key=True)
    
    # Transfer-specific fields
    from_account = Column(String(20), nullable=True)  # Source account type
    to_account = Column(String(20), nullable=True)    # Destination account type
    transfer_type = Column(String(50), nullable=True)  # Type of transfer
    
    # Polymorphic configuration
    __mapper_args__ = {
        'polymorphic_identity': 'TRANSFER'
    }
    
    def __repr__(self):
        return (f"<Transfer(id={self.id}, binance_id='{self.binance_id}', "
                f"symbol='{self.symbol}', quantity={self.quantity}, "
                f"from='{self.from_account}', to='{self.to_account}')>")