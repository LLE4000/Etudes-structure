# -*- coding: utf-8 -*-
"""
export_pdf.py
Rapport de dimensionnement – Poutre BA
- Formules LaTeX numériques avec résultat
- Agrandies 120% en largeur/hauteur
- Armatures et étriers formatés avec sections min/max et choix utilisateur
- Résultats choisis en bleu foncé
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from PIL import Image as PILImage
import json, os, math, tempfile, shutil
from datetime import datetime

# ========================== Constantes ===============================

ICON_OK  = "OK"
ICON_NOK = "NON"

# 120% de la taille par défaut
EQ_IMG_WIDTH_MM = 38 * 1.2  

# ============================ Utils =================================

def fr(x, nd=1):
    if x is None:
        return "-"
    s = f"{float(x):,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", " ")
    if s.startswith("-0,"):
        s = s.replace("-0,", "0,")
    return s

def tex_unit(u):
    return r"\ \mathrm{" + u + "}"

def render_equation(tex_expr, out_path, fontsize=13, pad=0.05):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig = plt.figure(figsize=(1, 1), dpi=250)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.text(0.0, 0.5, f"${tex_expr}$", fontsize=fontsize, va="center", ha="left")
    fig.savefig(out_path, dpi=250, transparent=True, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    return out_path

def aire_barres(n, phi):
    return float(n) * math.pi * (float(phi)/2.0)**2

def icon(ok_bool):
    return ICON_OK if ok_bool else ICON_NOK

# ============================ Styles ================================

def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSerif.ttf"))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", "DejaVuSerif-Bold.ttf"))
        return ("DejaVu", "DejaVu-Bold")
    except Exception:
        return ("Times-Roman", "Times-Bold")

def get_styles():
    base, base_b = register_fonts()
    ss = getSampleStyleSheet()
    black = colors.black
    return {
        "Body": ParagraphStyle("Body", parent=ss["BodyText"],
                               fontName=base, fontSize=9.5, leading=12,
                               textColor=black),
        "Hmain": ParagraphStyle("Hmain", parent=ss["BodyText"],
                                fontName=base_b, fontSize=9.5, leading=12,
                                spaceBefore=5, spaceAfter=3,
                                textColor=black),
        "Hnorm": ParagraphStyle("Hnorm", parent=ss["BodyText"],
                                fontName=base_b, fontSize=9.5, leading=12,
                                spaceBefore=4, spaceAfter=2,
                                textColor=black),
        "Hsub": ParagraphStyle("Hsub", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=12,
                               spaceBefore=2, spaceAfter=1,
                               textColor=black),
        "Eq": ParagraphStyle("Eq", parent=ss["BodyText"],
                             fontName=base, fontSize=9.5, leading=12,
                             textColor=black),
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9, leading=11,
                                textColor=black),
        "Blue": ParagraphStyle("Blue", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=12,
                               textColor=colors.HexColor("#003366")),
    }

# ====================== Equation image ==============================

def eq_img(tex_numeric, tmpdir, img_width_mm=EQ_IMG_WIDTH_MM):
    pth = os.path.join(tmpdir, f"eq_{abs(hash(tex_numeric))}.png")
    render_equation(tex_numeric, pth, fontsize=13, pad=0.05)
    with PILImage.open(pth) as im:
        w, h = im.size
    target_w = img_width_mm * mm
    target_h = target_w * h / w
    return Image(pth, width=target_w, height=target_h, hAlign="LEFT")

# ====================== Générateur PDF ==============================

def generer_rapport_pdf(
    nom_projet="", partie="", date="", indice="",
    beton="C30/37", fyk="500",
    b=20, h=40, enrobage=5.0,
    M_inf=0.0, M_sup=0.0,
    V=0.0, V_lim=0.0,
    n_as_inf=None, o_as_inf=None,
    n_as_sup=None, o_as_sup=None,
    n_etriers=None, o_etrier=None, pas_etrier=None,
    **kwargs,
):
    beton_data = load_beton_data()
    d = beton_data.get(beton, {})
    fck_cube = d.get("fck_cube", 30)
    alpha_b  = d.get("alpha_b", 0.72)
    mu_val   = d.get(f"mu_a{fyk}", 11.5)
    fyd      = int(fyk) / 1.5

    d_utile = h - enrobage
    M_max   = max(float(M_inf or 0.0), float(M_sup or 0.0))
    hmin    = math.sqrt((M_max*1e6)/(alpha_b*b*10*mu_val))/10.0 if M_max>0 else 0.0

    As_min      = 0.0013 * b * h * 1e2
    As_max      = 0.04   * b * h * 1e2
    As_inf_req  = (M_inf*1e6) / (fyd*0.9*d_utile*10) if M_inf>0 else 0.0

    tau   = (V*1e3) / (0.75*b*h*100) if V>0 else 0.0
    tau_1 = 0.016 * fck_cube / 1.05

    out_dir = "/mnt/data"
    os.makedirs(out_dir, exist_ok=True)
    proj = (nom_projet or "XXX")[:3].upper()
    part = (partie or "Partie").strip().replace(" ", "_")
    ind  = (indice or "0")
    date_str = datetime.now().strftime("%Y%m%d")
    out_name = f"{proj}_{part}_#{ind}_{date_str}.pdf"
    out_path = os.path.join(out_dir, out_name)

    leftM, rightM, topM, botM = 14*mm, 14*mm, 12*mm, 12*mm
    content_width = A4[0] - leftM - rightM
    S = get_styles()
    flow = []
    tmpdir = tempfile.mkdtemp(prefix="pdf_eq_")

    try:
        doc = SimpleDocTemplate(out_path,
            pagesize=A4,
            leftMargin=leftM, rightMargin=rightM,
            topMargin=topM, bottomMargin=botM)

        # Vérification de la hauteur utile
        flow.append(Paragraph("Vérification de la hauteur utile", S["Hnorm"]))
        tex_hmin = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + fr(M_max,2).replace(",", ".")
            + r"\cdot 10^{6}}{"
            + fr(alpha_b,2).replace(",", ".")
            + r"\cdot "
            + fr(b,1).replace(",", ".")
            + r"\cdot 10\cdot "
            + fr(mu_val,1).replace(",", ".")
            + r"}}/10"
            + r" = " + fr(hmin,1) + tex_unit("cm")
        )
        flow.append(eq_img(tex_hmin, tmpdir))
        flow.append(Paragraph(f"h<sub>min</sub> + enrob. = {fr(hmin+enrobage,1)} cm ≤ h = {fr(h,1)} cm", S["Eq"]))
        flow.append(Spacer(1,3))

        # Armatures inférieures
        flow.append(Paragraph("Armatures inférieures", S["Hsub"]))
        tex_as_inf = (
            r"A_{s,\mathrm{inf}}=\dfrac{"
            + fr(M_inf,2).replace(",", ".")
            + r"\cdot 10^{6}}{"
            + fr(fyd,1).replace(",", ".")
            + r"\cdot 0.9\cdot "
            + fr(d_utile,1).replace(",", ".")
            + r"\cdot 10}"
            + r" = " + fr(As_inf_req,1) + tex_unit("mm^2")
        )
        flow.append(eq_img(tex_as_inf, tmpdir))
        flow.append(Paragraph(f"Section d’acier minimale : A<sub>s,min</sub> = {fr(As_min,1)} mm²", S["Eq"]))
        flow.append(Paragraph(f"Section d’acier maximale : A<sub>s,max</sub> = {fr(As_max,1)} mm²", S["Eq"]))
        if n_as_inf and o_as_inf:
            As_inf_ch = aire_barres(n_as_inf, o_as_inf)
            flow.append(Paragraph(
                f"On prend : {int(n_as_inf)}Ø{int(o_as_inf)} → {fr(As_inf_ch,1)} mm²",
                S["Blue"]
            ))
        flow.append(Spacer(1,3))

        # Étriers
        if V and V>0:
            Ast_e = aire_barres(n_etriers or 1, o_etrier or 8)
            s_th = Ast_e * fyd * d_utile * 10 / (10 * V * 1e3)
            tex_s = (
                r"s_\mathrm{th}=\dfrac{"
                + fr(Ast_e,1).replace(",", ".")
                + r"\cdot "
                + fr(fyd,1).replace(",", ".")
                + r"\cdot "
                + fr(d_utile,1).replace(",", ".")
                + r"\cdot 10}{10\cdot "
                + fr(V,2).replace(",", ".")
                + r"\cdot 10^{3}}"
                + r" = " + fr(s_th,1) + tex_unit("cm")
            )
            flow.append(eq_img(tex_s, tmpdir))
            if n_etriers and o_etrier and pas_etrier is not None:
                flow.append(Paragraph(
                    f"On prend : {int(n_etriers)} étrier Ø{int(o_etrier)} – {fr(pas_etrier,1)} cm (pas théorique = {fr(s_th,1)} cm)",
                    S["Blue"]
                ))

        doc.build(flow)
        return out_path

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
