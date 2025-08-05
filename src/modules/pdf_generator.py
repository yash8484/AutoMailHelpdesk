import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import os

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    PDF generation utility for bank statements and other documents.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """
        Setup custom paragraph styles.
        """
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
    
    def generate_bank_statement(
        self,
        customer_data: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        months: int = 6,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate bank statement PDF.
        """
        try:
            # Create output path if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"/tmp/bank_statement_{timestamp}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Title
            title = Paragraph("Bank Statement", self.styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Customer information
            story.append(Paragraph("Account Information", self.styles['CustomHeading']))
            
            customer_info = [
                ["Account Holder:", customer_data.get('name', 'N/A')],
                ["Account Number:", customer_data.get('account_number', 'N/A')],
                ["Account Type:", customer_data.get('account_type', 'N/A')],
                ["Statement Period:", f"{months} months"],
                ["Generated On:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            ]
            
            customer_table = Table(customer_info, colWidths=[2*inch, 3*inch])
            customer_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(customer_table)
            story.append(Spacer(1, 20))
            
            # Account summary
            story.append(Paragraph("Account Summary", self.styles['CustomHeading']))
            
            # Calculate summary
            total_credits = sum(t.get('amount', 0) for t in transactions if t.get('amount', 0) > 0)
            total_debits = sum(abs(t.get('amount', 0)) for t in transactions if t.get('amount', 0) < 0)
            current_balance = customer_data.get('current_balance', 0)
            
            summary_info = [
                ["Opening Balance:", f"${customer_data.get('opening_balance', 0):,.2f}"],
                ["Total Credits:", f"${total_credits:,.2f}"],
                ["Total Debits:", f"${total_debits:,.2f}"],
                ["Closing Balance:", f"${current_balance:,.2f}"]
            ]
            
            summary_table = Table(summary_info, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Transaction history
            if transactions:
                story.append(Paragraph("Transaction History", self.styles['CustomHeading']))
                
                # Prepare transaction data
                transaction_data = [["Date", "Description", "Amount", "Balance"]]
                
                for transaction in transactions:
                    transaction_data.append([
                        transaction.get('date', ''),
                        transaction.get('description', '')[:40] + ('...' if len(transaction.get('description', '')) > 40 else ''),
                        f"${transaction.get('amount', 0):,.2f}",
                        f"${transaction.get('balance', 0):,.2f}"
                    ])
                
                # Create transaction table
                transaction_table = Table(
                    transaction_data,
                    colWidths=[1.2*inch, 2.8*inch, 1*inch, 1*inch]
                )
                
                transaction_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (2, 1), (3, -1), 'RIGHT'),  # Right align amounts
                ]))
                
                story.append(transaction_table)
            
            # Footer
            story.append(Spacer(1, 30))
            footer_text = "This statement is generated automatically. For any discrepancies, please contact customer support."
            footer = Paragraph(footer_text, self.styles['Normal'])
            story.append(footer)
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Generated bank statement PDF: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating bank statement PDF: {e}")
            raise
    
    def generate_receipt(
        self,
        transaction_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate transaction receipt PDF.
        """
        try:
            # Create output path if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"/tmp/receipt_{timestamp}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Title
            title = Paragraph("Transaction Receipt", self.styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Transaction details
            receipt_data = [
                ["Transaction ID:", transaction_data.get('transaction_id', 'N/A')],
                ["Date:", transaction_data.get('date', 'N/A')],
                ["Amount:", f"${transaction_data.get('amount', 0):,.2f}"],
                ["Description:", transaction_data.get('description', 'N/A')],
                ["Account:", transaction_data.get('account_number', 'N/A')],
                ["Status:", transaction_data.get('status', 'N/A')]
            ]
            
            receipt_table = Table(receipt_data, colWidths=[2*inch, 3*inch])
            receipt_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(receipt_table)
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Generated receipt PDF: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating receipt PDF: {e}")
            raise
    
    def generate_report(
        self,
        title: str,
        content: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate generic report PDF.
        """
        try:
            # Create output path if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_path = f"/tmp/{safe_title.replace(' ', '_')}_{timestamp}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            
            # Title
            title_para = Paragraph(title, self.styles['CustomTitle'])
            story.append(title_para)
            story.append(Spacer(1, 20))
            
            # Add content sections
            for section in content:
                if section.get('type') == 'heading':
                    heading = Paragraph(section.get('text', ''), self.styles['CustomHeading'])
                    story.append(heading)
                    story.append(Spacer(1, 10))
                
                elif section.get('type') == 'paragraph':
                    para = Paragraph(section.get('text', ''), self.styles['Normal'])
                    story.append(para)
                    story.append(Spacer(1, 10))
                
                elif section.get('type') == 'table':
                    table_data = section.get('data', [])
                    if table_data:
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, -1), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ]))
                        story.append(table)
                        story.append(Spacer(1, 15))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Generated report PDF: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating report PDF: {e}")
            raise
    
    # TODO: Add more PDF generation methods as needed

