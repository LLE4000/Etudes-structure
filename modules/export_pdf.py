from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generer_rapport_pdf(nom_projet, partie, date, indice, beton, fyk, b, h, enrobage, M_inf, M_sup, V, V_lim):
    nom_fichier = f"rapport_{nom_projet.replace(' ', '_')}.pdf"
    c = canvas.Canvas(nom_fichier, pagesize=A4)
    width, height = A4

    def titre(text, y): 
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, text)

    def ligne(text, y):
        c.setFont("Helvetica", 11)
        c.drawString(60, y, text)

    y = height - 50
    titre("Rapport de dimensionnement – Poutre en béton armé", y)

    y -= 30
    ligne(f"Projet : {nom_projet}", y)
    y -= 20
    ligne(f"Partie : {partie} | Date : {date} | Indice : {indice}", y)

    y -= 30
    titre("Caractéristiques de la poutre", y)
    y -= 20
    ligne(f"Classe béton : {beton} | Acier : {fyk} N/mm²", y)
    y -= 20
    ligne(f"Dimensions : {b} x {h} cm | Enrobage : {enrobage} cm", y)

    y -= 30
    titre("Moments fléchissants", y)
    y -= 20
    ligne(f"Mmax inf. : {M_inf:.1f} kN.m", y)
    if M_sup > 0:
        y -= 20
        ligne(f"Mmax sup. : {M_sup:.1f} kN.m", y)

    y -= 30
    titre("Efforts tranchants", y)
    y -= 20
    ligne(f"Ved : {V:.1f} kN", y)
    if V_lim > 0:
        y -= 20
        ligne(f"Ved réduit : {V_lim:.1f} kN", y)

    y -= 40
    ligne("Note : Les vérifications détaillées sont disponibles dans l'application Streamlit.", y)

    c.showPage()
    c.save()
    return nom_fichier
