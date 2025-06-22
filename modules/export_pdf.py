
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import matplotlib.pyplot as plt
import io
import traceback

def generer_rapport_pdf(nom_projet, partie, date, indice, beton, fyk, b, h, enrobage, M_inf, M_sup, V, V_lim):
    try:
        nom_fichier = f"rapport_{nom_projet.replace(' ', '_')}.pdf"
        doc = SimpleDocTemplate(nom_fichier, pagesize=A4,
                                rightMargin=2 * cm, leftMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)

        # Styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TitreSection', fontSize=14, leading=16, spaceAfter=12,
                                  textColor=colors.HexColor('#003366'), alignment=0, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name='Texte', fontSize=10, leading=14))
        styles.add(ParagraphStyle(name='Formule', fontSize=9, leading=12, textColor=colors.darkblue))

        elements = []

        # Titre
        elements.append(Paragraph("Rapport de dimensionnement – Poutre en béton armé", styles['TitreSection']))

        # En-tête
        data_header = [
            ["Projet :", nom_projet, "Date :", date],
            ["Partie :", partie, "Indice :", indice]
        ]
        table_header = Table(data_header, colWidths=[3*cm, 6*cm, 2*cm, 4*cm])
        elements.append(table_header)
        elements.append(Spacer(1, 12))

        # Caractéristiques
        elements.append(Paragraph("Caractéristiques de la poutre", styles['TitreSection']))
        data = [
            ["Classe de béton", beton],
            ["Acier (fyk)", f"{fyk} N/mm²"],
            ["Largeur (b)", f"{b} cm"],
            ["Hauteur (h)", f"{h} cm"],
            ["Enrobage", f"{enrobage} cm"]
        ]
        table = Table(data, hAlign='LEFT', colWidths=[6 * cm, 6 * cm])
        table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # Sollicitations
        elements.append(Paragraph("Sollicitations", styles['TitreSection']))
        elements.append(Paragraph(f"Moment inférieur Minf = {M_inf:.1f} kN·m", styles['Texte']))
        if M_sup > 0:
            elements.append(Paragraph(f"Moment supérieur Msup = {M_sup:.1f} kN·m", styles['Texte']))
        elements.append(Paragraph(f"Effort tranchant V = {V:.1f} kN", styles['Texte']))
        if V_lim > 0:
            elements.append(Paragraph(f"Effort tranchant réduit Vlim = {V_lim:.1f} kN", styles['Texte']))
        elements.append(Spacer(1, 12))

        # Vérification hauteur utile
        elements.append(Paragraph("Vérification de la hauteur utile", styles['TitreSection']))
        mu = 12.96
        d_calcule = ((M_inf * 1e6) / (0.1708 * b * 10 * mu)) ** 0.5 / 10
        d_min_total = d_calcule + enrobage

        # Formule LaTeX en image
        # Formule LaTeX en image – corrigée, non déformée
        fig, ax = plt.subplots(figsize=(2, 0.8))  # Taille plus équilibrée
        ax.axis("off")
        latex_formula = (
        rf"$h_{{min}} = \sqrt{{\frac{{{M_inf:.1f} \cdot 10^6}}{{0.1708 \cdot {b} \cdot 10 \cdot {mu}}}}} = {d_calcule:.1f}\,\mathrm{{cm}}$"
        )
        ax.text(0.5, 0.5, latex_formula, ha="center", va="center", fontsize=11)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', transparent=True)
        plt.close(fig)
        buf.seek(0)
        elements.append(Image(buf, width=12 * cm))  # On ne force plus la hauteur

        elements.append(Paragraph(f"hmin + enrobage = {d_min_total:.1f} cm ≤ h = {h:.1f} cm", styles['Texte']))
        elements.append(Spacer(1, 12))

        # Génération du PDF
        doc.build(elements)
        return nom_fichier

    except Exception as err:
        raise ValueError("Erreur dans la génération du PDF :\n" + traceback.format_exc())
