# -*- coding: utf-8 -*-
"""
Générateur PDF – Rapport de dimensionnement (Poutre BA)
- Formules LaTeX rendues avec matplotlib.mathtext, alignées à gauche
- Numérotation Eq.(1), Eq.(2)…
- Substitutions numériques + résultat
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
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
import tempfile
import shutil
from datetime import datetime

# ---------------------------------------------------------------------
# Utils typographiques
# ---------------------------------------------------------------------

def fr(x, nd=1):
    """Format FR (virgule) avec nd décimales."""
    if x is None:
        return "-"
    s = f"{float(x):,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", " ")
    if s.startswith("-0,"):
        s = s.replace("-0,", "0,")
    return s

def tex_unit(u):
    return r"\ \mathrm{" + u + "}"

# ---------------------------------------------------------------------
# Rendu d'équations (mathtext)
# ---------------------------------------------------------------------

def render_equation(tex_expr, out_path, fontsize=14, pad=0.1):
    """Rend une équation LaTeX en PNG transparent, prêt à être inséré à gauche."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig = plt.figure(figsize=(1, 1), dpi=250)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(0.0, 0.5, f"${tex_expr}$", fontsize=fontsize, va="center", ha="left")
    fig.savefig(out_path, dpi=250, transparent=True, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    return out_path

# ---------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------

def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSerif.ttf"))
        return "DejaVu"
    except Exception:
        return "Times-Roman"

def get_styles():
    base = register_fonts()
    ss = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle("Title", parent=ss["Title"],
                                fontName=base, fontSize=18, leading=22,
                                spaceAfter=8, alignment=0),
        "H1": ParagraphStyle("H1", parent=ss["Heading1"],
                             fontName=base, fontSize=14, leading=18,
                             spaceBefore=6, spaceAfter=6, alignment=0),
        "Normal": ParagraphStyle("Normal", parent=ss["BodyText"],
                                 fontName=base, fontSize=10.5, leading=13.5,
                                 spaceAfter=2, alignment=0),
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9.5, leading=12,
                                spaceAfter=0, alignment=0, textColor=colors.HexColor("#444")),
        "EqTitle": ParagraphStyle("EqTitle", parent=ss["BodyText"],
                                  fontName=base, fontSize=10, leading=12.5,
                                  textColor=colors.HexColor("#666"), spaceAfter=2),
        "EqResult": ParagraphStyle("EqResult", parent=ss["BodyText"],
                                   fontName=base, fontSize=10.5, leading=13.5,
                                   textColor=colors.black),
        "Green": ParagraphStyle("Green", parent=ss["BodyText"],
                                fontName=base, fontSize=10.5, leading=13.5,
                                textColor=colors.HexColor("#1e7e34")),
        "Red": ParagraphStyle("Red", parent=ss["BodyText"],
                              fontName=base, fontSize=10.5, leading=13.5,
                              textColor=colors.HexColor("#b00020")),
    }
    return styles

# ---------------------------------------------------------------------
# Données béton
# ---------------------------------------------------------------------

def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(p):
        p = "beton_classes.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------------------------------------------------------------
# Blocs équations
# ---------------------------------------------------------------------

def eq_block(eq_no, tex_symbolic, tmpdir, tex_numeric=None, result_text=None, img_width_mm=120):
    """Construit un bloc d’équation (titre + image(s) + résultat)."""
    S = get_styles()
    flows = [Paragraph(f"<b>Équation ({eq_no})</b>", S["EqTitle"])]

    pth_sym = os.path.join(tmpdir, f"eq_sym_{eq_no}.png")
    render_equation(tex_symbolic, pth_sym, fontsize=14)
    # ⚠️ ReportLab Image n'a pas preserveAspectRatio ; donner seulement width garde l'AR
    flows.append(Image(pth_sym, width=img_width_mm*mm, hAlign="LEFT"))

    if tex_numeric:
        pth_num = os.path.join(tmpdir, f"eq_num_{eq_no}.png")
        render_equation(tex_numeric, pth_num, fontsize=14)
        flows.append(Spacer(1, 3*mm))
        flows.append(Image(pth_num, width=img_width_mm*mm, hAlign="LEFT"))

    if result_text:
        flows.append(Spacer(1, 1.5*mm))
        flows.append(Paragraph(result_text, S["EqResult"]))

    flows.append(Spacer(1, 6*mm))
    return flows

# ---------------------------------------------------------------------
# Générateur PDF
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
    **kwargs,
):
    """Construit le PDF et retourne son chemin (dans un emplacement inscriptible)."""
    beton_data = load_beton_data()
    d = beton_data.get(beton, {})
    fck_cube = d.get("fck_cube", 30)
    alpha_b = d.get("alpha_b", 0.72)
    mu_val = d.get(f"mu_a{fyk}", 11.5)
    fyd = int(fyk) / 1.5

    d_utile = h - enrobage  # cm
    M_max = max(float(M_inf or 0.0), float(M_sup or 0.0))
    hmin = math.sqrt((M_max * 1e6) / (alpha_b * b * 10 * mu_val)) / 10.0 if M_max > 0 else 0.0

    As_min = 0.0013 * b * h * 1e2
    As_max = 0.04 * b * h * 1e2
    As_inf = (M_inf * 1e6) / (fyd * 0.9 * d_utile * 10) if M_inf > 0 else 0.0
    As_sup = (M_sup * 1e6) / (fyd * 0.9 * d_utile * 10) if M_sup > 0 else 0.0

    tau = (V * 1e3) / (0.75 * b * h * 100) if V > 0 else 0.0
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05

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

    # ---------- Sortie PDF : /mnt/data si possible, sinon /tmp ----------
    preferred_dir = "/mnt/data"
    out_dir = None
    try:
        os.makedirs(preferred_dir, exist_ok=True)
        out_dir = preferred_dir
    except PermissionError:
        out_dir = tempfile.gettempdir()
    except Exception:
        out_dir = tempfile.gettempdir()

    out_name = f"rapport__{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out_path = os.path.join(out_dir, out_name)

    # Dossier temporaire pour les équations
    tmpdir = tempfile.mkdtemp(prefix="pdf_eq_")

    S = get_styles()
    flow = []

    try:
        # Document
        doc = SimpleDocTemplate(
            out_path,
            pagesize=A4,
            leftMargin=18*mm, rightMargin=18*mm,
            topMargin=14*mm, bottomMargin=14*mm,
            title="Rapport de dimensionnement – Poutre BA",
        )

        # Titre & méta
        flow.append(Paragraph("Rapport de dimensionnement – Poutre en béton armé", S["Title"]))
        flow.append(Table(
            [
                ["Projet :", nom_projet or "—", "Date :", date or datetime.today().strftime("%d/%m/%Y")],
                ["Partie :", partie or "—", "Indice :", indice or "—"],
            ],
            colWidths=[18*mm, 70*mm, 18*mm, 70*mm],
            style=TableStyle([
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 10.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ])
        ))
        flow.append(Spacer(1, 6*mm))

        # Caractéristiques
        flow.append(Paragraph("Caractéristiques de la poutre", S["H1"]))
        flow.append(Table(
            [
                ["Classe de béton", beton, "Acier (fyk)", f"{fyk} N/mm²"],
                ["Largeur b", f"{fr(b,1)} cm", "Hauteur h", f"{fr(h,1)} cm"],
                ["Enrobage", f"{fr(enrobage,1)} cm", "Hauteur utile d", f"{fr(h-enrobage,1)} cm"],
            ],
            colWidths=[35*mm, 55*mm, 35*mm, 55*mm],
            style=TableStyle([
                ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#cccccc")),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f6f6f6")),
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 10.5),
                ("ALIGN", (0,0), (-1,-1), "LEFT"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 5*mm))

        # h_min
        flow.append(Paragraph("Vérification de la hauteur utile", S["H1"]))
        tex_hmin = r"h_\mathrm{min} = \sqrt{\frac{M_\mathrm{max}\,\cdot 10^{6}}{\alpha_b\,b\,10\,\mu_a}}\ /\ 10" + tex_unit("cm")
        tex_hmin_num = (
            r"h_\mathrm{min} = \sqrt{\frac{" + fr(M_max,2).replace(",", ".") + r"\,\cdot 10^{6}}{" +
            fr(alpha_b,2).replace(",", ".") + r"\,\cdot " + fr(b,1).replace(",", ".") + r"\,\cdot 10\,\cdot " +
            fr(mu_val,1).replace(",", ".") + r"}}\ /\ 10" + tex_unit("cm")
        )
        res_hmin = f"Résultat : <b>h_min = {fr(hmin, 1)} cm</b>"
        flow += eq_block(1, tex_hmin, tmpdir, tex_hmin_num, res_hmin)

        ok_h = (hmin + enrobage) <= h
        msg = f"h_min + enrobage = {fr(hmin+enrobage,1)} cm ≤ h = {fr(h,1)} cm — " + ("<b>Conforme</b>" if ok_h else "<b>Non conforme</b>")
        flow.append(Paragraph(msg, S["Green" if ok_h else "Red"]))
        flow.append(Spacer(1, 6*mm))

        # Armatures inférieures
        flow.append(Paragraph("Armatures inférieures", S["H1"]))
        tex_as = r"A_{s,\mathrm{inf}}=\dfrac{M_\mathrm{inf}\cdot 10^{6}}{f_{yd}\cdot 0.9\,d\cdot 10}" + tex_unit("mm^2")
        tex_as_num = (
            r"A_{s,\mathrm{inf}}=\dfrac{" + fr(M_inf,2).replace(",", ".") + r"\cdot 10^{6}}{" +
            fr(fyd,1).replace(",", ".") + r"\cdot 0.9\cdot " + fr(h-enrobage,1).replace(",", ".") + r"\cdot 10}" +
            tex_unit("mm^2")
        )
        As_min = 0.0013 * b * h * 1e2
        As_max = 0.04 * b * h * 1e2
        As_inf = (M_inf * 1e6) / (fyd * 0.9 * (h-enrobage) * 10) if M_inf > 0 else 0.0
        res_as = f"Résultat : <b>A<sub>s,inf</sub> = {fr(As_inf,1)} mm²</b>"
        flow += eq_block(2, tex_as, tmpdir, tex_as_num, res_as)
        flow.append(Paragraph(
            f"A<sub>s,min</sub> = 0,0013 · b · h · 10² = <b>{fr(As_min,1)} mm²</b> ; "
            f"A<sub>s,max</sub> = 0,04 · b · h · 10² = <b>{fr(As_max,1)} mm²</b>",
            S["Small"])
        )
        flow.append(Spacer(1, 3*mm))

        # Armatures supérieures
        if M_sup and M_sup > 0:
            flow.append(Paragraph("Armatures supérieures", S["H1"]))
            tex_as_sup = r"A_{s,\mathrm{sup}}=\dfrac{M_\mathrm{sup}\cdot 10^{6}}{f_{yd}\cdot 0.9\,d\cdot 10}" + tex_unit("mm^2")
            tex_as_sup_num = (
                r"A_{s,\mathrm{sup}}=\dfrac{" + fr(M_sup,2).replace(",", ".") + r"\cdot 10^{6}}{" +
                fr(fyd,1).replace(",", ".") + r"\cdot 0.9\cdot " + fr(h-enrobage,1).replace(",", ".") + r"\cdot 10}" +
                tex_unit("mm^2")
            )
            As_sup = (M_sup * 1e6) / (fyd * 0.9 * (h-enrobage) * 10) if M_sup > 0 else 0.0
            res_as_sup = f"Résultat : <b>A<sub>s,sup</sub> = {fr(As_sup,1)} mm²</b>"
            flow += eq_block(3, tex_as_sup, tmpdir, tex_as_sup_num, res_as_sup)
            flow.append(Paragraph(
                f"A<sub>s,min</sub> = <b>{fr(As_min,1)} mm²</b> ; A<sub>s,max</sub> = <b>{fr(As_max,1)} mm²</b>",
                S["Small"])
            )
            flow.append(Spacer(1, 3*mm))

        # Effort tranchant
        if V and V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["H1"]))
            tex_tau = r"\tau = \dfrac{V\cdot 10^{3}}{0.75\,b\,h\,100}" + tex_unit("N/mm^{2}")
            tex_tau_num = (
                r"\tau = \dfrac{" + fr(V,2).replace(",", ".") + r"\cdot 10^{3}}{0.75\cdot " +
                fr(b,1).replace(",", ".") + r"\cdot " + fr(h,1).replace(",", ".") + r"\cdot 100}" +
                tex_unit("N/mm^{2}")
            )
            tau = (V * 1e3) / (0.75 * b * h * 100)
            tau_1 = 0.016 * fck_cube / 1.05
            tau_2 = 0.032 * fck_cube / 1.05
            tau_4 = 0.064 * fck_cube / 1.05
            res_tau = f"Résultat : <b>τ = {fr(tau,2)} N/mm²</b>"
            flow += eq_block(4, tex_tau, tmpdir, tex_tau_num, res_tau)
            flow.append(Paragraph(
                f"Seuils : τ<sub>adm I</sub> = {fr(tau_1,2)} ; τ<sub>adm II</sub> = {fr(tau_2,2)} ; "
                f"τ<sub>adm IV</sub> = {fr(tau_4,2)} (N/mm²).", S["Small"])
            )
            besoin_str = (
                "Pas besoin d’étriers (≤ τ_adm I)." if tau <= tau_1 else
                "Besoin d’étriers (≤ τ_adm II)." if tau <= tau_2 else
                "Barres inclinées + étriers (≤ τ_adm IV)." if tau <= tau_4 else
                "Non acceptable (> τ_adm IV)."
            )
            color = "Green" if tau <= tau_4 else "Red"
            flow.append(Paragraph(besoin_str, S[color]))
            flow.append(Spacer(1, 4*mm))

        # (Optionnel) étriers si fournis
        n_et = kwargs.get("n_etriers")
        o_et = kwargs.get("ø_etrier") or kwargs.get("o_etrier")
        if all(v is not None for v in [n_et, o_et]) and V and V > 0:
            Ast_e = n_et * math.pi * (float(o_et)/2.0)**2
            pas_th = Ast_e * fyd * (h-enrobage) * 10 / (10 * V * 1e3)
            flow.append(Paragraph("Détermination des étriers (optionnel)", S["H1"]))
            tex_Aste = r"A_{st,e} = n \cdot \pi \left(\dfrac{\varnothing}{2}\right)^{2}" + tex_unit("mm^{2}")
            tex_Aste_num = (
                r"A_{st,e} = " + str(int(n_et)) + r"\cdot \pi \left(\dfrac{" +
                fr(o_et,0).replace(",", ".") + r"}{2}\right)^{2}" + tex_unit("mm^{2}")
            )
            flow += eq_block(5, tmpdir=tmpdir, tex_symbolic=tex_Aste, tex_numeric=tex_Aste_num,
                             result_text=f"Résultat : <b>A<sub>st,e</sub> = {fr(Ast_e,1)} mm²</b>")
            tex_pas = r"s_\mathrm{th} = \dfrac{A_{st,e}\, f_{yd}\, d\, 10}{10\, V \cdot 10^{3}}" + tex_unit("cm")
            tex_pas_num = (
                r"s_\mathrm{th} = \dfrac{" + fr(Ast_e,1).replace(",", ".") + r"\cdot " +
                fr(fyd,1).replace(",", ".") + r"\cdot " + fr(h-enrobage,1).replace(",", ".") +
                r"\cdot 10}{10\cdot " + fr(V,2).replace(",", ".") + r"\cdot 10^{3}}" + tex_unit("cm")
            )
            flow += eq_block(6, tmpdir=tmpdir, tex_symbolic=tex_pas, tex_numeric=tex_pas_num,
                             result_text=f"Résultat : <b>s_th = {fr(pas_th,1)} cm</b>")

        flow.append(Spacer(1, 8*mm))
        flow.append(Paragraph("Rapport généré automatiquement – © Études Structure", S["Small"]))

        # Build
        doc.build(flow)
        return out_path

    finally:
        # Nettoyage du répertoire temporaire des équations
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
