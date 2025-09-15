# Requirements Document

## Introduction

This feature will create a Python script that connects to a Binance account via API and extracts all cryptocurrency transactions within a specified date range (between start and end dates, or for a full year). The extracted data will be formatted according to the French FEC (Fichier des Écritures Comptables) standard, similar to the provided example file. This tool will enable automated accounting data extraction from Binance for compliance and bookkeeping purposes.

## Requirements

### Requirement 1

**User Story:** As an accountant or crypto trader, I want to connect to my Binance account via API, so that I can automatically retrieve transaction data without manual export.

#### Acceptance Criteria

1. WHEN the script is executed THEN the system SHALL authenticate with Binance API using provided API key and secret
2. IF authentication fails THEN the system SHALL display a clear error message and exit gracefully
3. WHEN API connection is established THEN the system SHALL verify account access permissions
4. IF API permissions are insufficient THEN the system SHALL inform the user about required permissions

### Requirement 2

**User Story:** As a user, I want to specify a date range for transaction extraction, so that I can get data for specific periods or full years.

#### Acceptance Criteria

1. WHEN the script is executed THEN the system SHALL accept start date and end date parameters
2. IF no dates are provided THEN the system SHALL default to the current year (January 1 to December 31)
3. WHEN a full year option is selected THEN the system SHALL extract all transactions for that specified year
4. IF invalid date format is provided THEN the system SHALL display format requirements and exit
5. WHEN start date is after end date THEN the system SHALL display an error and request valid date range

### Requirement 3

**User Story:** As an accountant, I want all transaction types to be extracted (trades, deposits, withdrawals, fees), so that I have complete financial records.

#### Acceptance Criteria

1. WHEN extracting data THEN the system SHALL retrieve all spot trading transactions
2. WHEN extracting data THEN the system SHALL retrieve all deposit transactions
3. WHEN extracting data THEN the system SHALL retrieve all withdrawal transactions
4. WHEN extracting data THEN the system SHALL retrieve all fee transactions
5. WHEN extracting data THEN the system SHALL retrieve all transfer transactions between accounts
6. IF API rate limits are encountered THEN the system SHALL implement proper delays and retry logic

### Requirement 4

**User Story:** As a compliance officer, I want the output to be in FEC format, so that it meets French accounting standards and can be imported into accounting software.

#### Acceptance Criteria

1. WHEN generating output THEN the system SHALL format data with all required FEC columns exactly as in the example: JournalCode, JournalLib, EcritureNum, EcritureDate, CompteNum, CompteLib, CompAuxNum, CompAuxLib, PieceRef, PieceDate, EcritureLib, Debit, Credit, EcritureLet, DateLet, ValidDate, Montantdevise, Idevise, NomPlateformeBlockchain, CUMP, TauxDeChange, DeviseEcartConvertion, AdresseSource, AdresseDestination, IdTransactionComptacrypto
2. WHEN formatting transactions THEN the system SHALL use "BIN" as JournalCode and "BINANCE" as JournalLib
3. WHEN formatting dates THEN the system SHALL use YYYYMMDD format for all date fields
4. WHEN processing trades THEN the system SHALL create double-entry bookkeeping records with proper Debit and Credit entries
5. WHEN processing fees THEN the system SHALL create appropriate entries using account "6278" for "Commissions" as shown in the example
6. WHEN dealing with different cryptocurrencies THEN the system SHALL assign appropriate CompteNum based on asset type (e.g., "5220011005" for USDC, "5220011011" for USDT, "5220012289" for other tokens)
7. WHEN creating internal transfers THEN the system SHALL use account "580" for "Mouvement intra-bancaire"
8. WHEN handling conversion differences THEN the system SHALL use accounts "767004" for "Produits nets sur cessions de jeton" and "667004" for "Charges nettes sur cessions de jetons"

### Requirement 5

**User Story:** As a user, I want the script to handle exchange rate conversions using ECB data, so that amounts are properly converted to EUR for accounting purposes with official rates.

#### Acceptance Criteria

1. WHEN processing transactions THEN the system SHALL fetch historical USD/EUR exchange rates from the European Central Bank (ECB) free API for the transaction dates
2. WHEN converting amounts THEN the system SHALL first convert cryptocurrency amounts to USD, then convert USD to EUR using ECB historical rates
3. WHEN exchange rate data is unavailable from ECB THEN the system SHALL log a warning and use the closest available rate within 5 business days
4. WHEN calculating conversion differences THEN the system SHALL create appropriate écart de conversion entries
5. IF ECB API fails THEN the system SHALL provide fallback options using alternative rate sources or manual rate input
6. WHEN storing exchange rates THEN the system SHALL cache ECB rates locally to minimize API calls

### Requirement 6

**User Story:** As a user, I want the script to save output to a file, so that I can import the data into accounting software or review it later.

#### Acceptance Criteria

1. WHEN extraction is complete THEN the system SHALL save output to a tab-separated text file
2. WHEN generating filename THEN the system SHALL include date range in the filename (e.g., "binance_fec_2023.txt")
3. IF output file already exists THEN the system SHALL ask for confirmation before overwriting
4. WHEN saving is complete THEN the system SHALL display the output file location and record count
5. IF file writing fails THEN the system SHALL display error message and suggest alternative locations

### Requirement 7

**User Story:** As a user, I want proper error handling and logging, so that I can troubleshoot issues and understand what the script is doing.

#### Acceptance Criteria

1. WHEN the script runs THEN the system SHALL log all major operations and progress
2. WHEN errors occur THEN the system SHALL provide clear, actionable error messages
3. WHEN API calls fail THEN the system SHALL log the specific error and suggest solutions
4. WHEN processing large datasets THEN the system SHALL display progress indicators
5. IF network issues occur THEN the system SHALL implement retry logic with exponential backoff

### Requirement 8

**User Story:** As a user, I want configuration options, so that I can customize the script behavior for my specific needs.

#### Acceptance Criteria

1. WHEN running the script THEN the system SHALL accept API credentials via command line arguments or environment variables
2. WHEN configuring output THEN the system SHALL allow custom output directory specification
3. WHEN setting up THEN the system SHALL support configuration file for default settings
4. IF sensitive data is involved THEN the system SHALL never log API keys or secrets
5. WHEN using environment variables THEN the system SHALL validate all required variables are present

### Requirement 9

**User Story:** As a compliance officer, I want each transaction to include USD values and exchange rate information, so that I have complete financial traceability and can meet audit requirements.

#### Acceptance Criteria

1. WHEN processing each transaction THEN the system SHALL include the original transaction value in USD in the Montantdevise field
2. WHEN processing each transaction THEN the system SHALL include the USD currency code in the Idevise field
3. WHEN processing each transaction THEN the system SHALL include the USD/EUR exchange rate from ECB API in the TauxDeChange field
4. WHEN processing each transaction THEN the system SHALL include the transaction date in the PieceDate field for rate reference
5. WHEN converting to EUR THEN the system SHALL calculate the EUR value using: USD_amount × USD_EUR_rate
6. WHEN storing rate information THEN the system SHALL use the ECB rate valid for the transaction date
7. IF multiple currencies are involved in a transaction THEN the system SHALL convert all amounts to USD first, then to EUR

### Requirement 10

**User Story:** As a French enterprise accountant, I want the FEC format to be fully compliant with French legal requirements, so that it can be used for official tax declarations and audits.

#### Acceptance Criteria

1. WHEN generating the FEC file THEN the system SHALL comply with Article A47 A-1 of the French General Tax Code (Code général des impôts)
2. WHEN formatting the file THEN the system SHALL use tab-separated values (.txt) format as required by French tax authorities
3. WHEN structuring data THEN the system SHALL include all 25 mandatory FEC columns in the exact order specified by French regulations
4. WHEN formatting dates THEN the system SHALL use YYYYMMDD format without separators as required by French standards
5. WHEN formatting amounts THEN the system SHALL use decimal notation with period as decimal separator (not comma)
6. WHEN creating journal entries THEN the system SHALL ensure each entry has balanced debits and credits
7. WHEN assigning account numbers THEN the system SHALL use the French Chart of Accounts (Plan Comptable Général) numbering system
8. WHEN generating sequential numbers THEN the system SHALL ensure EcritureNum follows sequential numbering within each journal
9. WHEN including platform information THEN the system SHALL populate NomPlateformeBlockchain field with "binance" for traceability
10. WHEN the file is complete THEN the system SHALL validate that the total debits equal total credits across all entries