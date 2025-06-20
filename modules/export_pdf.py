from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from datetime import datetime

def generer_rapport_pdf(nom_projet, partie, date, indice, beton, fyk, b, h, enrobage, M_inf, M_sup, V, V_lim):
    from pathlib import Path
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    file_path = f"{nom_projet or 'rapport_poutre'}_{datetime.today().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    story = []

    def add_title(text):
        story.append(Paragraph(f"<b>{text}</b>", styles["Heading2"]))
        story.append(Spacer(1, 12))

    def add_para(text):
        story.append(Paragraph(text, styles["Normal"]))
        story.append(Spacer(1, 8))

    def add_table(data):
        t = Table(data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

    # Titre
    add_title("Rapport de dimensionnement - Poutre en béton armé")

    # Infos projet
    add_para(f"Projet : {nom_projet or '-'}")
    add_para(f"Partie : {partie or '-'}")
    add_para(f"Date : {date or datetime.today().strftime('%d/%m/%Y')}   |   Indice : {indice or '0'}")

    # Paramètres géométriques et matériaux
    add_title("Caractéristiques de la poutre")
    add_table([
        ["Paramètre", "Valeur"],
        ["Classe béton", beton],
        ["Qualité acier", f"{fyk} N/mm²"],
        ["Largeur (b)", f"{b:.1f} cm"],
        ["Hauteur (h)", f"{h:.1f} cm"],
        ["Enrobage", f"{enrobage:.1f} cm"]
    ])

    # Sollicitations
    add_title("Sollicitations")
    add_table([
        ["Effort", "Valeur"],
        ["Moment inférieur", f"{M_inf:.2f} kN.m"],
        ["Moment supérieur", f"{M_sup:.2f} kN.m"] if M_sup else ["Moment supérieur", "-"],
        ["Effort tranchant", f"{V:.2f} kN"],
        ["Effort tranchant réduit", f"{V_lim:.2f} kN"] if V_lim else ["Effort tranchant réduit", "-"]
    ])

    # Formule hauteur utile
    alpha_b = 0.85
    mu_val = 12.96
    Mmax = max(abs(M_inf), abs(M_sup))
    h_min = ((alpha_b * Mmax * 1e6) / (0.1708 * b * 10 * mu_val))**0.5 / 10
    add_title("Hauteur utile minimale")
    add_para(f"h = √((0,85 × {Mmax:.1f}×10⁶)/(0,1708 × {b*10:.0f}mm × 12,96)) = {h_min:.1f} cm")

    # Armatures
    d = h - enrobage
    fyd = int(fyk) / 1.5
    As_inf = (M_inf * 1e6) / (fyd * 0.9 * d * 10)
    As_sup = (M_sup * 1e6) / (fyd * 0.9 * d * 10) if M_sup else 0

    add_title("Armatures")
    add_table([
        ["Zone", "Moment", "Formule", "Résultat"],
        ["Inférieure", f"{M_inf:.1f} kN.m", f"(M × 10⁶)/(fyd × 0.9 × d × 10)", f"{As_inf:.0f} mm²"],
        ["Supérieure", f"{M_sup:.1f} kN.m", f"(M × 10⁶)/(fyd × 0.9 × d × 10)", f"{As_sup:.0f} mm²"] if M_sup else ["Supérieure", "-", "-", "-"]
    ])

    doc.build(story)
    print(f"PDF généré : {file_path}")
