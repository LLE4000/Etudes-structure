# -*- coding: utf-8 -*-
"""
Générateur PDF – Rapport de dimensionnement (Poutre BA)
- Formules LaTeX alignées à gauche, à échelle maîtrisée
- Numérotation Eq.(1), Eq.(2)…
- Substitutions numériques + résultat
- Notation FR (virgule décimale), unités en roman

Dépendances : reportlab, matplotlib (mathtext, pas besoin de LaTeX système)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import json
import os
import math
from datetime import datetime

# ---------------------------------------------------------------------
# Utils typographiques
# ---------------------------------------------------------------------

def fr(x, nd=1):
    """Format FR avec virgule et nd décimales (et séparation fine des milliers)."""
    if x is None:
        return "-"
    fmt = f"{{:,.{nd}f}}".format(float(x)).replace(",", "§").replace(".", ",").replace("§", " ")
    # évite "-0,00"
    if fmt.startswith("-0,"):
        fmt = fmt.replace("-0,", "0,")
    return fmt

def tex_unit(u):
    """Unités en roman dans LaTeX mathtext : \\mathrm{...}"""
    return r"\ \mathrm{" + u + "}"

# ---------------------------------------------------------------------
# Rendu d'équations avec matplotlib (mathtext)
# ---------------------------------------------------------------------

def render_equation(tex_expr, out_path, fontsize=14, pad=0.1):
    """
    Rend une équation LaTeX (mathtext) en PNG transparent.
    - Alignée à gauche par insertion dans le PDF (hAlign='LEFT')
    """
    fig = plt.figure(figsize=(1, 1), dpi=250)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    # left aligned text inside figure
    ax.text(0.0, 0.5, f"${tex_expr}$", fontsize=fontsize, va="center", ha="left")
    fig.savefig(out_path, dpi=250, transparent=True, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    return out_path

def eq_block(eq_no, tex_symbolic, tex_numeric=None, result_text=None, img_width_mm=120):
    """
    Construit un petit bloc 'Equation' : titre Eq.(n) + image(s) + résultat.
    Retourne une liste de flowables (ReportLab).
    """
    flows = []
    styles = get_styles()

    flows.append(Paragraph(f"<b>Équation ({eq_no})</b>", styles["EqTitle"]))
    # image symbolique
    pth_sym = os.path.join("/mnt/data", f"eq_sym_{eq_no}.png")
    render_equation(tex_symbolic, pth_sym, fontsize=14)
    flows.append(Image(pth_sym, width=img_width_mm*mm, preserveAspectRatio=True, hAlign="LEFT"))
    if tex_numeric:
        pth_num = os.path.join("/mnt/data", f"eq_num_{eq_no}.png")
        render_equation(tex_numeric, pth_num, fontsize=14)
        flows.append(Spacer(1, 3*mm))
        flows.append(Image(pth_num, width=img_width_mm*mm, preserveAspectRatio=True, hAlign="LEFT"))
    if result_text:
        flows.append(Spacer(1, 1.5*mm))
        flows.append(Paragraph(result_text, styles["EqResult"]))
    flows.append(Spacer(1, 6*mm))
    return flows

# ---------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------

def register_fonts():
    """Optionnel : utiliser une fonte plus sobre si dispo (DejaVu)."""
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSerif.ttf"))
        base = "DejaVu"
    except Exception:
        base = "Times-Roman"
    return base

def get_styles():
    base = register_fonts()
    ss = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=ss["Title"],
            fontName=base,
            fontSize=18,
            leading=22,
            spaceAfter=8,
            alignment=0,  # left
        ),
        "H1": ParagraphStyle(
            "H1", parent=ss["Heading1"], fontName=base, fontSize=14,
            leading=18, spaceBefore=6, spaceAfter=6, alignment=0
        ),
        "H2": ParagraphStyle(
            "H2", parent=ss["Heading2"], fontName=base, fontSize=12.5,
            leading=16, spaceBefore=4, spaceAfter=4, alignment=0
        ),
        "Normal": ParagraphStyle(
            "Normal", parent=ss["BodyText"], fontName=base, fontSize=10.5,
            leading=13.5, spaceAfter=2, alignment=0
        ),
        "Small": ParagraphStyle(
            "Small", parent=ss["BodyText"], fontName=base, fontSize=9.5,
            leading=12, spaceAfter=0, alignment=0, textColor=colors.HexColor("#444")
        ),
        "EqTitle": ParagraphStyle(
            "EqTitle", parent=ss["BodyText"], fontName=base, fontSize=10,
            leading=12.5, textColor=colors.HexColor("#666"), spaceAfter=2
        ),
        "EqResult": ParagraphStyle(
            "EqResult", parent=ss["BodyText"], fontName=base, fontSize=10.5,
            leading=13.5, textColor=colors.black
        ),
        "Green": ParagraphStyle(
            "Green", parent=ss["BodyText"], fontName=base, fontSize=10.5,
            leading=13.5, textColor=colors.HexColor("#1e7e34")
        ),
        "Red": ParagraphStyle(
            "Red", parent=ss["BodyText"], fontName=base, fontSize=10.5,
            leading=13.5, textColor=colors.HexColor("#b00020")
        ),
    }
    return styles

# ---------------------------------------------------------------------
# Chargement des classes béton
# ---------------------------------------------------------------------

def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(path):
        # tentative locale (si module lancé ailleurs)
        path = "beton_classes.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------
# Générateur
# ---------------------------------------------------------------------

def generer_rapport_pdf(
    nom_projet="",
    partie="",
    date="",
    indice="",
    beton="C30/37",
    fyk="500",
    b=20,
    h=40,
    enrobage=5.0,
    M_inf=0.0,
    M_sup=0.0,
    V=0.0,
    V_lim=0.0,
    **kwargs,  # optionnel : n_etriers, o_etrier, pas_etrier, etc.
):
    """
    Crée un PDF professionnel avec les formules détaillées et numérotées.
    Retourne le chemin du fichier généré.
    """
    beton_data = load_beton_data()
    data = beton_data.get(beton, {})
    fck_cube = data.get("fck_cube", 30)
    alpha_b = data.get("alpha_b", 0.72)
    mu_val = data.get(f"mu_a{fyk}", 11.5)
    fyd = int(fyk) / 1.5

    # Grandeurs dérivées
    d_utile = h - enrobage  # cm
    M_max = max(float(M_inf or 0.0), float(M_sup or 0.0))

    # h_min (cm)
    # h_min = sqrt(M_max*1e6 / (alpha_b * b * 10 * mu_a)) / 10
    if M_max > 0:
        hmin = math.sqrt((M_max * 1e6) / (alpha_b * b * 10 * mu_val)) / 10.0
    else:
        hmin = 0.0

    # Armatures
    As_min = 0.0013 * b * h * 1e2
    As_max = 0.04 * b * h * 1e2
    As_inf = (M_inf * 1e6) / (fyd * 0.9 * d_utile * 10) if M_inf > 0 else 0.0
    As_sup = (M_sup * 1e6) / (fyd * 0.9 * d_utile * 10) if M_sup > 0 else 0.0

    # Effort tranchant
    # tau = V*1e3 / (0.75 * b * h * 100)
    tau = (V * 1e3) / (0.75 * b * h * 100) if V > 0 else 0.0
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05

    # Info “besoin d’étriers”
    besoin_str = ""
    etat_tranchant = "ok"
    if V > 0:
        if tau <= tau_1:
            besoin_str = "Pas besoin d’étriers (≤ τ_adm I)."
        elif tau <= tau_2:
            besoin_str = "Besoin d’étriers (≤ τ_adm II)."
        elif tau <= tau_4:
            besoin_str = "Barres inclinées + étriers (≤ τ_adm IV)."
            etat_tranchant = "warn"
        else:
            besoin_str = "Non acceptable (> τ_adm IV)."
            etat_tranchant = "nok"

    # Chemin du PDF
    out_name = f"rapport__{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out_path = os.path.join("/mnt/data", out_name)

    # Document
    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=14*mm, bottomMargin=14*mm,
        title="Rapport de dimensionnement – Poutre BA",
    )

    S = get_styles()
    flow = []

    # En-tête
    flow.append(Paragraph("Rapport de dimensionnement – Poutre en béton armé", S["Title"]))
    meta_tbl = Table(
        [
            ["Projet :", nom_projet or "—", "Date :", date or datetime.today().strftime("%d/%m/%Y")],
            ["Partie :", partie or "—", "Indice :", indice or "—"],
        ],
        colWidths=[18*mm, 70*mm, 18*mm, 70*mm]
    )
    meta_tbl.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
        ("FONTSIZE", (0,0), (-1,-1), 10.5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    flow.append(meta_tbl)
    flow.append(Spacer(1, 6*mm))

    # Caractéristiques
    flow.append(Paragraph("Caractéristiques de la poutre", S["H1"]))
    car_tbl = Table(
        [
            ["Classe de béton", beton, "Acier (fyk)", f"{fyk} N/mm²"],
            ["Largeur b", f"{fr(b,1)} cm", "Hauteur h", f"{fr(h,1)} cm"],
            ["Enrobage", f"{fr(enrobage,1)} cm", "Hauteur utile d", f"{fr(d_utile,1)} cm"],
        ],
        colWidths=[35*mm, 55*mm, 35*mm, 55*mm]
    )
    car_tbl.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#cccccc")),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f6f6f6")),
        ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
        ("FONTSIZE", (0,0), (-1,-1), 10.5),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    flow.append(car_tbl)
    flow.append(Spacer(1, 5*mm))

    # ------------------------------------------------------------
    # h_min
    # ------------------------------------------------------------
    flow.append(Paragraph("Vérification de la hauteur utile", S["H1"]))

    # Eq.1 : h_min
    tex_hmin = r"h_\mathrm{min} = \sqrt{\frac{M_\mathrm{max}\,\cdot 10^{6}}{\alpha_b\,b\,10\,\mu_a}}\ /\ 10" + tex_unit("cm")
    tex_hmin_num = (
        r"h_\mathrm{min} = \sqrt{\frac{" + fr(M_max,2).replace(",", ".") + r"\,\cdot 10^{6}}{" +
        fr(alpha_b,2).replace(",", ".") + r"\,\cdot " + fr(b,1).replace(",", ".") + r"\,\cdot 10\,\cdot " +
        fr(mu_val,1).replace(",", ".") + r"}}\ /\ 10" + tex_unit("cm")
    )
    res_hmin = f"Résultat : <b>h_min = {fr(hmin, 1)} cm</b>"
    flow += eq_block(1, tex_hmin, tex_hmin_num, res_hmin)

    ok_h = (hmin + enrobage) <= h
    msg = (
        f"h_min + enrobage = {fr(hmin+enrobage,1)} cm ≤ h = {fr(h,1)} cm — "
        + ("<b>Conforme</b>" if ok_h else "<b>Non conforme</b>")
    )
    flow.append(Paragraph(msg, S["Green" if ok_h else "Red"]))
    flow.append(Spacer(1, 6*mm))

    # ------------------------------------------------------------
    # Armatures inférieures
    # ------------------------------------------------------------
    flow.append(Paragraph("Armatures inférieures", S["H1"]))
    tex_as = r"A_{s,\mathrm{inf}}=\dfrac{M_\mathrm{inf}\cdot 10^{6}}{f_{yd}\cdot 0.9\,d\cdot 10}" + tex_unit("mm^2")
    tex_as_num = (
        r"A_{s,\mathrm{inf}}=\dfrac{" + fr(M_inf,2).replace(",", ".") + r"\cdot 10^{6}}{" +
        fr(fyd,1).replace(",", ".") + r"\cdot 0.9\cdot " + fr(d_utile,1).replace(",", ".") + r"\cdot 10}" +
        tex_unit("mm^2")
    )
    res_as = f"Résultat : <b>A<sub>s,inf</sub> = {fr(As_inf,1)} mm²</b>"
    flow += eq_block(2, tex_as, tex_as_num, res_as)

    flow.append(Paragraph(
        f"A<sub>s,min</sub> = 0,0013 · b · h · 10² = <b>{fr(As_min,1)} mm²</b> ; "
        f"A<sub>s,max</sub> = 0,04 · b · h · 10² = <b>{fr(As_max,1)} mm²</b>",
        S["Small"])
    )
    flow.append(Spacer(1, 3*mm))

    # ------------------------------------------------------------
    # Armatures supérieures (si M_sup > 0)
    # ------------------------------------------------------------
    if M_sup and M_sup > 0:
        flow.append(Paragraph("Armatures supérieures", S["H1"]))
        tex_as_sup = r"A_{s,\mathrm{sup}}=\dfrac{M_\mathrm{sup}\cdot 10^{6}}{f_{yd}\cdot 0.9\,d\cdot 10}" + tex_unit("mm^2")
        tex_as_sup_num = (
            r"A_{s,\mathrm{sup}}=\dfrac{" + fr(M_sup,2).replace(",", ".") + r"\cdot 10^{6}}{" +
            fr(fyd,1).replace(",", ".") + r"\cdot 0.9\cdot " + fr(d_utile,1).replace(",", ".") + r"\cdot 10}" +
            tex_unit("mm^2")
        )
        res_as_sup = f"Résultat : <b>A<sub>s,sup</sub> = {fr(As_sup,1)} mm²</b>"
        flow += eq_block(3, tex_as_sup, tex_as_sup_num, res_as_sup)
        flow.append(Paragraph(
            f"A<sub>s,min</sub> = <b>{fr(As_min,1)} mm²</b> ; A<sub>s,max</sub> = <b>{fr(As_max,1)} mm²</b>",
            S["Small"])
        )
        flow.append(Spacer(1, 3*mm))

    # ------------------------------------------------------------
    # Effort tranchant
    # ------------------------------------------------------------
    if V and V > 0:
        flow.append(Paragraph("Vérification de l'effort tranchant", S["H1"]))
        tex_tau = r"\tau = \dfrac{V\cdot 10^{3}}{0.75\,b\,h\,100}" + tex_unit("N/mm^{2}")
        tex_tau_num = (
            r"\tau = \dfrac{" + fr(V,2).replace(",", ".") + r"\cdot 10^{3}}{0.75\cdot " +
            fr(b,1).replace(",", ".") + r"\cdot " + fr(h,1).replace(",", ".") + r"\cdot 100}" +
            tex_unit("N/mm^{2}")
        )
        res_tau = f"Résultat : <b>τ = {fr(tau,2)} N/mm²</b>"
        flow += eq_block(4, tex_tau, tex_tau_num, res_tau)

        flow.append(Paragraph(
            f"Seuils : τ<sub>adm I</sub> = {fr(tau_1,2)} ; τ<sub>adm II</sub> = {fr(tau_2,2)} ; "
            f"τ<sub>adm IV</sub> = {fr(tau_4,2)} (N/mm²).", S["Small"])
        )
        flow.append(Paragraph(besoin_str, S["Green" if etat_tranchant != "nok" else "Red"]))
        flow.append(Spacer(1, 4*mm))

    # ------------------------------------------------------------
    # (Optionnel) Etriers si paramètres fournis au générateur
    # ------------------------------------------------------------
    n_et = kwargs.get("n_etriers")
    o_et = kwargs.get("o_etrier")
    if all(v is not None for v in [n_et, o_et]) and V and V > 0:
        flow.append(Paragraph("Détermination des étriers (optionnel)", S["H1"]))
        # Ast_e = n * π (φ/2)^2
        Ast_e = n_et * math.pi * (float(o_et)/2.0)**2
        pas_th = Ast_e * fyd * d_utile * 10 / (10 * V * 1e3) if V > 0 else 0.0

        tex_Aste = r"A_{st,e} = n \cdot \pi \left(\dfrac{\varnothing}{2}\right)^{2}" + tex_unit("mm^{2}")
        tex_Aste_num = (
            r"A_{st,e} = " + str(int(n_et)) + r"\cdot \pi \left(\dfrac{" +
            fr(o_et,0).replace(",", ".") + r"}{2}\right)^{2}" + tex_unit("mm^{2}")
        )
        flow += eq_block(5, tex_Aste, tex_Aste_num, f"Résultat : <b>A<sub>st,e</sub> = {fr(Ast_e,1)} mm²</b>")

        tex_pas = r"s_\mathrm{th} = \dfrac{A_{st,e}\, f_{yd}\, d\, 10}{10\, V \cdot 10^{3}}" + tex_unit("cm")
        tex_pas_num = (
            r"s_\mathrm{th} = \dfrac{" + fr(Ast_e,1).replace(",", ".") + r"\cdot " +
            fr(fyd,1).replace(",", ".") + r"\cdot " + fr(d_utile,1).replace(",", ".") +
            r"\cdot 10}{10\cdot " + fr(V,2).replace(",", ".") + r"\cdot 10^{3}}" + tex_unit("cm")
        )
        flow += eq_block(6, tex_pas, tex_pas_num, f"Résultat : <b>s_th = {fr(pas_th,1)} cm</b>")

    # Signature
    flow.append(Spacer(1, 8*mm))
    flow.append(Paragraph("Rapport généré automatiquement – © Études Structure", S["Small"]))

    doc.build(flow)
    return out_path
