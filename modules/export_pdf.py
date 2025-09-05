# -*- coding: utf-8 -*-
"""
export_pdf.py — Rapport Poutre BA (aligné, polices Arial, formules corrigées)

- Titres Arial Bold, texte Arial (fallback Helvetica) ; tailles -1 pt.
- Formules encadrées, largeur +30 % ; rendu stable via PNG transparents.
- h_min : √( M·10^6 / (αb · b_mm · μa) ), μa à 4 décimales ; comparaison "< h - enrob. = … cm" dans le cadre.
- Armatures : A_s = M·10^6 / (333 · 0.9 · d_mm) (sans ·10) ; résultat (0 déc., sans unité) < (choisi ou limite) mm².
- Cisaillement : τ = V·10^3 / (0.75 · b_mm · h_mm) ; résultat sans unité < limite (avec unité). Pas de rappel hors cadre.
- Étriers : s_th = ((n_br)·π·r^2 · 333 · d_mm) / (V·10^3), comparaison "< pas choisi".
- Table 4 colonnes : [Arm inf | OK] [Arm sup | OK] puis [Étriers | OK] [Étriers réduits | OK].
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

# ---------------- Réglages équations (agrandies +30 %) ----------------
EQ_IMG_WIDTH_MM = 38
EQ_IMG_SCALE    = 1.56    # 1.2 × 1.30 ≈ 1.56
MATH_FONTSIZE   = 14

GREEN = colors.HexColor("#1a7f37")
RED   = colors.HexColor("#c62828")
BLUE_DARK = colors.HexColor("#003366")

# ---------------- Utils nombre & format ----------------
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

# ---------------- Rendu equations encadrées ----------------
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
        ("BOX", (0,0), (-1,-1), 0.9, colors.black),
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
        from reportlab.lib.styles import getSampleStyleSheet
        ss = getSampleStyleSheet()
        return _boxed(Paragraph(f"${tex_expr}$", ss["BodyText"]), cell_width, padd=padd)

# ---------------- Polices & styles (Arial) ----------------
def register_fonts():
    # Essaye Arial ; fallback Helvetica
    bold_candidates = ["Arial-Bold.ttf", "Arial Bold.ttf", "Arial-BoldMT.ttf"]
    reg_candidates  = ["Arial.ttf", "ArialMT.ttf"]

    used_bold = None
    used_reg  = None
    for f in reg_candidates:
        if os.path.exists(f):
            pdfmetrics.registerFont(TTFont("Arial", f))
            used_reg = "Arial"; break
    for f in bold_candidates:
        if os.path.exists(f):
            pdfmetrics.registerFont(TTFont("Arial-Bold", f))
            used_bold = "Arial-Bold"; break

    if not used_reg:
        used_reg = "Helvetica"
    if not used_bold:
        used_bold = "Helvetica-Bold"
    return used_reg, used_bold

def get_styles():
    base, base_b = register_fonts()
    ss = getSampleStyleSheet()
    return {
        "Body": ParagraphStyle("Body", parent=ss["BodyText"],
                               fontName=base, fontSize=8.5, leading=11.0, textColor=colors.black),
        "Hmain": ParagraphStyle("Hmain", parent=ss["BodyText"],
                                fontName=base_b, fontSize=9.0, leading=12.0,
                                spaceBefore=5, spaceAfter=3, textColor=colors.black),
        "Hnorm": ParagraphStyle("Hnorm", parent=ss["BodyText"],
                                fontName=base_b, fontSize=8.8, leading=11.8,
                                spaceBefore=4, spaceAfter=3, textColor=colors.black),
        "Hsub": ParagraphStyle("Hsub", parent=ss["BodyText"],
                               fontName=base_b, fontSize=8.6, leading=11.4,
                               spaceBefore=3, spaceAfter=2, textColor=colors.black),
        "Eq": ParagraphStyle("Eq", parent=ss["BodyText"],
                             fontName=base, fontSize=8.5, leading=11.8, textColor=colors.black),
        "Blue": ParagraphStyle("Blue", parent=ss["BodyText"],
                               fontName=base_b, fontSize=8.5, leading=11.8, textColor=BLUE_DARK),
        "Center": ParagraphStyle("Center", parent=ss["BodyText"],
                                 fontName=base, fontSize=8.5, leading=11.0, alignment=1, textColor=colors.black),
        "OK": ParagraphStyle("OK", parent=ss["BodyText"],
                             fontName=base_b, fontSize=8.5, textColor=GREEN, alignment=1),
        "NOK": ParagraphStyle("NOK", parent=ss["BodyText"],
                              fontName=base_b, fontSize=8.5, textColor=RED, alignment=1),
    }

def ok_cell(ok, S):
    if ok is None: return Paragraph("—", S["Center"])
    return Paragraph("OK" if ok else "NON", S["OK"] if ok else S["NOK"])

# ---------------- Données matériau ----------------
def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(p):
        p = "beton_classes.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------------- Génération PDF ----------------
def generer_rapport_pdf(
    nom_projet="", partie="", date="", indice="",
    beton="C30/37", fyk="500",
    b=20, h=40, enrobage=5.0,
    M_inf=0.0, M_sup=0.0,
    V=0.0, V_lim=0.0,
    n_as_inf=None, o_as_inf=None,
    n_as_sup=None, o_as_sup=None,
    n_branches_etrier=2, o_etrier=None, pas_etrier=None,
    n_branches_etrier_r=2, o_etrier_r=None, pas_etrier_r=None,
    **kwargs,
):
    # Normalisation entrées
    b, h, enrobage = to_float(b), to_float(h), to_float(enrobage)
    M_inf, M_sup, V, V_lim = to_float(M_inf), to_float(M_sup), to_float(V), to_float(V_lim)
    n_as_inf = to_int(n_as_inf) if n_as_inf is not None else None
    o_as_inf = to_int(o_as_inf) if o_as_inf is not None else None
    n_as_sup = to_int(n_as_sup) if n_as_sup is not None else None
    o_as_sup = to_int(o_as_sup) if o_as_sup is not None else None
    n_branches_etrier   = to_int(n_branches_etrier, 2)
    o_etrier            = to_int(o_etrier) if o_etrier is not None else None
    pas_etrier          = to_float(pas_etrier) if pas_etrier is not None else None
    n_branches_etrier_r = to_int(n_branches_etrier_r, 2)
    o_etrier_r          = to_int(o_etrier_r) if o_etrier_r is not None else None
    pas_etrier_r        = to_float(pas_etrier_r) if pas_etrier_r is not None else None

    # Matériaux
    data = load_beton_data()
    d = data.get(beton, {})
    fck_cube = to_float(d.get("fck_cube", 30))
    alpha_b  = to_float(d.get("alpha_b", 12.96))     # 2 décimales
    mu_val   = to_float(d.get(f"mu_a{int(to_float(fyk))}", 0.1709))  # 4 décimales à l’affichage
    fyd      = int(to_float(fyk)) / 1.5              # 333… pour 500

    # Géométrie
    d_utile = h - enrobage
    b_mm, h_mm, d_mm = b*10.0, h*10.0, d_utile*10.0

    # Calculs
    M_max = max(float(M_inf or 0.0), float(M_sup or 0.0))
    # hmin = sqrt( M·10^6 / (αb · b_mm · μa) )
    hmin  = math.sqrt((M_max*1e6)/(alpha_b * b_mm * mu_val)) / 10.0 if M_max>0 else 0.0

    As_min      = 0.0013 * b * h * 1e2
    As_max      = 0.04   * b * h * 1e2
    # A_s demandé (mm²) : M*10^6 / (fyd · 0.9 · d_mm)
    As_inf_req  = (M_inf*1e6) / ( (fyd) * 0.9 * d_mm ) if M_inf>0 else 0.0
    As_sup_req  = (M_sup*1e6) / ( (fyd) * 0.9 * d_mm ) if M_sup>0 else 0.0

    tau   = (V*1e3) / (0.75*b_mm*h_mm) if V>0 else 0.0
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05

    # Fichier sortie
    out_dir = "/mnt/data"
    try: os.makedirs(out_dir, exist_ok=True)
    except Exception: import tempfile as _tf; out_dir = _tf.gettempdir()
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

    # Largeurs colonnes 4-col
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

        # 3.1 Vérification de la hauteur utile
        flow.append(Paragraph("3.1 Vérification de la hauteur utile", S["Hnorm"]))
        # hmin encadré : = XX.X cm < 65 - 5 = 60 cm (sans décimales sur 65/5/60)
        tex_hmin = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + num1(M_max) + r"\cdot 10^{6}}{"
            + num2(alpha_b) + r"\cdot " + num0(b_mm) + r"\cdot " + num4(mu_val) + r"}}"
            + r" = " + num1(hmin) + r"\ \mathrm{cm}\;\; <\; "
            + num0(h) + r" - " + num0(enrobage) + r" = " + num0(h - enrobage) + r"\ \mathrm{cm}"
        )
        flow.append(eq_flowable(tex_hmin, content_width-12*mm, tmpdir))
        flow.append(Spacer(1, 6))

        # 3.2 Calcul des armatures (4 colonnes) — inf à gauche, sup à droite
        flow.append(Paragraph("3.2 Calcul des armatures", S["Hnorm"]))

        def bloc_arm(M_val, As_req, titre, n_as, o_as):
            parts = [Paragraph(titre, S["Hsub"])]
            if M_val and M_val > 0:
                # A_s = M·10^6 / (333 · 0.9 · d_mm)
                tex = (
                    r"A_{s}=\dfrac{"
                    + num1(M_val) + r"\cdot 10^{6}}{"
                    + num0(round(fyd)) + r"\cdot 0.9\cdot " + num0(d_mm) + r"}"
                    + r" = " + num0(As_req)
                    + r"\ \;\;<\;\; "
                )
                # Comparaison : priorité au choisi ; sinon A_s,max
                if n_as and o_as:
                    As_ch = float(n_as) * math.pi * (float(o_as)/2.0)**2
                    tex += num0(As_ch) + r"\ \mathrm{mm^{2}}"
                    ok_val = (As_min <= As_ch <= As_max) and (As_ch >= As_req)
                else:
                    tex += num0(As_max) + r"\ \mathrm{mm^{2}}"
                    ok_val = None
                parts.append(eq_flowable(tex, COL_W_ARM-12*mm, tmpdir))
            else:
                ok_val = None
                parts.append(Paragraph("—", S["Eq"]))
            return parts, ok_val

        inf_parts, ok_inf = bloc_arm(M_inf, As_inf_req, "Armatures inférieures", n_as_inf, o_as_inf)
        sup_parts, ok_sup = bloc_arm(M_sup, As_sup_req, "Armatures supérieures", n_as_sup, o_as_sup)

        t_arm = Table(
            [[inf_parts, ok_cell(ok_inf, S), sup_parts, ok_cell(ok_sup, S)]],
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

        # 3.3 Effort tranchant & étriers
        if V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["Hnorm"]))
            # τ encadré, résultat sans unité puis comparaison avec unité
            if   tau <= tau_1: lim_lab, lim_val = "τ_{adm\ I}",  tau_1
            elif tau <= tau_2: lim_lab, lim_val = "τ_{adm\ II}", tau_2
            elif tau <= tau_4: lim_lab, lim_val = "τ_{adm\ IV}", tau_4
            else:              lim_lab, lim_val = "τ_{adm\ IV}", tau_4
            tex_tau = (
                r"\tau=\dfrac{"
                + num1(V) + r"\cdot 10^{3}}{0.75\cdot "
                + num0(b_mm) + r"\cdot " + num0(h_mm) + r"}"
                + r" = " + num2(tau)
                + r"\ \;\;<\;\; " + lim_lab + r" = " + num2(lim_val) + r"\ \mathrm{N/mm^{2}}"
            )
            flow.append(eq_flowable(tex_tau, content_width-12*mm, tmpdir))
            flow.append(Spacer(1, 6))

            # Étriers / Étriers réduits (4 colonnes)
            def bloc_etriers(Vval, titre, n_br, phi, pas):
                parts = [Paragraph(titre, S["Hsub"])]
                if Vval and Vval > 0:
                    n_br_i = int(n_br or 2)
                    phi_i  = int(phi or 8)
                    r_i    = phi_i / 2.0
                    A_st   = n_br_i * math.pi * (r_i**2)       # n_br · π · r²
                    s_th   = (A_st * (int(to_float(fyk))/1.5) * d_mm) / (Vval * 1e3)  # affichage 10^3
                    texs = (
                        r"s_\mathrm{th}=\dfrac{("
                        + str(n_br_i) + r"\cdot \pi \cdot " + num0(r_i) + r"^{2})\cdot "
                        + num0(round(int(to_float(fyk))/1.5)) + r"\cdot " + num0(d_mm) + r"}{"
                        + num1(Vval) + r"\cdot 10^{3}}"
                        + r" = " + num1(s_th)
                        + r"\ \;\;<\;\; " + (num1(pas) if pas is not None else "15") + r"\ \mathrm{cm}"
                    )
                    parts.append(eq_flowable(texs, COL_W_ARM-12*mm, tmpdir))
                    ok_pas = (pas is not None) and (pas <= s_th)
                    # Conclusion sans "(pas théorique = …)"
                    if phi and pas is not None:
                        parts.append(Paragraph(
                            f"On prend : {1} étrier – Ø{phi_i} – {fr1(pas)} cm", S["Blue"]))
                    return parts, ok_pas
                else:
                    parts.append(Paragraph("—", S["Eq"]))
                    return parts, None

            e_parts,  ok_e  = bloc_etriers(V,     "Calcul des étriers",         n_branches_etrier,   o_etrier,   pas_etrier)
            er_parts, ok_er = bloc_etriers(V_lim, "Calcul des étriers réduits", n_branches_etrier_r, o_etrier_r, pas_etrier_r) if (V_lim>0) else ([Paragraph("—", S["Center"])], None)

            t_et = Table(
                [[e_parts, ok_cell(ok_e, S), er_parts, ok_cell(ok_er, S)]],
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
