"""
PDF Report Writer for Binance Tax Reports.

This module generates formatted PDF files containing French tax calculations
for cryptocurrency operations.
"""

import os
from decimal import Decimal
from datetime import date
from dataclasses import dataclass
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from utils.logger import get_logger


class PDFWriterError(Exception):
    """Exception raised for PDF writer errors."""
    pass


@dataclass
class TaxReportRow:
    """Complete row for PDF report"""
    date: date
    operation_type: str  # "Dépôt" or "Retrait"
    amount_eur: Decimal
    portfolio_value_usd: Decimal
    exchange_rate: Decimal
    portfolio_value_eur: Optional[Decimal]  # None for deposits
    acquisition_cost: Decimal
    taxable_gain: Decimal
    cumulative_gains: Decimal


class PDFReportWriter:
    """Generates PDF tax report with proper formatting"""
    
    # Column headers in the exact order required
    COLUMN_HEADERS = [
        "Date",
        "Type d'opération",
        "Montant\nEUR",
        "Valeur\nUSD",
        "Taux\nUSD/EUR",
        "Valeur\nEUR",
        "Acquisition\nEUR",
        "Plus-value\nEUR",
        "Cumul\nEUR"
    ]
    
    def __init__(self):
        """Initialize the PDF report writer"""
        self.logger = get_logger()
    
    def create_report(self, operations: List[TaxReportRow], year: int, 
                     output_path: Optional[str] = None) -> str:
        """
        Create PDF report file.
        
        Args:
            operations: List of processed operations with tax calculations
            year: Fiscal year
            output_path: Path for output file (optional, defaults to standard name)
            
        Returns:
            Path to the created file
            
        Raises:
            PDFWriterError: If file creation fails
        """
        try:
            # Generate default filename if not provided
            if output_path is None:
                # Create rapports directory if it doesn't exist
                try:
                    os.makedirs("rapports", exist_ok=True)
                except OSError as e:
                    self.logger.error(f"Failed to create rapports directory: {e}")
                    raise PDFWriterError(f"Failed to create output directory: {e}")
                
                output_path = f"rapports/Declaration_Fiscale_Crypto_{year}.pdf"
            else:
                # Ensure the directory exists for custom paths
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    try:
                        os.makedirs(output_dir, exist_ok=True)
                    except OSError as e:
                        self.logger.error(f"Failed to create output directory '{output_dir}': {e}")
                        raise PDFWriterError(f"Failed to create output directory: {e}")
            
            # Check if file is writable (not locked by another process)
            if os.path.exists(output_path):
                try:
                    # Try to open the file to check if it's locked
                    with open(output_path, 'a'):
                        pass
                except IOError:
                    self.logger.error(f"Output file '{output_path}' is locked or not writable")
                    raise PDFWriterError(
                        f"Cannot write to '{output_path}'. "
                        "The file may be open in another program. Please close it and try again."
                    )
            
            self.logger.info(f"Creating PDF report: {output_path}")
            
            # Create PDF document in landscape mode for better table fit
            doc = SimpleDocTemplate(
                output_path,
                pagesize=landscape(A4),
                rightMargin=1*cm,
                leftMargin=1*cm,
                topMargin=1.5*cm,
                bottomMargin=1.5*cm
            )
            
            # Build document content
            story = []
            
            # Add title
            story.extend(self._create_title(year))
            
            # Add data table
            story.append(self._create_data_table(operations))
            
            # Add summary section
            story.extend(self._create_summary_section(operations))
            
            # Build PDF
            try:
                doc.build(story)
                self.logger.info(f"PDF report saved successfully: {output_path}")
            except IOError as e:
                self.logger.error(f"Failed to save PDF file: {e}")
                raise PDFWriterError(
                    f"Failed to save PDF file '{output_path}'. "
                    "Please check file permissions and ensure the file is not open in another program."
                )
            
            return output_path
            
        except PDFWriterError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating PDF report: {e}")
            raise PDFWriterError(f"Unexpected error creating PDF report: {e}")

    def _create_title(self, year: int) -> List:
        """
        Create title section for the PDF.
        
        Args:
            year: Fiscal year
            
        Returns:
            List of reportlab elements for the title
        """
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        title = Paragraph(
            f"Déclaration Fiscale Crypto - Année {year}",
            title_style
        )
        
        return [title, Spacer(1, 0.5*cm)]
    
    def _create_data_table(self, operations: List[TaxReportRow]) -> Table:
        """
        Create formatted data table for the PDF.
        
        Args:
            operations: List of tax report rows
            
        Returns:
            reportlab Table object
        """
        # Prepare table data
        table_data = [self.COLUMN_HEADERS]
        
        # Add data rows
        for operation in operations:
            row = [
                operation.date.strftime("%Y-%m-%d"),
                operation.operation_type,
                f"{float(operation.amount_eur):.2f}",
                f"{float(operation.portfolio_value_usd):.2f}",
                f"{float(operation.exchange_rate):.2f}",
                f"{float(operation.portfolio_value_eur):.2f}" if operation.portfolio_value_eur is not None else "",
                f"{float(operation.acquisition_cost):.2f}",
                f"{float(operation.taxable_gain):.2f}",
                f"{float(operation.cumulative_gains):.2f}"
            ]
            table_data.append(row)
        
        # Create table with appropriate column widths
        col_widths = [2.2*cm, 3*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2.2*cm, 2.2*cm, 2*cm]
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Apply table styling
        table_style = TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#D3D3D3')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Date column
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Operation type column
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # All numeric columns
            ('TOPPADDING', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternating row colors for better readability
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')])
        ])
        
        table.setStyle(table_style)
        
        return table
    
    def _create_summary_section(self, operations: List[TaxReportRow]) -> List:
        """
        Create summary section with totals.
        
        Args:
            operations: List of tax report rows
            
        Returns:
            List of reportlab elements for the summary
        """
        if not operations:
            return []
        
        # Calculate totals
        total_deposits = sum(
            op.amount_eur for op in operations if op.operation_type == "Dépôt"
        )
        total_withdrawals = sum(
            op.amount_eur for op in operations if op.operation_type == "Retrait"
        )
        total_taxable_gains = operations[-1].cumulative_gains if operations else Decimal("0")
        
        # Create summary table
        summary_data = [
            ["Total Dépôts:", f"{float(total_deposits):.2f} EUR"],
            ["Total Retraits:", f"{float(total_withdrawals):.2f} EUR"],
            ["Total Plus-values Imposables:", f"{float(total_taxable_gains):.2f} EUR"]
        ]
        
        summary_table = Table(summary_data, colWidths=[6*cm, 4*cm])
        
        summary_style = TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            
            # Highlight the total taxable gains row
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#FFFF00')),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            
            # Add borders
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.grey),
            ('LINEABOVE', (0, 2), (-1, 2), 0.5, colors.grey)
        ])
        
        summary_table.setStyle(summary_style)
        
        # Create summary section with title
        styles = getSampleStyleSheet()
        summary_title_style = ParagraphStyle(
            'SummaryTitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        summary_title = Paragraph("Résumé", summary_title_style)
        
        return [
            Spacer(1, 1*cm),
            summary_title,
            summary_table
        ]
