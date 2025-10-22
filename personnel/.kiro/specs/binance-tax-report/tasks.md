# Implementation Plan

- [x] 1. Set up project structure and dependencies



  - Create directory structure for the project (config, clients, calculators, writers, utils)
  - Create requirements.txt with all necessary dependencies (python-binance, openpyxl, requests, reportlab)
  - Create main entry point script generate_tax_report.py
  - _Requirements: 1.2, 1.3_

- [x] 2. Implement configuration management





  - Create config.py module with Config class
  - Implement load_binance_keys() function to parse binance_keys file
  - Add error handling for missing or malformed configuration files
  - _Requirements: 1.2, 6.1_


- [x] 3. Implement Binance API client




  - Create binance_client.py module with BinanceClient class
  - Implement authentication using API key and secret
  - Implement get_fiat_operations() to retrieve EUR deposits and withdrawals for a given year
  - Implement get_portfolio_value_usd() to get portfolio snapshot at specific timestamp
  - Add retry logic with exponential backoff for API failures
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.2_
- [x] 4. Implement Frankfurter API client




- [ ] 4. Implement Frankfurter API client

  - Create frankfurter_client.py module with FrankfurterClient class
  - Implement get_exchange_rate() to fetch historical USD/EUR rates
  - Add fallback logic to try nearest date within 7 days if exact date unavailable
  - Handle API errors gracefully
  - _Requirements: 3.2, 6.3_

- [x] 5. Implement flat tax calculator




  - Create flat_tax_calculator.py module with FlatTaxCalculator class
  - Implement process_deposit() method to update acquisition cost
  - Implement process_withdrawal() method with French flat tax formula
  - Ensure all calculations use Decimal for precision
  - Maintain cumulative gains tracking
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 6. Implement portfolio value calculator





  - Create portfolio_calculator.py module with PortfolioValueCalculator class
  - Implement method to convert USD portfolio value to EUR using exchange rate
  - Handle rounding to 2 decimal places
  - _Requirements: 3.1, 3.3, 3.4_

- [x] 7. Implement Excel report writer





  - Create excel_writer.py module with ExcelReportWriter class
  - Implement create_report() to generate Excel file with all required columns
  - Add column headers in correct order
  - Format dates as YYYY-MM-DD
  - Format monetary values with 2 decimal places
  - Leave portfolio value EUR empty for deposits
  - Add summary row with totals
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_


- [x] 8. Implement logging system




  - Create logger.py module with logging configuration
  - Set up file logging to tax_report_{year}.log
  - Configure log levels (INFO, WARNING, ERROR, DEBUG)
  - Add logging calls throughout the application
  - _Requirements: 6.5_




- [ ] 9. Implement PDF report writer

  - Create pdf_writer.py module with PDFReportWriter class
  - Implement create_report() to generate PDF file with formatted table
  - Add table headers and format data rows



  - Format dates and monetary values consistently with Excel
  - Add summary section at the end
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 10. Implement main orchestration logic





  - Complete generate_tax_report.py main function
  - Integrate all components (config, API clients, calculators, Excel writer, PDF writer)
  - Implement workflow: load config → fetch operations → get portfolio values → get exchange rates → calculate taxes → generate Excel → optionally generate PDF
  - Add command-line argument parsing for year parameter and --pdf flag



  - Handle empty operations case with appropriate message


  - _Requirements: 1.1, 1.3, 1.4, 6.6, 7.4_

- [ ] 11. Create data models



  - Create models.py with dataclass definitions
  - Define FiatOperation dataclass
  - Define TaxCalculation dataclass
  - Define TaxReportRow dataclass
  - _Requirements: All requirements (supporting data structures)_



- [ ] 12. Write unit tests



  - [ ] 12.1 Test configuration management
    - Test successful key loading
    - Test missing file error handling
    - Test malformed file error handling
    - _Requirements: 7.1_
  


  - [ ] 12.2 Test flat tax calculator
    - Test deposit processing (acquisition cost increase, zero gain)


    - Test withdrawal processing with known values from example Excel
    - Test cumulative gains tracking
    - Test decimal precision
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [ ] 12.3 Test portfolio value calculator
    - Test USD to EUR conversion




    - Test rounding to 2 decimal places
    - _Requirements: 3.3, 3.4_
  
  - [x] 12.4 Test Excel writer




    - Test file creation with correct name
    - Test column headers and order
    - Test date formatting
    - Test monetary value formatting
    - Test summary row calculations
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [ ] 12.5 Test PDF writer
    - Test PDF file creation with correct name
    - Test table formatting
    - Test summary section
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 13. Create integration test

  - Create test script using example data from Flat_Tax_Crypto_Annuel_Complet_v2.xlsx
  - Mock Binance API responses with test data
  - Mock Frankfurter API responses with known exchange rates
  - Verify generated Excel matches expected output
  - Test PDF generation with --pdf flag
  - _Requirements: All requirements (end-to-end validation)_

- [ ] 14. Add error handling and edge cases

  - Handle case when no operations found for year
  - Handle Binance API rate limiting
  - Handle network timeouts
  - Add user-friendly error messages
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 15. Create documentation

  - Create README.md with installation instructions
  - Document how to obtain Binance API keys
  - Document binance_keys file format
  - Add usage examples with --pdf option
  - Document output file formats (Excel and PDF)
  - _Requirements: All requirements (user documentation)_
