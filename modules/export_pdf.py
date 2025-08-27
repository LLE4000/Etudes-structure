# modules/export_pdf.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import io, json, math, os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Matplotlib pour rendre les formules LaTeX en images
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------- Police (optionnel : DejaVuSans pour une bonne couverture) ----------
def _register_fonts():
    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "DejaVuSans-Bold.ttf"))
        base, bold = "DejaVuSans", "DejaVuSans-Bold"
    except Exception:
        # fallback sur Times si la TTF n'est pas dispo
        base, bold = "Times-Roman", "Times-Bold"
    return base, bold

BASE_FONT, BOLD_FONT = _register_fonts()

# ---------- Styles ----------
def _styles():
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = BASE_FONT
    styles["Normal"].fontSize = 10.5
    styles["Normal"].leading = 14

    styles["Heading1"].fontName = BOLD_FONT
    styles["Heading1"].fontSize = 18
    styles["Heading1"].spaceAfter = 6

    styles["Heading2"] = ParagraphStyle(
        "Heading2", parent=styles["Normal"], fontName=BOLD_FONT,
        fontSize=12.5, spaceBefore=8, spaceAfter=4
    )

    styles["Small"] = ParagraphStyle(
        "Small", parent=styles["Normal"], fontSize=9.5, leading=12
    )

    styles["Mono"] = ParagraphStyle(
        "Mono", parent=styles["Normal"], fontName=BASE_FONT, fontSize=10.5
    )

    return styles

STY = _styles()

# ---------- Rendu LaTeX propre, aligné à gauche, taille ≈ texte ----------
def _latex_image(math_tex: str, text_pt: float = 10.5) -> Image:
    """
    Rend une formule LaTeX (MathText matplotlib) en image et renvoie
    un flowable Image reportlab aligné à gauche, dimensionné pour que
    la hauteur corresponde à ~1 ligne de texte (text_pt).
    """
    fig = plt.figure(figsize=(0.01, 0.01), dpi=300)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    # Rendre la formule — utiliser la même taille que le texte PDF
    ax.text(0, 0.7, f"${math_tex}$",
            fontsize=text_pt, ha="left", va="center",
            color="black", fontfamily="DejaVu Sans")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True, dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    buf.seek(0)

    img = Image(buf)
    img.hAlign = "LEFT"            # alignement à gauche
    # L’image sort à l’échelle « 1:1 » en points ; on laisse ReportLab garder la taille naturelle,
    # ce qui correspond bien à une ligne de texte ~ text_pt.
    return img

# ---------- Outils ----------
def _kv(label, value):
    return Paragraph(f"<b>{label}</b>&nbsp;&nbsp;{value}", STY["Normal"])

def _hr(thickness=0.6):
    t = Table([[""]], colWidths=[17*cm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), thickness, colors.lightgrey)]))
    return t

def _load_beton_props(beton_label: str, fyk_str: str):
    """
    Récupère fck_cube, alpha_b et mu (suivant fyk) depuis beton_classes.json.
    S'il n'est pas trouvé -> valeurs par défaut raisonnables.
    """
    try:
        with open("beton_classes.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        b = data[beton_label]
        fck_cube = float(b["fck_cube"])
        alpha_b  = float(b["alpha_b"])
        mu_val   = float(b[f"mu_a{fyk_str}"])
        return fck_cube, alpha_b, mu_val, True
    except Exception:
        # Défauts (sûrs mais génériques)
        # fck_cube ~ 1.23*fck ; on ne l’a pas, on prend 37 MPa et des valeurs EC2 « typiques »
        return 37.0, 0.85, 7.5, False

# ---------- Section formules (symbole + numérique) ----------
def _formula_block(title: str, lines: list[tuple[str, str]]):
    """
    title : titre de la mini-section
    lines : liste de tuples (formule_symbolique, formule_numérique_évaluée)
    """
    story = [Paragraph(title, STY["Heading2"])]
    for symb, num in lines:
        story.append(_latex_image(symb, text_pt=11))   # formule
        story.append(Spacer(0, 2))
        if num:
            story.append(_latex_image(num, text_pt=10.5))  # évaluation
            story.append(Spacer(0, 6))
        else:
            story.append(Spacer(0, 8))
    return KeepTogether(story)

# ---------- Génération ----------
def generer_rapport_pdf(
    nom_projet: str = "",
    partie: str = "",
    date: str = "",
    indice: str = "",
    beton: str = "",
    fyk: str = "",
    b: float = 0.0,
    h: float = 0.0,
    enrobage: float = 0.0,
    M_inf: float = 0.0,
    M_sup: float = 0.0,
    V: float = 0.0,
    V_lim: float = 0.0,
) -> str:
    """
    Construit un rapport PDF élégant, formules alignées à gauche et
    développées avec les valeurs numériques.
    Retourne le chemin du PDF généré.
    """

    # Chargement propriétés béton (pour h_min & cisaillement)
    fck_cube, alpha_b, mu_val, from_json = _load_beton_props(beton or "C30/37", fyk or "500")
    fyd = float(fyk or 500) / 1.5
    b_cm, h_cm, c_cm = float(b), float(h), float(enrobage)
    d_cm = h_cm - c_cm
    Mmax = max(float(M_inf or 0), float(M_sup or 0))

    # Hauteur mini (reprend ta relation du module)
    # h_min(cm) = sqrt( (M_max * 1e6) / (alpha_b * b*10 * mu_val) ) / 10
    if b_cm > 0 and alpha_b > 0 and mu_val > 0:
        hmin_cm = math.sqrt((Mmax * 1e6) / (alpha_b * b_cm * 10.0 * mu_val)) / 10.0
    else:
        hmin_cm = 0.0

    # A_s min/max
    As_min = 0.0013 * b_cm * h_cm * 1e2
    As_max = 0.04   * b_cm * h_cm * 1e2

    # A_s inf / sup
    As_inf = (M_inf * 1e6) / (fyd * 0.9 * d_cm * 10.0) if d_cm > 0 and fyd > 0 else 0.0
    As_sup = (M_sup * 1e6) / (fyd * 0.9 * d_cm * 10.0) if d_cm > 0 and fyd > 0 else 0.0

    # Cisaillement
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05
    tau = V * 1e3 / (0.75 * b_cm * h_cm * 100.0) if b_cm > 0 and h_cm > 0 else 0.0
    tau_r = V_lim * 1e3 / (0.75 * b_cm * h_cm * 100.0) if b_cm > 0 and h_cm > 0 else 0.0

    # Pas théorique d’étriers (si V>0) — formule issue de ton module
    # s_th (cm) = Ast * fyd * d * 10 / (10 * V * 1e3)
    # Ici on ne connaît pas Ast choisi -> on affiche la forme générale + la version avec un Ast symbolique.
    # On laisse Ast = A_st (mm²) dans la ligne « évaluée » pour montrer la dépendance.
    # (Tu pourras remplacer A_st par la valeur saisie si tu l’ajoutes dans l’appel.)
    s_th_expr = r"s_{\mathrm{th}}=\dfrac{A_{st}\,f_{yd}\,d\,10}{10\,V\,10^3}\ \ \text{[cm]}"
    s_th_eval = rf"s_{{\mathrm{{th}}}}=\dfrac{{A_{{st}} \times {fyd:.1f} \times {d_cm:.1f} \times 10}}{{10 \times {V:.2f} \times 10^3}}"

    # ---------- Document ----------
    out_name = f"rapport__{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(
        out_name, pagesize=A4,
        leftMargin=2.1*cm, rightMargin=1.6*cm, topMargin=1.6*cm, bottomMargin=1.6*cm
    )

    story = []

    # En-tête
    story.append(Paragraph("Rapport de dimensionnement – <i>Poutre en béton armé</i>", STY["Heading1"]))
    meta = [
        [_kv("Projet :", nom_projet or "—"), _kv("Date :", date or datetime.today().strftime("%d/%m/%Y"))],
        [_kv("Partie :", partie or "—"), _kv("Indice :", indice or "—")],
    ]
    t = Table(meta, colWidths=[8.3*cm, 8.3*cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story += [t, Spacer(0, 6), _hr(), Spacer(0, 6)]

    # Caractéristiques
    story.append(Paragraph("Caractéristiques", STY["Heading2"]))
    carac = [
        [_kv("Classe de béton", beton or "—"), _kv("Acier (fyk)", f"{(fyk or '—')} N/mm²")],
        [_kv("Largeur b", f"{b_cm:.2f} cm"), _kv("Hauteur h", f"{h_cm:.2f} cm")],
        [_kv("Enrobage", f"{c_cm:.2f} cm"), _kv("Hauteur utile d", f"{d_cm:.2f} cm")],
    ]
    tcar = Table(carac, colWidths=[8.3*cm, 8.3*cm])
    tcar.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWSPACING", (0,0), (-1,-1), 2),
    ]))
    note = ""
    if not from_json:
        note = " (valeurs par défaut)"
    story += [tcar, Spacer(0, 4), Paragraph(f"<font size=9.5>Paramètres béton{note} : "
                                           f"f<sub>ck,cube</sub>={fck_cube:.1f} MPa, "
                                           f"α<sub>b</sub>={alpha_b:.2f}, μ={mu_val:.2f}</font>", STY["Small"]),
              Spacer(0, 6), _hr(), Spacer(0, 6)]

    # ---- Vérification de la hauteur utile
    lines_h = [
        (r"h_{\min}=\sqrt{\dfrac{M_{\max}\times 10^6}{\alpha_b\ b\ 10\ \mu}}\ /\ 10",
         rf"h_{{\min}}=\sqrt{{\dfrac{{{Mmax:.2f}\times 10^6}}{{{alpha_b:.2f}\cdot {b_cm:.1f}\cdot 10\cdot {mu_val:.2f}}}}}\ /\ 10"
        ),
        (r"h_{\min}+c\leq h", rf"{hmin_cm:.1f}+{c_cm:.1f}\leq {h_cm:.1f}"),
    ]
    story.append(_formula_block("Vérification de la hauteur utile", lines_h))

    # ---- Armatures inférieures
    lines_As_inf = [
        (r"A_{s,\mathrm{inf}}=\dfrac{M_{\mathrm{inf}}\times 10^6}{f_{yd}\cdot 0.9\,d\cdot 10}\ \ \text{[mm}^2\text{]}",
         rf"A_{{s,\mathrm{{inf}}}}=\dfrac{{{M_inf:.2f}\times 10^6}}{{{fyd:.1f}\cdot 0.9\cdot {d_cm:.1f}\cdot 10}}"
        ),
        (r"A_{s,\min}=0.0013\,b\,h\cdot 10^2\ \ ;\ \ A_{s,\max}=0.04\,b\,h\cdot 10^2",
         rf"A_{{s,\min}}={As_min:.0f}\ \ \ ;\ \ A_{{s,\max}}={As_max:.0f}"
        ),
    ]
    story.append(_formula_block("Armatures inférieures", lines_As_inf))
    story.append(Paragraph(f"<b>Résultat :</b> A<sub>s,inf</sub> = {As_inf:.0f} mm²", STY["Normal"]))
    story += [Spacer(0, 6), _hr(), Spacer(0, 6)]

    # ---- Armatures supérieures (si M_sup > 0)
    if (M_sup or 0) > 0:
        lines_As_sup = [
            (r"A_{s,\mathrm{sup}}=\dfrac{M_{\mathrm{sup}}\times 10^6}{f_{yd}\cdot 0.9\,d\cdot 10}",
             rf"A_{{s,\mathrm{{sup}}}}=\dfrac{{{M_sup:.2f}\times 10^6}}{{{fyd:.1f}\cdot 0.9\cdot {d_cm:.1f}\cdot 10}}"
            ),
            (r"A_{s,\min}=0.0013\,b\,h\cdot 10^2\ \ ;\ \ A_{s,\max}=0.04\,b\,h\cdot 10^2",
             rf"A_{{s,\min}}={As_min:.0f}\ \ \ ;\ \ A_{{s,\max}}={As_max:.0f}"
            ),
        ]
        story.append(_formula_block("Armatures supérieures", lines_As_sup))
        story.append(Paragraph(f"<b>Résultat :</b> A<sub>s,sup</sub> = {As_sup:.0f} mm²", STY["Normal"]))
        story += [Spacer(0, 6), _hr(), Spacer(0, 6)]

    # ---- Effort tranchant
    lines_tau = [
        (r"\tau=\dfrac{V\cdot 10^3}{0.75\,b\,h\cdot 100}\ \ \text{[N/mm}^2\text{]}",
         rf"\tau=\dfrac{{{V:.2f}\cdot 10^3}}{{0.75\cdot {b_cm:.1f}\cdot {h_cm:.1f}\cdot 100}}={tau:.2f}"
        ),
        (r"\tau_{\mathrm{adm},I}=0.016\,\dfrac{f_{ck,\mathrm{cube}}}{1.05},\ \tau_{\mathrm{adm},II}=0.032\,\dfrac{f_{ck,\mathrm{cube}}}{1.05},\ \tau_{\mathrm{adm},IV}=0.064\,\dfrac{f_{ck,\mathrm{cube}}}{1.05}",
         rf"\tau_{{I}}={tau_1:.2f},\ \tau_{{II}}={tau_2:.2f},\ \tau_{{IV}}={tau_4:.2f}"
        ),
    ]
    story.append(_formula_block("Vérification de l'effort tranchant", lines_tau))

    # ---- Effort tranchant réduit (si saisi)
    if (V_lim or 0) > 0:
        lines_tau_r = [
            (r"\tau_{\mathrm{r}}=\dfrac{V_{\mathrm{réduit}}\cdot 10^3}{0.75\,b\,h\cdot 100}",
             rf"\tau_r=\dfrac{{{V_lim:.2f}\cdot 10^3}}{{0.75\cdot {b_cm:.1f}\cdot {h_cm:.1f}\cdot 100}}={tau_r:.2f}"
            )
        ]
        story.append(_formula_block("Vérification de l'effort tranchant réduit", lines_tau_r))

    story += [Spacer(0, 6), _hr(), Spacer(0, 6)]

    # ---- Étriers : rappel formule s_th
    story.append(_formula_block("Détermination des étriers (rappel)", [(s_th_expr, s_th_eval)]))
    story.append(Paragraph(
        "Unités : M en kN·m, V en kN, b/h/c/d en cm, A<sub>s</sub> en mm², τ en N/mm². "
        "Les formules ci-dessus reprennent exactement celles du module Streamlit.",
        STY["Small"])
    )

    # Build
    doc.build(story)
    return out_name
