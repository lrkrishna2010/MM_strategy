import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def build_pdf(out_path: str, title: str, summary: dict, image_paths: list):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 2*cm, title)
    c.setFont("Helvetica", 10)
    y = height - 3*cm
    for k, v in summary.items():
        c.drawString(2*cm, y, f"{k}: {v}"); y -= 0.6*cm
        if y < 5*cm: c.showPage(); y = height - 2*cm
    for img in image_paths:
        if os.path.exists(img):
            c.showPage(); c.setFont("Helvetica-Bold", 12)
            c.drawString(2*cm, height - 2*cm, os.path.basename(img))
            c.drawImage(img, 2*cm, 4*cm, width=16*cm, preserveAspectRatio=True, mask='auto')
    c.save()
    return out_path
