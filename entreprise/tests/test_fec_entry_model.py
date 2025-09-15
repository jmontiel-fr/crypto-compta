"""
Unit tests for FEC Entry SQLAlchemy model.

Tests FEC entry creation, validation, relationships, and formatting.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from binance_fec_extractor.models.database import Base
from binance_fec_extractor.models.transaction import Transaction
from binance_fec_extractor.models.fec_entry import FECEntry, FECEntryBuilder


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
def sample_transaction(db_session):
    """Create a sample transaction for testing."""
    transaction = Transaction(
        binance_id='TEST123456',
        timestamp=datetime(2023, 3, 18, 10, 30, 0),
        symbol='BTCUSDT',
        quantity=Decimal('0.001'),
        transaction_type='TRADE'
    )
    db_session.add(transaction)
    db_session.commit()
    return transaction


@pytest.fixture
def sample_fec_data():
    """Sample FEC entry data for testing."""
    return {
        'journal_code': 'BIN',
        'journal_lib': 'BINANCE',
        'ecriture_num': 2,
        'ecriture_date': '20230318',
        'compte_num': '5220011005',
        'compte_lib': 'Jetons detenus en Usd Coin (USDC) du compte VOXOMA',
        'piece_ref': 'EXEMPLE',
        'piece_date': '20240318',
        'ecriture_lib': 'Virement interne',
        'debit': '20007,25',
        'montant_devise': '21754,56875',
        'idevise': 'USDC',
        'nom_plateforme_blockchain': 'binance',
        'cump': '0.91967',
        'taux_de_change': '0.91968024'
    }


class TestFECEntryModel:
    """Test cases for the FECEntry model."""
    
    def test_create_fec_entry(self, db_session, sample_transaction, sample_fec_data):
        """Test creating a basic FEC entry."""
        sample_fec_data['transaction_id'] = sample_transaction.id
        
        fec_entry = FECEntry(**sample_fec_data)
        db_session.add(fec_entry)
        db_session.commit()
        
        assert fec_entry.id is not None
        assert fec_entry.transaction_id == sample_transaction.id
        assert fec_entry.journal_code == 'BIN'
        assert fec_entry.ecriture_num == 2
        assert fec_entry.compte_num == '5220011005'
    
    def test_required_fields_validation(self, db_session, sample_transaction):
        """Test validation of required fields."""
        # Missing compte_num
        with pytest.raises(ValueError, match="Account number.*required"):
            fec_entry = FECEntry(
                transaction_id=sample_transaction.id,
                ecriture_num=1,
                ecriture_date='20230318',
                compte_lib='Test Account',
                piece_ref='TEST',
                ecriture_lib='Test Entry'
            )
        
        # Missing compte_lib
        with pytest.raises(ValueError, match="Account label.*required"):
            fec_entry = FECEntry(
                transaction_id=sample_transaction.id,
                ecriture_num=1,
                ecriture_date='20230318',
                compte_num='5220011005',
                piece_ref='TEST',
                ecriture_lib='Test Entry'
            )
        
        # Missing piece_ref
        with pytest.raises(ValueError, match="Piece reference.*required"):
            fec_entry = FECEntry(
                transaction_id=sample_transaction.id,
                ecriture_num=1,
                ecriture_date='20230318',
                compte_num='5220011005',
                compte_lib='Test Account',
                ecriture_lib='Test Entry'
            )
        
        # Missing ecriture_lib
        with pytest.raises(ValueError, match="Entry description.*required"):
            fec_entry = FECEntry(
                transaction_id=sample_transaction.id,
                ecriture_num=1,
                ecriture_date='20230318',
                compte_num='5220011005',
                compte_lib='Test Account',
                piece_ref='TEST'
            )
    
    def test_date_format_validation(self, db_session, sample_transaction):
        """Test date format validation."""
        # Valid date format
        fec_entry = FECEntry(
            transaction_id=sample_transaction.id,
            ecriture_num=1,
            ecriture_date='20230318',
            compte_num='5220011005',
            compte_lib='Test Account',
            piece_ref='TEST',
            piece_date='20230318',
            ecriture_lib='Test Entry'
        )
        assert fec_entry.ecriture_date == '20230318'
        
        # Invalid date format - too short
        with pytest.raises(ValueError, match="must be in YYYYMMDD format"):
            fec_entry.ecriture_date = '2023318'
        
        # Invalid date format - non-numeric
        with pytest.raises(ValueError, match="must be in YYYYMMDD format"):
            fec_entry.ecriture_date = '2023-03-18'
    
    def test_ecriture_num_validation(self, db_session, sample_transaction):
        """Test ecriture number validation."""
        fec_entry = FECEntry(
            transaction_id=sample_transaction.id,
            compte_num='5220011005',
            compte_lib='Test Account',
            piece_ref='TEST',
            ecriture_date='20230318',
            ecriture_lib='Test Entry'
        )
        
        # Valid positive number
        fec_entry.ecriture_num = 1
        assert fec_entry.ecriture_num == 1
        
        # Invalid negative number
        with pytest.raises(ValueError, match="must be positive"):
            fec_entry.ecriture_num = -1
        
        # Invalid zero
        with pytest.raises(ValueError, match="must be positive"):
            fec_entry.ecriture_num = 0
    
    def test_amount_validation(self, db_session, sample_transaction):
        """Test debit/credit amount validation."""
        fec_entry = FECEntry(
            transaction_id=sample_transaction.id,
            ecriture_num=1,
            ecriture_date='20230318',
            compte_num='5220011005',
            compte_lib='Test Account',
            piece_ref='TEST',
            ecriture_lib='Test Entry'
        )
        
        # Valid amounts
        fec_entry.debit = '100,50'
        assert fec_entry.debit == '100,50'
        
        fec_entry.credit = '200.75'
        assert fec_entry.credit == '200.75'
        
        # Invalid negative amount
        with pytest.raises(ValueError, match="cannot be negative"):
            fec_entry.debit = '-100'
        
        # Invalid format
        with pytest.raises(ValueError, match="Invalid.*amount format"):
            fec_entry.credit = 'invalid_amount'
    
    def test_field_length_validation(self, db_session, sample_transaction):
        """Test field length validation."""
        fec_entry = FECEntry(
            transaction_id=sample_transaction.id,
            ecriture_num=1,
            ecriture_date='20230318',
            compte_num='5220011005',
            compte_lib='Test Account',
            piece_ref='TEST',
            ecriture_lib='Test Entry'
        )
        
        # Test journal_code length
        with pytest.raises(ValueError, match="cannot exceed 10 characters"):
            fec_entry.journal_code = 'A' * 11
        
        # Test compte_num length
        with pytest.raises(ValueError, match="cannot exceed 20 characters"):
            fec_entry.compte_num = 'A' * 21
        
        # Test compte_lib length
        with pytest.raises(ValueError, match="cannot exceed 200 characters"):
            fec_entry.compte_lib = 'A' * 201
        
        # Test piece_ref length
        with pytest.raises(ValueError, match="cannot exceed 50 characters"):
            fec_entry.piece_ref = 'A' * 51
        
        # Test ecriture_lib length
        with pytest.raises(ValueError, match="cannot exceed 200 characters"):
            fec_entry.ecriture_lib = 'A' * 201
    
    def test_default_values(self, db_session, sample_transaction):
        """Test default values are set correctly."""
        fec_entry = FECEntry(
            transaction_id=sample_transaction.id,
            ecriture_num=1,
            ecriture_date='20230318',
            compte_num='5220011005',
            compte_lib='Test Account',
            piece_ref='TEST',
            ecriture_lib='Test Entry'
        )
        
        assert fec_entry.journal_code == 'BIN'
        assert fec_entry.journal_lib == 'BINANCE'
        assert fec_entry.nom_plateforme_blockchain == 'binance'
        assert fec_entry.comp_aux_num == ''
        assert fec_entry.comp_aux_lib == ''
        assert fec_entry.debit == ''
        assert fec_entry.credit == ''
    
    def test_relationship_with_transaction(self, db_session, sample_transaction, sample_fec_data):
        """Test relationship between FEC entry and transaction."""
        sample_fec_data['transaction_id'] = sample_transaction.id
        
        fec_entry = FECEntry(**sample_fec_data)
        db_session.add(fec_entry)
        db_session.commit()
        
        # Test forward relationship
        assert fec_entry.transaction == sample_transaction
        
        # Test backward relationship
        assert fec_entry in sample_transaction.fec_entries
    
    def test_is_debit_credit_methods(self, db_session, sample_transaction):
        """Test debit/credit checking methods."""
        fec_entry = FECEntry(
            transaction_id=sample_transaction.id,
            ecriture_num=1,
            ecriture_date='20230318',
            compte_num='5220011005',
            compte_lib='Test Account',
            piece_ref='TEST',
            ecriture_lib='Test Entry'
        )
        
        # Test debit entry
        fec_entry.debit = '100,50'
        fec_entry.credit = ''
        assert fec_entry.is_debit_entry() is True
        assert fec_entry.is_credit_entry() is False
        
        # Test credit entry
        fec_entry.debit = ''
        fec_entry.credit = '200,75'
        assert fec_entry.is_debit_entry() is False
        assert fec_entry.is_credit_entry() is True
        
        # Test no amount
        fec_entry.debit = ''
        fec_entry.credit = ''
        assert fec_entry.is_debit_entry() is False
        assert fec_entry.is_credit_entry() is False
    
    def test_get_amount_decimal(self, db_session, sample_transaction):
        """Test getting amount as Decimal."""
        fec_entry = FECEntry(
            transaction_id=sample_transaction.id,
            ecriture_num=1,
            ecriture_date='20230318',
            compte_num='5220011005',
            compte_lib='Test Account',
            piece_ref='TEST',
            ecriture_lib='Test Entry'
        )
        
        # Test debit amount
        fec_entry.debit = '100,50'
        fec_entry.credit = ''
        amount = fec_entry.get_amount_decimal()
        assert amount == Decimal('100.50')
        
        # Test credit amount
        fec_entry.debit = ''
        fec_entry.credit = '200.75'
        amount = fec_entry.get_amount_decimal()
        assert amount == Decimal('200.75')
        
        # Test no amount
        fec_entry.debit = ''
        fec_entry.credit = ''
        amount = fec_entry.get_amount_decimal()
        assert amount is None
    
    def test_format_for_export(self, db_session, sample_transaction, sample_fec_data):
        """Test formatting for export."""
        sample_fec_data['transaction_id'] = sample_transaction.id
        
        fec_entry = FECEntry(**sample_fec_data)
        export_data = fec_entry.format_for_export()
        
        # Check all required columns are present
        expected_columns = [
            'JournalCode', 'JournalLib', 'EcritureNum', 'EcritureDate',
            'CompteNum', 'CompteLib', 'CompAuxNum', 'CompAuxLib',
            'PieceRef', 'PieceDate', 'EcritureLib', 'Debit', 'Credit',
            'EcritureLet', 'DateLet', 'ValidDate', 'Montantdevise',
            'Idevise', 'NomPlateformeBlockchain', 'CUMP', 'TauxDeChange',
            'DeviseEcartConvertion', 'AdresseSource', 'AdresseDestination',
            'IdTransactionComptacrypto'
        ]
        
        for column in expected_columns:
            assert column in export_data
        
        # Check specific values
        assert export_data['JournalCode'] == 'BIN'
        assert export_data['EcritureNum'] == '2'
        assert export_data['CompteNum'] == '5220011005'
        assert export_data['Debit'] == '20007,25'


class TestFECEntryBuilder:
    """Test cases for the FECEntryBuilder."""
    
    def test_builder_basic_usage(self, db_session, sample_transaction):
        """Test basic builder usage."""
        builder = FECEntryBuilder(sample_transaction.id)
        
        fec_entry = (builder
                    .with_journal('BIN', 'BINANCE')
                    .with_ecriture(1, '20230318', 'Test Entry')
                    .with_account('5220011005', 'Test Account')
                    .with_piece('TEST', '20230318')
                    .with_debit('100,50')
                    .build())
        
        assert fec_entry.transaction_id == sample_transaction.id
        assert fec_entry.journal_code == 'BIN'
        assert fec_entry.ecriture_num == 1
        assert fec_entry.compte_num == '5220011005'
        assert fec_entry.debit == '100,50'
        assert fec_entry.credit == ''  # Should be empty for debit entry
    
    def test_builder_credit_entry(self, db_session, sample_transaction):
        """Test builder for credit entry."""
        builder = FECEntryBuilder(sample_transaction.id)
        
        fec_entry = (builder
                    .with_ecriture(1, '20230318', 'Test Entry')
                    .with_account('580', 'Mouvement intra-bancaire')
                    .with_piece('TEST', '20230318')
                    .with_credit('100,50')
                    .build())
        
        assert fec_entry.credit == '100,50'
        assert fec_entry.debit == ''  # Should be empty for credit entry
    
    def test_builder_with_currency_info(self, db_session, sample_transaction):
        """Test builder with currency information."""
        builder = FECEntryBuilder(sample_transaction.id)
        
        fec_entry = (builder
                    .with_ecriture(1, '20230318', 'Test Entry')
                    .with_account('5220011005', 'Test Account')
                    .with_piece('TEST', '20230318')
                    .with_debit('100,50')
                    .with_currency_info('110', 'USDC', '0.91')
                    .build())
        
        assert fec_entry.montant_devise == '110'
        assert fec_entry.idevise == 'USDC'
        assert fec_entry.taux_de_change == '0.91'
    
    def test_builder_with_blockchain_info(self, db_session, sample_transaction):
        """Test builder with blockchain information."""
        builder = FECEntryBuilder(sample_transaction.id)
        
        fec_entry = (builder
                    .with_ecriture(1, '20230318', 'Test Entry')
                    .with_account('5220011005', 'Test Account')
                    .with_piece('TEST', '20230318')
                    .with_debit('100,50')
                    .with_blockchain_info('binance', '0.91', 'addr1', 'addr2')
                    .build())
        
        assert fec_entry.nom_plateforme_blockchain == 'binance'
        assert fec_entry.cump == '0.91'
        assert fec_entry.adresse_source == 'addr1'
        assert fec_entry.adresse_destination == 'addr2'
    
    def test_repr_method(self, db_session, sample_transaction, sample_fec_data):
        """Test string representation of FEC entry."""
        sample_fec_data['transaction_id'] = sample_transaction.id
        
        fec_entry = FECEntry(**sample_fec_data)
        repr_str = repr(fec_entry)
        
        assert 'FECEntry' in repr_str
        assert 'ecriture_num=2' in repr_str
        assert '5220011005' in repr_str
        assert '20230318' in repr_str