from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph
import xml.sax.saxutils as saxutils
import os

from .excel_generator import generate_excel  # relative import

# === COLOR PALETTE ===
bg_color   = colors.HexColor("#FEFDF9")
text_color = colors.HexColor("#3D4335")

# === STYLES ===
styles     = getSampleStyleSheet()
body_style = ParagraphStyle(
    name='Body',
    parent=styles['BodyText'],
    fontName='Helvetica',
    fontSize=12,
    leading=16,
    textColor=text_color,
    allowWidows=1,
    allowOrphans=1
)
just_style = ParagraphStyle(
    name='Justification',
    parent=body_style,
    fontSize=10,
    leading=14
)

def generate_pdf(logo_path, client_name, claim_text, estimate_data):
    # ensure output directory
    out_dir = "finalized_pdfs"
    os.makedirs(out_dir, exist_ok=True)
    # consistently name the PDF path
    pdf_path = os.path.join(
        out_dir,
        f"{client_name.replace(' ','_')}_Claim.pdf"
    )

    c = canvas.Canvas(pdf_path, pagesize=LETTER)
    width, height = LETTER

    # Helpers:
    def start_contents_page(include_title: bool):
        c.setFillColor(bg_color)
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setFillColor(text_color)
        try:
            img = ImageReader(logo_path)
            c.drawImage(img, 0.5*inch, height - 1.4*inch,
                        width=3.2*inch, height=1.2*inch,
                        preserveAspectRatio=True)
        except:
            pass
        if include_title:
            c.setFont("Helvetica-Bold", 20)
            # half-inch below logo (logo bottom ~1.4")
            c.drawCentredString(width/2, height - 1.9*inch, "Contents Estimate")

    def draw_table_headers(y_pos):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch,            y_pos, "Category")
        c.drawString(inch + 2.3*inch, y_pos, "Justification")
        c.drawString(7.1*inch,        y_pos, "Total")
        y2 = y_pos - 0.3*inch
        c.line(inch, y2, width - inch, y2)
        return y2 - 0.2*inch

    # === PAGE 1: Claim Package ===
    c.setFillColor(bg_color); c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setFillColor(text_color)
    try:
        img = ImageReader(logo_path)
        c.drawImage(img, 0.5*inch, height - 1.4*inch,
                    width=3.2*inch, height=1.2*inch, preserveAspectRatio=True)
    except:
        pass

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 2.5*inch, "Claim Package")

    raw = claim_text or ""
    esc = saxutils.escape(raw).replace('\t','&nbsp;'*4).replace('\r\n','\n').replace('\n','<br/>')
    para = Paragraph(esc, body_style)
    avail_w = width - 2*inch
    avail_h = height - 3*inch
    _, h = para.wrap(avail_w, avail_h)
    para.drawOn(c, inch, height - 3*inch - h)

    c.showPage()

    # === PAGE 2+: Contents Estimate ===
    start_contents_page(include_title=True)

    # Metadata
    y = height - 3.2*inch
    for label in ["claimant","property","estimator","estimate_type","date_entered","date_completed"]:
        label_text = f"{label.replace('_',' ').title()}: "
        val        = estimate_data.get(label, "")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(inch, y, label_text)
        lw = c.stringWidth(label_text, "Helvetica-Bold", 12)
        c.setFont("Helvetica", 12)
        c.drawString(inch + lw, y, val)
        y -= 0.3*inch

    # Grand total
    y -= 0.3*inch
    total_sum = sum(r.get("total",0) for r in estimate_data.get("rows",[]))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, y, f"Total Replacement Cost Value: ${total_sum:,.2f}")
    y -= 0.6*inch

    # Initial table headers
    y = draw_table_headers(y)

    # Layout constants
    cat_x, cat_w = inch, 2*inch
    just_x       = cat_x + cat_w + 0.2*inch
    total_x      = 7.4*inch
    just_w       = (total_x - 1.0*inch) - just_x
    bottom_margin= inch

    # Rows
    for row in estimate_data.get("rows", []):
        avail_h = y - bottom_margin

        cat_para  = Paragraph(row.get("category","—"), just_style)
        raw_j     = row.get("justification","—")
        esc_j     = saxutils.escape(raw_j).replace('\t','&nbsp;'*4).replace('\r\n','\n').replace('\n','<br/>')
        just_para = Paragraph(esc_j, just_style)

        w_cat, h_cat   = cat_para.wrap(cat_w,    avail_h)
        w_just, h_just = just_para.wrap(just_w, avail_h)
        row_h = max(h_cat, h_just, 14)

        if y - row_h < bottom_margin:
            c.showPage()
            start_contents_page(include_title=False)
            y = height - 1.9*inch    # headers 0.5" below logo
            y = draw_table_headers(y)
            avail_h = y - bottom_margin

        cat_para.drawOn(c,  cat_x,   y - h_cat)
        just_para.drawOn(c, just_x,  y - h_just)
        c.setFont("Helvetica", 10)
        c.drawRightString(total_x,
                          y - (row_h/2) + 4,
                          f"${row.get('total',0):,.2f}")
        y -= (row_h + 6)

    c.save()

    # Generate Excel beside the PDF
    excel_path = generate_excel(
        pdf_path,
        logo_path=logo_path,
        claim_text=claim_text,
        estimate_data=estimate_data,
        client_name=client_name
    )

    return pdf_path, excel_path

