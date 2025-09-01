# -*- coding: utf-8 -*-
"""
export_pdf.py — Rapport Poutre BA (aligné & unités mm)
- Sections & sollicitations numérotées (cf. ta version précédente)
- μ_a et α_b sur 4 décimales
- Dimensions en mm et fyd affichées sans décimales dans les équations
- s_th : section transversale développée n·π·φ²/4 (pas un nombre brut)
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

EQ_IMG_WIDTH_MM = 38
EQ_IMG_SCALE    = 1.20
MATH_FONTSIZE   = 14

ICON_OK  = "OK"
ICON_NOK = "NON"
BLUE_DARK = colors.HexColor("#003366")

# ================================ Utils ===================================

def fr(x, nd=1):
    if x is None:
        return "-"
    s = f"{float(x):,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", " ")
    if s.startswith("-0,"):
        s = s.replace("-0,", "0,")
    return s

# décimales standardisées
def fr0(x): return fr(x, 0)
def fr1(x): return fr(x, 1)
def fr2(x): return fr(x, 2)
def fr4(x): return fr(x, 4)

def num_from_fr(s):  # FR → TeX
    return s.replace(",", ".")

def num0(x): return num_from_fr(fr0(x))
def num1(x): return num_from_fr(fr1(x))
def num2(x): return num_from_fr(fr2(x))
def num4(x): return num_from_fr(fr4(x))

def render_equation(tex_expr, out_path, fontsize=MATH_FONTSIZE, pad=0.05):
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
        # lignes techniques aérées
        "Eq": ParagraphStyle("Eq", parent=ss["BodyText"],
                             fontName=base, fontSize=9.5, leading=18, textColor=black),
        "Blue": ParagraphStyle("Blue", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=18, textColor=BLUE_DARK),
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9, leading=11, textColor=black),
    }

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
    img_path = os.path.join(tmpdir, f"eq_{abs(hash(tex_numeric))}.png")
    render_equation(tex_numeric, img_path, fontsize=MATH_FONTSIZE, pad=0.05)
    with PILImage.open(img_path) as im:
        w, h = im.size
    target_w = EQ_IMG_WIDTH_MM * mm * EQ_IMG_SCALE
    target_h = target_w * h / w
    img = Image(img_path, width=target_w, height=target_h, hAlign="LEFT")
    # Cadre noir autour de l'équation
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
    # étriers + branches (nouveaux)
    n_branches_etrier=1, o_etrier=None, pas_etrier=None,
    n_branches_etrier_r=1, o_etrier_r=None, pas_etrier_r=None,
    **kwargs,
):
    data = load_beton_data()
    d = data.get(beton, {})
    fck_cube = d.get("fck_cube", 30)
    alpha_b  = d.get("alpha_b", 0.72)
    mu_val   = d.get(f"mu_a{fyk}", 0.1700)   # ex. 0.1709
    fyd      = int(fyk) / 1.5               # sera affiché en 0 décimale

    # Géométrie (cm) + mm
    d_utile = h - enrobage
    b_mm = b * 10.0
    h_mm = h * 10.0
    d_mm = d_utile * 10.0

    # Calculs
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

        # 1. Caractéristiques
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
                ["Largeur b", f"{fr1(b)} cm", "Hauteur h", f"{fr1(h)} cm"],
                ["Enrobage", f"{fr1(enrobage)} cm", "Hauteur utile d", f"{fr1(d_utile)} cm"],
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

        # 2. Sollicitations
        flow.append(Paragraph("<u>2. Sollicitations</u>", S["Hmain"]))
        sol_table = Table(
            [
                ["Moment inférieur M", f"{fr1(M_inf)} kNm" if (M_inf and M_inf>0) else "—",
                 "Moment supérieur M_sup", f"{fr1(M_sup)} kNm" if (M_sup and M_sup>0) else "—"],
                ["Effort tranchant V", f"{fr1(V)} kN" if (V and V>0) else "—",
                 "Effort tranchant réduit V_réduit", f"{fr1(V_lim)} kN" if (V_lim and V_lim>0) else "—"],
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

        # 3. Dimensionnement
        flow.append(Paragraph("<u>3. Dimensionnement</u>", S["Hmain"]))

        # 3.1 Hauteur utile — b en mm (0 décimale), α_b & μ_a sur 4 décimales
        flow.append(Paragraph("3.1 Vérification de la hauteur utile", S["Hnorm"]))
        tex_hmin = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + num2(M_max) + r"\cdot 10^{6}}{"
            + num4(alpha_b) + r"\cdot " + num0(b_mm) + r"\cdot "
            + num4(mu_val) + r"\cdot 100}}"
            + r"} = " + num1(hmin) + r"\ \mathrm{cm}"
        )
        flow.append(eq_row(tex_hmin, tmpdir, S, content_width, icon_text=""))
        ok_h = (hmin + enrobage) <= h
        flow.append(status_row(
            f"h<sub>min</sub> + enrob. = {fr1(hmin+enrobage)} cm ≤ h = {fr1(h)} cm",
            ok_h, S, content_width, "Eq"
        ))
        flow.append(Spacer(1, 5))

        # 3.2 Armatures
        flow.append(Paragraph("3.2 Calcul des armatures", S["Hnorm"]))

        # Inférieures — fyd & d_mm sans décimales
        flow.append(Paragraph("Armatures inférieures", S["Hsub"]))
        tex_as_inf = (
            r"A_{s,\mathrm{inf}}=\dfrac{"
            + num2(M_inf) + r"\cdot 10^{6}}{"
            + num0(fyd) + r"\cdot 0.9\cdot " + num0(d_mm) + r"\cdot 10}"
            + r"} = " + num1(As_inf_req) + r"\ \mathrm{mm^2}"
        )
        flow.append(eq_row(tex_as_inf, tmpdir, S, content_width, icon_text=""))
        flow.append(text_row(f"Section d’acier minimale : A<sub>s,min</sub> = {fr0(As_min)} mm²", S, content_width))
        flow.append(text_row(f"Section d’acier maximale : A<sub>s,max</sub> = {fr0(As_max)} mm²", S, content_width))

        if n_as_inf and o_as_inf:
            As_inf_ch = aire_barres(n_as_inf, o_as_inf)
            ok_inf = (As_min <= As_inf_ch <= As_max) and (As_inf_ch >= As_inf_req)
            flow.append(status_row(
                f"On prend : {int(n_as_inf)}Ø{int(o_as_inf)} → {fr0(As_inf_ch)} mm²",
                ok_inf, S, content_width, "Blue"
            ))
        flow.append(Spacer(1, 4))

        # Supérieures (si besoin)
        if M_sup and M_sup > 0:
            flow.append(Paragraph("Armatures supérieures", S["Hsub"]))
            tex_as_sup = (
                r"A_{s,\mathrm{sup}}=\dfrac{"
                + num2(M_sup) + r"\cdot 10^{6}}{"
                + num0(fyd) + r"\cdot 0.9\cdot " + num0(d_mm) + r"\cdot 10}"
                + r"} = " + num1(As_sup_req) + r"\ \mathrm{mm^2}"
            )
            flow.append(eq_row(tex_as_sup, tmpdir, S, content_width, icon_text=""))
            flow.append(text_row(f"Section d’acier minimale : A<sub>s,min</sub> = {fr0(As_min)} mm²", S, content_width))
            flow.append(text_row(f"Section d’acier maximale : A<sub>s,max</sub> = {fr0(As_max)} mm²", S, content_width))
            if n_as_sup and o_as_sup:
                As_sup_ch = aire_barres(n_as_sup, o_as_sup)
                ok_sup = (As_min <= As_sup_ch <= As_max) and (As_sup_ch >= As_sup_req)
                flow.append(status_row(
                    f"On prend : {int(n_as_sup)}Ø{int(o_as_sup)} → {fr0(As_sup_ch)} mm²",
                    ok_sup, S, content_width, "Blue"
                ))
            flow.append(Spacer(1, 6))

        # Effort tranchant — b,h en mm sans décimales
        if V and V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["Hnorm"]))
            tex_tau = (
                r"\tau=\dfrac{" + num2(V) + r"\cdot 10^{3}}{0.75\cdot "
                + num0(b_mm) + r"\cdot " + num0(h_mm) + r"}"
                + r"} = " + num2(tau) + r"\ \mathrm{N/mm^{2}}"
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
                (f"τ = {fr2(tau)} N/mm² < {lim_lab} = {fr2(lim_val)} N/mm²")
                if ok_tau else
                (f"τ = {fr2(tau)} N/mm² > {lim_lab} = {fr2(lim_val)} N/mm²"),
                ok_tau, S, content_width, "Eq"
            ))
            flow.append(Spacer(1, 6))

            # Calcul du pas des étriers — A_st développé : n·π·φ²/4 (φ en mm, entier)
            flow.append(Paragraph("Calcul des étriers", S["Hsub"]))
            n_br = int(n_branches_etrier or 1)
            phi  = int(o_etrier or 8)
            # valeur numérique (pour le s_th)
            A_st_e_val = aire_barres(n_br, phi)
            s_th = (A_st_e_val * fyd * d_mm) / (V * 1e4) if V else 0.0  # cm
            # forme développée
            A_st_dev = f"{n_br}\\cdot\\pi\\cdot {phi}^{2}/4"
            tex_s = (
                r"s_\mathrm{th}=\dfrac{(" + A_st_dev + r")\cdot "
                + num0(fyd) + r"\cdot " + num0(d_mm) + r"}{"
                + num2(V) + r"\cdot 10^{4}}"
                + r"} = " + num1(s_th) + r"\ \mathrm{cm}"
            )
            flow.append(eq_row(tex_s, tmpdir, S, content_width, icon_text=""))
            if o_etrier and pas_etrier is not None:
                ok_pas = pas_etrier <= s_th
                flow.append(status_row(
                    f"On prend : 1 étrier – Ø{phi} – {fr1(pas_etrier)} cm (pas théorique = {fr1(s_th)} cm)",
                    ok_pas, S, content_width, "Blue"
                ))
            flow.append(Spacer(1, 6))

        # Étriers réduits
        if V_lim and V_lim > 0:
            flow.append(Paragraph("Calcul des étriers réduits", S["Hsub"]))
            n_brr = int(n_branches_etrier_r or n_branches_etrier or 1)
            phir  = int(o_etrier_r or o_etrier or 8)
            A_st_er_val = aire_barres(n_brr, phir)
            s_thr = (A_st_er_val * fyd * d_mm) / (V_lim * 1e4)
            A_st_dev_r = f"{n_brr}\\cdot\\pi\\cdot {phir}^{2}/4"
            tex_sr = (
                r"s_{\mathrm{th},r}=\dfrac{(" + A_st_dev_r + r")\cdot "
                + num0(fyd) + r"\cdot " + num0(d_mm) + r"}{"
                + num2(V_lim) + r"\cdot 10^{4}}"
                + r"} = " + num1(s_thr) + r"\ \mathrm{cm}"
            )
            flow.append(eq_row(tex_sr, tmpdir, S, content_width, icon_text=""))
            if o_etrier_r and pas_etrier_r is not None:
                ok_pas_r = pas_etrier_r <= s_thr
                flow.append(status_row(
                    f"On prend : 1 étrier – Ø{phir} – {fr1(pas_etrier_r)} cm (pas théorique = {fr1(s_thr)} cm)",
                    ok_pas_r, S, content_width, "Blue"
                ))

        doc.build(flow)
        return out_path

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
