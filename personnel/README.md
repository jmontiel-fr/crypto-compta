# Binance Tax Report Generator

A Python application that automatically generates French tax reports for cryptocurrency assets held on Binance. The system calculates taxable capital gains (flat tax) on EUR withdrawals according to French tax regulations.

## Features

- 🔄 Automatic retrieval of EUR deposit/withdrawal operations from Binance
- 💰 Accurate capital gains calculation using the French flat tax method
- 📊 Excel report generation with detailed transaction history
- 📄 Optional PDF report generation
- 🔒 Secure API key management
- 📝 Comprehensive logging for audit trails
- ⚡ Retry logic for API resilience

## Requirements

- Python 3.8 or higher
- Binance account with API access
- Internet connection for API calls

## Installation

1. Clone or download this repository:
```bash
git clone <repository-url>
cd binance-tax-report
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create your Binance API keys configuration file (see Configuration section below)

## Configuration

### Obtaining Binance API Keys

1. Log in to your Binance account at [https://www.binance.com](https://www.binance.com)
2. Navigate to **API Management** (Profile → API Management)
3. Click **Create API** and choose **System generated**
4. Complete the security verification (2FA, email, etc.)
5. Label your API key (e.g., "Tax Report Generator")
6. **Important**: Configure API restrictions:
   - Enable **Read Only** permissions
   - Disable trading, withdrawals, and other write permissions
   - Optionally restrict to your IP address for added security
7. Save your **API Key** and **Secret Key** securely

### binance_keys File Format

Create a file named `binance_keys` in the project root directory with the following format:

```
API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
```

**Example:**
```
API_KEY=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
SECRET_KEY=xyz987wvu654tsr321qpo098nml765kji432hgf210edc098ba
```

**Security Notes:**
- Never commit this file to version control
- Keep your secret key confidential
- Use read-only API permissions
- Consider restricting API access to your IP address

## Usage

### Basic Usage (Excel Only)

Generate a tax report for a specific year:

```bash
python generate_tax_report.py 2024
```

This will create an Excel file at:
```
rapports/Declaration_Fiscale_Crypto_2024.xlsx
```

### Generate Both Excel and PDF

To generate both Excel and PDF reports:

```bash
python generate_tax_report.py 2024 --pdf
```

This will create:
```
rapports/Declaration_Fiscale_Crypto_2024.xlsx
rapports/Declaration_Fiscale_Crypto_2024.pdf
```

### Command-Line Options

```
python generate_tax_report.py <year> [--pdf]

Arguments:
  year          Fiscal year to generate report for (e.g., 2024)

Options:
  --pdf         Generate PDF report in addition to Excel
```

## Output File Formats

### Excel Report

The Excel file contains the following columns:

| Column | Description |
|--------|-------------|
| Date | Operation date (YYYY-MM-DD format) |
| Type d'opération | Operation type (Dépôt/Retrait Fiat) |
| Montant en EUR | Amount in EUR (2 decimal places) |
| Valeur portefeuille USD (après opération) | Portfolio value in USD after operation |
| Taux de change USD/EUR | USD to EUR exchange rate |
| Valeur totale du portefeuille (EUR) | Total portfolio value in EUR (empty for deposits) |
| Prix total d'acquisition restant (EUR) | Remaining acquisition cost in EUR |
| Plus-value imposable (EUR) | Taxable capital gain in EUR |
| Cumul plus-values (EUR) | Cumulative capital gains in EUR |

**Summary Row:**
- The last row contains totals for deposits, withdrawals, and cumulative gains
- All monetary values are formatted with 2 decimal places
- Operations are sorted chronologically

### PDF Report

The PDF file contains:
- Same data as Excel in a formatted table
- Clear headers and readable fonts
- Summary section at the end with totals
- Professional layout suitable for printing

## How It Works

### French Flat Tax Calculation Method

The system implements the official French tax calculation method for cryptocurrency:

1. **Deposits**: Increase the acquisition cost by the deposit amount
   - Taxable gain = 0 EUR

2. **Withdrawals**: Calculate taxable gain using the formula:
   ```
   Taxable Gain = Withdrawal Amount - (Acquisition Cost × (Withdrawal Amount / Portfolio Value))
   New Acquisition Cost = Old Cost - (Old Cost × (Withdrawal Amount / Portfolio Value))
   ```

3. **Cumulative Tracking**: Maintains running total of all taxable gains for the year

### Data Flow

1. Load Binance API credentials from `binance_keys` file
2. Retrieve all EUR deposit/withdrawal operations for the specified year
3. For each operation:
   - Get portfolio snapshot value in USD from Binance
   - Fetch historical USD/EUR exchange rate from Frankfurter API
   - Convert portfolio value to EUR
   - Calculate taxable gain using French method
4. Generate Excel report with all calculations
5. Optionally generate PDF report

## Logging

All operations are logged to `tax_report_{year}.log` with:
- INFO: Normal operations and API calls
- WARNING: Retry attempts and fallback operations
- ERROR: Failed operations and exceptions
- Timestamps for all events

## Error Handling

The system handles common errors gracefully:

- **Missing API keys**: Clear error message with configuration instructions
- **Binance API errors**: Automatic retry with exponential backoff (up to 3 attempts)
- **Exchange rate unavailable**: Tries nearest date within ±7 days
- **No operations found**: Creates empty report with informative message
- **Network issues**: Timeout handling and retry logic

## Troubleshooting

### "binance_keys file not found"
- Ensure the `binance_keys` file exists in the project root directory
- Check the file format matches the example above

### "Invalid API credentials"
- Verify your API key and secret key are correct
- Ensure there are no extra spaces or line breaks
- Check that API key is still active in Binance

### "No operations found for year"
- Verify you had EUR deposits or withdrawals in that year
- Check your Binance account has fiat transaction history
- Ensure API key has permission to read fiat operations

### Exchange rate errors
- The system automatically tries nearby dates if exact date unavailable
- Check your internet connection
- Frankfurter API may have temporary outages (check status)

## Project Structure

```
binance-tax-report/
├── generate_tax_report.py      # Main entry point
├── binance_keys                 # API credentials (not in git)
├── requirements.txt             # Python dependencies
├── config/
│   └── config.py               # Configuration management
├── clients/
│   ├── binance_client.py       # Binance API client
│   └── frankfurter_client.py   # Exchange rate API client
├── calculators/
│   ├── flat_tax_calculator.py  # Tax calculation logic
│   └── portfolio_calculator.py # Portfolio value conversion
├── writers/
│   ├── excel_writer.py         # Excel report generation
│   └── pdf_writer.py           # PDF report generation
├── utils/
│   └── logger.py               # Logging configuration
├── models.py                    # Data models
├── tests/                       # Unit and integration tests
└── rapports/                    # Generated reports (created automatically)
```

## Security Best Practices

1. **API Key Security**:
   - Use read-only API keys
   - Never share your secret key
   - Restrict API access to your IP if possible
   - Rotate keys periodically

2. **File Permissions**:
   - Restrict `binance_keys` file to owner only: `chmod 600 binance_keys`
   - Keep generated reports secure (contain sensitive financial data)

3. **Version Control**:
   - Never commit `binance_keys` to git
   - Add to `.gitignore`: `binance_keys`
   - Don't commit generated reports

## Legal Disclaimer

This tool is provided for informational purposes only. It calculates capital gains based on the French flat tax method, but:

- Always verify calculations with a tax professional
- Tax laws may change; ensure compliance with current regulations
- The authors are not responsible for any tax filing errors
- This is not financial or legal advice

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the log file for detailed error messages
3. Verify your API keys and configuration
4. Ensure all dependencies are installed correctly

## License

[Add your license information here]

## Contributing

[Add contribution guidelines if applicable]
