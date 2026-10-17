"""
Safe PDF generation utility with fallback for systems missing GTK/Pango C libraries (e.g. Windows without GTK3).
Prevents 'OSError: cannot load library libgobject-2.0-0' from crashing FastAPI/uvicorn server startup.
"""
import io
import re

HAS_WEASYPRINT = False
weasyprint = None

try:
    import weasyprint as _wp
    weasyprint = _wp
    HAS_WEASYPRINT = True
except (ImportError, OSError, Exception) as e:
    # On Windows or systems without GTK/GObject libraries, weasyprint will fail gracefully
    weasyprint = None
    HAS_WEASYPRINT = False


def html_to_pdf_bytes(html_content: str, title: str = "BLIA Hsinchu Youth Document") -> bytes:
    """
    Safely convert HTML string to PDF bytes.
    If WeasyPrint is available and functional, uses WeasyPrint.
    Otherwise, gracefully falls back to ReportLab to generate a clean, valid PDF.
    """
    if HAS_WEASYPRINT and weasyprint is not None:
        try:
            return weasyprint.HTML(string=html_content).write_pdf()
        except Exception:
            pass

    # Fallback using reportlab
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Clean HTML tags for basic text rendering
        clean_text = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL)
        clean_text = re.sub(r'<script.*?</script>', '', clean_text, flags=re.DOTALL)
        clean_text = re.sub(r'<[^<]+?>', ' ', clean_text)
        clean_text = re.sub(r'&nbsp;', ' ', clean_text)
        clean_text = re.sub(r'&amp;', '&', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        # Header
        p.setFillColor(colors.HexColor("#D97706")) # Amber 600
        p.rect(0, height - 60, width, 60, fill=True, stroke=False)
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(40, height - 38, f"BLIA Hsinchu Youth - {title}")

        # Notice badge if running via fallback
        p.setFillColor(colors.HexColor("#78350F"))
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(40, height - 75, "[System Note: Document rendered via Lightweight Safe PDF Engine]")

        # Body text chunks
        p.setFillColor(colors.black)
        p.setFont("Helvetica", 10)
        y = height - 100
        words = clean_text.split(' ')
        current_line = []
        
        for w in words:
            current_line.append(w)
            if len(' '.join(current_line)) > 75:
                line_str = ' '.join(current_line)
                # Filter non-latin characters for standard Helvetica fallback if needed
                safe_str = line_str.encode('latin-1', 'replace').decode('latin-1')
                p.drawString(40, y, safe_str)
                y -= 15
                current_line = []
                if y < 60:
                    p.showPage()
                    y = height - 60
                    p.setFont("Helvetica", 10)

        if current_line:
            line_str = ' '.join(current_line)
            safe_str = line_str.encode('latin-1', 'replace').decode('latin-1')
            p.drawString(40, y, safe_str)

        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        # Ultimate minimal valid PDF fallback
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000108 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n185\n%%EOF"
