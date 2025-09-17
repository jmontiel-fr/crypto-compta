# Theoretical FEC Example - Detailed Explanation

This document explains the theoretical FEC (Fichier des Écritures Comptables) example created for French accounting compliance with cryptocurrency transactions.

## Overview

The example demonstrates a complete set of cryptocurrency transactions over 10 days (January 15-25, 2024) including:
- EUR deposits and withdrawals
- Cryptocurrency purchases and sales
- Crypto-to-crypto conversions
- Transaction fees
- Capital gains and losses
- Staking rewards
- Currency conversion differences

## Exchange Rates Used

- **USD/EUR Rate**: 0.8696 (1 USD = 0.8696 EUR)
- **EUR/USD Rate**: 1.1500 (1 EUR = 1.15 USD)

## Cryptocurrency Prices Used

| Crypto | Price (USD) | Date Range |
|--------|-------------|------------|
| BTC | $43,478.26 - $45,217.39 | Jan 16-17 |
| ETH | $2,608.70 | Jan 18-19 |
| BNB | $347.83 | Jan 19-25 |
| SEI | $0.8696 - $0.7826 | Jan 21-22 |
| USDC | $1.00 | All dates |
| USDT | $1.00 | All dates |

## Transaction Details

### 1. EUR Deposit (Entry 1)
**Date**: January 15, 2024
- **Amount**: €1,000
- **Accounts**: 
  - Debit: 512000 (Bank account) €1,000
  - Credit: 5220011005 (USDC holdings) €1,000
- **Purpose**: Initial EUR deposit to Binance account

### 2. BTC Purchase (Entries 2-3)
**Date**: January 16, 2024
- **Trade**: Buy 0.575 BTC with $25,000 USDC
- **BTC Price**: $43,478.26
- **EUR Amount**: €21,739.13
- **Fee**: $10 (€8.70)
- **Accounts**:
  - Trade: Debit BTC holdings, Credit USDC holdings
  - Fee: Debit Commissions (6278), Credit USDC holdings

### 3. BTC Sale (Entries 4-6)
**Date**: January 17, 2024
- **Trade**: Sell 0.575 BTC for $26,000 USDT
- **BTC Price**: $45,217.39
- **EUR Amount**: €22,826.09
- **Capital Gain**: $1,000 (€956.52)
- **Fee**: $10 (€8.78)
- **Accounts**:
  - Trade: Debit BTC holdings, Credit USDT holdings
  - Gain: Credit Gains account (767004), Debit BTC holdings
  - Fee: Debit Commissions (6278), Credit USDT holdings

### 4. USDT to ETH Conversion (Entries 7-8)
**Date**: January 18, 2024
- **Trade**: Convert $20,000 USDT to 7.67 ETH
- **ETH Price**: $2,608.70
- **EUR Amount**: €17,391.30
- **Fee**: $10 (€8.70)

### 5. ETH to BNB Swap (Entries 9-10)
**Date**: January 19, 2024
- **Trade**: Swap 3.83 ETH for 28.75 BNB
- **Trade Value**: $10,000
- **EUR Amount**: €8,695.65
- **Fee**: $5 (€4.35)

### 6. Internal Transfer (Entry 11)
**Date**: January 20, 2024
- **Transfer**: Move 14.38 BNB to Spot wallet
- **Value**: $5,000 (€4,347.83)
- **Account**: 580 (Internal movements)

### 7. SEI Purchase (Entries 12-13)
**Date**: January 21, 2024
- **Trade**: Buy 11,494 SEI with $10,000 USDT
- **SEI Price**: $0.8696
- **EUR Amount**: €8,695.65
- **Fee**: $5 (€4.35)

### 8. SEI Sale with Loss (Entries 14-16)
**Date**: January 22, 2024
- **Trade**: Sell 11,494 SEI for $9,000 USDC
- **SEI Price**: $0.7826 (price dropped)
- **EUR Amount**: €7,826.09
- **Capital Loss**: $1,000 (€869.56)
- **Fee**: $5 (€4.35)
- **Accounts**:
  - Trade: Debit SEI holdings, Credit USDC holdings
  - Loss: Debit Losses account (667004), Credit SEI holdings

### 9. EUR Withdrawal (Entries 17-18)
**Date**: January 23, 2024
- **Amount**: €800
- **Fee**: $5 (€4.35)
- **Accounts**:
  - Withdrawal: Credit Bank account, Debit USDC holdings
  - Fee: Debit Commissions, Credit USDC holdings

### 10. Currency Conversion Difference (Entry 19)
**Date**: January 24, 2024
- **Purpose**: Record conversion difference between USD and EUR
- **Amount**: €2.17 (representing small conversion gains)
- **Account**: 767004 (Conversion gains)

### 11. Staking Reward (Entry 20)
**Date**: January 25, 2024
- **Reward**: 0.144 BNB staking reward
- **Value**: $50 (€43.48)
- **Accounts**:
  - Credit: BNB holdings
  - Debit: 758000 (Investment income)

## French Accounting Compliance

### Account Numbers Used (Plan Comptable Général)

| Account | Description | Type |
|---------|-------------|------|
| 512000 | Bank current account | Asset |
| 580 | Internal bank movements | Asset |
| 6278 | Commissions | Expense |
| 667004 | Net losses on token sales | Expense |
| 758000 | Investment income | Revenue |
| 767004 | Net gains on token sales | Revenue |
| 5220011005 | USDC token holdings | Asset |
| 5220011011 | USDT token holdings | Asset |
| 5220020188 | Bitcoin holdings | Asset |
| 5220020189 | Ethereum holdings | Asset |
| 5220020190 | BNB holdings | Asset |
| 5220012289 | SEI token holdings | Asset |

### Key Compliance Features

1. **Double-Entry Bookkeeping**: Every transaction has balanced debits and credits
2. **Sequential Numbering**: EcritureNum follows sequential order within journal
3. **Date Format**: YYYYMMDD format as required
4. **USD Values**: All transactions include USD amounts in Montantdevise
5. **Exchange Rates**: TauxDeChange shows USD/EUR conversion rate
6. **Platform Identification**: NomPlateformeBlockchain = "binance"
7. **Transaction References**: Unique IDs for audit trail

### Summary Totals

| Transaction Type | Count | Total EUR Value |
|------------------|-------|-----------------|
| Deposits | 1 | €1,000.00 |
| Withdrawals | 1 | €800.00 |
| Purchases | 3 | €47,826.08 |
| Sales | 2 | €30,652.18 |
| Conversions | 2 | €26,086.95 |
| Fees | 8 | €43.48 |
| Gains | 2 | €958.69 |
| Losses | 1 | €869.56 |
| Staking | 1 | €43.48 |

**Net Position**: The example shows a diversified crypto portfolio with realized gains and losses, demonstrating proper French accounting treatment for all transaction types.

## File Format Compliance

- **Encoding**: UTF-8
- **Separator**: Tab-separated values
- **Extension**: .csv (can be .txt)
- **Columns**: All 25 mandatory FEC columns present
- **Validation**: Debits = Credits for each transaction group

This theoretical example provides a comprehensive template for implementing French FEC compliance in cryptocurrency accounting systems.