from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.units import mm

def draw_line_in_blank_pdf(output_file, x_start, y_start, x_end, y_end, stroke_color='red', stroke_width=1):
    c = canvas.Canvas(output_file, pagesize=portrait(A4))

    c.setStrokeColor(stroke_color)
    c.setLineWidth(stroke_width * mm)  # Convert stroke width to mm
    c.line(x_start * mm, y_start * mm, x_end * mm, y_end * mm)  # Convert coordinates to mm

    c.save()

# Usage Example
output_file = 'output.pdf'
x_start, y_start = 100, 100  # Starting coordinates of the line in mm
x_end, y_end = 100, 200  # Ending coordinates of the line in mm

draw_line_in_blank_pdf(output_file, x_start, y_start, x_end, y_end)
