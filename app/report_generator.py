"""
Report generator module for creating professional PDF reports.

Generates PDF documents with scores, explanations, visualizations, and recommendations.
Uses reportlab for lightweight PDF generation without external services.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from io import BytesIO
from datetime import datetime
import base64


def generate_pdf_report(
    location: str,
    store_type: str,
    radius_km: float,
    demand_score: float,
    competition_score: float,
    accessibility_score: float,
    diversity_score: float,
    viability_score: float,
    recommendation: str,
    explanation: str,
    chart_image_base64: str = None,
    map_image_base64: str = None
) -> bytes:
    """
    Generate a professional PDF report for a location analysis.
    
    Args:
        location: Location name
        store_type: Type of store analyzed
        radius_km: Search radius in kilometers
        demand_score: Demand metric (0-100)
        competition_score: Competition metric (0-100)
        accessibility_score: Accessibility metric (0-100)
        diversity_score: Diversity metric (0-100)
        viability_score: Overall viability score (0-100)
        recommendation: Recommendation text
        explanation: Executive summary/explanation
        chart_image_base64: Base64-encoded radar chart image
        map_image_base64: Base64-encoded map image
        
    Returns:
        PDF bytes ready for download
    """
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Build document
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77d2'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=12
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leading=14
    )
    
    # Title
    story.append(Paragraph("🗺️ SiteSense AI – Location Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Executive Summary Section
    story.append(Paragraph("Executive Summary", heading_style))
    
    summary_data = [
        ["Location", location],
        ["Store Type", store_type],
        ["Search Radius", f"{radius_km} km"],
        ["Report Date", datetime.now().strftime("%B %d, %Y at %I:%M %p")]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Viability Assessment
    story.append(Paragraph("Viability Assessment", heading_style))
    
    # Color coding for recommendation
    rec_color = colors.HexColor('#27ae60') if viability_score > 60 else (
        colors.HexColor('#f39c12') if viability_score > 40 else colors.HexColor('#e74c3c')
    )
    
    assessment_data = [
        ["Viability Score", f"{viability_score:.1f} / 100"],
        ["Recommendation", recommendation]
    ]
    
    assessment_table = Table(assessment_data, colWidths=[2*inch, 4*inch])
    assessment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('BACKGROUND', (1, 0), (1, 0), rec_color if viability_score > 60 else colors.HexColor('#fff3cd') if viability_score > 40 else colors.HexColor('#f8d7da')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
    ]))
    
    story.append(assessment_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Score Breakdown
    story.append(Paragraph("Score Breakdown", heading_style))
    
    scores_data = [
        ["Metric", "Score", "Assessment"],
        ["Demand", f"{demand_score:.1f}", "Market demand based on POI density"],
        ["Competition", f"{competition_score:.1f}", "Competitive pressure in the area"],
        ["Accessibility", f"{accessibility_score:.1f}", "Public transport & road connectivity"],
        ["Diversity", f"{diversity_score:.1f}", "Economic diversity & mixed-use"]
    ]
    
    scores_table = Table(scores_data, colWidths=[1.5*inch, 1*inch, 3.5*inch])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77d2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7'))
    ]))
    
    story.append(scores_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Explanation
    story.append(Paragraph("Executive Explanation", heading_style))
    story.append(Paragraph(explanation, body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Add charts if available
    if chart_image_base64:
        story.append(PageBreak())
        story.append(Paragraph("Score Profile Visualization", heading_style))
        
        try:
            # Decode base64 image
            image_data = base64.b64decode(chart_image_base64)
            img_buffer = BytesIO(image_data)
            img = Image(img_buffer, width=5*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.3*inch))
        except:
            pass
    
    if map_image_base64:
        story.append(Paragraph("Location Map", heading_style))
        
        try:
            # Decode base64 image
            image_data = base64.b64decode(map_image_base64)
            img_buffer = BytesIO(image_data)
            img = Image(img_buffer, width=5*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 0.3*inch))
        except:
            pass
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_text = f"Report generated by SiteSense AI on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1
    )))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
