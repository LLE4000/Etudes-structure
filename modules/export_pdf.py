from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

def generer_rapport_pdf(nom_projet, partie, date, indice, beton, fyk, b, h, enrobage, M_inf, M_sup, V, V_lim):
    nom_fichier = f"rapport_{nom_projet.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(nom_fichier, pagesize=A4,
                            rightMargin=2 * cm, leftMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitreSection', fontSize=14, leading=16, spaceAfter=12, textColor=colors.HexColor('#003366'), alignment=0, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='Texte', fontSize=10, leading=14))
    styles.add(ParagraphStyle(name='Formule', fontSize=9, leading=12, textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='Note', fontSize=9, leading=12, textColor=colors.grey))

    elements = []

    elements.append(Paragraph("Rapport de dimensionnement – Poutre en béton armé", styles['TitreSection']))
    infos = f"<b>Projet :</b> {nom_projet} &nbsp;&nbsp;&nbsp; <b>Partie :</b> {partie}<br/><b>Date :</b> {date} &nbsp;&nbsp;&nbsp; <b>Indice :</b> {indice}"
    elements.append(Paragraph(infos, styles['Texte']))
    elements.append(Spacer(1, 1.2 * cm))

    elements.append(Paragraph("Caractéristiques de la poutre", styles['TitreSection']))
    data = [
        ["Classe de béton", beton],
        ["Acier (fyk)", f"{fyk} N/mm²"],
        ["Dimensions (b x h)", f"{b} cm x {h} cm"],
        ["Enrobage", f"{enrobage} cm"]
    ]
    table = Table(data, hAlign='LEFT', colWidths=[6 * cm, 6 * cm])
    table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 1.2 * cm))

    elements.append(Paragraph("Moments fléchissants", styles['TitreSection']))
    moments_text = f"Moment inférieur M<sub>inf</sub> = {M_inf:.1f} kN.m"
    if M_sup > 0:
        moments_text += f"<br/>Moment supérieur M<sub>sup</sub> = {M_sup:.1f} kN.m"
    elements.append(Paragraph(moments_text, styles['Texte']))
    elements.append(Spacer(1, 1.2 * cm))

    elements.append(Paragraph("Note : Rapport généré automatiquement via l'application Streamlit.", styles['Note']))
    doc.build(elements)
    return nom_fichier
