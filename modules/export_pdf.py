from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                 Image, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import matplotlib.pyplot as plt
import io
import traceback
import math
from datetime import datetime

def generer_rapport_pdf(nom_projet, partie, date, indice, beton, fyk, b, h, enrobage, M_inf, M_sup, V, V_lim):
    try:
        # Vérification des entrées
        for var_name, value in [("fyk", fyk), ("b", b), ("h", h), ("enrobage", enrobage),
                                ("M_inf", M_inf), ("M_sup", M_sup), ("V", V), ("V_lim", V_lim)]:
            if value in ("", None):
                raise ValueError(f"Erreur : la valeur de {var_name} est vide ou invalide.")

        # Conversion sécurisée
        fyk = float(fyk)
        b = float(b)
        h = float(h)
        enrobage = float(enrobage)
        M_inf = float(M_inf)
        M_sup = float(M_sup)
        V = float(V)
        V_lim = float(V_lim)

        # Constantes et calculs
        fyd = fyk / 1.15
        mu = 12.96
        d = h - enrobage

        nom_fichier = f"rapport_{nom_projet.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(nom_fichier, pagesize=A4,
                                rightMargin=2 * cm, leftMargin=2 * cm,
                                topMargin=2 * cm, bottomMargin=2 * cm)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TitreSection', fontSize=14, leading=16, spaceAfter=12,
                                  textColor=colors.HexColor('#003366'), alignment=0, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name='Texte', fontSize=10, leading=14))
        styles.add(ParagraphStyle(name='Formule', fontSize=9, leading=12, textColor=colors.darkblue))

        elements = []

        # --- En-tête ---
        elements.append(Paragraph("Rapport de dimensionnement – Poutre en béton armé", styles['TitreSection']))

        data_header = [
            ["Projet :", nom_projet, "Date :", date],
            ["Partie :", partie, "Indice :", indice]
        ]
        table_header = Table(data_header, colWidths=[3*cm, 6*cm, 2*cm, 4*cm])
        elements.append(table_header)
        elements.append(Spacer(1, 12))

        # --- Caractéristiques ---
        elements.append(Paragraph("Caractéristiques de la poutre", styles['TitreSection']))
        data = [
            ["Classe de béton", beton],
            ["Acier (fyk)", f"{fyk:.0f} N/mm²"],
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

        # --- Sollicitations ---
        elements.append(Paragraph("Sollicitations", styles['TitreSection']))
        elements.append(Paragraph(f"Moment inférieur M_inf = {M_inf:.1f} kN·m", styles['Texte']))
        if M_sup > 0:
            elements.append(Paragraph(f"Moment supérieur M_sup = {M_sup:.1f} kN·m", styles['Texte']))
        elements.append(Paragraph(f"Effort tranchant V = {V:.1f} kN", styles['Texte']))
        if V_lim > 0:
            elements.append(Paragraph(f"Effort tranchant réduit V_lim = {V_lim:.1f} kN", styles['Texte']))
        elements.append(Spacer(1, 12))

        # --- Hauteur utile ---
        elements.append(Paragraph("Vérification de la hauteur utile", styles['TitreSection']))
        d_calcule = ((M_inf * 1e6) / (0.1708 * b * 10 * mu)) ** 0.5 / 10
        d_min_total = d_calcule + enrobage

        fig, ax = plt.subplots(figsize=(1.97, 0.6))
        ax.axis("off")
        latex_formula = (
            rf"$\sqrt{{\frac{{{M_inf:.1f} \cdot 10^6}}{{0.1708 \cdot {b:.0f} \cdot 10 \cdot {mu:.2f}}}}}$"
        )
        ax.text(0.5, 0.5, latex_formula, ha="center", va="center", fontsize=11)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', transparent=True)
        plt.close(fig)
        buf.seek(0)
        elements.append(Paragraph("h<sub>min</sub> =", styles['Texte']))
        elements.append(Image(buf, width=5 * cm))
        elements.append(Paragraph(f"h<sub>min</sub> + enrobage = {d_min_total:.1f} cm ≤ h = {h:.1f} cm", styles['Texte']))
        elements.append(PageBreak())

        # --- Armatures inférieures ---
        elements.append(Paragraph("Armatures inférieures", styles['TitreSection']))
        As_inf = (M_inf * 1e6) / (fyd * 0.9 * d * 10)
        As_min = 0.0013 * b * h * 100
        As_max = 0.04 * b * h * 100
        elements.append(Paragraph(f"d = h - enrobage = {d:.1f} cm", styles['Texte']))
        elements.append(Paragraph(f"f<sub>yd</sub> = f<sub>yk</sub> / 1.15 = {fyd:.1f} N/mm²", styles['Texte']))

        fig2, ax2 = plt.subplots(figsize=(1.97, 0.6))
        ax2.axis("off")
        latex_as = rf"$A_s = \frac{{M}}{{f_{{yd}} \cdot 0.9 \cdot d}}$"
        ax2.text(0.5, 0.5, latex_as, ha="center", va="center", fontsize=11)
        buf2 = io.BytesIO()
        plt.savefig(buf2, format='png', dpi=300, bbox_inches='tight', transparent=True)
        plt.close(fig2)
        buf2.seek(0)
        elements.append(Image(buf2, width=5 * cm))

        elements.append(Paragraph(f"As<sub>inf</sub> = {As_inf:.1f} mm²", styles['Texte']))
        elements.append(Paragraph(f"As<sub>min</sub> = {As_min:.1f} mm², As<sub>max</sub> = {As_max:.1f} mm²", styles['Texte']))
        elements.append(Spacer(1, 12))

        # --- Armatures supérieures ---
        if M_sup > 0:
            elements.append(Paragraph("Armatures supérieures", styles['TitreSection']))
            As_sup = (M_sup * 1e6) / (fyd * 0.9 * d * 10)
            elements.append(Paragraph(f"As<sub>sup</sub> = {As_sup:.1f} mm²", styles['Texte']))
            elements.append(Spacer(1, 12))

        # --- Vérification effort tranchant ---
        elements.append(Paragraph("Vérification de l'effort tranchant", styles['TitreSection']))
        tau = (V * 1e3) / (0.75 * b * h * 100)
        tau_adm = 0.6
        elements.append(Paragraph(f"τ = {tau:.2f} N/mm²", styles['Texte']))
        elements.append(Paragraph(f"τ<sub>adm</sub> = {tau_adm:.2f} N/mm²", styles['Texte']))
        elements.append(Paragraph("✔️ τ ≤ τ<sub>adm</sub> → pas d’étriers nécessaires" if tau <= tau_adm
                                  else "❌ τ > τ<sub>adm</sub> → étriers nécessaires", styles['Texte']))
        elements.append(Spacer(1, 12))

        # --- Effort tranchant réduit ---
        if V_lim > 0:
            elements.append(Paragraph("Vérification de l'effort tranchant réduit", styles['TitreSection']))
            tau_r = (V_lim * 1e3) / (0.75 * b * h * 100)
            elements.append(Paragraph(f"τ<sub>réduit</sub> = {tau_r:.2f} N/mm²", styles['Texte']))
            elements.append(Paragraph("✔️ τ<sub>réduit</sub> ≤ τ<sub>adm</sub> → pas d’étriers nécessaires" if tau_r <= tau_adm
                                      else "❌ τ<sub>réduit</sub> > τ<sub>adm</sub> → étriers nécessaires", styles['Texte']))
            elements.append(Spacer(1, 12))

        doc.build(elements)
        return nom_fichier

    except Exception as err:
        raise ValueError("Erreur dans la génération du PDF :\n" + traceback.format_exc())
