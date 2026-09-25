from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from schemas.audit_schema import CompanyAuditSchema

def generate_audit_pdf(audit: CompanyAuditSchema) -> BytesIO:
    """
    Génère un document PDF en mémoire à partir des données d'un audit.
    """
    buffer = BytesIO()
    
    # Configuration du document (marges de 2 cm)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Palette de couleurs
    PRIMARY_COLOR = colors.HexColor("#1E3A8A")   # Bleu foncé
    TEXT_COLOR = colors.HexColor("#1F2937")      # Gris anthracite
    ACCENT_COLOR = colors.HexColor("#3B82F6")    # Bleu clair

    # Customisation des styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        textColor=PRIMARY_COLOR,
        spaceAfter=6
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=TEXT_COLOR,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "BulletCustom",
        parent=body_style,
        leftIndent=12,
        bulletIndent=4,
        spaceAfter=3
    )

    story = []

    # En-tête
    story.append(Paragraph(f"Audit d'Entreprise : {audit.company_name}", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_COLOR, spaceAfter=12))

    # Section 1 : Résumé
    story.append(Paragraph("Résumé de l'activité", section_style))
    story.append(Paragraph(audit.summary, body_style))

    # Section 2 : Produits et Services
    story.append(Paragraph("Produits & Services principaux", section_style))
    for item in audit.products_and_services:
        story.append(Paragraph(f"• {item}", bullet_style))

    # Section 3 : Culture d'entreprise
    story.append(Paragraph("Culture & Valeurs", section_style))
    for item in audit.company_culture:
        story.append(Paragraph(f"• {item}", bullet_style))

    # Section 4 : Questions d'entretien préparatoires
    story.append(Paragraph("Questions clés pour l'entretien", section_style))
    for item in audit.interview_questions:
        story.append(Paragraph(f"• {item}", bullet_style))

    # Section 5 : Actualités récentes
    story.append(Paragraph("Actualités & Faits marquants", section_style))
    for item in audit.recent_news:
        story.append(Paragraph(f"• {item}", bullet_style))

    # Construction du document
    doc.build(story)
    
    # Replacer le pointeur au début du buffer
    buffer.seek(0)
    return buffer