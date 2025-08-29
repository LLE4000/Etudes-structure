# -*- coding: utf-8 -*-
"""
export_pdf.py
Rapport de dimensionnement – Poutre BA (compact et propre)
- Nom de fichier : PRO_PARTIE_#Indice_AAAAMMJJ.pdf
- Titres en gras (principaux en gras + soulignés)
- Formules LaTeX NUMÉRIQUES avec résultat dans la même équation
- Images proportionnelles (~120 %)
- Lignes de validation à droite (OK / NON)
- 'On prend : ...' en bleu foncé
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

# largeur de base ~32 mm * 1.2 ≈ 38 mm. On garde l'AR => H suit W.
EQ_IMG_WIDTH_MM = 38

BLUE_DARK = colors.HexColor("#003366")

# ============================ Utils =================================

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

def render_equation(tex_expr, out_path, fontsize=13, pad=0.05):
    """Rend une équation LaTeX (mathtext) en PNG transparent (proportionnel)."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig = plt.figure(figsize=(1, 1), dpi=250)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.text(0.0, 0.5, f"${tex_expr}$", fontsize=fontsize, va="center", ha="left")
    fig.savefig(out_path, dpi=250, transparent=True, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    return out_path

def aire_barres(n, phi):
    """Aire en mm² pour n barres de diamètre phi (mm)."""
    return float(n) * math.pi * (float(phi)/2.0)**2

def icon(ok_bool):
    return ICON_OK if ok_bool else ICON_NOK

# ============================ Styles ================================

def register_fonts():
    """Police normale + bold (DejaVu si possible, sinon Times)."""
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
        # Titres principaux (gras ; souligné via <u>...</u>)
        "Hmain": ParagraphStyle("Hmain", parent=ss["BodyText"],
                                fontName=base_b, fontSize=9.5, leading=12,
                                spaceBefore=5, spaceAfter=3, textColor=black),
        # Titres normaux (gras)
        "Hnorm": ParagraphStyle("Hnorm", parent=ss["BodyText"],
                                fontName=base_b, fontSize=9.5, leading=12,
                                spaceBefore=4, spaceAfter=2, textColor=black),
        # Sous-titres (gras)
        "Hsub": ParagraphStyle("Hsub", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=12,
                               spaceBefore=2, spaceAfter=1, textColor=black),
        # Texte normal (équations / résultats)
        "Eq": ParagraphStyle("Eq", parent=ss["BodyText"],
                             fontName=base, fontSize=9.5, leading=12,
                             textColor=black),
        # Résultats choisis en bleu foncé
        "Blue": ParagraphStyle("Blue", parent=ss["BodyText"],
                               fontName=base_b, fontSize=9.5, leading=12,
                               textColor=BLUE_DARK),
        # Petits compléments
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9, leading=11,
                                textColor=black),
    }

# ======================== Données béton ==============================

def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(p):
        p = "beton_classes.json"
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

# ====================== Composants de mise en page ===================

def eq_img(tex_numeric, tmpdir, img_width_mm=EQ_IMG_WIDTH_MM):
    """Image LaTeX NUMÉRIQUE proportionnelle (pas d’étirement)."""
    pth = os.path.join(tmpdir, f"eq_{abs(hash(tex_numeric))}.png")
    render_equation(tex_numeric, pth, fontsize=13, pad=0.05)  # ~120%
    with PILImage.open(pth) as im:
        w, h = im.size
    target_w = img_width_mm * mm * 1.2  # +20% largeur
    target_h = target_w * h / w          # hauteur suit proportionnellement
    return Image(pth, width=target_w, height=target_h, hAlign="LEFT")

def status_row(text_html, ok_bool, content_width, styles, text_style_name="Eq"):
    """
    Ligne 2 colonnes : (texte) | (OK/NON à droite).
    text_style_name: "Eq" (noir) ou "Blue" (résultats choisis).
    """
    col_icon = 10*mm
    col_text = content_width - col_icon
    tbl = Table(
        [[Paragraph(text_html, styles[text_style_name]), Paragraph(icon(ok_bool), styles["Eq"])]],
        colWidths=[col_text, col_icon]
    )
    tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    return tbl

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
    n_etriers=None, o_etrier=None, pas_etrier=None,
    n_etriers_r=None, o_etrier_r=None, pas_etrier_r=None,
    **kwargs,
):
    # Données matériaux & calculs
    beton_data = load_beton_data()
    d = beton_data.get(beton, {})
    fck_cube = d.get("fck_cube", 30)
    alpha_b  = d.get("alpha_b", 0.72)
    mu_val   = d.get(f"mu_a{fyk}", 11.5)
    fyd      = int(fyk) / 1.5

    d_utile = h - enrobage  # cm
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

    # Répertoire & nom fichier
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

    # Doc
    leftM, rightM, topM, botM = 14*mm, 14*mm, 12*mm, 12*mm
    content_width = A4[0] - leftM - rightM
    S = get_styles()
    flow = []
    tmpdir = tempfile.mkdtemp(prefix="pdf_eq_")

    try:
        doc = SimpleDocTemplate(
            out_path, pagesize=A4,
            leftMargin=leftM, rightMargin=rightM,
            topMargin=topM, bottomMargin=botM,
            title="Rapport de dimensionnement – Poutre BA",
        )

        # ========== En-tête ==========
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

        # ========== Caractéristiques ==========
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

        # ========== Dimensionnement ==========
        flow.append(Paragraph("<u>Dimensionnement</u>", S["Hmain"]))

        # --- Vérification de la hauteur utile ---
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
        ok_h = (hmin + enrobage) <= h
        flow.append(status_row(
            f"h<sub>min</sub> + enrob. = {fr(hmin+enrobage,1)} cm ≤ h = {fr(h,1)} cm",
            ok_h, content_width, S, "Eq"
        ))
        flow.append(Spacer(1, 3))

        # --- Calcul des armatures ---
        flow.append(Paragraph("Calcul des armatures", S["Hnorm"]))

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
        # Sections min / max en lignes séparées, indices corrects
        flow.append(Paragraph(f"Section d’acier minimale : A<sub>s,min</sub> = {fr(As_min,1)} mm²", S["Eq"]))
        flow.append(Paragraph(f"Section d’acier maximale : A<sub>s,max</sub> = {fr(As_max,1)} mm²", S["Eq"]))
        if n_as_inf and o_as_inf:
            As_inf_ch = aire_barres(n_as_inf, o_as_inf)
            ok_inf = (As_min <= As_inf_ch <= As_max) and (As_inf_ch >= As_inf_req)
            flow.append(status_row(
                f"On prend : {int(n_as_inf)}Ø{int(o_as_inf)} → {fr(As_inf_ch,1)} mm²",
                ok_inf, content_width, S, "Blue"
            ))
        flow.append(Spacer(1, 2))

        # Armatures supérieures
        if M_sup and M_sup > 0:
            flow.append(Paragraph("Armatures supérieures", S["Hsub"]))
            tex_as_sup = (
                r"A_{s,\mathrm{sup}}=\dfrac{"
                + fr(M_sup,2).replace(",", ".")
                + r"\cdot 10^{6}}{"
                + fr(fyd,1).replace(",", ".")
                + r"\cdot 0.9\cdot "
                + fr(d_utile,1).replace(",", ".")
                + r"\cdot 10}"
                + r" = " + fr(As_sup_req,1) + tex_unit("mm^2")
            )
            flow.append(eq_img(tex_as_sup, tmpdir))
            flow.append(Paragraph(f"Section d’acier minimale : A<sub>s,min</sub> = {fr(As_min,1)} mm²", S["Eq"]))
            flow.append(Paragraph(f"Section d’acier maximale : A<sub>s,max</sub> = {fr(As_max,1)} mm²", S["Eq"]))
            if n_as_sup and o_as_sup:
                As_sup_ch = aire_barres(n_as_sup, o_as_sup)
                ok_sup = (As_min <= As_sup_ch <= As_max) and (As_sup_ch >= As_sup_req)
                flow.append(status_row(
                    f"On prend : {int(n_as_sup)}Ø{int(o_as_sup)} → {fr(As_sup_ch,1)} mm²",
                    ok_sup, content_width, S, "Blue"
                ))
            flow.append(Spacer(1, 3))

        # --- Vérification de l'effort tranchant ---
        if V and V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["Hnorm"]))
            tex_tau = (
                r"\tau=\dfrac{"
                + fr(V,2).replace(",", ".")
                + r"\cdot 10^{3}}{0.75\cdot "
                + fr(b,1).replace(",", ".")
                + r"\cdot "
                + fr(h,1).replace(",", ".")
                + r"\cdot 100}"
                + r" = " + fr(tau,2) + tex_unit("N/mm^{2}")
            )
            flow.append(eq_img(tex_tau, tmpdir))
            if tau <= tau_1:
                lim_lab, lim_val, ok_tau = "τ_adm I", tau_1, True
            elif tau <= tau_2:
                lim_lab, lim_val, ok_tau = "τ_adm II", tau_2, True
            elif tau <= tau_4:
                lim_lab, lim_val, ok_tau = "τ_adm IV", tau_4, True
            else:
                lim_lab, lim_val, ok_tau = "τ_adm IV", tau_4, False
            flow.append(status_row(
                f"τ = {fr(tau,2)} N/mm² < {lim_lab} = {fr(lim_val,2)} N/mm²"
                if ok_tau else
                f"τ = {fr(tau,2)} N/mm² > {lim_lab} = {fr(lim_val,2)} N/mm²",
                ok_tau, content_width, S, "Eq"
            ))
            flow.append(Spacer(1, 3))

            # --- Calcul des étriers (V) ---
            flow.append(Paragraph("Calcul des étriers", S["Hsub"]))
            Ast_e = aire_barres(n_etriers or 1, o_etrier or 8)
            s_th = Ast_e * fyd * d_utile * 10 / (10 * V * 1e3)
            tex_s = (
                r"s_\mathrm{th}=\dfrac{"
                + fr(Ast_e,1).replace(",", ".")
                + r"\cdot " + fr(fyd,1).replace(",", ".")
                + r"\cdot " + fr(d_utile,1).replace(",", ".")
                + r"\cdot 10}{10\cdot " + fr(V,2).replace(",", ".")
                + r"\cdot 10^{3}}"
                + r" = " + fr(s_th,1) + tex_unit("cm")
            )
            flow.append(eq_img(tex_s, tmpdir))
            if n_etriers and o_etrier and pas_etrier is not None:
                ok_pas = pas_etrier <= s_th
                flow.append(status_row(
                    f"On prend : 1 étrier – Ø{int(o_etrier)} – {fr(pas_etrier,1)} cm (pas théorique = {fr(s_th,1)} cm)",
                    ok_pas, content_width, S, "Blue"
                ))
            flow.append(Spacer(1, 3))

        # --- Étriers réduits (V_lim) ---
        if V_lim and V_lim > 0:
            flow.append(Paragraph("Calcul des étriers réduits", S["Hsub"]))
            Ast_er = aire_barres(n_etriers_r or n_etriers or 1, o_etrier_r or o_etrier or 8)
            s_thr = Ast_er * fyd * d_utile * 10 / (10 * V_lim * 1e3)
            tex_sr = (
                r"s_{\mathrm{th},r}=\dfrac{"
                + fr(Ast_er,1).replace(",", ".")
                + r"\cdot " + fr(fyd,1).replace(",", ".")
                + r"\cdot " + fr(d_utile,1).replace(",", ".")
                + r"\cdot 10}{10\cdot " + fr(V_lim,2).replace(",", ".")
                + r"\cdot 10^{3}}"
                + r" = " + fr(s_thr,1) + tex_unit("cm")
            )
            flow.append(eq_img(tex_sr, tmpdir))
            if n_etriers_r and o_etrier_r and pas_etrier_r is not None:
                ok_pas_r = pas_etrier_r <= s_thr
                flow.append(status_row(
                    f"On prend : 1 étrier – Ø{int(o_etrier_r)} – {fr(pas_etrier_r,1)} cm (pas théorique = {fr(s_thr,1)} cm)",
                    ok_pas_r, content_width, S, "Blue"
                ))

        # Build
        doc.build(flow)
        return out_path

    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
