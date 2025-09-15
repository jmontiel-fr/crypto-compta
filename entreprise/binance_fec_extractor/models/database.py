"""
Database configuration and session management for the Binance FEC Extractor.

This module provides SQLAlchemy database configuration, connection management,
and session handling for the application.
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Create the declarative base for all models
Base = declarative_base()


class DatabaseManager:
    """
    Manages database connections and sessions for the application.
    
    Provides methods for database initialization, connection management,
    and session creation/cleanup.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the DatabaseManager.
        
        Args:
            database_url: Database connection URL. If None, uses SQLite default.
        """
        self.database_url = database_url or self._get_default_database_url()
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        
    def _get_default_database_url(self) -> str:
        """
        Get the default database URL from environment or use SQLite.
        
        Returns:
            Database connection URL string.
        """
        # Check for environment variable first
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            return db_url
            
        # Default to SQLite database in the project root
        db_path = os.path.join(os.getcwd(), 'binance_fec.db')
        return f'sqlite:///{db_path}'
    
    def init_database(self) -> None:
        """
        Initialize the database engine and session factory.
        
        Creates the SQLAlchemy engine with appropriate configuration
        and sets up the session factory.
        """
        try:
            # Configure engine based on database type
            if self.database_url.startswith('sqlite'):
                # SQLite specific configuration
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={
                        'check_same_thread': False,
                        'timeout': 30
                    },
                    echo=False  # Set to True for SQL debugging
                )
            else:
                # PostgreSQL or other database configuration
                self.engine = create_engine(
                    self.database_url,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    echo=False  # Set to True for SQL debugging
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"Database initialized successfully: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_tables(self) -> None:
        """
        Create all database tables based on the defined models.
        
        This method should be called after all models are imported
        to ensure all tables are created.
        """
        try:
            if not self.engine:
                raise RuntimeError("Database not initialized. Call init_database() first.")
            
            # Import all models to ensure they're registered with Base
            from . import transaction, fec_entry
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        Create and return a new database session.
        
        Returns:
            SQLAlchemy Session instance.
            
        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call init_database() first.")
        
        return self.SessionLocal()
    
    def close_session(self, session: Session) -> None:
        """
        Close a database session.
        
        Args:
            session: The session to close.
        """
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
    
    def get_engine(self) -> Engine:
        """
        Get the database engine.
        
        Returns:
            SQLAlchemy Engine instance.
            
        Raises:
            RuntimeError: If database is not initialized.
        """
        if not self.engine:
            raise RuntimeError("Database not initialized. Call init_database() first.")
        
        return self.engine
    
    def test_connection(self) -> bool:
        """
        Test the database connection.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            if not self.engine:
                self.init_database()
            
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            
            logger.info("Database connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def cleanup(self) -> None:
        """
        Clean up database resources.
        
        Closes all connections and disposes of the engine.
        """
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("Database resources cleaned up")
        except Exception as e:
            logger.warning(f"Error during database cleanup: {e}")


# Global database manager instance
db_manager = DatabaseManager()


def init_database(database_url: Optional[str] = None) -> DatabaseManager:
    """
    Initialize the global database manager.
    
    Args:
        database_url: Optional database URL. If None, uses default.
        
    Returns:
        Initialized DatabaseManager instance.
    """
    global db_manager
    if database_url:
        db_manager = DatabaseManager(database_url)
    
    db_manager.init_database()
    return db_manager


def get_session() -> Session:
    """
    Get a database session from the global database manager.
    
    Returns:
        SQLAlchemy Session instance.
    """
    return db_manager.get_session()


def close_session(session: Session) -> None:
    """
    Close a database session using the global database manager.
    
    Args:
        session: The session to close.
    """
    db_manager.close_session(session)


def create_tables() -> None:
    """
    Create all database tables using the global database manager.
    """
    db_manager.create_tables()


def test_connection() -> bool:
    """
    Test the database connection using the global database manager.
    
    Returns:
        True if connection is successful, False otherwise.
    """
    return db_manager.test_connection()