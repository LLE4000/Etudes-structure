# -*- coding: utf-8 -*-
"""
Rapport de dimensionnement – Poutre BA (compact, aligné marges, validations à droite)
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
    if x is None:
        return "-"
    s = f"{float(x):,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", " ")
    if s.startswith("-0,"):
        s = s.replace("-0,", "0,")
    return s

def tex_unit(u):
    return r"\ \mathrm{" + u + "}"

def render_equation(tex_expr, out_path, fontsize=11, pad=0.05):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig = plt.figure(figsize=(1, 1), dpi=250)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.text(0.0, 0.5, f"${tex_expr}$", fontsize=fontsize, va="center", ha="left")
    fig.savefig(out_path, dpi=250, transparent=True, bbox_inches="tight", pad_inches=pad)
    plt.close(fig)
    return out_path

def aire_barres(n, phi): return float(n) * math.pi * (float(phi)/2.0)**2
def verdict(ok): return "ok" if ok else "non"
def icon(ok): return "✅" if ok else "❌"

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
        # Texte normal (taille de référence)
        "Body": ParagraphStyle("Body", parent=ss["BodyText"],
                               fontName=base, fontSize=9.5, leading=12,
                               spaceAfter=1, alignment=0),
        # Titres
        "Hmain": ParagraphStyle("Hmain", parent=ss["BodyText"],  # Titre principal (souligné + gras)
                                fontName=base, fontSize=9.5, leading=12,
                                spaceBefore=4, spaceAfter=3, alignment=0,
                                textColor=colors.black, underline=True, bold=True),
        "Hnorm": ParagraphStyle("Hnorm", parent=ss["BodyText"],  # Titre normal (gras)
                                fontName=base, fontSize=9.5, leading=12,
                                spaceBefore=3, spaceAfter=2, alignment=0,
                                textColor=colors.black, bold=True),
        "Hsub": ParagraphStyle("Hsub", parent=ss["BodyText"],   # Sous-titre (gras)
                               fontName=base, fontSize=9.5, leading=12,
                               spaceBefore=2, spaceAfter=1, alignment=0,
                               textColor=colors.black, bold=True),
        # Couleurs verdict
        "Green": ParagraphStyle("Green", parent=ss["BodyText"],
                                fontName=base, fontSize=9.5, leading=12,
                                textColor=colors.HexColor("#1e7e34")),
        "Red": ParagraphStyle("Red", parent=ss["BodyText"],
                              fontName=base, fontSize=9.5, leading=12,
                              textColor=colors.HexColor("#b00020")),
        # Petit
        "Small": ParagraphStyle("Small", parent=ss["BodyText"],
                                fontName=base, fontSize=9, leading=11,
                                spaceAfter=0, alignment=0, textColor=colors.HexColor("#444")),
    }

# ----------------------- Données béton -------------------------------

def load_beton_data():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "beton_classes.json")
    if not os.path.exists(p): p = "beton_classes.json"
    with open(p, "r", encoding="utf-8") as f: return json.load(f)

# ------------- Bloc équation (image proportionnelle + texte) ---------

def eq_img(tex_numeric, tmpdir, img_width_mm=38):
    """
    Image LaTeX NUMÉRIQUE proportionnelle (≈ +20% vs 32 mm).
    """
    pth = os.path.join(tmpdir, f"eq_{abs(hash(tex_numeric))}.png")
    render_equation(tex_numeric, pth, fontsize=11, pad=0.05)
    with PILImage.open(pth) as im: w, h = im.size
    target_w = img_width_mm * mm; target_h = target_w * h / w
    return Image(pth, width=target_w, height=target_h, hAlign="LEFT")

# ------ Ligne avec validation (texte à gauche + icône colonne droite) -----

def status_row(text_para, ok_bool, content_width):
    """
    Petit tableau 2 colonnes :
      - gauche : texte (paragraphe)
      - droite : icône ✅/❌ (colonne fine alignée à droite)
    'content_width' = largeur utile doc (pour fixer les largeurs).
    """
    S = get_styles()
    col_icon = 8*mm
    col_text = content_width - col_icon
    tbl = Table(
        [[Paragraph(text_para, S["Green" if ok_bool else "Red"]), Paragraph(icon(ok_bool), S["Body"])]],
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

# ------------------------- Générateur PDF ----------------------------

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
    n_etriers_r=None, o_etrier_r=None, pas_etrier_r=None,  # réduits
    **kwargs,
):
    beton_data = load_beton_data()
    d = beton_data.get(beton, {})
    fck_cube = d.get("fck_cube", 30)
    alpha_b  = d.get("alpha_b", 0.72)
    mu_val   = d.get(f"mu_a{fyk}", 11.5)
    fyd      = int(fyk)/1.5

    d_utile = h - enrobage  # cm
    M_max   = max(float(M_inf or 0.0), float(M_sup or 0.0))
    hmin    = math.sqrt((M_max*1e6)/(alpha_b*b*10*mu_val))/10.0 if M_max>0 else 0.0

    As_min      = 0.0013*b*h*1e2
    As_max      = 0.04*b*h*1e2
    As_inf_req  = (M_inf*1e6)/(fyd*0.9*d_utile*10) if M_inf>0 else 0.0
    As_sup_req  = (M_sup*1e6)/(fyd*0.9*d_utile*10) if M_sup>0 else 0.0

    tau   = (V*1e3)/(0.75*b*h*100) if V>0 else 0.0
    tau_1 = 0.016*fck_cube/1.05
    tau_2 = 0.032*fck_cube/1.05
    tau_4 = 0.064*fck_cube/1.05

    out_dir = "/mnt/data"
    try: os.makedirs(out_dir, exist_ok=True)
    except Exception: out_dir = tempfile.gettempdir()
    out_name = f"rapport__{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    out_path = os.path.join(out_dir, out_name)

    tmpdir = tempfile.mkdtemp(prefix="pdf_eq_")
    S = get_styles()
    flow = []

    try:
        # Marges = nos “lignes rouges”
        leftM, rightM, topM, botM = 14*mm, 14*mm, 12*mm, 12*mm
        doc = SimpleDocTemplate(out_path, pagesize=A4,
                                leftMargin=leftM, rightMargin=rightM,
                                topMargin=topM, bottomMargin=botM)
        content_width = A4[0] - leftM - rightM  # largeur utile (alignements)

        # --- En-tête projet (aligné aux marges)
        # Colonnage: [label, valeur] (gauche large) | [label, valeur] (droite)
        flow.append(Table(
            [
                ["Projet :", nom_projet or "—", "Date :", date or datetime.today().strftime("%d/%m/%Y")],
                ["Partie :", partie or "—", "Indice :", indice or "—"],
            ],
            colWidths=[16*mm, content_width*0.58, 16*mm, content_width*0.26],  # gauche large, droite compact
            style=TableStyle([
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 9.5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 2),
                ("ALIGN", (0,0), (-1,-1), "LEFT"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 3))

        # --- Caractéristiques (titre principal)
        flow.append(Paragraph("Caractéristiques de la poutre", S["Hmain"]))
        flow.append(Table(
            [
                ["Classe de béton", beton, "Armature", f"{fyk} N/mm²"],
                ["Largeur b", f"{fr(b,1)} cm", "Hauteur h", f"{fr(h,1)} cm"],
                ["Enrobage", f"{fr(enrobage,1)} cm", "Hauteur utile d", f"{fr(d_utile,1)} cm"],
            ],
            colWidths=[34*mm, content_width/2-34*mm, 34*mm, content_width/2-34*mm],
            style=TableStyle([
                ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#cccccc")),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#f6f6f6")),
                ("FONTNAME", (0,0), (-1,-1), "Times-Roman"),
                ("FONTSIZE", (0,0), (-1,-1), 9.5),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ])
        ))
        flow.append(Spacer(1, 3))

        # --- Dimensionnement (titre principal souligné)
        flow.append(Paragraph("Dimensionnement", S["Hmain"]))

        # Vérification de la hauteur utile (titre normal)
        flow.append(Paragraph("Vérification de la hauteur utile", S["Hnorm"]))
        tex_hmin = (
            r"h_\mathrm{min}=\sqrt{\frac{"
            + fr(M_max,2).replace(",", ".")
            + r"\cdot 10^{6}}{"
            + fr(alpha_b,2).replace(",", ".")
            + r"\cdot " + fr(b,1).replace(",", ".")
            + r"\cdot 10\cdot " + fr(mu_val,1).replace(",", ".")
            + r"}}/10" + tex_unit("cm")
        )
        flow.append(eq_img(tex_hmin, tmpdir))
        flow.append(Paragraph(f"h_min = {fr(hmin,1)} cm", S["Body"]))
        ok_h = (hmin + enrobage) <= h
        flow.append(status_row(
            f"h_min + enrobage = {fr(hmin+enrobage,1)} cm ≤ h = {fr(h,1)} cm — {verdict(ok_h)}",
            ok_h, content_width
        ))
        flow.append(Spacer(1, 3))

        # Calcul des armatures
        flow.append(Paragraph("Calcul des armatures", S["Hnorm"]))

        # Armatures inférieures
        flow.append(Paragraph("Armatures inférieures", S["Hsub"]))
        tex_as_inf = (
            r"A_{s,\mathrm{inf}}=\dfrac{"
            + fr(M_inf,2).replace(",", ".")
            + r"\cdot 10^{6}}{" + fr(fyd,1).replace(",", ".")
            + r"\cdot 0.9\cdot " + fr(d_utile,1).replace(",", ".")
            + r"\cdot 10}" + tex_unit("mm^2")
        )
        flow.append(eq_img(tex_as_inf, tmpdir))
        flow.append(Paragraph(f"A_s,inf = {fr(As_inf_req,1)} mm²", S["Body"]))
        flow.append(Paragraph(
            f"A_s,min = {fr(As_min,1)} mm² ; A_s,max = {fr(As_max,1)} mm²", S["Small"]
        ))
        if n_as_inf and o_as_inf:
            As_inf_ch = aire_barres(n_as_inf, o_as_inf)
            ok_inf = (As_min <= As_inf_ch <= As_max) and (As_inf_ch >= As_inf_req)
            flow.append(status_row(
                f"On prend : {int(n_as_inf)}Ø{int(o_as_inf)} ({fr(As_inf_ch,1)} mm²) — {verdict(ok_inf)}",
                ok_inf, content_width
            ))
        flow.append(Spacer(1, 2))

        # Armatures supérieures
        if M_sup and M_sup > 0:
            flow.append(Paragraph("Armatures supérieures", S["Hsub"]))
            tex_as_sup = (
                r"A_{s,\mathrm{sup}}=\dfrac{"
                + fr(M_sup,2).replace(",", ".")
                + r"\cdot 10^{6}}{" + fr(fyd,1).replace(",", ".")
                + r"\cdot 0.9\cdot " + fr(d_utile,1).replace(",", ".")
                + r"\cdot 10}" + tex_unit("mm^2")
            )
            flow.append(eq_img(tex_as_sup, tmpdir))
            flow.append(Paragraph(f"A_s,sup = {fr(As_sup_req,1)} mm²", S["Body"]))
            flow.append(Paragraph(
                f"A_s,min = {fr(As_min,1)} mm² ; A_s,max = {fr(As_max,1)} mm²", S["Small"]
            ))
            if n_as_sup and o_as_sup:
                As_sup_ch = aire_barres(n_as_sup, o_as_sup)
                ok_sup = (As_min <= As_sup_ch <= As_max) and (As_sup_ch >= As_sup_req)
                flow.append(status_row(
                    f"On prend : {int(n_as_sup)}Ø{int(o_as_sup)} ({fr(As_sup_ch,1)} mm²) — {verdict(ok_sup)}",
                    ok_sup, content_width
                ))
            flow.append(Spacer(1, 3))

        # Vérification de l'effort tranchant
        if V and V > 0:
            flow.append(Paragraph("Vérification de l'effort tranchant", S["Hnorm"]))
            tex_tau = (
                r"\tau=\dfrac{"
                + fr(V,2).replace(",", ".")
                + r"\cdot 10^{3}}{0.75\cdot " + fr(b,1).replace(",", ".")
                + r"\cdot " + fr(h,1).replace(",", ".")
                + r"\cdot 100}" + tex_unit("N/mm^{2}")
            )
            flow.append(eq_img(tex_tau, tmpdir))
            flow.append(Paragraph(f"τ = {fr(tau,2)} N/mm²", S["Body"]))
            # Seuil pertinent
            if tau <= tau_1: lim_lab, lim_val, ok_tau = "τ_adm I", tau_1, True
            elif tau <= tau_2: lim_lab, lim_val, ok_tau = "τ_adm II", tau_2, True
            elif tau <= tau_4: lim_lab, lim_val, ok_tau = "τ_adm IV", tau_4, True
            else: lim_lab, lim_val, ok_tau = "τ_adm IV", tau_4, False
            flow.append(status_row(
                f"τ = {fr(tau,2)} N/mm² < {lim_lab} = {fr(lim_val,2)} N/mm² — {verdict(ok_tau)}"
                if ok_tau else
                f"τ = {fr(tau,2)} N/mm² > {lim_lab} = {fr(lim_val,2)} N/mm² — {verdict(False)}",
                ok_tau, content_width
            ))
            flow.append(Spacer(1, 3))

            # Calcul des étriers
            flow.append(Paragraph("Calcul des étriers", S["Hnorm"]))
            Ast_e = aire_barres(n_etriers or 1, o_etrier or 8)
            s_th  = Ast_e * fyd * d_utile * 10 / (10 * V * 1e3)
            tex_s = (
                r"s_\mathrm{th}=\dfrac{" + fr(Ast_e,1).replace(",", ".")
                + r"\cdot " + fr(fyd,1).replace(",", ".")
                + r"\cdot " + fr(d_utile,1).replace(",", ".")
                + r"\cdot 10}{10\cdot " + fr(V,2).replace(",", ".")
                + r"\cdot 10^{3}}" + tex_unit("cm")
            )
            flow.append(eq_img(tex_s, tmpdir))
            flow.append(Paragraph(f"s_th = {fr(s_th,1)} cm", S["Body"]))
            if n_etriers and o_etrier and pas_etrier is not None:
                ok_pas = pas_etrier <= s_th
                flow.append(status_row(
                    f"On prend : Ø{int(o_etrier)} – {int(n_etriers)} brin(s) – pas {fr(pas_etrier,1)} cm (s_th = {fr(s_th,1)} cm) — {verdict(ok_pas)}",
                    ok_pas, content_width
                ))
            flow.append(Spacer(1, 3))

        # Calcul des étriers réduits (si V_lim)
        if V_lim and V_lim > 0:
            flow.append(Paragraph("Calcul des étriers réduits", S["Hnorm"]))
            Ast_er = aire_barres(n_etriers_r or n_etriers or 1, o_etrier_r or o_etrier or 8)
            s_thr  = Ast_er * fyd * d_utile * 10 / (10 * V_lim * 1e3)
            tex_sr = (
                r"s_{\mathrm{th},r}=\dfrac{" + fr(Ast_er,1).replace(",", ".")
                + r"\cdot " + fr(fyd,1).replace(",", ".")
                + r"\cdot " + fr(d_utile,1).replace(",", ".")
                + r"\cdot 10}{10\cdot " + fr(V_lim,2).replace(",", ".")
                + r"\cdot 10^{3}}" + tex_unit("cm")
            )
            flow.append(eq_img(tex_sr, tmpdir))
            flow.append(Paragraph(f"s_th,r = {fr(s_thr,1)} cm", S["Body"]))
            if n_etriers_r and o_etrier_r and pas_etrier_r is not None:
                ok_pas_r = pas_etrier_r <= s_thr
                flow.append(status_row(
                    f"On prend : Ø{int(o_etrier_r)} – {int(n_etriers_r)} brin(s) – pas {fr(pas_etrier_r,1)} cm (s_th,r = {fr(s_thr,1)} cm) — {verdict(ok_pas_r)}",
                    ok_pas_r, content_width
                ))

        # Build
        doc.build(flow)
        return out_path

    finally:
        try: shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception: pass
