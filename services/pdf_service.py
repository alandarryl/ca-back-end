from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from schemas.audit_schema import CompanyAuditSchema

def _format_content(content):
    """Convertit du texte ou des listes en paragraphes lisibles pour ReportLab."""
    if isinstance(content, list):
        return "<br/>".join([f"• {item}" for item in content])
    elif isinstance(content, dict):
        return "<br/>".join([f"<b>{k.upper()} :</b> {v}" for k, v in content.items()])
    return str(content)

def generate_audit_pdf(audit: CompanyAuditSchema, company_name: str = "Entreprise") -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    PRIMARY_COLOR = colors.HexColor("#1E3A8A")
    TEXT_COLOR = colors.HexColor("#1F2937")
    ACCENT_COLOR = colors.HexColor("#3B82F6")

    title_style = ParagraphStyle("DocTitle", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, textColor=PRIMARY_COLOR, spaceAfter=6)
    section_style = ParagraphStyle("SectionHeading", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, textColor=PRIMARY_COLOR, spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle("BodyTextCustom", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, textColor=TEXT_COLOR, spaceAfter=6)

    story = [
        Paragraph(f"Rapport d'Audit : {company_name}", title_style),
        HRFlowable(width="100%", thickness=1.5, color=ACCENT_COLOR, spaceAfter=10)
    ]

    sections_map = [
        ("Identité", audit.identite),
        ("Activité & Produits", audit.activite),
        ("Données Financières", audit.finances),
        ("Marché & Concurrence", audit.marche),
        ("Culture d'Entreprise", audit.culture),
        ("Actualités Récentes", audit.actualites),
        ("Analyse SWOT", audit.swot),
        ("Recommandations & Conseils", audit.conseils),
    ]

    for title, content in sections_map:
        story.append(Paragraph(title, section_style))
        story.append(Paragraph(_format_content(content), body_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    buffer.seek(0)
    return buffer