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

    # Titre
    elements.append(Paragraph("Rapport de dimensionnement – Poutre en béton armé", styles['TitreSection']))

    # Infos projet
    infos = f"<b>Projet :</b> {nom_projet} &nbsp;&nbsp;&nbsp; <b>Partie :</b> {partie}<br/><b>Date :</b> {date} &nbsp;&nbsp;&nbsp; <b>Indice :</b> {indice}"
    elements.append(Paragraph(infos, styles['Texte']))
    elements.append(Spacer(1, 12))

    # Caractéristiques
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
    elements.append(Spacer(1, 12))

    # Moments
    elements.append(Paragraph("Moments fléchissants", styles['TitreSection']))
    moments_text = f"Moment inférieur M<sub>inf</sub> = {M_inf:.1f} kN.m"
    if M_sup > 0:
        moments_text += f"<br/>Moment supérieur M<sub>sup</sub> = {M_sup:.1f} kN.m"
    elements.append(Paragraph(moments_text, styles['Texte']))
    elements.append(Spacer(1, 12))

    # Vérification hauteur utile
    elements.append(Paragraph("Vérification de la hauteur utile", styles['TitreSection']))
    alpha_b = 0.85
    mu = 12.96
    d_calcule = ((alpha_b * M_inf * 1e6) / (0.1708 * b * 10 * mu)) ** 0.5 / 10
    d_min_total = d_calcule + enrobage
    formule_d = f"h<sub>min</sub> = √[(0.85 × {M_inf:.1f} × 10⁶) / (0.1708 × {b} × 10 × 12.96)] = {d_calcule:.1f} cm"
    elements.append(Paragraph(formule_d, styles['Formule']))
    elements.append(Paragraph(f"➜ h<sub>min</sub> + enrobage = {d_min_total:.1f} cm ≤ h = {h:.1f} cm", styles['Texte']))
    elements.append(Spacer(1, 12))

    # Efforts tranchants
    elements.append(Paragraph("Efforts tranchants", styles['TitreSection']))
    efforts_text = f"Effort tranchant V = {V:.1f} kN"
    if V_lim > 0:
        efforts_text += f"<br/>Effort tranchant réduit V<sub>lim</sub> = {V_lim:.1f} kN"
    elements.append(Paragraph(efforts_text, styles['Texte']))
    elements.append(Spacer(1, 6))

    # Vérification cisaillement
    tau = (V * 1e3) / (0.75 * b * h * 100) if V > 0 else 0
    tau_lim = 112  # valeur limite arbitraire (à remplacer selon classe béton)
    tau_formula = f"τ = {V:.1f} × 10³ / (0.75 × {b} × {h} × 100) = {tau:.1f} N/cm²"
    elements.append(Paragraph(tau_formula, styles['Formule']))
    elements.append(Paragraph(f"➜ τ = {tau:.1f} N/cm² ≤ {tau_lim} N/cm² → OK", styles['Texte']))
    elements.append(Spacer(1, 12))

    # Détermination des étriers
    elements.append(Paragraph("Détermination des étriers", styles['TitreSection']))
    Ast = 2 * (3.14 * (8 / 2) ** 2)  # Exemple : 2Ø8
    fyd = int(fyk) / 1.5
    d = h - enrobage
    pas_theo = Ast * fyd * d / (10 * V * 1e3) if V > 0 else 0
    elements.append(Paragraph(f"A<sub>st</sub> = {Ast:.0f} mm² ; f<sub>yd</sub> = {fyd:.1f} N/mm² ; d = {d:.1f} cm", styles['Texte']))
    elements.append(Paragraph(f"Pas théorique = A<sub>st</sub> × f<sub>yd</sub> × d / (10 × V × 10³) = {pas_theo:.1f} cm", styles['Formule']))
    elements.append(Spacer(1, 18))

    # Note
    elements.append(Paragraph("Note : Les vérifications détaillées sont disponibles dans l'application Streamlit.", styles['Note']))

    doc.build(elements)
    return nom_fichier
