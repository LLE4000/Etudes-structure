-# -*- coding: utf-8 -*-
"""
export_pdf.py
Rapport de dimensionnement – Poutre BA (aligné, propre)
- Grille 2 colonnes pour TOUTES les lignes (alignement cohérent)
- Formules LaTeX en mm (présentation) + résultat dans la même équation
- Equations ~120% (proportion conservée)
- Titres en gras, principaux gras + soulignés
- "On prend : ..." en bleu foncé, OK/NON à droite si souhaité
- Nom fichier : PRO_PARTIE_#Indice_AAAAMMJJ.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, Flowable
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

# ====================== Réglages généraux ============================

# Taille des équations (tu peux ajuster ces 2 constantes)
EQ_IMG_WIDTH_MM = 38        # largeur "logique" en mm (base)
EQ_IMG_SCALE    = 1.20      # facteur d'échelle global (120 %)
MATH_FONTSIZE   = 14        # taille des glyphes math (13–16 conseillé)

# Symboles de validation (compatibles partout)
ICON_OK  = "OK"
ICON_NOK = "NON"

BLUE_DARK = colors.HexColor("#003366")

# ============================ Utils =================================

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

def render_equation(tex_expr, out_path, fontsize=MATH_FONTSIZE, pad=0.05):
    """Rend une équation LaTeX (mathtext) en PNG transparent."""
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

def icon(ok_bool):
    return ICON_OK if ok_bool else ICON_NOK

# ============================ Styles ================================

def register_fonts():
    """Police normale + bold (DejaVu si possible)."""
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
                                fontName=base_b, fontSize=9.5, leading=12,
                                spaceBefore=5, spaceAfter=3, textColor=black),  # <u> dans le texte
        "Hnorm": ParagraphStyle("Hnorm", parent=ss["BodyText"],
                                fontName=base_b, fontSize=9.5, leading=12,
                                spaceBefore=4, spaceAfter=2, textColor=black),
        "Hsub": ParagraphStyle("Hsub", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=12,
                               spaceBefore=2, spaceAfter=1, textColor=black),
        "Eq": ParagraphStyle("Eq", parent=ss["BodyText"],
                             fontName=base, fontSize=9.5, leading=12, textColor=black),
        "Blue": ParagraphStyle("Blue", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=12, textColor=BLUE_DARK),
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9, leading=11, textColor=black),
    }

# ======================== Données béton ==============================

def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(p):
        p = "beton_classes.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# ===================== Grille 2 colonnes (alignement) ================

def make_row(left_flowable, styles, content_width, icon_text=""):
    """
    LIGNE GRIllÉE 2 colonnes :
      [ contenu (Paragraph/Image) | icône (OK/NON/"" à droite) ]
    => garantit un alignement horizontal identique partout.
    """
    col_icon = 12*mm
    col_text = content_width - col_icon
    tbl = Table([[left_flowable, Paragraph(icon_text, styles["Eq"]) ]],
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
    return text_row(html_text, styles, content_width, style_name, ICON_OK if ok_bool else ICON_NOK)

def eq_row(tex_numeric, tmpdir, styles, content_width, icon_text=""):
    # Rend l’équation et la met dans la même grille
    img_path = os.path.join(tmpdir, f"eq_{abs(hash(tex_numeric))}.png")
    render_equation(tex_numeric, img_path, fontsize=MATH_FONTSIZE, pad=0.05)
    with PILImage.open(img_path) as im:
        w, h = im.size
    target_w = EQ_IMG_WIDTH_MM * mm * EQ_IMG_SCALE
    target_h = target_w * h / w
    img = Image(img_path, width=target_w, height=target_h, hAlign="LEFT")
    return make_row(img, styles, content_width, icon_text)

# ========================= Générateur PDF ============================

def generer_rapport_pdf(
    nom_projet="", partie="", date="", indice="",
    beton="C30/37", fyk="500",
    b=20, h=40, enrobage=5.0,
    M_inf=0.0, M_sup=0.0,
    V=0.0, V_lim=0.0,
    # Choix utilisateur
    n_as_inf=None, o_as_inf=None,
    n_as_sup=None, o_as_sup=None,
    pas_etrier=None, o_etrier=None,  # 1 étrier – Øo – pas
    pas_etrier_r=None, o_etrier_r=None,
    **kwargs,
):
    # --- Matériaux / constantes
    beton_data = load_beton_data()
    d = beton_data.get(beton, {})
    fck_cube = d.get("fck_cube", 30)
    alpha_b  = d.get("alpha_b", 0.72)
    mu_val   = d.get(f"mu_a{fyk}", 11.5)
    fyd      = int(fyk) / 1.5

    # --- Géométrie (cm) + utiles (mm pour affichage)
    d_utile = h - enrobage  # cm
    b_mm = b * 10.0; h_mm = h * 10.0; d_mm = d_utile * 10.0

    # --- Calculs
    M_max   = max(float(M_inf or 0.0), float(M_sup or 0.0))
    hmin    = math.sqrt((M_max*1e6)/(alpha_b*b*10*mu_val))/10.0 if M_max>0 else 0.0  # résultat cm (calcul inchangé)

    As_min      = 0.0013 * b * h * 1e2
    As_max      = 0.04   * b * h * 1e2
    As_inf_req  = (M_inf*1e6) / (fyd*0.9*d_utile*10) if M_inf>0 else 0.0
    As_sup_req  = (M_sup*1e6) / (fyd*0.9*d_utile*10) if M_sup>0 else 0.0

    tau   = (V*1e3) / (0.75*b*h*100) if V>0 else 0.0
    tau_1 = 0.016 * fck_cube / 1.05
    tau_2 = 0.032 * fck_cube / 1.05
    tau_4 = 0.064 * fck_cube / 1.05

    # --- Nom de fichier
    out_dir = "/mnt/data"
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        out_dir = tempfile.gettempdir()
    proj = (nom_projet or "XXX")[:3].upper()
    part = (partie or "Partie").strip().replace(" ", "_")
    ind  = (indice or "0")
    date_str = datetime.now().strftime("%Y%m%d")
    out_name = f"{proj}_{part}_#{ind}_{date_str}.pdf"
    out_path = os.path.join(out_dir, out_name)

    # --- Document
    leftM, rightM, topM, botM = 14*mm, 14*mm, 12*mm, 12*mm
    content_width = A4[0] - leftM - rightM
    S = get_styles()
    flow = []
    tmpdir = tempfile.mkdtemp(prefix="pdf_eq_")

    try:
        doc = SimpleDocTemplate(
            out_path, pagesize=A4,
            leftMargin=leftM, rightMargin=rightM, topMargin=topM, bottomMargin=botM,
            title="Rapport de dimensionnement – Poutre BA",
        )

        # ---------- En-tête ----------
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

        # ---------- Caractéristiques ----------
        flow.append(Paragraph("<u>Caractéristiques de la poutre</u>", S["Hmain"]))
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
        flow.append(Spacer(1, 3))

        # ---------- Dimensionnement ----------
        flow.append(Paragraph("<u>Dimensionnement</u>", S["Hmain"]))

        # Vérification de la hauteur utile
        flow.append(Paragraph("Vérification de la hauteur utile", S["Hnorm"]))
        # LaTeX en mm (présentation), pas de "/10" final ; facteur 100 sous la racine
        tex_hmin = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + fr(M_max,2).replace(",", ".") + r"\cdot 10^{6}}{"
            + fr(alpha_b,2).replace(",", ".") + r"\cdot "
            + fr(b_mm,1).replace(",", ".") + r"\cdot "
            + fr(mu_val,1).replace(",", ".") + r"\cdot 100}}"
            + r" = " + fr(hmin,1) + tex_unit("cm")
        )
        flow.append(eq_row(tex_hmin, tmpdir, S, content_width, icon_text=""))
        ok_h = (hmin + enrobage) <= h
        flow.append(status_row(
            f"h<sub>min</sub> + enrob. = {fr(hmin+enrobage,1)} cm ≤ h = {fr(h,1)} cm",
            ok_h, S, content_width, "Eq"
        ))
        flow.append(Spacer(1, 3))

        # Calcul des armatures
        flow.append(Paragraph("Calcul des armatures", S["Hnorm"]))

        # Armatures inférieures
        flow.append(Paragraph("Armatures inférieures", S["Hsub"]))
        tex_as_inf = (
            r"A_{s,\mathrm{inf}}=\dfrac{"
            + fr(M_inf,2).replace(",", ".") + r"\cdot 10^{6}}{"
            + fr(fyd,1).replace(",", ".") + r"\cdot 0.9\cdot "
            + fr(d_mm,1).replace(",", ".") + r"}"
            + r" = " + fr(As_inf_req,1) + tex_unit("mm^2")
        )
        flow.append(eq_row(tex_as_inf, tmpdir, S, content_width, icon_text=""))
        # Sections min / max (alignées)
        flow.append(text_row(f"Section d’acier minimale : A<sub>s,min</sub> = {fr(As_min,1)} mm²", S, content_width, "Eq", icon_text=""))
        flow.append(text_row(f"Section d’acier maximale : A<sub>s,max</sub> = {fr(As_max,1)} mm²", S, content_width, "Eq", icon_text=""))
        # Choix (bleu) + validation
        if n_as_inf and o_as_inf:
            As_inf_ch = aire_barres(n_as_inf, o_as_inf)
            ok_inf = (As_min <= As_inf_ch <= As_max) and (As_inf_ch >= As_inf_req)
            flow.append(status_row(
                f"On prend : {int(n_as_inf)}Ø{int(o_as_inf)} → {fr(As_inf_ch,1)} mm²",
                ok_inf, S, content_width, "Blue"
            ))
        flow.append(Spacer(1, 2))

        # Armatures supérieures
        if M_sup and M_sup > 0:
            flow.append(Paragraph("Armatures supérieures", S["Hsub"]))
            tex_as_sup = (
                r"A_{s,\mathrm{sup}}=\dfrac{"
                + fr(M_sup,2).replace(",", ".") + r"\cdot 10^{6}}{"
                + fr(fyd,1).replace(",", ".") + r"\cdot 0.9\cdot "
                + fr(d_mm,1).replace(",", ".") + r"}"
                + r" = " + fr(As_sup_req,1) + tex_unit("mm^2")
            )
            flow.append(eq_row(tex_as_sup, tmpdir, S, content_width, icon_text=""))
            flow.append(text_row(f"Section d’acier minimale : A<sub>s,min</sub> = {fr(As_min,1)} mm²", S, content_width, "Eq", icon_text=""))
            flow.append(text_row(f"Section d’acier maximale : A<sub>s,max</sub> = {fr(As_max,1)} mm²", S, content_width, "Eq", icon_text=""))
            if n_as_sup and o_as_sup:
                As_sup_ch = aire_barres(n_as_sup, o_as_sup)
                ok_sup = (As_min <= As_sup_ch <= As_max) and (As_sup_ch >= As_sup_req)
                flow.append(status_row(
                    f"On prend : {int(n_as_sup)}Ø{int(o_as_sup)} → {fr(As_sup_ch,1)} mm²",
                    ok_sup, S, content_width, "Blue"
                ))
            flow.append(Spacer(1, 3))

        # Vérification de l'effort tranchant
        if V and V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["Hnorm"]))
            # τ avec b_mm et h_mm
            tex_tau = (
                r"\tau=\dfrac{"
                + fr(V,2).replace(",", ".") + r"\cdot 10^{3}}{0.75\cdot "
                + fr(b_mm,1).replace(",", ".") + r"\cdot "
                + fr(h_mm,1).replace(",", ".") + r"}"
                + r" = " + fr(tau,2) + tex_unit("N/mm^{2}")
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
            flow.append(Spacer(1, 3))

            # Calcul des étriers (V)
            flow.append(Paragraph("Calcul des étriers", S["Hsub"]))
            # Aire d'un étrier (on affiche seulement le pas ici ; l'aire est implicite)
            Ast_e = aire_barres(1, o_etrier or 8)  # 1 étrier
            s_th = Ast_e * fyd * d_mm / (10 * V * 1e3)  # cm (présentation avec d_mm)
            tex_s = (
                r"s_\mathrm{th}=\dfrac{"
                + fr(Ast_e,1).replace(",", ".") + r"\cdot "
                + fr(fyd,1).replace(",", ".") + r"\cdot "
                + fr(d_mm,1).replace(",", ".") + r"}{10\cdot "
                + fr(V,2).replace(",", ".") + r"\cdot 10^{3}}"
                + r" = " + fr(s_th,1) + tex_unit("cm")
            )
            flow.append(eq_row(tex_s, tmpdir, S, content_width, icon_text=""))
            if o_etrier and pas_etrier is not None:
                ok_pas = pas_etrier <= s_th
                flow.append(status_row(
                    f"On prend : 1 étrier – Ø{int(o_etrier)} – {fr(pas_etrier,1)} cm (pas théorique = {fr(s_th,1)} cm)",
                    ok_pas, S, content_width, "Blue"
                ))
            flow.append(Spacer(1, 3))

        # Étriers réduits (V_lim)
        if V_lim and V_lim > 0:
            flow.append(Paragraph("Calcul des étriers réduits", S["Hsub"]))
            Ast_er = aire_barres(1, o_etrier_r or o_etrier or 8)
            s_thr = Ast_er * fyd * d_mm / (10 * V_lim * 1e3)  # cm
            tex_sr = (
                r"s_{\mathrm{th},r}=\dfrac{"
                + fr(Ast_er,1).replace(",", ".") + r"\cdot "
                + fr(fyd,1).replace(",", ".") + r"\cdot "
                + fr(d_mm,1).replace(",", ".") + r"}{10\cdot "
                + fr(V_lim,2).replace(",", ".") + r"\cdot 10^{3}}"
                + r" = " + fr(s_thr,1) + tex_unit("cm")
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
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
