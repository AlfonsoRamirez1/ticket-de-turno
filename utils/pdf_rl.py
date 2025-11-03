import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

# Obtenemos la ruta absoluta al directorio 'static'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
LOGO1_PATH = os.path.join(STATIC_DIR, 'images', 'logo1.png')
LOGO2_PATH = os.path.join(STATIC_DIR, 'images', 'logo2.png')


def crear_comprobante_rl(data):
    """
    Crea el comprobante en PDF usando ReportLab.
    """
    buffer = io.BytesIO()

    # Usamos tamaño Carta (LETTER)
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER  # Obtenemos las dimensiones (en puntos)

    # --- Dibujar Logos ---
    # (ReportLab usa puntos, no píxeles. 1 mm = 2.83 puntos)
    try:
        # [cite_start]Logo 1 (Izquierda) [cite: 10-11]
        c.drawImage(LOGO1_PATH, x=10 * mm, y=height - 30 * mm, width=33 * mm, height=25 * mm, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar logo1.png: {e}")

    try:
        # [cite_start]Logo 2 (Derecha) [cite: 2-3]
        c.drawImage(LOGO2_PATH, x=width - 43 * mm, y=height - 30 * mm, width=33 * mm, height=25 * mm,
                    preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar logo2.png: {e}")

    # --- Título ---
    c.setFont('Helvetica-Bold', 16)
    c.drawCentredString(width / 2.0, height - 20 * mm, 'Comprobante de Turno')
    c.setFont('Helvetica', 12)
    c.drawCentredString(width / 2.0, height - 26 * mm, 'SECRETARÍA DE EDUCACIÓN')

    # --- Datos del Turno ---
    y_start = height - 50 * mm
    c.setFont('Helvetica-Bold', 18)
    c.drawCentredString(width / 2.0, y_start, f"Turno Asignado: {data['numero_turno']}")
    c.setFont('Helvetica', 12)
    c.drawCentredString(width / 2.0, y_start - 6 * mm, f"Oficina: {data['oficina']}")

    # --- Datos del Solicitante ---
    y_start -= 20 * mm
    c.setFont('Helvetica-Bold', 14)
    c.drawString(20 * mm, y_start, 'Datos del Solicitante')
    c.setFont('Helvetica', 11)
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start, f"Tramitante: {data['nombre_tramitante']}")
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start, f"CURP Alumno: {data['curp']}")
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start,
                 f"Alumno: {data['nombre_solicitante']} {data['paterno_solicitante']} {data['materno_solicitante']}")
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start, f"Teléfono: {data['celular']}")
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start, f"Correo: {data['correo']}")

    # --- Datos del Trámite ---
    y_start -= 12 * mm
    c.setFont('Helvetica-Bold', 14)
    c.drawString(20 * mm, y_start, 'Datos del Trámite')
    c.setFont('Helvetica', 11)
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start, f"Fecha de Solicitud: {data['fecha_solicitud'].strftime('%Y-%m-%d %H:%M')}")
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start, f"Nivel: {data['nivel']}")
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start, f"Municipio: {data['municipio']}")
    y_start -= 7 * mm
    c.drawString(20 * mm, y_start, f"Asunto: {data['descripcion']}")

    # --- Código QR ---
    qr_code = qr.QrCodeWidget(data['curp'])  #
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]

    # Tamaño y posición del QR
    qr_size = 50 * mm
    x_pos = width - 65 * mm
    y_pos = 30 * mm

    d = Drawing(qr_size, qr_size, transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0])
    d.add(qr_code)
    renderPDF.draw(d, c, x_pos, y_pos)

    # --- Finalizar PDF ---
    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes