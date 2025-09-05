# -*- coding: utf-8 -*-
"""
export_pdf.py — Rapport Poutre BA (Arial, tailles -1 pt, OK/NON colorés)

- Titres/sous-titres : Arial Bold ; texte : Arial Regular (fallback propre si Arial absent).
- h_min : dénominateur = k_b (2 déc.) · b(mm, 0 déc.) · μ_a (4 déc.). Affiche comparaison avec h - enrobage.
- Armatures : plus de “·10” dans la formule affichée. Compare A_s,req avec A_s,choisi si présent.
- Ordre colonnes armatures : [M_inf | OK/NON | M_sup | OK/NON].
- Cisaillement : ajoute comparaison τ avec limite active dans la formule.
- Étriers : équation avec n·2·π·r² (r = Ø/2) et comparaison avec le pas choisi. Conclu “On prend …”
  sans parenthèse “(pas théorique = …)”.
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

# ---------------------- Réglages équations ----------------------
EQ_IMG_WIDTH_MM = 38
EQ_IMG_SCALE    = 1.20
MATH_FONTSIZE   = 14

ICON_OK  = "OK"
ICON_NOK = "NON"
BLUE_DARK   = colors.HexColor("#003366")
GREEN_OK    = "#2e7d32"
RED_NOK     = "#c62828"

# ---------------------- Utils nombre & format -------------------
def fr(x, nd=1):
    if x is None or x == "":
        return "-"
    if isinstance(x, str):
        x = x.strip().replace(" ", "").replace(",", ".")
    try:
        v = float(x)
    except Exception:
        return "-"
    s = f"{v:,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", " ")
    if s.startswith("-0,"):
        s = s.replace("-0,", "0,")
    return s

def fr0(x): return fr(x, 0)
def fr1(x): return fr(x, 1)
def fr2(x): return fr(x, 2)
def fr4(x): return fr(x, 4)

def num_from_fr(s): return s.replace(",", ".")
def num0(x): return num_from_fr(fr0(x))
def num1(x): return num_from_fr(fr1(x))
def num2(x): return num_from_fr(fr2(x))
def num4(x): return num_from_fr(fr4(x))

def to_float(x, default=0.0):
    if x is None or x == "":
        return float(default)
    if isinstance(x, str):
        x = x.strip().replace(" ", "").replace(",", ".")
    try:
        return float(x)
    except Exception:
        return float(default)

def to_int(x, default=0):
    if x is None or x == "":
        return int(default)
    if isinstance(x, str):
        x = x.strip().replace(" ", "").replace(",", ".")
    try:
        return int(float(x))
    except Exception:
        return int(default)

def as_int_str(x):
    try:
        return num0(round(float(x)))
    except Exception:
        return num0(x)

# ---------------------- Rendu équations -------------------------
def _render_equation_png(tex_expr, out_path, fontsize=MATH_FONTSIZE, pad=0.05):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig = plt.figure(figsize=(1, 1), dpi=250)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.text(0.0, 0.5, f"${tex_expr}$", fontsize=fontsize, va="center", ha="left")
    fig.savefig(out_path, dpi=250, transparent=True, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)

def _boxed(flowable, width, padd=(3,6,1,1)):
    L, R, T, B = padd
    tbl = Table([[flowable]], colWidths=[width])
    tbl.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.75, colors.black),
        ("LEFTPADDING",  (0,0), (-1,-1), L),
        ("RIGHTPADDING", (0,0), (-1,-1), R),
        ("TOPPADDING",   (0,0), (-1,-1), T),
        ("BOTTOMPADDING",(0,0), (-1,-1), B),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    return tbl

def eq_flowable(tex_expr, cell_width, tmpdir, padd=(3,6,1,1)):
    try:
        img_path = os.path.join(tmpdir, f"eq_{abs(hash(tex_expr))}.png")
        _render_equation_png(tex_expr, img_path, fontsize=MATH_FONTSIZE, pad=0.05)

        max_w = EQ_IMG_WIDTH_MM * mm * EQ_IMG_SCALE
        w = min(cell_width, max_w)

        try:
            with PILImage.open(img_path) as im:
                px_w, px_h = im.size
            h = w * (px_h / px_w)
            img = Image(img_path, width=w, height=h)
        except Exception:
            img = Image(img_path, width=w)

        return _boxed(img, w, padd=padd)
    except Exception:
        return _boxed(Paragraph(f"${tex_expr}$", get_styles()["Eq"]), cell_width, padd=padd)

# ---------------------- Styles (Arial) --------------------------
def register_fonts():
    # Tente Arial ; fallback propre
    try:
        # chemins possibles
        candidates_regular = ["Arial.ttf", "ArialMT.ttf", "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
                              "/usr/share/fonts/truetype/freefont/FreeSans.ttf"]
        candidates_bold    = ["Arial-Bold.ttf", "Arial Bold.ttf", "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
                              "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"]
        reg = next((p for p in candidates_regular if os.path.exists(p)), None)
        bld = next((p for p in candidates_bold    if os.path.exists(p)), None)
        if reg and bld:
            pdfmetrics.registerFont(TTFont("Arial", reg))
            pdfmetrics.registerFont(TTFont("Arial-Bold", bld))
            return ("Arial", "Arial-Bold")
    except Exception:
        pass
    # Fallback
    return ("Helvetica", "Helvetica-Bold")

def get_styles():
    base, base_b = register_fonts()
    ss = getSampleStyleSheet()
    black = colors.black
    return {
        "Body": ParagraphStyle("Body", parent=ss["BodyText"],
                               fontName=base, fontSize=8.5, leading=11, textColor=black),
        "Hmain": ParagraphStyle("Hmain", parent=ss["BodyText"],
                                fontName=base_b, fontSize=9.0, leading=12,
                                spaceBefore=6, spaceAfter=4, textColor=black),
        "Hnorm": ParagraphStyle("Hnorm", parent=ss["BodyText"],
                                fontName=base_b, fontSize=8.8, leading=11.5,
                                spaceBefore=5, spaceAfter=3, textColor=black),
        "Hsub": ParagraphStyle("Hsub", parent=ss["BodyText"],
                               fontName=base_b, fontSize=8.6, leading=11.5,
                               spaceBefore=4, spaceAfter=3, textColor=black),
        "Eq": ParagraphStyle("Eq", parent=ss["BodyText"],
                             fontName=base, fontSize=8.5, leading=18, textColor=black),
        "Blue": ParagraphStyle("Blue", parent=ss["BodyText"],
                               fontName=base_b, fontSize=8.5, leading=18, textColor=BLUE_DARK),
        "Center": ParagraphStyle("Center", parent=ss["BodyText"],
                                 fontName=base, fontSize=8.5, leading=12, alignment=1, textColor=black),
    }

def make_row(flowable, styles, content_width, icon_text=""):
    col_icon = 12*mm
    tbl = Table([[flowable, Paragraph(icon_text, styles["Eq"])]],
                colWidths=[content_width - col_icon, col_icon])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",  (1,0), (1,0), "RIGHT"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING",   (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",(0,0), (-1,-1), 0),
    ]))
    return tbl

def ok_bad_html(ok_bool):
    if ok_bool is None:
        return ""
    return f'<font color="{GREEN_OK if ok_bool else RED_NOK}">{ICON_OK if ok_bool else ICON_NOK}</font>'

# ---------------------- Données matériau ------------------------
def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(p):
        p = "beton_classes.json"
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"C30/37": {"fck_cube": 30, "alpha_b": 0.72, "mu_a500": 0.1709}}

# ---------------------- Génération PDF --------------------------
def generer_rapport_pdf(
    nom_projet="", partie="", date="", indice="",
    beton="C30/37", fyk="500",
    b=20, h=40, enrobage=5.0,
    M_inf=0.0, M_sup=0.0,
    V=0.0, V_lim=0.0,
    n_as_inf=None, o_as_inf=None,
    n_as_sup=None, o_as_sup=None,
    n_branches_etrier=1, o_etrier=None, pas_etrier=None,
    n_branches_etrier_r=1, o_etrier_r=None, pas_etrier_r=None,
    **kwargs,
):
    # Normalisation
    b, h, enrobage = to_float(b), to_float(h), to_float(enrobage)
    M_inf, M_sup, V, V_lim = to_float(M_inf), to_float(M_sup), to_float(V), to_float(V_lim)
    n_as_inf = to_int(n_as_inf) if n_as_inf is not None else None
    o_as_inf = to_int(o_as_inf) if o_as_inf is not None else None
    n_as_sup = to_int(n_as_sup) if n_as_sup is not None else None
    o_as_sup = to_int(o_as_sup) if o_as_sup is not None else None
    n_branches_etrier   = to_int(n_branches_etrier, 1)
    o_etrier            = to_int(o_etrier) if o_etrier is not None else None
    pas_etrier          = to_float(pas_etrier) if pas_etrier is not None else None
    n_branches_etrier_r = to_int(n_branches_etrier_r, 1)
    o_etrier_r          = to_int(o_etrier_r) if o_etrier_r is not None else None
    pas_etrier_r        = to_float(pas_etrier_r) if pas_etrier_r is not None else None

    # Matériaux
    data = load_beton_data()
    d = data.get(beton, {})
    fck_cube = to_float(d.get("fck_cube", 30))
    alpha_b  = to_float(d.get("alpha_b", 0.72))
    mu_val   = to_float(d.get(f"mu_a{int(to_float(fyk))}", d.get("mu_a500", 0.1709)))  # 4 déc. en affichage
    kb       = round(alpha_b*18.0, 2)   # 2 déc.
    fyd      = int(to_float(fyk)) / 1.5

    # Géométrie
    d_utile = h - enrobage
    b_mm, h_mm, d_mm = b*10.0, h*10.0, d_utile*10.0

    # Calculs
    M_max = max(float(M_inf or 0.0), float(M_sup or 0.0))
    hmin  = math.sqrt((M_max*1e6)/(kb*b_mm*mu_val))/10.0 if M_max>0 else 0.0

    As_min      = 0.0013 * b * h * 1e2
    As_max      = 0.04   * b * h * 1e2
    As_inf_req  = (M_inf*1e6) / (fyd*0.9*d_utile*10) if M_inf>0 else 0.0
    As_sup_req  = (M_sup*1e6) / (fyd*0.9*d_utile*10) if M_sup>0 else 0.0

    tau   = (V*1e3) / (0.75*b*h*100) if V>0 else 0.0
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05

    # Fichier sortie
    out_dir = "/mnt/data"
    try: os.makedirs(out_dir, exist_ok=True)
    except Exception: out_dir = tempfile.gettempdir()
    proj = (nom_projet or "XXX")[:3].upper()
    part = (partie or "Partie").strip().replace(" ", "_")
    ind  = (indice or "0")
    date_str = datetime.now().strftime("%Y%m%d")
    out_path = os.path.join(out_dir, f"{proj}_{part}_#{ind}_{date_str}.pdf")

    # Doc
    leftM, rightM, topM, botM = 14*mm, 14*mm, 12*mm, 12*mm
    content_width = A4[0] - leftM - rightM
    S = get_styles()
    flow = []
    tmpdir = tempfile.mkdtemp(prefix="pdf_eq_")

    # Largeurs pour les 4 colonnes
    COL_W_ARM = content_width * 0.42
    COL_W_OK  = content_width * 0.08

    try:
        doc = SimpleDocTemplate(out_path, pagesize=A4,
                                leftMargin=leftM, rightMargin=rightM,
                                topMargin=topM, bottomMargin=botM)

        # En-tête
        flow.append(Table(
            [
                ["Projet :", nom_projet or "—", "Date :", date or datetime.today().strftime("%d/%m/%Y")],
                ["Partie :", partie or "—", "Indice :", indice or "—"],
            ],
            colWidths=[16*mm, content_width*0.58, 16*mm, content_width*0.26],
            style=TableStyle([
                ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
                ("FONTSIZE", (0,0), (-1,-1), 8.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ("ALIGN", (0,0), (-1,-1), "LEFT"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 3))

        # 1. Caractéristiques
        flow.append(Paragraph("<u>1. Caractéristiques de la poutre</u>", S["Hmain"]))
        flow.append(Table(
            [
                ["Classe de béton", beton, "Armature", f"{int(to_float(fyk))} N/mm²"],
                ["Largeur: b", f"{fr1(b)} cm", "Hauteur: h", f"{fr1(h)} cm"],
                ["Enrobage: c", f"{fr1(enrobage)} cm", "Hauteur utile: d", f"{fr1(d_utile)} cm"],
            ],
            colWidths=[34*mm, content_width/2-34*mm, 34*mm, content_width/2-34*mm],
            style=TableStyle([
                ("GRID", (0,0), (-1,-1), 0.25, colors.black),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f6f6f6")),
                ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
                ("FONTSIZE", (0,0), (-1,-1), 8.5),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 5))

        # 2. Sollicitations
        flow.append(Paragraph("<u>2. Sollicitations</u>", S["Hmain"]))
        flow.append(Table(
            [
                ["Moment inférieur M", f"{fr1(M_inf)} kNm" if (M_inf>0) else "—",
                 "Moment supérieur M_sup", f"{fr1(M_sup)} kNm" if (M_sup>0) else "—"],
                ["Effort tranchant V", f"{fr1(V)} kN" if (V>0) else "—",
                 "Effort tranchant réduit V_réduit", f"{fr1(V_lim)} kN" if (V_lim>0) else "—"],
            ],
            colWidths=[48*mm, content_width/2-48*mm, 58*mm, content_width/2-58*mm],
            style=TableStyle([
                ("GRID", (0,0), (-1,-1), 0.25, colors.black),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f6f6f6")),
                ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
                ("FONTSIZE", (0,0), (-1,-1), 8.5),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 6))

        # 3. Dimensionnement
        flow.append(Paragraph("<u>3. Dimensionnement</u>", S["Hmain"]))

        # 3.1 h_min — équation + comparaison
        flow.append(Paragraph("3.1 Vérification de la hauteur utile", S["Hnorm"]))
        tex_hmin = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + num2(M_max) + r"\cdot 10^{6}}{"
            + num2(kb) + r"\cdot " + num0(b_mm) + r"\cdot " + num4(mu_val) + r"}}"
            + r" = " + num1(hmin) + r"\ \mathrm{cm}"
            + r"\;\ " + ("<" if hmin < (h - enrobage) else ">")
            + r"\ " + num1(h) + r" - " + num1(enrobage) + r" = " + num1(h - enrobage) + r"\ \mathrm{cm}"
        )
        flow.append(make_row(eq_flowable(tex_hmin, content_width-12*mm, tmpdir, padd=(3,6,1,1)),
                             S, content_width, ""))

        ok_h = (hmin + enrobage) <= h
        flow.append(make_row(
            Paragraph(f"h<sub>min</sub> + enrob. = {fr1(hmin+enrobage)} cm ≤ h = {fr1(h)} cm", S["Eq"]),
            S, content_width, ok_bad_html(ok_h)
        ))
        flow.append(Spacer(1, 6))

        # 3.2 Armatures — M_inf (gauche) / M_sup (droite)
        flow.append(Paragraph("3.2 Calcul des armatures", S["Hnorm"]))

        def bloc_arm(M_val, As_req, titre, n_as, o_as):
            parts = [Paragraph(titre, S["Hsub"])]
            ok_val = None
            if M_val and M_val > 0:
                # Formule sans “·10” affiché
                tex = (
                    r"A_{s}=\dfrac{" + num2(M_val) + r"\cdot 10^{6}}{"
                    + as_int_str(fyd) + r"\cdot 0.9\cdot " + as_int_str(d_mm) + r"}"
                    + r" = " + num1(As_req) + r"\ \mathrm{mm^2}"
                )
                # comparaison avec As choisi si présent
                As_ch = None
                if n_as and o_as:
                    As_ch = float(n_as) * math.pi * (float(o_as)/2.0)**2
                    tex += (r"\;\ " + ("<" if As_req <= As_ch else ">") + r"\ " + num0(As_ch) + r"\ \mathrm{mm^2}")
                parts.append(eq_flowable(tex, COL_W_ARM-12*mm, tmpdir, padd=(3,6,1,1)))
                parts.append(Paragraph(f"A<sub>s,min</sub> = {fr0(As_min)} mm²", S["Eq"]))
                parts.append(Paragraph(f"A<sub>s,max</sub> = {fr0(As_max)} mm²", S["Eq"]))
                if As_ch is not None:
                    ok_val = (As_min <= As_ch <= As_max) and (As_ch >= As_req)
                    parts.append(Paragraph(
                        f"On prend : {int(n_as)}Ø{int(o_as)} → {fr0(As_ch)} mm²", S["Blue"]))
            else:
                parts.append(Paragraph("—", S["Eq"]))
            return parts, ok_val

        # Inversé : inf à gauche, sup à droite
        inf_parts, ok_inf = bloc_arm(M_inf, As_inf_req, "Armatures inférieures", n_as_inf, o_as_inf)
        sup_parts, ok_sup = bloc_arm(M_sup, As_sup_req, "Armatures supérieures", n_as_sup, o_as_sup)

        t_arm = Table(
            [[inf_parts, Paragraph(ok_bad_html(ok_inf), S["Center"]),
              sup_parts, Paragraph(ok_bad_html(ok_sup), S["Center"])]],
            colWidths=[COL_W_ARM, COL_W_OK, COL_W_ARM, COL_W_OK],
            style=TableStyle([
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING",  (0,0), (-1,-1), 2),
                ("RIGHTPADDING", (0,0), (-1,-1), 2),
                ("TOPPADDING",   (0,0), (-1,-1), 1),
                ("BOTTOMPADDING",(0,0), (-1,-1), 1),
            ])
        )
        flow.append(t_arm)
        flow.append(Spacer(1, 6))

        # 3.x Cisaillement & étriers
        if V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["Hnorm"]))

            # Limite active
            if   tau <= tau_1: lim_lab, lim_val, ok_tau = "τ_adm I",  tau_1, True
            elif tau <= tau_2: lim_lab, lim_val, ok_tau = "τ_adm II", tau_2, True
            elif tau <= tau_4: lim_lab, lim_val, ok_tau = "τ_adm IV", tau_4, True
            else:              lim_lab, lim_val, ok_tau = "τ_adm IV", tau_4, False

            tex_tau = (
                r"\tau=\dfrac{" + num2(V) + r"\cdot 10^{3}}{0.75\cdot "
                + num0(b_mm) + r"\cdot " + num0(h_mm) + r"}"
                + r" = " + num2(tau) + r"\ \mathrm{N/mm^{2}}"
                + r"\;\ " + ("<" if tau <= lim_val else ">") + r"\ " + num2(lim_val) + r"\ \mathrm{N/mm^{2}}"
            )
            flow.append(make_row(eq_flowable(tex_tau, content_width-12*mm, tmpdir, padd=(3,6,1,1)),
                                 S, content_width, ""))

            flow.append(make_row(Paragraph(
                (f"τ = {fr2(tau)} N/mm² < {lim_lab} = {fr2(lim_val)} N/mm²") if ok_tau
                else (f"τ = {fr2(tau)} N/mm² > {lim_lab} = {fr2(lim_val)} N/mm²"), S["Eq"]),
                S, content_width, ok_bad_html(ok_tau)
            ))
            flow.append(Spacer(1, 6))

            # Étriers (normal) et réduits — 4 colonnes
            def bloc_etriers(Vval, titre, n_br, phi, pas):
                parts = [Paragraph(titre, S["Hsub"])]
                ok_pas = None
                if Vval and Vval > 0:
                    n_br_i = int(n_br or 1)
                    phi_i  = int(phi or 8)
                    A_st_val = float(n_br_i) * math.pi * (float(phi_i)/2.0)**2  # calc. identique
                    s_th = (A_st_val * fyd * d_mm) / (Vval * 1e4)

                    # Affiche n·2·π·r² (r = Ø/2), constantes entières
                    texs = (
                        r"s_\mathrm{th}=\dfrac{("
                        + f"{n_br_i}" + r"\cdot 2\cdot \pi\cdot r^{2})\cdot "
                        + as_int_str(fyd) + r"\cdot " + as_int_str(d_mm) + r"}{"
                        + num2(Vval) + r"\cdot 10^{4}}"
                        + r" = " + num1(s_th) + r"\ \mathrm{cm}"
                    )
                    if pas is not None:
                        texs += r"\;\ " + ("<" if s_th <= pas else ">") + r"\ " + num1(pas) + r"\ \mathrm{cm}"
                    parts.append(eq_flowable(texs, COL_W_ARM-12*mm, tmpdir, padd=(3,6,1,1)))

                    if pas is not None:
                        ok_pas = pas <= s_th
                        parts.append(Paragraph(
                            f"On prend : 1 étrier – Ø{phi_i} – {fr1(pas)} cm", S["Blue"]))  # pas de parenthèse
                else:
                    parts.append(Paragraph("—", S["Eq"]))
                return parts, ok_pas

            e_parts,  ok_e  = bloc_etriers(V,     "Calcul des étriers",         n_branches_etrier,   o_etrier,   pas_etrier)
            er_parts, ok_er = bloc_etriers(V_lim, "Calcul des étriers réduits", n_branches_etrier_r, o_etrier_r, pas_etrier_r) if (V_lim>0) else ([Paragraph("—", S["Center"])], None)

            t_et = Table(
                [[e_parts, Paragraph(ok_bad_html(ok_e), S["Center"]),
                  er_parts, Paragraph(ok_bad_html(ok_er), S["Center"])]],
                colWidths=[COL_W_ARM, COL_W_OK, COL_W_ARM, COL_W_OK],
                style=TableStyle([
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                    ("LEFTPADDING",  (0,0), (-1,-1), 2),
                    ("RIGHTPADDING", (0,0), (-1,-1), 2),
                    ("TOPPADDING",   (0,0), (-1,-1), 1),
                    ("BOTTOMPADDING",(0,0), (-1,-1), 1),
                ])
            )
            flow.append(t_et)

        # Build
        doc.build(flow)
        return out_path

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
