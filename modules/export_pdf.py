# -*- coding: utf-8 -*-
"""
export_pdf.py — Rapport Poutre BA (aligné & unités mm)
- 1 Caractéristiques, 2 Sollicitations (NOUVEAU), 3 Dimensionnement
- 3.1 Vérification de la hauteur utile, 3.2 Calcul des armatures
- Grille 2 colonnes pour l’alignement (texte à gauche, OK/NON à droite)
- Formules LaTeX en mm, ENCADRÉES (cadre noir)
- Espacement +50 % sur les lignes techniques (lisibilité)
- Nom de fichier : PRO_PARTIE_#Indice_AAAAMMJJ.pdf
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

# =================== Réglages d'affichage des équations ===================

EQ_IMG_WIDTH_MM = 38      # largeur base (mm)
EQ_IMG_SCALE    = 1.20    # facteur d’échelle global (120 %)
MATH_FONTSIZE   = 14      # taille glyphes mathtext (13–16 conseillé)

ICON_OK  = "OK"
ICON_NOK = "NON"
BLUE_DARK = colors.HexColor("#003366")

# ================================ Utils ===================================

def fr(x, nd=1):
    """Format FR (virgule)."""
    if x is None:
        return "-"
    s = f"{float(x):,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", " ")
    if s.startswith("-0,"):
        s = s.replace("-0,", "0,")
    return s

def num(x, nd):
    """Nombre au format LaTeX (point décimal)."""
    return fr(x, nd).replace(",", ".")

def render_equation(tex_expr, out_path, fontsize=MATH_FONTSIZE, pad=0.05):
    """Rendu d’une équation (mathtext) en PNG transparent."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig = plt.figure(figsize=(1, 1), dpi=250)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.text(0.0, 0.5, f"${tex_expr}$", fontsize=fontsize, va="center", ha="left")
    fig.savefig(out_path, dpi=250, transparent=True, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    return out_path

def aire_barres(n, phi):
    """Aire mm² pour n barres Øphi (mm)."""
    return float(n) * math.pi * (float(phi)/2.0)**2

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
    # leading +50 % sur Eq/Blue/BodyTech pour aérer les lignes techniques
    return {
        "Body": ParagraphStyle("Body", parent=ss["BodyText"],
                               fontName=base, fontSize=9.5, leading=12, textColor=black),
        "Hmain": ParagraphStyle("Hmain", parent=ss["BodyText"],
                                fontName=base_b, fontSize=10.0, leading=13,
                                spaceBefore=6, spaceAfter=4, textColor=black),
        "Hnorm": ParagraphStyle("Hnorm", parent=ss["BodyText"],
                                fontName=base_b, fontSize=9.8, leading=13,
                                spaceBefore=5, spaceAfter=3, textColor=black),
        "Hsub": ParagraphStyle("Hsub", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.6, leading=12.5,
                               spaceBefore=4, spaceAfter=3, textColor=black),
        # Styles techniques (lignes à espacement augmenté)
        "Eq": ParagraphStyle("Eq", parent=ss["BodyText"],
                             fontName=base, fontSize=9.5, leading=18, textColor=black),
        "Blue": ParagraphStyle("Blue", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=18, textColor=BLUE_DARK),
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9, leading=11, textColor=black),
    }

# --------------------- Grille 2 colonnes (alignement) ---------------------

def make_row(left_flowable, styles, content_width, icon_text=""):
    col_icon = 12*mm
    col_text = content_width - col_icon
    tbl = Table([[left_flowable, Paragraph(icon_text, styles["Eq"])]],
                colWidths=[col_text, col_icon])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",  (1,0), (1,0), "RIGHT"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING",   (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",(0,0), (-1,-1), 0),
    ]))
    return tbl

def text_row(html_text, styles, content_width, style_name="Eq", icon_text=""):
    return make_row(Paragraph(html_text, styles[style_name]), styles, content_width, icon_text)

def status_row(html_text, ok_bool, styles, content_width, style_name="Eq"):
    return text_row(html_text, styles, content_width, style_name,
                    ICON_OK if ok_bool else ICON_NOK)

def eq_row(tex_numeric, tmpdir, styles, content_width, icon_text=""):
    """
    Rend l’équation + l’encadre dans un petit cadre noir,
    puis l’insère dans la grille 2 colonnes (alignée).
    """
    img_path = os.path.join(tmpdir, f"eq_{abs(hash(tex_numeric))}.png")
    render_equation(tex_numeric, img_path, fontsize=MATH_FONTSIZE, pad=0.05)
    with PILImage.open(img_path) as im:
        w, h = im.size
    target_w = EQ_IMG_WIDTH_MM * mm * EQ_IMG_SCALE
    target_h = target_w * h / w
    img = Image(img_path, width=target_w, height=target_h, hAlign="LEFT")
    # Encadrement (cadre noir) autour de l’image
    box = Table([[img]], colWidths=[target_w])
    box.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.75, colors.black),
        ("LEFTPADDING",  (0,0), (-1,-1), 3),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING",   (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0), (-1,-1), 2),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    return make_row(box, styles, content_width, icon_text)

# =============================== Données ==============================

def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(p):
        p = "beton_classes.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================ Générateur PDF ==========================

def generer_rapport_pdf(
    nom_projet="", partie="", date="", indice="",
    beton="C30/37", fyk="500",
    b=20, h=40, enrobage=5.0,
    M_inf=0.0, M_sup=0.0,
    V=0.0, V_lim=0.0,
    n_as_inf=None, o_as_inf=None,
    n_as_sup=None, o_as_sup=None,
    o_etrier=None, pas_etrier=None,
    o_etrier_r=None, pas_etrier_r=None,
    **kwargs,
):
    data = load_beton_data()
    d = data.get(beton, {})
    fck_cube = d.get("fck_cube", 30)
    alpha_b  = d.get("alpha_b", 0.72)
    mu_val   = d.get(f"mu_a{fyk}", 10.2)
    fyd      = int(fyk) / 1.5

    # Géométrie (cm) + mm pour affichage
    d_utile = h - enrobage
    b_mm = b * 10.0
    h_mm = h * 10.0
    d_mm = d_utile * 10.0

    # Calculs (cohérents avec le module Streamlit)
    M_max   = max(float(M_inf or 0.0), float(M_sup or 0.0))
    hmin    = math.sqrt((M_max*1e6)/(alpha_b*b*10*mu_val))/10.0 if M_max>0 else 0.0

    As_min      = 0.0013 * b * h * 1e2
    As_max      = 0.04   * b * h * 1e2
    As_inf_req  = (M_inf*1e6) / (fyd*0.9*d_utile*10) if M_inf>0 else 0.0
    As_sup_req  = (M_sup*1e6) / (fyd*0.9*d_utile*10) if M_sup>0 else 0.0

    tau   = (V*1e3) / (0.75*b*h*100) if V>0 else 0.0
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05

    # Sortie
    out_dir = "/mnt/data"
    try: os.makedirs(out_dir, exist_ok=True)
    except Exception: out_dir = tempfile.gettempdir()
    proj = (nom_projet or "XXX")[:3].upper()
    part = (partie or "Partie").strip().replace(" ", "_")
    ind  = (indice or "0")
    date_str = datetime.now().strftime("%Y%m%d")
    out_path = os.path.join(out_dir, f"{proj}_{part}_#{ind}_{date_str}.pdf")

    leftM, rightM, topM, botM = 14*mm, 14*mm, 12*mm, 12*mm
    content_width = A4[0] - leftM - rightM
    S = get_styles()
    flow = []
    tmpdir = tempfile.mkdtemp(prefix="pdf_eq_")

    try:
        doc = SimpleDocTemplate(out_path, pagesize=A4,
                                leftMargin=leftM, rightMargin=rightM,
                                topMargin=topM, bottomMargin=botM)

        # ------------------------------------------------------------------ #
        # 1. CARACTÉRISTIQUES
        # ------------------------------------------------------------------ #
        flow.append(Table(
            [
                ["Projet :", nom_projet or "—", "Date :", date or datetime.today().strftime("%d/%m/%Y")],
                ["Partie :", partie or "—", "Indice :", indice or "—"],
            ],
            colWidths=[16*mm, content_width*0.58, 16*mm, content_width*0.26],
            style=TableStyle([
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 9.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ("ALIGN", (0,0), (-1,-1), "LEFT"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 3))

        flow.append(Paragraph("<u>1. Caractéristiques de la poutre</u>", S["Hmain"]))
        flow.append(Table(
            [
                ["Classe de béton", beton, "Armature", f"{fyk} N/mm²"],
                ["Largeur b", f"{fr(b,1)} cm", "Hauteur h", f"{fr(h,1)} cm"],
                ["Enrobage", f"{fr(enrobage,1)} cm", "Hauteur utile d", f"{fr(d_utile,1)} cm"],
            ],
            colWidths=[34*mm, content_width/2-34*mm, 34*mm, content_width/2-34*mm],
            style=TableStyle([
                ("GRID", (0,0), (-1,-1), 0.25, colors.black),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f6f6f6")),
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 9.5),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 5))

        # ------------------------------------------------------------------ #
        # 2. SOLLICITATIONS (NOUVEAU)
        # ------------------------------------------------------------------ #
        flow.append(Paragraph("<u>2. Sollicitations</u>", S["Hmain"]))
        sol_table = Table(
            [
                ["Moment inférieur M", f"{fr(M_inf,1)} kNm" if (M_inf and M_inf>0) else "—",
                 "Moment supérieur M_sup", f"{fr(M_sup,1)} kNm" if (M_sup and M_sup>0) else "—"],
                ["Effort tranchant V", f"{fr(V,1)} kN" if (V and V>0) else "—",
                 "Effort tranchant réduit V_réduit", f"{fr(V_lim,1)} kN" if (V_lim and V_lim>0) else "—"],
            ],
            colWidths=[48*mm, content_width/2-48*mm, 58*mm, content_width/2-58*mm],
            style=TableStyle([
                ("GRID", (0,0), (-1,-1), 0.25, colors.black),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f6f6f6")),
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 9.5),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        )
        flow.append(sol_table)
        flow.append(Spacer(1, 6))

        # ------------------------------------------------------------------ #
        # 3. DIMENSIONNEMENT
        # ------------------------------------------------------------------ #
        flow.append(Paragraph("<u>3. Dimensionnement</u>", S["Hmain"]))

        # 3.1 Hauteur utile
        flow.append(Paragraph("3.1 Vérification de la hauteur utile", S["Hnorm"]))
        tex_hmin = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + num(M_max,2) + r"\cdot 10^{6}}{"
            + num(alpha_b,4) + r"\cdot " + num(b_mm,1) + r"\cdot "
            + num(mu_val,4) + r"\cdot 100}}"
            + r" = " + num(hmin,1) + r"\ \mathrm{cm}"
        )
        flow.append(eq_row(tex_hmin, tmpdir, S, content_width, icon_text=""))
        ok_h = (hmin + enrobage) <= h
        flow.append(status_row(
            f"h<sub>min</sub> + enrob. = {fr(hmin+enrobage,1)} cm ≤ h = {fr(h,1)} cm",
            ok_h, S, content_width, "Eq"
        ))
        flow.append(Spacer(1, 5))

        # 3.2 Calcul des armatures
        flow.append(Paragraph("3.2 Calcul des armatures", S["Hnorm"]))

        # Armatures inférieures
        flow.append(Paragraph("Armatures inférieures", S["Hsub"]))
        tex_as_inf = (
            r"A_{s,\mathrm{inf}}=\dfrac{"
            + num(M_inf,2) + r"\cdot 10^{6}}{"
            + num(fyd,1) + r"\cdot 0.9\cdot " + num(d_mm,1) + r"}"
            + r" = " + num(As_inf_req,1) + r"\ \mathrm{mm^2}"
        )
        flow.append(eq_row(tex_as_inf, tmpdir, S, content_width, icon_text=""))
        flow.append(text_row(f"Section d’acier minimale : A<sub>s,min</sub> = {fr(As_min,1)} mm²", S, content_width))
        flow.append(text_row(f"Section d’acier maximale : A<sub>s,max</sub> = {fr(As_max,1)} mm²", S, content_width))
        if n_as_inf and o_as_inf:
            As_inf_ch = aire_barres(n_as_inf, o_as_inf)
            ok_inf = (As_min <= As_inf_ch <= As_max) and (As_inf_ch >= As_inf_req)
            flow.append(status_row(
                f"On prend : {int(n_as_inf)}Ø{int(o_as_inf)} → {fr(As_inf_ch,1)} mm²",
                ok_inf, S, content_width, "Blue"
            ))
        flow.append(Spacer(1, 4))

        # Armatures supérieures (si M_sup)
        if M_sup and M_sup > 0:
            flow.append(Paragraph("Armatures supérieures", S["Hsub"]))
            tex_as_sup = (
                r"A_{s,\mathrm{sup}}=\dfrac{"
                + num(M_sup,2) + r"\cdot 10^{6}}{"
                + num(fyd,1) + r"\cdot 0.9\cdot " + num(d_mm,1) + r"}"
                + r" = " + num(As_sup_req,1) + r"\ \mathrm{mm^2}"
            )
            flow.append(eq_row(tex_as_sup, tmpdir, S, content_width, icon_text=""))
            flow.append(text_row(f"Section d’acier minimale : A<sub>s,min</sub> = {fr(As_min,1)} mm²", S, content_width))
            flow.append(text_row(f"Section d’acier maximale : A<sub>s,max</sub> = {fr(As_max,1)} mm²", S, content_width))
            if n_as_sup and o_as_sup:
                As_sup_ch = aire_barres(n_as_sup, o_as_sup)
                ok_sup = (As_min <= As_sup_ch <= As_max) and (As_sup_ch >= As_sup_req)
                flow.append(status_row(
                    f"On prend : {int(n_as_sup)}Ø{int(o_as_sup)} → {fr(As_sup_ch,1)} mm²",
                    ok_sup, S, content_width, "Blue"
                ))
            flow.append(Spacer(1, 6))

        # Effort tranchant (τ)
        if V and V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["Hnorm"]))
            tex_tau = (
                r"\tau=\dfrac{" + num(V,2) + r"\cdot 10^{3}}{0.75\cdot "
                + num(b_mm,1) + r"\cdot " + num(h_mm,1) + r"}"
                + r" = " + num(tau,2) + r"\ \mathrm{N/mm^{2}}"
            )
            flow.append(eq_row(tex_tau, tmpdir, S, content_width, icon_text=""))
            if tau <= tau_1:
                lim_lab, lim_val, ok_tau = "τ_adm I", tau_1, True
            elif tau <= tau_2:
                lim_lab, lim_val, ok_tau = "τ_adm II", tau_2, True
            elif tau <= tau_4:
                lim_lab, lim_val, ok_tau = "τ_adm IV", tau_4, True
            else:
                lim_lab, lim_val, ok_tau = "τ_adm IV", tau_4, False
            flow.append(status_row(
                (f"τ = {fr(tau,2)} N/mm² < {lim_lab} = {fr(lim_val,2)} N/mm²")
                if ok_tau else
                (f"τ = {fr(tau,2)} N/mm² > {lim_lab} = {fr(lim_val,2)} N/mm²"),
                ok_tau, S, content_width, "Eq"
            ))
            flow.append(Spacer(1, 6))

            # Calcul des étriers
            flow.append(Paragraph("Calcul des étriers", S["Hsub"]))
            A_st_e = aire_barres(1, o_etrier or 8)  # 1 étrier
            s_th = (A_st_e * fyd * d_mm) / (V * 1e4) if V else 0.0  # cm
            tex_s = (
                r"s_\mathrm{th}=\dfrac{" + num(A_st_e,1) + r"\cdot "
                + num(fyd,1) + r"\cdot " + num(d_mm,1) + r"}{"
                + num(V,2) + r"\cdot 10^{4}}"
                + r" = " + num(s_th,1) + r"\ \mathrm{cm}"
            )
            flow.append(eq_row(tex_s, tmpdir, S, content_width, icon_text=""))
            if o_etrier and pas_etrier is not None:
                ok_pas = pas_etrier <= s_th
                flow.append(status_row(
                    f"On prend : 1 étrier – Ø{int(o_etrier)} – {fr(pas_etrier,1)} cm (pas théorique = {fr(s_th,1)} cm)",
                    ok_pas, S, content_width, "Blue"
                ))
            flow.append(Spacer(1, 6))

        # Étriers réduits (V_lim)
        if V_lim and V_lim > 0:
            flow.append(Paragraph("Calcul des étriers réduits", S["Hsub"]))
            A_st_er = aire_barres(1, o_etrier_r or o_etrier or 8)
            s_thr = (A_st_er * fyd * d_mm) / (V_lim * 1e4)
            tex_sr = (
                r"s_{\mathrm{th},r}=\dfrac{" + num(A_st_er,1) + r"\cdot "
                + num(fyd,1) + r"\cdot " + num(d_mm,1) + r"}{"
                + num(V_lim,2) + r"\cdot 10^{4}}"
                + r" = " + num(s_thr,1) + r"\ \mathrm{cm}"
            )
            flow.append(eq_row(tex_sr, tmpdir, S, content_width, icon_text=""))
            if o_etrier_r and pas_etrier_r is not None:
                ok_pas_r = pas_etrier_r <= s_thr
                flow.append(status_row(
                    f"On prend : 1 étrier – Ø{int(o_etrier_r)} – {fr(pas_etrier_r,1)} cm (pas théorique = {fr(s_thr,1)} cm)",
                    ok_pas_r, S, content_width, "Blue"
                ))

        # Build
        doc.build(flow)
        return out_path

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
