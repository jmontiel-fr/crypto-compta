# Design Document - Binance Tax Report Generator

## Overview

Le système est une application Python en ligne de commande qui génère automatiquement des rapports fiscaux Excel pour les actifs numériques détenus sur Binance. Il récupère les opérations fiat EUR via l'API Binance, calcule les plus-values imposables selon la méthode française, et produit un fichier Excel formaté conforme aux exigences fiscales.

### Key Design Principles

- **Separation of Concerns**: Chaque composant a une responsabilité unique (API clients, calculateurs, générateur Excel)
- **Error Resilience**: Gestion robuste des erreurs avec retry logic pour les APIs externes
- **Data Accuracy**: Tous les calculs financiers utilisent des décimales précises (Decimal) pour éviter les erreurs d'arrondi
- **Configurability**: Les clés API sont externalisées dans un fichier séparé

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Application                         │
│                  (tax_report_generator.py)                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Binance    │ │ Frankfurter  │ │    Excel     │
│ API Client   │ │ API Client   │ │    Writer    │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  Tax Calculator  │
              │   (flat_tax.py)  │
              └──────────────────┘
```

### Component Interaction Flow

1. **Initialization**: Lecture des clés API depuis binance_keys
2. **Data Retrieval**: Récupération des opérations fiat EUR pour l'année
3. **Portfolio Snapshots**: Pour chaque opération, récupération de la valeur du portefeuille en USD
4. **Exchange Rates**: Récupération des taux USD/EUR historiques
5. **Tax Calculation**: Calcul des plus-values selon la formule française
6. **Report Generation**: Création du fichier Excel avec toutes les données

## Components and Interfaces

### 1. Configuration Manager (`config.py`)

**Responsibility**: Gestion de la configuration et des clés API

```python
class Config:
    """Manages application configuration"""
    
    @staticmethod
    def load_binance_keys(file_path: str = "binance_keys") -> tuple[str, str]:
        """
        Load Binance API credentials from file
        
        Returns:
            tuple: (api_key, secret_key)
        Raises:
            ConfigError: If file is missing or malformed
        """
```

### 2. Binance API Client (`binance_client.py`)

**Responsibility**: Communication avec l'API Binance

```python
class BinanceClient:
    """Client for Binance API operations"""
    
    def __init__(self, api_key: str, secret_key: str):
        """Initialize with API credentials"""
    
    def get_fiat_operations(self, year: int, currency: str = "EUR") -> list[FiatOperation]:
        """
        Retrieve all fiat deposit/withdrawal operations for a year
        
        Args:
            year: Fiscal year (e.g., 2024)
            currency: Fiat currency code (default: EUR)
            
        Returns:
            List of FiatOperation objects sorted by date
        """
    
    def get_portfolio_value_usd(self, timestamp: int) -> Decimal:
        """
        Get total portfolio value in USD at a specific timestamp
        
        Args:
            timestamp: Unix timestamp in milliseconds
            
        Returns:
            Total portfolio value in USD
        """
```

### 3. Frankfurter API Client (`frankfurter_client.py`)

**Responsibility**: Récupération des taux de change historiques

```python
class FrankfurterClient:
    """Client for Frankfurter exchange rate API"""
    
    def get_exchange_rate(self, date: datetime.date, from_currency: str = "USD", 
                         to_currency: str = "EUR") -> Decimal:
        """
        Get historical exchange rate for a specific date
        
        Args:
            date: Date for exchange rate
            from_currency: Source currency
            to_currency: Target currency
            
        Returns:
            Exchange rate (e.g., 0.92 means 1 USD = 0.92 EUR)
            
        Note:
            If exact date unavailable, tries nearest date within 7 days
        """
```

### 4. Tax Calculator (`flat_tax_calculator.py`)

**Responsibility**: Calcul des plus-values imposables selon la méthode française

```python
class FlatTaxCalculator:
    """Calculator for French crypto flat tax"""
    
    def __init__(self):
        self.acquisition_cost = Decimal("0")
        self.cumulative_gains = Decimal("0")
    
    def process_deposit(self, amount_eur: Decimal) -> TaxCalculation:
        """
        Process a fiat deposit operation
        
        Args:
            amount_eur: Deposit amount in EUR
            
        Returns:
            TaxCalculation with updated acquisition cost
        """
    
    def process_withdrawal(self, amount_eur: Decimal, 
                          portfolio_value_eur: Decimal) -> TaxCalculation:
        """
        Process a fiat withdrawal and calculate taxable gain
        
        Formula: 
            Taxable Gain = Withdrawal - (Acquisition Cost × (Withdrawal / Portfolio Value))
            New Acquisition Cost = Old Cost - (Old Cost × (Withdrawal / Portfolio Value))
        
        Args:
            amount_eur: Withdrawal amount in EUR
            portfolio_value_eur: Total portfolio value before withdrawal in EUR
            
        Returns:
            TaxCalculation with taxable gain and updated acquisition cost
        """
```

### 5. Excel Report Writer (`excel_writer.py`)

**Responsibility**: Génération du fichier Excel

```python
class ExcelReportWriter:
    """Generates Excel tax report"""
    
    def create_report(self, operations: list[TaxReportRow], year: int, 
                     output_path: str) -> None:
        """
        Create Excel report file
        
        Args:
            operations: List of processed operations with tax calculations
            year: Fiscal year
            output_path: Path for output file
        """
    
    def _format_worksheet(self, worksheet) -> None:
        """Apply formatting to worksheet (headers, number formats, etc.)"""
    
    def _add_summary_row(self, worksheet, operations: list[TaxReportRow]) -> None:
        """Add summary row with totals"""
```

### 6. PDF Report Writer (`pdf_writer.py`)

**Responsibility**: Génération du fichier PDF (optionnel)

```python
class PDFReportWriter:
    """Generates PDF tax report"""
    
    def create_report(self, operations: list[TaxReportRow], year: int, 
                     output_path: str) -> None:
        """
        Create PDF report file
        
        Args:
            operations: List of processed operations with tax calculations
            year: Fiscal year
            output_path: Path for output file
        """
    
    def _format_table(self, operations: list[TaxReportRow]) -> None:
        """Format data as table in PDF"""
    
    def _add_summary_section(self, operations: list[TaxReportRow]) -> None:
        """Add summary section with totals"""
```

### 7. Main Application (`generate_tax_report.py`)

**Responsibility**: Orchestration de tous les composants

```python
def generate_tax_report(year: int, generate_pdf: bool = False) -> None:
    """
    Main function to generate tax report
    
    Args:
        year: Fiscal year to generate report for
        generate_pdf: If True, also generate PDF report
    """
```

## Data Models

### FiatOperation

```python
@dataclass
class FiatOperation:
    """Represents a fiat deposit or withdrawal operation"""
    date: datetime.datetime
    operation_type: str  # "Dépôt" or "Retrait"
    amount_eur: Decimal
    timestamp: int  # Unix timestamp in milliseconds
```

### TaxCalculation

```python
@dataclass
class TaxCalculation:
    """Result of tax calculation for an operation"""
    acquisition_cost: Decimal
    taxable_gain: Decimal
    cumulative_gains: Decimal
```

### TaxReportRow

```python
@dataclass
class TaxReportRow:
    """Complete row for Excel report"""
    date: datetime.date
    operation_type: str
    amount_eur: Decimal
    portfolio_value_usd: Decimal
    exchange_rate: Decimal
    portfolio_value_eur: Decimal | None  # None for deposits
    acquisition_cost: Decimal
    taxable_gain: Decimal
    cumulative_gains: Decimal
```

## Error Handling

### Error Types

1. **ConfigError**: Configuration file issues
2. **BinanceAPIError**: Binance API communication errors
3. **FrankfurterAPIError**: Exchange rate API errors
4. **CalculationError**: Tax calculation errors

### Retry Strategy

- **Binance API**: 3 retries with exponential backoff (1s, 2s, 4s)
- **Frankfurter API**: Try nearest date within ±7 days if exact date unavailable
- **Network Errors**: Automatic retry with timeout increase

### Logging

- Log file: `tax_report_{year}.log`
- Log levels:
  - INFO: Normal operations, API calls
  - WARNING: Retry attempts, fallback to nearest date
  - ERROR: Failed operations, exceptions
  - DEBUG: Detailed calculation steps (optional)

## Testing Strategy

### Unit Tests

1. **Config Tests**: Validate key file parsing, error handling
2. **Calculator Tests**: Verify flat tax formula with known examples
3. **API Client Tests**: Mock API responses, test error handling
4. **Excel Writer Tests**: Verify output format and formulas

### Integration Tests

1. **End-to-End Test**: Use test Binance account with known operations
2. **Exchange Rate Test**: Verify Frankfurter API integration
3. **Report Validation**: Compare generated Excel with expected output

### Test Data

- Use the example from `Flat_Tax_Crypto_Annuel_Complet_v2.xlsx` as reference
- Create fixtures with known operations and expected results

## Dependencies

### Required Python Packages

- `python-binance`: Official Binance API client
- `openpyxl`: Excel file generation
- `requests`: HTTP client for Frankfurter API
- `reportlab`: PDF generation (optional, only if --pdf flag used)
- `python-dotenv`: Optional, for environment variable support

### External APIs

1. **Binance API**
   - Endpoint: `https://api.binance.com`
   - Authentication: API Key + Secret
   - Rate Limits: Respect Binance rate limits (weight-based)

2. **Frankfurter API**
   - Endpoint: `https://api.frankfurter.app`
   - No authentication required
   - Rate Limits: Reasonable use policy

## Security Considerations

1. **API Keys**: Never log or expose API keys
2. **File Permissions**: Restrict binance_keys file to owner only
3. **Data Privacy**: Generated reports contain sensitive financial data
4. **API Permissions**: Binance keys should have read-only permissions

## Performance Considerations

- **Batch Operations**: Retrieve all operations in single API call when possible
- **Caching**: Cache exchange rates to avoid redundant API calls
- **Async Operations**: Consider async for parallel API calls (future enhancement)
- **Memory**: Process operations sequentially to minimize memory usage

## Future Enhancements

1. Support for multiple fiat currencies
2. Historical portfolio value tracking
3. Multi-exchange support (Coinbase, Kraken, etc.)
4. Automated backup of generated reports
5. Support for other tax calculation methods (FIFO, LIFO)
