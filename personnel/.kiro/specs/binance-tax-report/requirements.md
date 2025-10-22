# Requirements Document

## Introduction

Ce document définit les exigences pour un système de génération automatique de déclarations fiscales françaises pour les actifs numériques détenus sur Binance. Le système calcule la flat tax applicable aux plus-values réalisées lors des retraits de fiat EUR, en conformité avec la réglementation fiscale française.

## Glossary

- **Tax Report Generator**: Le système Python qui génère le fichier Excel de déclaration fiscale
- **Binance API Client**: Le composant qui communique avec l'API Binance pour récupérer les données de compte
- **Frankfurter API Client**: Le composant qui récupère les taux de change historiques USD/EUR
- **Portfolio Value Calculator**: Le composant qui calcule la valeur totale du portefeuille en EUR
- **Capital Gains Calculator**: Le composant qui calcule les plus-values imposables selon la méthode française
- **Excel Report Writer**: Le composant qui génère le fichier Excel final
- **Fiat Operation**: Une opération de dépôt ou retrait en EUR sur le compte Binance
- **Acquisition Cost**: Le prix total d'acquisition restant du portefeuille crypto
- **Taxable Gain**: La plus-value imposable calculée lors d'un retrait

## Requirements

### Requirement 1

**User Story:** En tant qu'utilisateur avec un compte Binance, je veux générer un rapport fiscal Excel pour une année donnée, afin de déclarer mes plus-values crypto aux autorités fiscales françaises.

#### Acceptance Criteria

1. WHEN the user executes the script with a year parameter, THE Tax Report Generator SHALL retrieve all fiat EUR deposit and withdrawal operations for that fiscal year from Binance
2. THE Tax Report Generator SHALL read Binance API credentials from the binance_keys file
3. THE Tax Report Generator SHALL generate an Excel file containing all required fiscal information
4. THE Tax Report Generator SHALL complete execution within 60 seconds for a year with up to 100 operations

### Requirement 2

**User Story:** En tant qu'utilisateur, je veux que le système récupère automatiquement mes opérations fiat EUR depuis Binance, afin d'éviter la saisie manuelle des données.

#### Acceptance Criteria

1. THE Binance API Client SHALL authenticate using API key and secret key from the binance_keys file
2. WHEN retrieving operations for a fiscal year, THE Binance API Client SHALL fetch all fiat deposit and withdrawal transactions in EUR currency
3. THE Binance API Client SHALL retrieve the operation date, type, and amount in EUR for each transaction
4. IF the Binance API returns an authentication error, THEN THE Binance API Client SHALL raise an exception with a clear error message

### Requirement 3

**User Story:** En tant qu'utilisateur, je veux que le système calcule la valeur de mon portefeuille en EUR à chaque opération, afin de déterminer correctement les plus-values.

#### Acceptance Criteria

1. WHEN processing each operation, THE Portfolio Value Calculator SHALL retrieve the total portfolio value in USD from Binance after the operation
2. THE Frankfurter API Client SHALL fetch the USD to EUR exchange rate for the operation date
3. THE Portfolio Value Calculator SHALL convert the USD portfolio value to EUR using the retrieved exchange rate
4. THE Portfolio Value Calculator SHALL round the EUR portfolio value to 2 decimal places

### Requirement 4

**User Story:** En tant qu'utilisateur, je veux que le système calcule les plus-values imposables selon la méthode française officielle, afin d'être en conformité avec la réglementation fiscale.

#### Acceptance Criteria

1. WHEN processing a deposit operation, THE Capital Gains Calculator SHALL increase the acquisition cost by the deposit amount
2. WHEN processing a deposit operation, THE Capital Gains Calculator SHALL set the taxable gain to zero
3. WHEN processing a withdrawal operation, THE Capital Gains Calculator SHALL calculate the taxable gain using the formula: Withdrawal Amount - (Acquisition Cost Before × (Withdrawal Amount / Portfolio Value Before))
4. WHEN processing a withdrawal operation, THE Capital Gains Calculator SHALL reduce the acquisition cost by: Acquisition Cost Before × (Withdrawal Amount / Portfolio Value Before)
5. THE Capital Gains Calculator SHALL maintain a cumulative sum of all taxable gains for the fiscal year
6. THE Capital Gains Calculator SHALL round all calculated values to 2 decimal places

### Requirement 5

**User Story:** En tant qu'utilisateur, je veux un fichier Excel structuré avec toutes les informations requises, afin de faciliter ma déclaration fiscale.

#### Acceptance Criteria

1. THE Excel Report Writer SHALL create a file named "Declaration_Fiscale_Crypto_{year}.xlsx" in the rapports/ directory
2. THE Excel Report Writer SHALL include columns in this exact order: Date, Type d'opération (Dépôt/Retrait Fiat), Montant en EUR, Valeur portefeuille USD (après opération), Taux de change USD/EUR, Valeur totale du portefeuille (EUR), Prix total d'acquisition restant (EUR), Plus-value imposable (EUR), Cumul plus-values (EUR)
3. THE Excel Report Writer SHALL format dates as YYYY-MM-DD
4. THE Excel Report Writer SHALL format all monetary values with 2 decimal places
5. THE Excel Report Writer SHALL sort operations chronologically by date
6. THE Excel Report Writer SHALL add a summary row at the end showing total deposits, total withdrawals, and total taxable gains
7. THE Excel Report Writer SHALL leave the portfolio value in EUR empty for deposit operations as it is not needed for the calculation
8. THE Excel Report Writer SHALL create the rapports/ directory if it does not exist

### Requirement 6

**User Story:** En tant qu'utilisateur, je veux pouvoir générer un rapport PDF en plus du fichier Excel, afin d'avoir un format facilement partageable et imprimable.

#### Acceptance Criteria

1. WHEN the user provides the --pdf command-line option, THE Tax Report Generator SHALL generate both Excel and PDF files
2. THE PDF Report Writer SHALL create a file named "Declaration_Fiscale_Crypto_{year}.pdf" in the rapports/ directory
3. THE PDF Report Writer SHALL include the same data as the Excel report in a formatted table
4. THE PDF Report Writer SHALL format the document with clear headers and readable fonts
5. THE PDF Report Writer SHALL include the summary section at the end of the document
6. WHEN the --pdf option is not provided, THE Tax Report Generator SHALL generate only the Excel file
7. THE PDF Report Writer SHALL create the rapports/ directory if it does not exist

### Requirement 7

**User Story:** En tant qu'utilisateur, je veux que le système gère les erreurs de manière claire, afin de comprendre et résoudre les problèmes rapidement.

#### Acceptance Criteria

1. IF the binance_keys file is missing or malformed, THEN THE Tax Report Generator SHALL display an error message indicating the file issue
2. IF the Binance API is unreachable, THEN THE Tax Report Generator SHALL retry up to 3 times with exponential backoff before failing
3. IF the Frankfurter API is unreachable for a specific date, THEN THE Tax Report Generator SHALL retry with the closest available date within 7 days
4. IF no fiat operations are found for the specified year, THEN THE Tax Report Generator SHALL create an empty report with a message indicating no operations
5. THE Tax Report Generator SHALL log all errors to a log file named "tax_report_{year}.log"
