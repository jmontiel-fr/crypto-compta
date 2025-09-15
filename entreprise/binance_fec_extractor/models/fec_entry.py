"""
FEC Entry SQLAlchemy model for the Binance FEC Extractor.

This module defines the FECEntry model that represents French FEC
(Fichier des Écritures Comptables) accounting entries with all required columns.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, Numeric, ForeignKey, 
    Index, CheckConstraint, Text
)
from sqlalchemy.orm import relationship, validates
from .database import Base


class FECEntry(Base):
    """
    FEC Entry model representing French accounting entries.
    
    This model contains all the required columns for French FEC format
    as specified in the example file and French accounting standards.
    """
    
    __tablename__ = 'fec_entries'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to transaction
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False, index=True)
    
    # FEC Required Columns (matching exact column names from example)
    journal_code = Column(String(10), nullable=False, default="BIN")
    journal_lib = Column(String(100), nullable=False, default="BINANCE")
    ecriture_num = Column(Integer, nullable=False, index=True)
    ecriture_date = Column(String(8), nullable=False, index=True)  # YYYYMMDD format
    compte_num = Column(String(20), nullable=False, index=True)
    compte_lib = Column(String(200), nullable=False)
    comp_aux_num = Column(String(20), nullable=True, default="")
    comp_aux_lib = Column(String(200), nullable=True, default="")
    piece_ref = Column(String(50), nullable=False)
    piece_date = Column(String(8), nullable=False)  # YYYYMMDD format
    ecriture_lib = Column(String(200), nullable=False)
    debit = Column(String(20), nullable=True, default="")  # String to handle empty values
    credit = Column(String(20), nullable=True, default="")  # String to handle empty values
    ecriture_let = Column(String(10), nullable=True, default="")
    date_let = Column(String(8), nullable=True, default="")  # YYYYMMDD format
    valid_date = Column(String(8), nullable=True, default="")  # YYYYMMDD format
    montant_devise = Column(String(20), nullable=True, default="")
    idevise = Column(String(10), nullable=True, default="")
    nom_plateforme_blockchain = Column(String(50), nullable=False, default="binance")
    cump = Column(String(20), nullable=True, default="")
    taux_de_change = Column(String(20), nullable=True, default="")
    devise_ecart_convertion = Column(String(10), nullable=True, default="")
    adresse_source = Column(String(200), nullable=True, default="")
    adresse_destination = Column(String(200), nullable=True, default="")
    id_transaction_comptacrypto = Column(String(100), nullable=True, default="")
    
    # Metadata fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="fec_entries")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_fec_ecriture_date_num', 'ecriture_date', 'ecriture_num'),
        Index('idx_fec_compte_date', 'compte_num', 'ecriture_date'),
        Index('idx_fec_journal_date', 'journal_code', 'ecriture_date'),
    )
    
    @validates('journal_code')
    def validate_journal_code(self, key, journal_code):
        """Validate journal code format."""
        if journal_code and len(journal_code) > 10:
            raise ValueError("Journal code cannot exceed 10 characters")
        return journal_code or "BIN"
    
    @validates('ecriture_date', 'piece_date', 'date_let', 'valid_date')
    def validate_date_format(self, key, date_value):
        """Validate date format is YYYYMMDD."""
        if date_value and date_value != "":
            if len(date_value) != 8 or not date_value.isdigit():
                raise ValueError(f"{key} must be in YYYYMMDD format")
        return date_value or ""
    
    @validates('ecriture_num')
    def validate_ecriture_num(self, key, ecriture_num):
        """Validate ecriture number is positive."""
        if ecriture_num is not None and ecriture_num <= 0:
            raise ValueError("Ecriture number must be positive")
        return ecriture_num
    
    @validates('compte_num')
    def validate_compte_num(self, key, compte_num):
        """Validate account number format."""
        if not compte_num:
            raise ValueError("Account number (compte_num) is required")
        if len(compte_num) > 20:
            raise ValueError("Account number cannot exceed 20 characters")
        return compte_num
    
    @validates('compte_lib')
    def validate_compte_lib(self, key, compte_lib):
        """Validate account label is provided."""
        if not compte_lib:
            raise ValueError("Account label (compte_lib) is required")
        if len(compte_lib) > 200:
            raise ValueError("Account label cannot exceed 200 characters")
        return compte_lib
    
    @validates('piece_ref')
    def validate_piece_ref(self, key, piece_ref):
        """Validate piece reference is provided."""
        if not piece_ref:
            raise ValueError("Piece reference (piece_ref) is required")
        if len(piece_ref) > 50:
            raise ValueError("Piece reference cannot exceed 50 characters")
        return piece_ref
    
    @validates('ecriture_lib')
    def validate_ecriture_lib(self, key, ecriture_lib):
        """Validate entry description is provided."""
        if not ecriture_lib:
            raise ValueError("Entry description (ecriture_lib) is required")
        if len(ecriture_lib) > 200:
            raise ValueError("Entry description cannot exceed 200 characters")
        return ecriture_lib
    
    @validates('debit', 'credit')
    def validate_amounts(self, key, amount):
        """Validate debit/credit amounts."""
        if amount and amount != "":
            try:
                # Try to parse as decimal to validate format
                decimal_amount = Decimal(amount.replace(',', '.'))
                if decimal_amount < 0:
                    raise ValueError(f"{key} amount cannot be negative")
            except (ValueError, TypeError):
                raise ValueError(f"Invalid {key} amount format: {amount}")
        return amount or ""
    
    def is_debit_entry(self) -> bool:
        """Check if this is a debit entry."""
        return bool(self.debit and self.debit.strip())
    
    def is_credit_entry(self) -> bool:
        """Check if this is a credit entry."""
        return bool(self.credit and self.credit.strip())
    
    def get_amount_decimal(self) -> Optional[Decimal]:
        """Get the entry amount as a Decimal."""
        if self.is_debit_entry():
            return Decimal(self.debit.replace(',', '.'))
        elif self.is_credit_entry():
            return Decimal(self.credit.replace(',', '.'))
        return None
    
    def format_for_export(self) -> dict:
        """
        Format the FEC entry for export to tab-separated file.
        
        Returns:
            Dictionary with all FEC columns formatted for export.
        """
        return {
            'JournalCode': self.journal_code,
            'JournalLib': self.journal_lib,
            'EcritureNum': str(self.ecriture_num),
            'EcritureDate': self.ecriture_date,
            'CompteNum': self.compte_num,
            'CompteLib': self.compte_lib,
            'CompAuxNum': self.comp_aux_num,
            'CompAuxLib': self.comp_aux_lib,
            'PieceRef': self.piece_ref,
            'PieceDate': self.piece_date,
            'EcritureLib': self.ecriture_lib,
            'Debit': self.debit,
            'Credit': self.credit,
            'EcritureLet': self.ecriture_let,
            'DateLet': self.date_let,
            'ValidDate': self.valid_date,
            'Montantdevise': self.montant_devise,
            'Idevise': self.idevise,
            'NomPlateformeBlockchain': self.nom_plateforme_blockchain,
            'CUMP': self.cump,
            'TauxDeChange': self.taux_de_change,
            'DeviseEcartConvertion': self.devise_ecart_convertion,
            'AdresseSource': self.adresse_source,
            'AdresseDestination': self.adresse_destination,
            'IdTransactionComptacrypto': self.id_transaction_comptacrypto
        }
    
    def __repr__(self):
        return (f"<FECEntry(id={self.id}, ecriture_num={self.ecriture_num}, "
                f"compte_num='{self.compte_num}', ecriture_date='{self.ecriture_date}', "
                f"debit='{self.debit}', credit='{self.credit}')>")


class FECEntryBuilder:
    """
    Builder class for creating FEC entries with proper validation.
    
    Provides a fluent interface for building FEC entries with
    validation and default value handling.
    """
    
    def __init__(self, transaction_id: int):
        """
        Initialize the builder with a transaction ID.
        
        Args:
            transaction_id: ID of the associated transaction.
        """
        self.entry = FECEntry(transaction_id=transaction_id)
    
    def with_journal(self, code: str = "BIN", lib: str = "BINANCE") -> 'FECEntryBuilder':
        """Set journal code and library."""
        self.entry.journal_code = code
        self.entry.journal_lib = lib
        return self
    
    def with_ecriture(self, num: int, date: str, lib: str) -> 'FECEntryBuilder':
        """Set entry number, date, and description."""
        self.entry.ecriture_num = num
        self.entry.ecriture_date = date
        self.entry.ecriture_lib = lib
        return self
    
    def with_account(self, num: str, lib: str, aux_num: str = "", aux_lib: str = "") -> 'FECEntryBuilder':
        """Set account information."""
        self.entry.compte_num = num
        self.entry.compte_lib = lib
        self.entry.comp_aux_num = aux_num
        self.entry.comp_aux_lib = aux_lib
        return self
    
    def with_piece(self, ref: str, date: str) -> 'FECEntryBuilder':
        """Set piece reference and date."""
        self.entry.piece_ref = ref
        self.entry.piece_date = date
        return self
    
    def with_debit(self, amount: str) -> 'FECEntryBuilder':
        """Set debit amount."""
        self.entry.debit = amount
        self.entry.credit = ""  # Ensure credit is empty for debit entries
        return self
    
    def with_credit(self, amount: str) -> 'FECEntryBuilder':
        """Set credit amount."""
        self.entry.credit = amount
        self.entry.debit = ""  # Ensure debit is empty for credit entries
        return self
    
    def with_currency_info(self, montant_devise: str = "", idevise: str = "", 
                          taux_change: str = "") -> 'FECEntryBuilder':
        """Set currency information."""
        self.entry.montant_devise = montant_devise
        self.entry.idevise = idevise
        self.entry.taux_de_change = taux_change
        return self
    
    def with_blockchain_info(self, platform: str = "binance", cump: str = "",
                           adresse_source: str = "", adresse_destination: str = "") -> 'FECEntryBuilder':
        """Set blockchain-specific information."""
        self.entry.nom_plateforme_blockchain = platform
        self.entry.cump = cump
        self.entry.adresse_source = adresse_source
        self.entry.adresse_destination = adresse_destination
        return self
    
    def build(self) -> FECEntry:
        """
        Build and return the FEC entry.
        
        Returns:
            Configured FECEntry instance.
        """
        return self.entry