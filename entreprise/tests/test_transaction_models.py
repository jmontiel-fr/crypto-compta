"""
Unit tests for Transaction SQLAlchemy models.

Tests model creation, relationships, constraints, and validation.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from binance_fec_extractor.models.database import Base
from binance_fec_extractor.models.transaction import (
    Transaction, Trade, Deposit, Withdrawal, Fee, Transfer
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for testing."""
    return {
        'binance_id': 'TEST123456',
        'timestamp': datetime(2023, 1, 15, 10, 30, 0),
        'symbol': 'BTCUSDT',
        'base_asset': 'BTC',
        'quote_asset': 'USDT',
        'quantity': Decimal('0.001'),
        'price': Decimal('42000.00'),
        'transaction_type': 'TRADE'
    }


class TestTransactionModel:
    """Test cases for the base Transaction model."""
    
    def test_create_transaction(self, db_session, sample_transaction_data):
        """Test creating a basic transaction."""
        transaction = Transaction(**sample_transaction_data)
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.id is not None
        assert transaction.binance_id == 'TEST123456'
        assert transaction.symbol == 'BTCUSDT'
        assert transaction.quantity == Decimal('0.001')
    
    def test_unique_binance_id_constraint(self, db_session, sample_transaction_data):
        """Test that binance_id must be unique."""
        # Create first transaction
        transaction1 = Transaction(**sample_transaction_data)
        db_session.add(transaction1)
        db_session.commit()
        
        # Try to create second transaction with same binance_id
        transaction2 = Transaction(**sample_transaction_data)
        transaction2.binance_id = 'TEST123456'  # Same ID
        db_session.add(transaction2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_positive_quantity_constraint(self, db_session, sample_transaction_data):
        """Test that quantity must be positive."""
        sample_transaction_data['quantity'] = Decimal('-1.0')
        transaction = Transaction(**sample_transaction_data)
        db_session.add(transaction)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_transaction_type_validation(self, db_session, sample_transaction_data):
        """Test transaction type validation."""
        # Valid transaction type
        transaction = Transaction(**sample_transaction_data)
        transaction.transaction_type = 'TRADE'
        assert transaction.transaction_type == 'TRADE'
        
        # Invalid transaction type
        with pytest.raises(ValueError):
            transaction.transaction_type = 'INVALID_TYPE'
    
    def test_side_validation(self, db_session, sample_transaction_data):
        """Test side validation for trades."""
        transaction = Transaction(**sample_transaction_data)
        
        # Valid sides
        transaction.side = 'BUY'
        assert transaction.side == 'BUY'
        
        transaction.side = 'SELL'
        assert transaction.side == 'SELL'
        
        # Invalid side
        with pytest.raises(ValueError):
            transaction.side = 'INVALID_SIDE'
    
    def test_status_validation(self, db_session, sample_transaction_data):
        """Test status validation."""
        transaction = Transaction(**sample_transaction_data)
        
        # Valid statuses
        valid_statuses = ['COMPLETED', 'PENDING', 'FAILED', 'CANCELLED']
        for status in valid_statuses:
            transaction.status = status
            assert transaction.status == status
        
        # Invalid status
        with pytest.raises(ValueError):
            transaction.status = 'INVALID_STATUS'
    
    def test_timestamps(self, db_session, sample_transaction_data):
        """Test automatic timestamp creation."""
        transaction = Transaction(**sample_transaction_data)
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.created_at is not None
        assert transaction.updated_at is not None
        assert isinstance(transaction.created_at, datetime)
        assert isinstance(transaction.updated_at, datetime)


class TestTradeModel:
    """Test cases for the Trade model."""
    
    def test_create_trade(self, db_session, sample_transaction_data):
        """Test creating a trade transaction."""
        sample_transaction_data.update({
            'side': 'BUY',
            'is_buyer': 'true',
            'is_maker': 'false',
            'commission': Decimal('0.001'),
            'commission_asset': 'BNB'
        })
        
        trade = Trade(**sample_transaction_data)
        db_session.add(trade)
        db_session.commit()
        
        assert trade.id is not None
        assert trade.transaction_type == 'TRADE'
        assert trade.side == 'BUY'
        assert trade.is_buyer == 'true'
        assert trade.is_maker == 'false'
    
    def test_boolean_string_validation(self, db_session, sample_transaction_data):
        """Test validation of boolean strings from Binance API."""
        trade = Trade(**sample_transaction_data)
        
        # Valid boolean strings
        trade.is_buyer = 'true'
        assert trade.is_buyer == 'true'
        
        trade.is_maker = 'false'
        assert trade.is_maker == 'false'
        
        # Invalid boolean string
        with pytest.raises(ValueError):
            trade.is_buyer = 'invalid'


class TestDepositModel:
    """Test cases for the Deposit model."""
    
    def test_create_deposit(self, db_session, sample_transaction_data):
        """Test creating a deposit transaction."""
        sample_transaction_data.update({
            'transaction_type': 'DEPOSIT',
            'network': 'BTC',
            'address': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            'tx_id': 'abc123def456',
            'confirm_times': '1/1',
            'wallet_type': '0'
        })
        
        deposit = Deposit(**sample_transaction_data)
        db_session.add(deposit)
        db_session.commit()
        
        assert deposit.id is not None
        assert deposit.transaction_type == 'DEPOSIT'
        assert deposit.network == 'BTC'
        assert deposit.address == '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
        assert deposit.confirm_times == '1/1'


class TestWithdrawalModel:
    """Test cases for the Withdrawal model."""
    
    def test_create_withdrawal(self, db_session, sample_transaction_data):
        """Test creating a withdrawal transaction."""
        sample_transaction_data.update({
            'transaction_type': 'WITHDRAWAL',
            'network': 'BTC',
            'address': '1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2',
            'tx_id': 'def456abc789',
            'transaction_fee': Decimal('0.0005'),
            'withdraw_order_id': 'WD123456'
        })
        
        withdrawal = Withdrawal(**sample_transaction_data)
        db_session.add(withdrawal)
        db_session.commit()
        
        assert withdrawal.id is not None
        assert withdrawal.transaction_type == 'WITHDRAWAL'
        assert withdrawal.network == 'BTC'
        assert withdrawal.transaction_fee == Decimal('0.0005')
        assert withdrawal.withdraw_order_id == 'WD123456'
    
    def test_negative_transaction_fee_validation(self, db_session, sample_transaction_data):
        """Test that transaction fee cannot be negative."""
        withdrawal = Withdrawal(**sample_transaction_data)
        
        with pytest.raises(ValueError):
            withdrawal.transaction_fee = Decimal('-0.001')


class TestFeeModel:
    """Test cases for the Fee model."""
    
    def test_create_fee(self, db_session, sample_transaction_data):
        """Test creating a fee transaction."""
        sample_transaction_data.update({
            'transaction_type': 'FEE',
            'commission': Decimal('0.001'),
            'commission_asset': 'BNB',
            'fee_type': 'trading_fee',
            'related_transaction_id': 'TRADE123456'
        })
        
        fee = Fee(**sample_transaction_data)
        db_session.add(fee)
        db_session.commit()
        
        assert fee.id is not None
        assert fee.transaction_type == 'FEE'
        assert fee.fee_type == 'trading_fee'
        assert fee.related_transaction_id == 'TRADE123456'


class TestTransferModel:
    """Test cases for the Transfer model."""
    
    def test_create_transfer(self, db_session, sample_transaction_data):
        """Test creating a transfer transaction."""
        sample_transaction_data.update({
            'transaction_type': 'TRANSFER',
            'from_account': 'SPOT',
            'to_account': 'MARGIN',
            'transfer_type': 'MAIN_MARGIN'
        })
        
        transfer = Transfer(**sample_transaction_data)
        db_session.add(transfer)
        db_session.commit()
        
        assert transfer.id is not None
        assert transfer.transaction_type == 'TRANSFER'
        assert transfer.from_account == 'SPOT'
        assert transfer.to_account == 'MARGIN'
        assert transfer.transfer_type == 'MAIN_MARGIN'


class TestModelRelationships:
    """Test relationships between models."""
    
    def test_polymorphic_queries(self, db_session, sample_transaction_data):
        """Test polymorphic queries work correctly."""
        # Create different transaction types
        trade_data = sample_transaction_data.copy()
        trade_data['binance_id'] = 'TRADE123'
        trade = Trade(**trade_data)
        
        deposit_data = sample_transaction_data.copy()
        deposit_data.update({
            'binance_id': 'DEPOSIT123',
            'transaction_type': 'DEPOSIT',
            'network': 'BTC'
        })
        deposit = Deposit(**deposit_data)
        
        db_session.add_all([trade, deposit])
        db_session.commit()
        
        # Query all transactions
        all_transactions = db_session.query(Transaction).all()
        assert len(all_transactions) == 2
        
        # Query specific types
        trades = db_session.query(Trade).all()
        assert len(trades) == 1
        assert isinstance(trades[0], Trade)
        
        deposits = db_session.query(Deposit).all()
        assert len(deposits) == 1
        assert isinstance(deposits[0], Deposit)
    
    def test_repr_methods(self, db_session, sample_transaction_data):
        """Test string representations of models."""
        transaction = Transaction(**sample_transaction_data)
        db_session.add(transaction)
        db_session.commit()
        
        repr_str = repr(transaction)
        assert 'Transaction' in repr_str
        assert 'TEST123456' in repr_str
        assert 'BTCUSDT' in repr_str