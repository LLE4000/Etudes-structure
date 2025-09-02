# -*- coding: utf-8 -*-
"""
export_pdf.py — Rapport Poutre BA (mise en page 4 colonnes)
- hmin : cadre compact + dénominateur = kb(2 déc.) · b(mm, 0 déc.) · μa(4 déc.) — sans '·100'
- Armatures : affichages entiers sans décimales (ex. 333 → pas 333.3 ; 500 → pas 500.0)
- 3.2 présenté sur une ligne en 4 colonnes (sup | OK/NON | inf | OK/NON)
- Puis vérification du cisaillement et 4 colonnes (étriers | OK/NON | réduits | OK/NON)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
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

def as_int_str(x):
    """Affiche sans décimales si la valeur est 'entière attendue' (ex. 333.3 -> '333')."""
    try:
        v = float(x)
        return num0(round(v))
    except Exception:
        return num0(x)

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
        "Eq": ParagraphStyle("Eq", parent=ss["BodyText"],
                             fontName=base, fontSize=9.5, leading=18, textColor=black),
        "Blue": ParagraphStyle("Blue", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=18, textColor=BLUE_DARK),
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9, leading=11, textColor=black),
        "Center": ParagraphStyle("Center", parent=ss["BodyText"],
                                 fontName=base, fontSize=9.5, leading=12, alignment=1, textColor=black),
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

def eq_box(img_path, padd=(3,6,1,1)):
    """Cadre autour de l'équation avec padding (L, R, T, B)."""
    left, right, top, bottom = padd
    with PILImage.open(img_path) as im:
        w, h = im.size
    target_w = EQ_IMG_WIDTH_MM * mm * EQ_IMG_SCALE
    target_h = target_w * h / w
    img = Image(img_path, width=target_w, height=target_h, hAlign="LEFT")
    box = Table([[img]], colWidths=[target_w])
    box.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.75, colors.black),
        ("LEFTPADDING",  (0,0), (-1,-1), left),
        ("RIGHTPADDING", (0,0), (-1,-1), right),
        ("TOPPADDING",   (0,0), (-1,-1), top),
        ("BOTTOMPADDING",(0,0), (-1,-1), bottom),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    return box, target_w

def eq_row(tex_numeric, tmpdir, styles, content_width, icon_text="", padd=(3,3,2,2)):
    img_path = os.path.join(tmpdir, f"eq_{abs(hash(tex_numeric))}.png")
    render_equation(tex_numeric, img_path, fontsize=MATH_FONTSIZE, pad=0.05)
    box, _ = eq_box(img_path, padd=padd)
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
    kb       = d.get("kb", round(alpha_b*18.0, 2))  # coefficient kb affiché et utilisé (ex. 12.96)
    fyd      = int(fyk) / 1.5               # affiché sans décimales

    # Géométrie (cm) + mm
    d_utile = h - enrobage
    b_mm = b * 10.0
    h_mm = h * 10.0
    d_mm = d_utile * 10.0

    # Calculs
    M_max   = max(float(M_inf or 0.0), float(M_sup or 0.0))
    # hmin basé sur 'kb' (plus de facteur *100) — cohérent avec l'affichage
    hmin    = math.sqrt((M_max*1e6)/(kb*b_mm*mu_val))/10.0 if M_max>0 else 0.0

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

    # Helpers “bloc” pour la mise en page 4 colonnes
    def bloc_armatures(M_val, As_req, titre, n_as, o_as):
        parts = []
        parts.append(Paragraph(titre, S["Hsub"]))
        tex = (
            r"A_{s}=\dfrac{"
            + num2(M_val) + r"\cdot 10^{6}}{"
            + as_int_str(fyd) + r"\cdot 0.9\cdot " + as_int_str(d_mm) + r"\cdot 10}"
            + r"} = " + num1(As_req) + r"\ \mathrm{mm^2}"
        )
        # cadre compact pour les équations dans les colonnes
        parts.append(eq_row(tex, tmpdir, S, content_width/2, icon_text="", padd=(3,6,1,1)))
        parts.append(Paragraph(f"A<sub>s,min</sub> = {fr0(As_min)} mm²", S["Eq"]))
        parts.append(Paragraph(f"A<sub>s,max</sub> = {fr0(As_max)} mm²", S["Eq"]))
        ok_val = None
        if n_as and o_as:
            As_ch = aire_barres(n_as, o_as)
            ok_val = (As_min <= As_ch <= As_max) and (As_ch >= As_req)
            parts.append(Paragraph(
                f"On prend : {int(n_as)}Ø{int(o_as)} → {fr0(As_ch)} mm²",
                S["Blue"]))
        return KeepTogether(parts), ok_val

    def bloc_etriers(Vval, titre, n_br, phi, pas):
        parts = []
        parts.append(Paragraph(titre, S["Hsub"]))
        if Vval and Vval > 0:
            n_br_i = int(n_br or 1)
            phi_i  = int(phi or 8)
            A_st_val = aire_barres(n_br_i, phi_i)
            s_th = (A_st_val * fyd * d_mm) / (Vval * 1e4)
            A_dev = f"{n_br_i}\\cdot\\pi\\cdot {phi_i}^{2}/4"
            texs = (
                r"s_\mathrm{th}=\dfrac{(" + A_dev + r")\cdot "
                + as_int_str(fyd) + r"\cdot " + as_int_str(d_mm) + r"}{"
                + num2(Vval) + r"\cdot 10^{4}}"
                + r"} = " + num1(s_th) + r"\ \mathrm{cm}"
            )
            parts.append(eq_row(texs, tmpdir, S, content_width/2, icon_text="", padd=(3,6,1,1)))
            ok_pas = None
            if phi and pas is not None:
                ok_pas = pas <= s_th
                parts.append(Paragraph(
                    f"On prend : 1 étrier – Ø{phi_i} – {fr1(pas)} cm (pas théorique = {fr1(s_th)} cm)",
                    S["Blue"]))
            return KeepTogether(parts), ok_pas
        else:
            parts.append(Paragraph("—", S["Eq"]))
            return KeepTogether(parts), None

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

        # 3.1 Vérification h_min (cadre compact + padding droite augmenté)
        flow.append(Paragraph("3.1 Vérification de la hauteur utile", S["Hnorm"]))
        tex_hmin = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + num2(M_max) + r"\cdot 10^{6}}{"
            + num2(kb) + r"\cdot " + num0(b_mm) + r"\cdot "
            + num4(mu_val) + r"}}"
            + r" = " + num1(hmin) + r"\ \mathrm{cm}"
        )
        # padding (L=3, R=6 pour écarter du 'cm', T=1, B=1 pour réduire la hauteur)
        flow.append(eq_row(tex_hmin, tmpdir, S, content_width, icon_text="", padd=(3,6,1,1)))
        ok_h = (hmin + enrobage) <= h
        flow.append(status_row(
            f"h<sub>min</sub> + enrob. = {fr1(hmin+enrobage)} cm ≤ h = {fr1(h)} cm",
            ok_h, S, content_width, "Eq"
        ))
        flow.append(Spacer(1, 6))

        # 3.2 Armatures — 4 colonnes sur une ligne
        flow.append(Paragraph("3.2 Calcul des armatures", S["Hnorm"]))

        bloc_sup, ok_sup = bloc_armatures(M_sup, As_sup_req, "Armatures supérieures", n_as_sup, o_as_sup) if (M_sup and M_sup>0) else (Paragraph("—", S["Center"]), None)
        bloc_inf, ok_inf = bloc_armatures(M_inf, As_inf_req, "Armatures inférieures", n_as_inf, o_as_inf) if (M_inf and M_inf>0) else (Paragraph("—", S["Center"]), None)

        t_arm = Table(
            [[bloc_sup, Paragraph(ICON_OK if ok_sup else ICON_NOK if ok_sup is not None else "—", S["Center"]),
              bloc_inf, Paragraph(ICON_OK if ok_inf else ICON_NOK if ok_inf is not None else "—", S["Center"])]],
            colWidths=[content_width*0.42, content_width*0.08,
                       content_width*0.42, content_width*0.08],
            style=TableStyle([
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("ALIGN", (1,0), (1,0), "CENTER"),
                ("ALIGN", (3,0), (3,0), "CENTER"),
                ("LEFTPADDING",  (0,0), (-1,-1), 2),
                ("RIGHTPADDING", (0,0), (-1,-1), 2),
                ("TOPPADDING",   (0,0), (-1,-1), 1),
                ("BOTTOMPADDING",(0,0), (-1,-1), 1),
            ])
        )
        flow.append(t_arm)
        flow.append(Spacer(1, 6))

        # Effort tranchant
        if V and V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["Hnorm"]))
            tex_tau = (
                r"\tau=\dfrac{" + num2(V) + r"\cdot 10^{3}}{0.75\cdot "
                + num0(b_mm) + r"\cdot " + num0(h_mm) + r"}"
                + r"} = " + num2(tau) + r"\ \mathrm{N/mm^{2}}"
            )
            flow.append(eq_row(tex_tau, tmpdir, S, content_width, icon_text="", padd=(3,6,1,1)))

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

            # Ligne 4 colonnes : étriers / OK | réduits / OK
            bloc_e, ok_e = bloc_etriers(V, "Calcul des étriers", n_branches_etrier, o_etrier, pas_etrier)
            bloc_er, ok_er = bloc_etriers(V_lim, "Calcul des étriers réduits", n_branches_etrier_r, o_etrier_r, pas_etrier_r) if (V_lim and V_lim>0) else (Paragraph("—", S["Center"]), None)

            t_et = Table(
                [[bloc_e, Paragraph(ICON_OK if ok_e else ICON_NOK if ok_e is not None else "—", S["Center"]),
                  bloc_er, Paragraph(ICON_OK if ok_er else ICON_NOK if ok_er is not None else "—", S["Center"])]],
                colWidths=[content_width*0.42, content_width*0.08,
                           content_width*0.42, content_width*0.08],
                style=TableStyle([
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("ALIGN", (1,0), (1,0), "CENTER"),
                    ("ALIGN", (3,0), (3,0), "CENTER"),
                    ("LEFTPADDING",  (0,0), (-1,-1), 2),
                    ("RIGHTPADDING", (0,0), (-1,-1), 2),
                    ("TOPPADDING",   (0,0), (-1,-1), 1),
                    ("BOTTOMPADDING",(0,0), (-1,-1), 1),
                ])
            )
            flow.append(t_et)

        doc.build(flow)
        return out_path

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
