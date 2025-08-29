# -*- coding: utf-8 -*-
"""
Rapport de dimensionnement – Poutre BA (PDF, compact, 1 page)
- Formules LaTeX rendues par matplotlib.mathtext (NUMÉRIQUES UNIQUEMENT)
- Images proportionnelles (width & height, pas de déformation)
- Espacements minimaux
- Conclusions de CHOIX pour As_inf / As_sup et étriers
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from PIL import Image as PILImage
import json, os, math, tempfile, shutil
from datetime import datetime

# ----------------------------- Utils ---------------------------------

def fr(x, nd=1):
    """Format FR (virgule)."""
    if x is None:
        return "-"
    s = f"{float(x):,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", " ")
    if s.startswith("-0,"):
        s = s.replace("-0,", "0,")
    return s

def tex_unit(u):
    return r"\ \mathrm{" + u + "}"

def render_equation(tex_expr, out_path, fontsize=11, pad=0.05):
    """Rend une équation LaTeX (mathtext) en PNG transparent."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig = plt.figure(figsize=(1, 1), dpi=250)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(0.0, 0.5, f"${tex_expr}$", fontsize=fontsize, va="center", ha="left")
    fig.savefig(out_path, dpi=250, transparent=True, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    return out_path

def aire_barres(n, phi):
    """mm² pour n barres de diamètre phi (mm)."""
    return float(n) * math.pi * (float(phi)/2.0)**2

def verdict(ok_bool):
    return "✅ OK" if ok_bool else "❌ Non conforme"

# ---------------------------- Styles ---------------------------------

def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSerif.ttf"))
        return "DejaVu"
    except Exception:
        return "Times-Roman"

def get_styles():
    base = register_fonts()
    ss = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle("Title", parent=ss["Title"],
                                fontName=base, fontSize=16, leading=19,
                                spaceAfter=4, alignment=0),
        "H1": ParagraphStyle("H1", parent=ss["Heading1"],
                             fontName=base, fontSize=12.5, leading=15.5,
                             spaceBefore=4, spaceAfter=2, alignment=0),
        "Normal": ParagraphStyle("Normal", parent=ss["BodyText"],
                                 fontName=base, fontSize=9.5, leading=12,
                                 spaceAfter=1, alignment=0),
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9, leading=11,
                                spaceAfter=0, alignment=0, textColor=colors.HexColor("#444")),
        "EqResult": ParagraphStyle("EqResult", parent=ss["BodyText"],
                                   fontName=base, fontSize=9.5, leading=12,
                                   textColor=colors.black),
        "Green": ParagraphStyle("Green", parent=ss["BodyText"],
                                fontName=base, fontSize=9.5, leading=12,
                                textColor=colors.HexColor("#1e7e34")),
        "Red": ParagraphStyle("Red", parent=ss["BodyText"],
                              fontName=base, fontSize=9.5, leading=12,
                              textColor=colors.HexColor("#b00020")),
    }

# ----------------------- Données béton -------------------------------

def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(p):
        p = "beton_classes.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# ------------- Bloc équation (image seule, proportionnelle) ----------

def eq_block(eq_no, tmpdir, tex_numeric, result_text=None, img_width_mm=32):
    """
    Bloc équation compact: image NUMÉRIQUE proportionnelle + résultat.
    - pas de titre 'Équation (x)'
    - ratio conservé (width & height fixés)
    - espacements minimaux
    """
    S = get_styles()
    flows = []
    pth = os.path.join(tmpdir, f"eq_{eq_no}.png")
    render_equation(tex_numeric, pth, fontsize=11, pad=0.05)

    with PILImage.open(pth) as im:
        w, h = im.size
    target_w = img_width_mm * mm
    target_h = target_w * h / w

    flows.append(Image(pth, width=target_w, height=target_h, hAlign="LEFT"))
    if result_text:
        flows.append(Spacer(1, 0.8*mm))
        flows.append(Paragraph(result_text, S["EqResult"]))
    flows.append(Spacer(1, 1.6*mm))
    return flows

# ------------------------- Générateur PDF ----------------------------

def generer_rapport_pdf(
    nom_projet="",
    partie="",
    date="",
    indice="",
    beton="C30/37",
    fyk="500",
    b=20, h=40, enrobage=5.0,
    M_inf=0.0, M_sup=0.0,
    V=0.0, V_lim=0.0,  # V_lim non imprimé ici (rapport compact)
    # Choix utilisateur (pour les conclusions)
    n_as_inf=None, o_as_inf=None,
    n_as_sup=None, o_as_sup=None,
    n_etriers=None, o_etrier=None, pas_etrier=None,
    **kwargs,
):
    # Données & constantes
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
    As_inf_req = (M_inf * 1e6) / (fyd * 0.9 * d_utile * 10) if M_inf > 0 else 0.0
    As_sup_req = (M_sup * 1e6) / (fyd * 0.9 * d_utile * 10) if M_sup > 0 else 0.0

    tau = (V * 1e3) / (0.75 * b * h * 100) if V > 0 else 0.0
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05

    # Sortie
    out_dir = "/mnt/data"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        out_dir = tempfile.gettempdir()
    out_name = f"rapport__{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out_path = os.path.join(out_dir, out_name)

    tmpdir = tempfile.mkdtemp(prefix="pdf_eq_")
    S = get_styles()
    flow = []

    try:
        doc = SimpleDocTemplate(
            out_path,
            pagesize=A4,
            leftMargin=14*mm, rightMargin=14*mm,
            topMargin=12*mm, bottomMargin=12*mm,
            title="Rapport de dimensionnement – Poutre BA",
        )

        # Titre + méta
        flow.append(Paragraph("Rapport de dimensionnement – Poutre en béton armé", S["Title"]))
        flow.append(Table(
            [
                ["Projet :", nom_projet or "—", "Date :", date or datetime.today().strftime("%d/%m/%Y")],
                ["Partie :", partie or "—", "Indice :", indice or "—"],
            ],
            colWidths=[16*mm, 70*mm, 16*mm, 70*mm],
            style=TableStyle([
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 9.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ])
        ))
        flow.append(Spacer(1, 3*mm))

        # Caractéristiques
        flow.append(Paragraph("Caractéristiques de la poutre", S["H1"]))
        flow.append(Table(
            [
                ["Classe de béton", beton, "Acier (fyk)", f"{fyk} N/mm²"],
                ["Largeur b", f"{fr(b,1)} cm", "Hauteur h", f"{fr(h,1)} cm"],
                ["Enrobage", f"{fr(enrobage,1)} cm", "Hauteur utile d", f"{fr(d_utile,1)} cm"],
            ],
            colWidths=[34*mm, 53*mm, 34*mm, 53*mm],
            style=TableStyle([
                ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#cccccc")),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f6f6f6")),
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 9.5),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 3*mm))

        # Hauteur utile
        flow.append(Paragraph("Vérification de la hauteur utile", S["H1"]))
        tex_hmin_num = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + fr(M_max,2).replace(",", ".")
            + r"\cdot 10^{6}}{"
            + fr(alpha_b,2).replace(",", ".")
            + r"\cdot "
            + fr(b,1).replace(",", ".")
            + r"\cdot 10\cdot "
            + fr(mu_val,1).replace(",", ".")
            + r"}}/10"
            + tex_unit("cm")
        )
        res_hmin = f"Résultat : <b>h_min = {fr(hmin, 1)} cm</b>"
        flow += eq_block(1, tmpdir, tex_hmin_num, res_hmin)
        ok_h = (hmin + enrobage) <= h
        msg = f"h_min + enrobage = {fr(hmin+enrobage,1)} cm ≤ h = {fr(h,1)} cm — " + ("<b>Conforme</b>" if ok_h else "<b>Non conforme</b>")
        flow.append(Paragraph(msg, S["Green" if ok_h else "Red"]))
        flow.append(Spacer(1, 2*mm))

        # Armatures inférieures
        flow.append(Paragraph("Armatures inférieures", S["H1"]))
        tex_as_inf_num = (
            r"A_{s,\mathrm{inf}}=\dfrac{"
            + fr(M_inf,2).replace(",", ".")
            + r"\cdot 10^{6}}{"
            + fr(fyd,1).replace(",", ".")
            + r"\cdot 0.9\cdot "
            + fr(d_utile,1).replace(",", ".")
            + r"\cdot 10}"
            + tex_unit("mm^2")
        )
        res_as_inf = f"Résultat : <b>A<sub>s,inf</sub> = {fr(As_inf_req,1)} mm²</b>"
        flow += eq_block(2, tmpdir, tex_as_inf_num, res_as_inf)
        flow.append(Paragraph(
            f"A<sub>s,min</sub> = <b>{fr(As_min,1)} mm²</b> ; A<sub>s,max</sub> = <b>{fr(As_max,1)} mm²</b>",
            S["Small"])
        )
        if n_as_inf and o_as_inf:
            As_inf_ch = aire_barres(n_as_inf, o_as_inf)
            ok_inf = (As_min <= As_inf_ch <= As_max) and (As_inf_ch >= As_inf_req)
            flow.append(Paragraph(
                f"<b>Choix :</b> {int(n_as_inf)}Ø{int(o_as_inf)} → {fr(As_inf_ch,1)} mm² — <b>{verdict(ok_inf)}</b>",
                S["EqResult"]
            ))
        flow.append(Spacer(1, 2*mm))

        # Armatures supérieures (si M_sup)
        if M_sup and M_sup > 0:
            flow.append(Paragraph("Armatures supérieures", S["H1"]))
            tex_as_sup_num = (
                r"A_{s,\mathrm{sup}}=\dfrac{"
                + fr(M_sup,2).replace(",", ".")
                + r"\cdot 10^{6}}{"
                + fr(fyd,1).replace(",", ".")
                + r"\cdot 0.9\cdot "
                + fr(d_utile,1).replace(",", ".")
                + r"\cdot 10}"
                + tex_unit("mm^2")
            )
            res_as_sup = f"Résultat : <b>A<sub>s,sup</sub> = {fr(As_sup_req,1)} mm²</b>"
            flow += eq_block(3, tmpdir, tex_as_sup_num, res_as_sup)
            flow.append(Paragraph(
                f"A<sub>s,min</sub> = <b>{fr(As_min,1)} mm²</b> ; A<sub>s,max</sub> = <b>{fr(As_max,1)} mm²</b>",
                S["Small"])
            )
            if n_as_sup and o_as_sup:
                As_sup_ch = aire_barres(n_as_sup, o_as_sup)
                ok_sup = (As_min <= As_sup_ch <= As_max) and (As_sup_ch >= As_sup_req)
                flow.append(Paragraph(
                    f"<b>Choix :</b> {int(n_as_sup)}Ø{int(o_as_sup)} → {fr(As_sup_ch,1)} mm² — <b>{verdict(ok_sup)}</b>",
                    S["EqResult"]
                ))
            flow.append(Spacer(1, 2*mm))

        # Effort tranchant
        if V and V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["H1"]))
            tex_tau_num = (
                r"\tau=\dfrac{"
                + fr(V,2).replace(",", ".")
                + r"\cdot 10^{3}}{0.75\cdot "
                + fr(b,1).replace(",", ".")
                + r"\cdot "
                + fr(h,1).replace(",", ".")
                + r"\cdot 100}"
                + tex_unit("N/mm^{2}")
            )
            res_tau = f"Résultat : <b>τ = {fr(tau,2)} N/mm²</b>"
            flow += eq_block(4, tmpdir, tex_tau_num, res_tau)
            flow.append(Paragraph(
                f"Seuils : τ<sub>adm I</sub> = {fr(tau_1,2)} ; τ<sub>adm II</sub> = {fr(tau_2,2)} ; τ<sub>adm IV</sub> = {fr(tau_4,2)} (N/mm²).",
                S["Small"])
            )
            besoin_str = (
                "Pas besoin d’étriers (≤ τ_adm I)." if tau <= tau_1 else
                "Besoin d’étriers (≤ τ_adm II)." if tau <= tau_2 else
                "Barres inclinées + étriers (≤ τ_adm IV)." if tau <= tau_4 else
                "Non acceptable (> τ_adm IV)."
            )
            flow.append(Paragraph(besoin_str, S["Green" if tau <= tau_4 else "Red"]))

            if n_etriers and o_etrier and pas_etrier is not None:
                Ast_e = aire_barres(n_etriers, o_etrier)
                s_th = Ast_e * fyd * d_utile * 10 / (10 * V * 1e3)
                ok_pas = pas_etrier <= s_th
                flow.append(Paragraph(
                    f"<b>Choix :</b> Ø{int(o_etrier)} – {int(n_etriers)} brin(s) – pas {fr(pas_etrier,1)} cm ; "
                    f"s<sub>th</sub> = {fr(s_th,1)} cm — <b>{verdict(ok_pas)}</b>",
                    S["EqResult"]
                ))
            flow.append(Spacer(1, 2*mm))

        # Pied de page
        flow.append(Paragraph("Rapport généré automatiquement – © Études Structure", S["Small"]))

        # Build
        doc.build(flow)
        return out_path

    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
