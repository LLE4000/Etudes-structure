# modules/export_pdf.py
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import matplotlib
matplotlib.use("Agg")  # rendu offscreen
import matplotlib.pyplot as plt

from datetime import datetime
import math
import os
import io

# --------------------------------------------------------------------------------------
# Mini BDD matériaux (extrait suffisant pour le rapport, cohérent avec ton module)
# --------------------------------------------------------------------------------------
BETON_DB = {
    "C20/25": {"fck": 20, "fck_cube": 25, "alpha_b": 0.68, "mu_a400": 9.0, "mu_a500": 10.5},
    "C25/30": {"fck": 25, "fck_cube": 30, "alpha_b": 0.70, "mu_a400": 9.5, "mu_a500": 11.0},
    "C30/37": {"fck": 30, "fck_cube": 37, "alpha_b": 0.72, "mu_a400": 10.0, "mu_a500": 11.5},
    "C35/45": {"fck": 35, "fck_cube": 45, "alpha_b": 0.74, "mu_a400": 10.5, "mu_a500": 12.0},
    "C40/50": {"fck": 40, "fck_cube": 50, "alpha_b": 0.76, "mu_a400": 11.0, "mu_a500": 12.5},
    "C45/55": {"fck": 45, "fck_cube": 55, "alpha_b": 0.78, "mu_a400": 11.5, "mu_a500": 13.0},
    "C50/60": {"fck": 50, "fck_cube": 60, "alpha_b": 0.80, "mu_a400": 12.0, "mu_a500": 13.5},
}

# --------------------------------------------------------------------------------------
# Outils LaTeX -> image (aligné gauche)
# --------------------------------------------------------------------------------------
def latex_to_img_bytes(latex_str: str, fontsize: int = 18, dpi: int = 300, pad: float = 0.15):
    """
    Rend une expression LaTeX en image (PNG) alignée à gauche.
    Retourne des bytes (PNG) à insérer dans le PDF via reportlab Image.
    """
    fig = plt.figure(figsize=(0.01, 0.01), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.text(0.0, 1.0, r"$%s$" % latex_str, ha="left", va="top", fontsize=fontsize)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=pad, transparent=False)
    plt.close(fig)
    buf.seek(0)
    return buf

def latex_paragraph(latex_str: str, width: float = 14*cm, fontsize: int = 18):
    """
    Helper : retourne un flowable Image depuis latex, contraint en largeur (garde proportion).
    """
    img_bytes = latex_to_img_bytes(latex_str, fontsize=fontsize)
    img = Image(img_bytes)
    img._restrictSize(width, 8*cm)
    return img

# --------------------------------------------------------------------------------------
# Styles
# --------------------------------------------------------------------------------------
def _styles():
    ss = getSampleStyleSheet()
    base = ss["Normal"]
    base.fontName = "Helvetica"
    base.fontSize = 10
    base.leading = 14

    title = ParagraphStyle("Title", parent=base, fontSize=18, leading=22, spaceAfter=8, spaceBefore=2, alignment=0, fontName="Helvetica-Bold")
    h1 = ParagraphStyle("H1", parent=base, fontSize=14, leading=18, spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold")
    h2 = ParagraphStyle("H2", parent=base, fontSize=12, leading=16, spaceBefore=8, spaceAfter=6, fontName="Helvetica-Bold")
    small = ParagraphStyle("Small", parent=base, fontSize=9, leading=12, textColor=colors.grey)
    ok = ParagraphStyle("OK", parent=base, textColor=colors.green, fontName="Helvetica-Bold")
    nok = ParagraphStyle("NOK", parent=base, textColor=colors.red, fontName="Helvetica-Bold")
    return {"base": base, "title": title, "h1": h1, "h2": h2, "small": small, "ok": ok, "nok": nok}

# --------------------------------------------------------------------------------------
# Rapport
# --------------------------------------------------------------------------------------
def generer_rapport_pdf(
    nom_projet: str = "",
    partie: str = "",
    date: str = "",
    indice: str = "",
    beton: str = "",
    fyk: str = "500",
    b: float = 0,
    h: float = 0,
    enrobage: float = 0,
    M_inf: float = 0,
    M_sup: float = 0,
    V: float = 0,
    V_lim: float = 0,
):
    """
    Génère un PDF pro avec formules détaillées (LaTeX rendues).
    Retourne le chemin du fichier PDF généré.
    """
    st = _styles()

    # Sécurité matériaux
    if beton not in BETON_DB:
        # fallback neutre si la classe n'est pas dans la mini BDD
        mat = {"fck": 30, "fck_cube": 37, "alpha_b": 0.72, "mu_a400": 10.0, "mu_a500": 11.5}
    else:
        mat = BETON_DB[beton]

    mu = mat["mu_a500"] if str(fyk) == "500" else mat["mu_a400"]
    alpha_b = mat["alpha_b"]
    fck_cube = mat["fck_cube"]
    fyd = float(fyk) / 1.5  # même convention que ton module

    # Conversions utiles
    d_utile = h - enrobage  # cm

    # Hauteur utile : hmin
    M_max = max(M_inf, M_sup or 0.0)
    hmin = math.sqrt((M_max * 1e6) / (alpha_b * b * 10 * mu)) / 10.0  # cm
    hauteur_ok = (hmin + enrobage) <= h

    # Armatures
    As_min = 0.0013 * b * h * 1e2
    As_max = 0.04   * b * h * 1e2

    As_inf = (M_inf * 1e6) / (fyd * 0.9 * d_utile * 10) if M_inf > 0 else 0.0
    As_sup = (M_sup * 1e6) / (fyd * 0.9 * d_utile * 10) if M_sup and M_sup > 0 else 0.0

    # Tranchant (ELS simplifié comme dans ton module)
    tau = V * 1e3 / (0.75 * b * h * 100) if V > 0 else 0.0
    tau_I   = 0.016 * fck_cube / 1.05
    tau_II  = 0.032 * fck_cube / 1.05
    tau_IV  = 0.064 * fck_cube / 1.05

    def verdict_tau(t):
        if t <= tau_I:  return "✓ Pas besoin d’étriers", "ok"
        if t <= tau_II: return "✓ Besoin d’étriers (Niveau II)", "ok"
        if t <= tau_IV: return "⚠ Besoin de barres inclinées + étriers (Niveau IV)", "nok"
        return "✗ Pas acceptable", "nok"

    msg_tau, etat_tau = verdict_tau(tau)

    # Tranchant réduit
    tau_r = V_lim * 1e3 / (0.75 * b * h * 100) if V_lim and V_lim > 0 else 0.0
    if V_lim and V_lim > 0:
        msg_tau_r, etat_tau_r = verdict_tau(tau_r)
    else:
        msg_tau_r, etat_tau_r = "", "ok"

    # Nom de fichier
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rapport__{ts}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=1.5*cm, bottomMargin=1.5*cm
    )

    flow = []

    # En-tête
    flow.append(Paragraph("Rapport de dimensionnement – Poutre en béton armé", st["title"]))
    flow.append(HRFlowable(color=colors.HexColor("#555555"), thickness=0.6))
    flow.append(Spacer(1, 8))

    # Infos projet
    info_data = [
        ["Projet :", nom_projet or "—", "Date :", date or datetime.today().strftime("%d/%m/%Y")],
        ["Partie :", partie or "—", "Indice :", indice or "—"],
    ]
    t = Table(info_data, colWidths=[2.5*cm, 8*cm, 2.5*cm, 3*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 10))

    # Caractéristiques
    flow.append(Paragraph("Caractéristiques de la poutre", st["h1"]))
    car_data = [
        ["Classe de béton", beton or "—", "Acier (fyk)", f"{fyk} N/mm²"],
        ["Largeur b", f"{b:.1f} cm", "Hauteur h", f"{h:.1f} cm"],
        ["Enrobage", f"{enrobage:.1f} cm", "Hauteur utile d", f"{d_utile:.1f} cm"],
    ]
    t = Table(car_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 10))

    # ==========================
    # Vérif hauteur utile
    # ==========================
    flow.append(Paragraph("Vérification de la hauteur utile", st["h1"]))
    # Formule générique
    flow.append(latex_paragraph(r"h_{\min}=\sqrt{\dfrac{M_{\max}\cdot 10^{6}}{\alpha_b\, b\, 10\, \mu_a}}\;\div\;10", fontsize=18))
    # Substitution
    sub = (
        r"h_{\min}"
        rf"=\sqrt{{\dfrac{{{M_max:.2f}\cdot 10^{{6}}}}{{{alpha_b:.3g}\cdot {b:.0f}\cdot 10 \cdot {mu:.3g}}}}}\div 10"
        rf"={hmin:.1f}\ \mathrm{{cm}}"
    )
    flow.append(latex_paragraph(sub, fontsize=16))
    # Conclusion
    concl = f"h,min + enrobage = {hmin+enrobage:.1f} cm {'≤' if hauteur_ok else '>'} h = {h:.1f} cm — "
    concl += "✓ Conforme" if hauteur_ok else "✗ Non conforme"
    flow.append(Paragraph(concl, st["ok"] if hauteur_ok else st["nok"]))
    flow.append(Spacer(1, 6))

    # ==========================
    # Armatures inférieures
    # ==========================
    flow.append(Paragraph("Armatures inférieures", st["h1"]))
    flow.append(latex_paragraph(r"A_{s,\mathrm{inf}}=\dfrac{M_{\mathrm{inf}}\cdot 10^{6}}{f_{yd}\cdot 0.9\, d\cdot 10}", fontsize=18))
    sub = (
        r"A_{s,\mathrm{inf}}"
        rf"=\dfrac{{{M_inf:.2f}\cdot 10^{{6}}}}{{{fyd:.1f}\cdot 0.9\cdot {d_utile:.1f}\cdot 10}}"
        rf"={As_inf:.1f}\ \mathrm{{mm^2}}"
    )
    flow.append(latex_paragraph(sub, fontsize=16))
    flow.append(latex_paragraph(
        rf"A_{{s,\min}}=0.0013\, b\, h \cdot 10^{{2}}={0.0013*b*h*1e2:.1f}\ \mathrm{{mm^2}},\quad "
        rf"A_{{s,\max}}=0.04\, b\, h \cdot 10^{{2}}={0.04*b*h*1e2:.1f}\ \mathrm{{mm^2}}", fontsize=14
    ))
    flow.append(Spacer(1, 6))

    # ==========================
    # Armatures supérieures (si M_sup)
    # ==========================
    if M_sup and M_sup > 0:
        flow.append(Paragraph("Armatures supérieures", st["h1"]))
        flow.append(latex_paragraph(r"A_{s,\mathrm{sup}}=\dfrac{M_{\mathrm{sup}}\cdot 10^{6}}{f_{yd}\cdot 0.9\, d\cdot 10}", fontsize=18))
        sub = (
            r"A_{s,\mathrm{sup}}"
            rf"=\dfrac{{{M_sup:.2f}\cdot 10^{{6}}}}{{{fyd:.1f}\cdot 0.9\cdot {d_utile:.1f}\cdot 10}}"
            rf"={As_sup:.1f}\ \mathrm{{mm^2}}"
        )
        flow.append(latex_paragraph(sub, fontsize=16))
        flow.append(latex_paragraph(
            rf"A_{{s,\min}}=0.0013\, b\, h \cdot 10^{{2}}={As_min:.1f}\ \mathrm{{mm^2}},\quad "
            rf"A_{{s,\max}}=0.04\, b\, h \cdot 10^{{2}}={As_max:.1f}\ \mathrm{{mm^2}}", fontsize=14
        ))
        flow.append(Spacer(1, 6))

    # ==========================
    # Effort tranchant
    # ==========================
    flow.append(Paragraph("Vérification de l'effort tranchant", st["h1"]))
    flow.append(latex_paragraph(r"\tau=\dfrac{V\cdot 10^{3}}{0.75\, b\, h \cdot 100}", fontsize=18))
    sub = (
        r"\tau"
        rf"=\dfrac{{{V:.2f}\cdot 10^{{3}}}}{{0.75\cdot {b:.0f}\cdot {h:.0f} \cdot 100}}"
        rf"={tau:.2f}\ \mathrm{{N/mm^2}}"
    )
    flow.append(latex_paragraph(sub, fontsize=16))
    flow.append(latex_paragraph(
        rf"\tau_{{\mathrm{{adm}},I}}=0.016\,\dfrac{{f_{{ck,cube}}}}{{1.05}}={tau_I:.2f}\ \mathrm{{N/mm^2}},\quad"
        rf"\tau_{{\mathrm{{adm}},II}}=0.032\,\dfrac{{f_{{ck,cube}}}}{{1.05}}={tau_II:.2f},\quad"
        rf"\tau_{{\mathrm{{adm}},IV}}=0.064\,\dfrac{{f_{{ck,cube}}}}{{1.05}}={tau_IV:.2f}", fontsize=14
    ))
    flow.append(Paragraph(msg_tau, st["ok"] if etat_tau == "ok" else st["nok"]))
    flow.append(Spacer(1, 6))

    # ==========================
    # Tranchant réduit (option)
    # ==========================
    if V_lim and V_lim > 0:
        flow.append(Paragraph("Vérification de l'effort tranchant réduit", st["h1"]))
        flow.append(latex_paragraph(r"\tau_{\mathrm{réduit}}=\dfrac{V_{\mathrm{lim}}\cdot 10^{3}}{0.75\, b\, h \cdot 100}", fontsize=18))
        sub = (
            r"\tau_{\mathrm{réduit}}"
            rf"=\dfrac{{{V_lim:.2f}\cdot 10^{{3}}}}{{0.75\cdot {b:.0f}\cdot {h:.0f} \cdot 100}}"
            rf"={tau_r:.2f}\ \mathrm{{N/mm^2}}"
        )
        flow.append(latex_paragraph(sub, fontsize=16))
        flow.append(Paragraph(msg_tau_r, st["ok"] if etat_tau_r == "ok" else st["nok"]))
        flow.append(Spacer(1, 6))

    # ==========================
    # Étriers (si V>0)
    # ==========================
    if V > 0:
        flow.append(Paragraph("Détermination des étriers (rappel formule théorique)", st["h1"]))
        flow.append(latex_paragraph(
            r"s_{\mathrm{th}}=\dfrac{A_{st}\, f_{yd}\, d \cdot 10}{10\, V\cdot 10^{3}}", fontsize=18
        ))
        flow.append(Paragraph(
            "Avec \(A_{st}\) l’aire totale d’acier d’étriers par section, \(f_{yd}\) la limite élastique de calcul, "
            "et \(d\) la hauteur utile.", st["base"])
        )
        flow.append(Spacer(1, 6))

    # Pied de page
    flow.append(Spacer(1, 12))
    flow.append(HRFlowable(color=colors.HexColor("#dddddd"), thickness=0.4))
    flow.append(Paragraph(
        "Généré automatiquement – unités : M en kN·m, V en kN, b/h/enrobage/d en cm, \(A_s\) en mm², \(\\tau\) en N/mm².",
        st["small"])
    )

    # Build
    doc.build(flow)
    return filename
