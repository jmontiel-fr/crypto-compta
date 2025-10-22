#!/usr/bin/env python3
"""
Binance Tax Report Generator

Generates French tax reports for cryptocurrency operations on Binance.
Calculates flat tax on capital gains from fiat EUR withdrawals.
"""

import argparse
import sys
from datetime import datetime
from decimal import Decimal

from config.config import Config, ConfigError
from clients.binance_client import (
    BinanceClient, BinanceAPIError, BinanceRateLimitError, BinanceNetworkError
)
from clients.frankfurter_client import (
    FrankfurterClient, FrankfurterAPIError, FrankfurterNetworkError
)
from calculators.flat_tax_calculator import FlatTaxCalculator, TaxCalculationError
from calculators.portfolio_calculator import PortfolioValueCalculator
from writers.excel_writer import ExcelReportWriter, ExcelWriterError, TaxReportRow
from writers.pdf_writer import PDFReportWriter, PDFWriterError
from utils.logger import setup_logger, get_logger


def generate_tax_report(year: int, generate_pdf: bool = False) -> None:
    """
    Main function to generate tax report
    
    Args:
        year: Fiscal year to generate report for
        generate_pdf: If True, also generate PDF report
    """
    # Initialize logger
    logger = setup_logger(year, log_level="INFO")
    
    logger.info(f"Starting tax report generation for year {year}")
    logger.info(f"PDF generation: {'enabled' if generate_pdf else 'disabled'}")
    
    print(f"\n{'='*60}")
    print(f"Binance Tax Report Generator - Year {year}")
    print(f"{'='*60}\n")
    
    try:
        # Step 1: Load configuration
        print("📋 Loading configuration...")
        logger.info("Loading Binance API credentials")
        api_key, secret_key = Config.load_binance_keys()
        print("✓ Configuration loaded successfully\n")
        
        # Step 2: Initialize API clients
        print("🔌 Initializing API clients...")
        logger.info("Initializing Binance and Frankfurter API clients")
        binance_client = BinanceClient(api_key, secret_key)
        frankfurter_client = FrankfurterClient()
        print("✓ API clients initialized\n")
        
        # Step 3: Fetch fiat operations
        print(f"📥 Fetching EUR fiat operations for {year}...")
        logger.info(f"Fetching fiat operations for year {year}")
        operations = binance_client.get_fiat_operations(year, currency="EUR")
        
        if not operations:
            logger.warning(f"No fiat operations found for year {year}")
            print(f"\n⚠️  No EUR fiat operations found for year {year}")
            print(f"   This could mean:")
            print(f"   • You had no EUR deposits or withdrawals in {year}")
            print(f"   • Your API keys don't have access to fiat operation history")
            print(f"   • The operations are still pending or failed\n")
            print("   Creating empty report...\n")
            
            # Create empty report
            excel_writer = ExcelReportWriter()
            excel_path = excel_writer.create_report([], year)
            print(f"✓ Empty Excel report created: {excel_path}")
            
            if generate_pdf:
                pdf_writer = PDFReportWriter()
                pdf_path = pdf_writer.create_report([], year)
                print(f"✓ Empty PDF report created: {pdf_path}")
            
            print(f"\n{'='*60}")
            print("Report generation complete!")
            print(f"{'='*60}\n")
            logger.info("Empty report generation complete")
            return
        
        print(f"✓ Found {len(operations)} operation(s)\n")
        
        # Step 4: Initialize calculators
        print("🧮 Initializing tax calculator...")
        tax_calculator = FlatTaxCalculator()
        portfolio_calculator = PortfolioValueCalculator()
        print("✓ Calculator initialized\n")
        
        # Step 5: Process operations and calculate taxes
        print("💰 Processing operations and calculating taxes...")
        logger.info("Processing operations and calculating taxes")
        
        report_rows = []
        
        for idx, operation in enumerate(operations, 1):
            logger.info(f"Processing operation {idx}/{len(operations)}: {operation.operation_type} - €{operation.amount_eur}")
            print(f"   [{idx}/{len(operations)}] {operation.date.strftime('%Y-%m-%d')} - {operation.operation_type} - €{operation.amount_eur}")
            
            # Get portfolio value in USD after the operation
            portfolio_value_usd = binance_client.get_portfolio_value_usd(operation.timestamp)
            logger.debug(f"Portfolio value: ${portfolio_value_usd} USD")
            
            # Get exchange rate for the operation date
            operation_date = operation.date.date()
            exchange_rate = frankfurter_client.get_exchange_rate(operation_date, "USD", "EUR")
            logger.debug(f"Exchange rate: {exchange_rate} USD/EUR")
            
            # Calculate portfolio value in EUR (only for withdrawals)
            portfolio_value_eur = None
            if operation.operation_type == "Retrait":
                portfolio_value_eur = portfolio_calculator.convert_usd_to_eur(
                    portfolio_value_usd, exchange_rate
                )
                logger.debug(f"Portfolio value: €{portfolio_value_eur} EUR")
            
            # Calculate taxes
            if operation.operation_type == "Dépôt":
                tax_calc = tax_calculator.process_deposit(operation.amount_eur)
            else:  # Retrait
                tax_calc = tax_calculator.process_withdrawal(
                    operation.amount_eur, 
                    portfolio_value_eur
                )
            
            logger.debug(f"Tax calculation: gain=€{tax_calc.taxable_gain}, cumulative=€{tax_calc.cumulative_gains}")
            
            # Create report row
            report_row = TaxReportRow(
                date=operation_date,
                operation_type=operation.operation_type,
                amount_eur=operation.amount_eur,
                portfolio_value_usd=portfolio_value_usd,
                exchange_rate=exchange_rate,
                portfolio_value_eur=portfolio_value_eur,
                acquisition_cost=tax_calc.acquisition_cost,
                taxable_gain=tax_calc.taxable_gain,
                cumulative_gains=tax_calc.cumulative_gains
            )
            
            report_rows.append(report_row)
        
        print(f"✓ All operations processed\n")
        
        # Display summary
        total_deposits = sum(row.amount_eur for row in report_rows if row.operation_type == "Dépôt")
        total_withdrawals = sum(row.amount_eur for row in report_rows if row.operation_type == "Retrait")
        total_gains = report_rows[-1].cumulative_gains if report_rows else Decimal("0")
        
        print("📊 Summary:")
        print(f"   Total Deposits:     €{total_deposits:,.2f}")
        print(f"   Total Withdrawals:  €{total_withdrawals:,.2f}")
        print(f"   Total Taxable Gains: €{total_gains:,.2f}\n")
        
        # Step 6: Generate Excel report
        print("📄 Generating Excel report...")
        logger.info("Generating Excel report")
        excel_writer = ExcelReportWriter()
        excel_path = excel_writer.create_report(report_rows, year)
        print(f"✓ Excel report created: {excel_path}\n")
        
        # Step 7: Optionally generate PDF report
        if generate_pdf:
            print("📄 Generating PDF report...")
            logger.info("Generating PDF report")
            pdf_writer = PDFReportWriter()
            pdf_path = pdf_writer.create_report(report_rows, year)
            print(f"✓ PDF report created: {pdf_path}\n")
        
        logger.info("Tax report generation complete")
        print(f"{'='*60}")
        print("✅ Report generation complete!")
        print(f"{'='*60}\n")
        
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}\n", file=sys.stderr)
        print("💡 Tip: Make sure your binance_keys file exists and contains valid API credentials.", file=sys.stderr)
        print("   Format: BINANCE_API_KEY='your_key' and BINANCE_SECRET_KEY='your_secret'\n", file=sys.stderr)
        raise
    
    except BinanceRateLimitError as e:
        logger.error(f"Binance rate limit error: {e}")
        print(f"\n❌ Rate Limit Error: {e}\n", file=sys.stderr)
        print("💡 Tip: Wait a few minutes before trying again. Binance has rate limits to prevent abuse.\n", file=sys.stderr)
        raise
    
    except BinanceNetworkError as e:
        logger.error(f"Binance network error: {e}")
        print(f"\n❌ Network Error: {e}\n", file=sys.stderr)
        print("💡 Tip: Check your internet connection and try again.\n", file=sys.stderr)
        raise
    
    except BinanceAPIError as e:
        logger.error(f"Binance API error: {e}")
        print(f"\n❌ Binance API Error: {e}\n", file=sys.stderr)
        print("💡 Tip: Verify your API keys are correct and have the necessary permissions.\n", file=sys.stderr)
        raise
    
    except FrankfurterNetworkError as e:
        logger.error(f"Frankfurter network error: {e}")
        print(f"\n❌ Network Error: {e}\n", file=sys.stderr)
        print("💡 Tip: Check your internet connection. The exchange rate service may be temporarily unavailable.\n", file=sys.stderr)
        raise
    
    except FrankfurterAPIError as e:
        logger.error(f"Frankfurter API error: {e}")
        print(f"\n❌ Exchange Rate API Error: {e}\n", file=sys.stderr)
        print("💡 Tip: The exchange rate service may be temporarily unavailable. Try again later.\n", file=sys.stderr)
        raise
    
    except ExcelWriterError as e:
        logger.error(f"Excel writer error: {e}")
        print(f"\n❌ Excel File Error: {e}\n", file=sys.stderr)
        print("💡 Tip: Make sure the output file is not open in Excel or another program.\n", file=sys.stderr)
        raise
    
    except PDFWriterError as e:
        logger.error(f"PDF writer error: {e}")
        print(f"\n❌ PDF File Error: {e}\n", file=sys.stderr)
        print("💡 Tip: Make sure the output file is not open in a PDF viewer.\n", file=sys.stderr)
        raise
    
    except TaxCalculationError as e:
        logger.error(f"Tax calculation error: {e}")
        print(f"\n❌ Tax Calculation Error: {e}\n", file=sys.stderr)
        print("💡 Tip: There may be invalid data in your operations. Check the log file for details.\n", file=sys.stderr)
        raise
    
    except KeyboardInterrupt:
        logger.warning("Report generation interrupted by user")
        print("\n\n⚠️  Report generation interrupted by user.\n", file=sys.stderr)
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        print(f"\n❌ Unexpected Error: {e}\n", file=sys.stderr)
        print("💡 Tip: Check the log file for more details.\n", file=sys.stderr)
        raise


def main():
    """Main entry point with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Generate French tax report for Binance cryptocurrency operations",
        epilog="Example: python generate_tax_report.py 2024 --pdf"
    )
    parser.add_argument(
        "year",
        type=int,
        help="Fiscal year to generate report for (e.g., 2024)"
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also generate PDF report in addition to Excel"
    )
    
    try:
        args = parser.parse_args()
    except SystemExit:
        # argparse already printed the error message
        sys.exit(1)
    
    # Validate year
    current_year = datetime.now().year
    if args.year < 2000 or args.year > current_year:
        print(f"\n❌ Error: Year must be between 2000 and {current_year}", file=sys.stderr)
        print(f"   You provided: {args.year}\n", file=sys.stderr)
        sys.exit(1)
    
    try:
        generate_tax_report(args.year, args.pdf)
        sys.exit(0)
    except KeyboardInterrupt:
        # Already handled in generate_tax_report
        sys.exit(130)
    except (ConfigError, BinanceAPIError, BinanceRateLimitError, BinanceNetworkError,
            FrankfurterAPIError, FrankfurterNetworkError, ExcelWriterError, 
            PDFWriterError, TaxCalculationError):
        # These errors are already logged and displayed with user-friendly messages
        sys.exit(1)
    except Exception as e:
        # Unexpected error - try to log it
        try:
            logger = get_logger()
            logger.error(f"Fatal unexpected error: {e}", exc_info=True)
        except:
            pass
        print(f"\n❌ Fatal Error: {e}", file=sys.stderr)
        print(f"   An unexpected error occurred. Please check the log file for details.\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
