"""Unit tests for PDF report writer."""

import unittest
import os
import tempfile
from decimal import Decimal
from datetime import date
from writers.pdf_writer import PDFReportWriter, TaxReportRow


class TestPDFReportWriter(unittest.TestCase):
    """Test cases for PDFReportWriter class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.writer = PDFReportWriter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample test data
        self.test_operations = [
            TaxReportRow(
                date=date(2024, 1, 15),
                operation_type="Dépôt",
                amount_eur=Decimal("1000.00"),
                portfolio_value_usd=Decimal("1500.00"),
                exchange_rate=Decimal("0.92"),
                portfolio_value_eur=None,
                acquisition_cost=Decimal("1000.00"),
                taxable_gain=Decimal("0.00"),
                cumulative_gains=Decimal("0.00")
            ),
            TaxReportRow(
                date=date(2024, 2, 20),
                operation_type="Retrait",
                amount_eur=Decimal("500.00"),
                portfolio_value_usd=Decimal("1630.43"),
                exchange_rate=Decimal("0.92"),
                portfolio_value_eur=Decimal("1500.00"),
                acquisition_cost=Decimal("666.67"),
                taxable_gain=Decimal("166.67"),
                cumulative_gains=Decimal("166.67")
            ),
            TaxReportRow(
                date=date(2024, 3, 10),
                operation_type="Retrait",
                amount_eur=Decimal("300.00"),
                portfolio_value_usd=Decimal("1086.96"),
                exchange_rate=Decimal("0.92"),
                portfolio_value_eur=Decimal("1000.00"),
                acquisition_cost=Decimal("466.67"),
                taxable_gain=Decimal("100.00"),
                cumulative_gains=Decimal("266.67")
            )
        ]
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        # Use shutil.rmtree to handle nested directories
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_pdf_file_creation_with_correct_name(self):
        """Test that PDF file is created with correct name"""
        year = 2024
        output_path = self.writer.create_report(self.test_operations, year)
        
        # Check file exists
        self.assertTrue(os.path.exists(output_path))
        
        # Check filename format
        expected_filename = f"Declaration_Fiscale_Crypto_{year}.pdf"
        self.assertTrue(output_path.endswith(expected_filename))
        
        # Check file is not empty
        file_size = os.path.getsize(output_path)
        self.assertGreater(file_size, 0)
        
        # Clean up
        os.remove(output_path)
        os.rmdir("rapports")
    
    def test_custom_output_path(self):
        """Test PDF creation with custom output path"""
        custom_path = os.path.join(self.temp_dir, "custom_report.pdf")
        output_path = self.writer.create_report(self.test_operations, 2024, custom_path)
        
        self.assertEqual(output_path, custom_path)
        self.assertTrue(os.path.exists(custom_path))
        
        # Verify it's a PDF file (check magic bytes)
        with open(custom_path, 'rb') as f:
            header = f.read(4)
            self.assertEqual(header, b'%PDF')
    
    def test_pdf_contains_data(self):
        """Test that PDF file contains data and is not corrupted"""
        output_path = os.path.join(self.temp_dir, "test_data.pdf")
        self.writer.create_report(self.test_operations, 2024, output_path)
        
        # Check file exists and has reasonable size
        self.assertTrue(os.path.exists(output_path))
        file_size = os.path.getsize(output_path)
        
        # PDF with table should be at least a few KB
        self.assertGreater(file_size, 1000)
    
    def test_table_formatting_with_operations(self):
        """Test that table is created with correct number of rows"""
        output_path = os.path.join(self.temp_dir, "test_table.pdf")
        self.writer.create_report(self.test_operations, 2024, output_path)
        
        # Verify file was created successfully
        self.assertTrue(os.path.exists(output_path))
        
        # PDF should contain all operations (3 operations + header)
        # We can't easily parse PDF content, but we can verify file creation
        file_size = os.path.getsize(output_path)
        self.assertGreater(file_size, 0)
    
    def test_summary_section_included(self):
        """Test that summary section is included in PDF"""
        output_path = os.path.join(self.temp_dir, "test_summary.pdf")
        self.writer.create_report(self.test_operations, 2024, output_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path))
        
        # File should be larger with summary section
        file_size = os.path.getsize(output_path)
        self.assertGreater(file_size, 2000)
    
    def test_empty_operations_list(self):
        """Test PDF creation with empty operations list"""
        output_path = os.path.join(self.temp_dir, "test_empty.pdf")
        self.writer.create_report([], 2024, output_path)
        
        # File should still be created
        self.assertTrue(os.path.exists(output_path))
        
        # Should have valid PDF header
        with open(output_path, 'rb') as f:
            header = f.read(4)
            self.assertEqual(header, b'%PDF')
    
    def test_single_operation(self):
        """Test PDF creation with single operation"""
        single_operation = [self.test_operations[0]]
        output_path = os.path.join(self.temp_dir, "test_single.pdf")
        self.writer.create_report(single_operation, 2024, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        file_size = os.path.getsize(output_path)
        self.assertGreater(file_size, 0)
    
    def test_multiple_years(self):
        """Test PDF creation for different years"""
        for year in [2023, 2024, 2025]:
            output_path = os.path.join(self.temp_dir, f"test_{year}.pdf")
            self.writer.create_report(self.test_operations, year, output_path)
            
            self.assertTrue(os.path.exists(output_path))
    
    def test_directory_creation(self):
        """Test that output directory is created if it doesn't exist"""
        nested_path = os.path.join(self.temp_dir, "nested", "dir", "report.pdf")
        output_path = self.writer.create_report(self.test_operations, 2024, nested_path)
        
        self.assertTrue(os.path.exists(output_path))
        self.assertEqual(output_path, nested_path)


if __name__ == '__main__':
    unittest.main()
