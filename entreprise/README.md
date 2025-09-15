# Binance FEC Extractor

A Python application that connects to the Binance API to retrieve cryptocurrency transactions and formats them according to French FEC (Fichier des Écritures Comptables) accounting standards.

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy configuration files:
   ```bash
   cp .env.example .env
   cp config.json.example config.json
   ```

4. Configure your Binance API credentials in `.env`

## Usage

```bash
python main.py --start-date 2023-01-01 --end-date 2023-12-31
```

## Project Structure

```
binance_fec_extractor/
├── main.py                 # Entry point and CLI interface
├── config/                 # Configuration management
├── api/                    # Binance API and exchange rate services
├── processors/             # Transaction processing and FEC formatting
├── models/                 # Database models
└── utils/                  # Utilities and helpers
```

## Requirements

- Python 3.8+
- Binance API key with read permissions
- Internet connection for API access

## License

This project is for educational and compliance purposes.