"""
Tests for Alembic database migrations.

Tests migration up and down operations to ensure database schema
is correctly created and destroyed.
"""

import os
import pytest
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations

from binance_fec_extractor.models.database import Base


class TestAlembicMigrations:
    """Test cases for Alembic migrations."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def alembic_config(self, temp_db_path):
        """Create Alembic configuration for testing."""
        # Create a temporary alembic.ini for testing
        config = Config()
        config.set_main_option('script_location', 'alembic')
        config.set_main_option('sqlalchemy.url', f'sqlite:///{temp_db_path}')
        return config
    
    def test_migration_upgrade(self, alembic_config, temp_db_path):
        """Test that migration upgrade creates all tables correctly."""
        # Run migration upgrade
        command.upgrade(alembic_config, 'head')
        
        # Connect to the database and verify tables exist
        engine = create_engine(f'sqlite:///{temp_db_path}')
        
        with engine.connect() as connection:
            # Check that all expected tables exist
            result = connection.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables = [row[0] for row in result]
            
            expected_tables = [
                'alembic_version',
                'transactions',
                'trades',
                'deposits',
                'withdrawals',
                'fees',
                'transfers',
                'fec_entries'
            ]
            
            for table in expected_tables:
                assert table in tables, f"Table {table} not found in database"
    
    def test_migration_downgrade(self, alembic_config, temp_db_path):
        """Test that migration downgrade removes all tables correctly."""
        # First upgrade to create tables
        command.upgrade(alembic_config, 'head')
        
        # Then downgrade to remove tables
        command.downgrade(alembic_config, 'base')
        
        # Connect to the database and verify only alembic_version table exists
        engine = create_engine(f'sqlite:///{temp_db_path}')
        
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables = [row[0] for row in result]
            
            # Only alembic_version should remain
            assert len(tables) == 1
            assert 'alembic_version' in tables
    
    def test_migration_up_down_cycle(self, alembic_config, temp_db_path):
        """Test complete migration cycle: up -> down -> up."""
        # Initial upgrade
        command.upgrade(alembic_config, 'head')
        
        # Verify tables exist
        engine = create_engine(f'sqlite:///{temp_db_path}')
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables_after_upgrade = [row[0] for row in result]
            assert 'transactions' in tables_after_upgrade
            assert 'fec_entries' in tables_after_upgrade
        
        # Downgrade
        command.downgrade(alembic_config, 'base')
        
        # Verify tables are removed
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables_after_downgrade = [row[0] for row in result]
            assert 'transactions' not in tables_after_downgrade
            assert 'fec_entries' not in tables_after_downgrade
        
        # Upgrade again
        command.upgrade(alembic_config, 'head')
        
        # Verify tables are recreated
        with engine.connect() as connection:
            result = connection.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables_after_second_upgrade = [row[0] for row in result]
            assert 'transactions' in tables_after_second_upgrade
            assert 'fec_entries' in tables_after_second_upgrade
    
    def test_table_constraints_created(self, alembic_config, temp_db_path):
        """Test that table constraints are properly created."""
        # Run migration upgrade
        command.upgrade(alembic_config, 'head')
        
        # Connect to the database and check constraints
        engine = create_engine(f'sqlite:///{temp_db_path}')
        
        with engine.connect() as connection:
            # Check transactions table structure
            result = connection.execute(text(
                "PRAGMA table_info(transactions)"
            ))
            columns = {row[1]: row for row in result}  # column_name -> row
            
            # Verify key columns exist with correct properties
            assert 'id' in columns
            assert 'binance_id' in columns
            assert 'timestamp' in columns
            assert 'quantity' in columns
            assert 'transaction_type' in columns
            
            # Check that binance_id is not nullable
            assert columns['binance_id'][3] == 1  # not null = 1
            
            # Check FEC entries table structure
            result = connection.execute(text(
                "PRAGMA table_info(fec_entries)"
            ))
            fec_columns = {row[1]: row for row in result}
            
            # Verify key FEC columns exist
            assert 'transaction_id' in fec_columns
            assert 'journal_code' in fec_columns
            assert 'ecriture_num' in fec_columns
            assert 'compte_num' in fec_columns
            assert 'debit' in fec_columns
            assert 'credit' in fec_columns
    
    def test_indexes_created(self, alembic_config, temp_db_path):
        """Test that database indexes are properly created."""
        # Run migration upgrade
        command.upgrade(alembic_config, 'head')
        
        # Connect to the database and check indexes
        engine = create_engine(f'sqlite:///{temp_db_path}')
        
        with engine.connect() as connection:
            # Check indexes on transactions table
            result = connection.execute(text(
                "PRAGMA index_list(transactions)"
            ))
            transaction_indexes = [row[1] for row in result]  # index names
            
            # Should have indexes on key fields
            index_names = [idx for idx in transaction_indexes if not idx.startswith('sqlite_')]
            assert len(index_names) > 0, "No custom indexes found on transactions table"
            
            # Check indexes on fec_entries table
            result = connection.execute(text(
                "PRAGMA index_list(fec_entries)"
            ))
            fec_indexes = [row[1] for row in result]
            
            # Should have indexes on key fields
            fec_index_names = [idx for idx in fec_indexes if not idx.startswith('sqlite_')]
            assert len(fec_index_names) > 0, "No custom indexes found on fec_entries table"