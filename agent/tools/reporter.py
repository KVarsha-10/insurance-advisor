"""
Report Generator — exports comparison results as PDF.
"""

import json
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import os


def generate_pdf_report(comparison: dict, output_path: str = "output/insurance_report.pdf"):
    os.makedirs("output", exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=13, textColor=colors.darkred)
    normal_style = styles['Normal']

    story.append(Paragraph("Insurance Comparison Report", title_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(f"Policyholder: {comparison.get('policyholder_name', 'N/A')}", normal_style))
    story.append(Paragraph(f"Current Plan: {comparison.get('current_plan_name', 'N/A')}", normal_style))
    story.append(Paragraph(f"New Plan: {comparison.get('new_plan_name', 'N/A')}", normal_style))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Weaknesses & Fixes", heading_style))
    for item in comparison.get("weaknesses_and_fixes", []):
        fixed = "✅ Fixed" if item.get("is_fixed") else "⚠️ Not Fixed"
        story.append(Paragraph(f"❌ {item.get('weakness', '')} [{item.get('impact', '')} Impact]", normal_style))
        story.append(Paragraph(f"   Current: {item.get('current_value', 'N/A')}", normal_style))
        story.append(Paragraph(f"   New: {item.get('new_value', 'N/A')} — {fixed}", normal_style))
        story.append(Paragraph(f"   {item.get('explanation', '')}", normal_style))
        story.append(Spacer(1, 0.1 * inch))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Premium Analysis", heading_style))
    premium = comparison.get("premium_analysis", {})
    data = [
        ["Item", "Value"],
        ["Current Premium", premium.get("current_premium", "N/A")],
        ["New Premium", premium.get("new_premium", "N/A")],
        ["Difference", premium.get("difference", "N/A")],
        ["Worth It?", "Yes" if premium.get("is_worth_it") else "No"],
    ]
    table = Table(data, colWidths=[2.5 * inch, 4 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))
    story.append(table)

    story.append(Spacer(1, 0.3 * inch))
    scores = comparison.get("overall_score", {})
    verdict = comparison.get("verdict", "N/A")
    story.append(Paragraph(f"Final Verdict: {verdict}", heading_style))
    story.append(Paragraph(f"Current Plan Score: {scores.get('current_plan_score', 'N/A')} / {scores.get('max_score', 10)}", normal_style))
    story.append(Paragraph(f"New Plan Score: {scores.get('new_plan_score', 'N/A')} / {scores.get('max_score', 10)}", normal_style))
    story.append(Paragraph(comparison.get("verdict_reasoning", ""), normal_style))

    doc.build(story)
    return output_path