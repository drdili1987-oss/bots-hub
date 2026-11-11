import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import config

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "akts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# O'zbek lotin alifbosidagi belgilar (oʻ, gʻ) va boshqa harflarni to'g'ri
# ko'rsatish uchun DejaVu shriftidan foydalanamiz (standart shriftlarda bu
# belgilar chiqmasligi mumkin).
pdfmetrics.registerFont(TTFont("DejaVu", os.path.join(FONT_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")))

title_style = ParagraphStyle(
    "title", fontName="DejaVu-Bold", fontSize=15, alignment=TA_CENTER, spaceAfter=4
)
normal_style = ParagraphStyle("normal", fontName="DejaVu", fontSize=10, leading=14)
bold_style = ParagraphStyle("bold", fontName="DejaVu-Bold", fontSize=10, leading=14)
jami_style = ParagraphStyle(
    "jami", fontName="DejaVu-Bold", fontSize=12, alignment=TA_RIGHT
)


def format_money(n) -> str:
    return f"{n:,.0f}".replace(",", " ") + " so'm"


def create_akt_pdf(akt_raqami, kod, manzil, sana, items, jami, client_name=None):
    """
    items: [(xizmat_nomi, miqdor_matni, summa_matni, summa_son), ...]
    """
    client = client_name or config.CLIENT_NAME
    filename = f"akt_{akt_raqami}_{kod if kod else 'custom'}.pdf".replace(" ", "_")
    filepath = os.path.join(OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    story = []
    story.append(Paragraph("BAJARILGAN ISHLAR AKTI", title_style))
    story.append(Paragraph(f"№ {akt_raqami}&nbsp;&nbsp;&nbsp;&nbsp;Sana: {sana}", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Ijrochi:</b>", bold_style))
    story.append(Paragraph(config.COMPANY_NAME, normal_style))
    story.append(Paragraph(config.COMPANY_ADDRESS, normal_style))
    story.append(Paragraph(f"Tel: {config.COMPANY_PHONE}", normal_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Buyurtmachi:</b>", bold_style))
    story.append(Paragraph(client, normal_style))
    if kod:
        story.append(Paragraph(f"Do'kon kodi: {kod}", normal_style))
    story.append(Paragraph(f"Manzil: {manzil}", normal_style))
    story.append(Spacer(1, 14))

    table_data = [["№", "Xizmat", "Miqdor", "Summasi"]]
    for i, (name, qty_text, price_text, _total) in enumerate(items, start=1):
        table_data.append([str(i), name, qty_text, price_text])

    table = Table(table_data, colWidths=[12 * mm, 68 * mm, 45 * mm, 45 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
                ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"<b>Jami summa: {format_money(jami)}</b>", jami_style))
    story.append(Spacer(1, 36))

    sig_data = [
        ["Ijrochi: _____________________", "Buyurtmachi: _____________________"],
        [f"({config.COMPANY_NAME})", f"({client})"],
    ]
    sig_table = Table(sig_data, colWidths=[85 * mm, 85 * mm])
    sig_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 1), (-1, 1), 4),
            ]
        )
    )
    story.append(sig_table)

    doc.build(story)
    return filepath
