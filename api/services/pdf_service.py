"""
Servicio de generación de PDF de presupuesto con ReportLab.
Genera un PDF profesional con el detalle del presupuesto para enviar al cliente.
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle,
    Spacer,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def _formatear_moneda(monto: float) -> str:
    """Formatea un monto como moneda argentina."""
    if monto is None:
        return "$ 0,00"
    entero = int(monto)
    decimales = int(round((monto - entero) * 100))
    entero_str = f"{entero:,}".replace(",", ".")
    return f"$ {entero_str},{decimales:02d}"


def _formatear_fecha(fecha: date) -> str:
    """Formatea fecha al formato argentino."""
    return fecha.strftime("%d/%m/%Y")


def generar_pdf_presupuesto(
    ot: dict,
    cliente: dict,
    presupuesto: dict,
) -> bytes:
    """
    Genera un PDF de presupuesto listo para enviar al cliente.
    
    Args:
        ot: Datos de la orden de trabajo
        cliente: Datos del cliente
        presupuesto: Datos del presupuesto con items desglosados
    
    Returns:
        Contenido del PDF en bytes
    """
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    
    # Estilos
    estilos = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle(
        "TituloKonmethal",
        parent=estilos["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=2 * mm,
    )
    
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=estilos["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#16213e"),
        spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    )
    
    estilo_normal = ParagraphStyle(
        "NormalKonmethal",
        parent=estilos["Normal"],
        fontSize=9,
        leading=12,
    )
    
    estilo_derecha = ParagraphStyle(
        "DerechaKonmethal",
        parent=estilos["Normal"],
        fontSize=9,
        alignment=TA_RIGHT,
    )
    
    estilo_total = ParagraphStyle(
        "TotalKonmethal",
        parent=estilos["Normal"],
        fontSize=11,
        alignment=TA_RIGHT,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
    )
    
    elementos = []
    
    # --- ENCABEZADO ---
    elementos.append(Paragraph("KONMETHAL", estilo_titulo))
    elementos.append(Paragraph("Taller Metalúrgico Industrial", estilos["Normal"]))
    elementos.append(Spacer(1, 3 * mm))
    elementos.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a1a2e")))
    elementos.append(Spacer(1, 5 * mm))
    
    # --- DATOS DEL PRESUPUESTO ---
    fecha_hoy = _formatear_fecha(date.today())
    ot_id = ot.get("id", "-")
    
    datos_header = [
        ["PRESUPUESTO", "", f"Fecha: {fecha_hoy}"],
        ["Orden de Trabajo:", ot_id, ""],
    ]
    
    tabla_header = Table(datos_header, colWidths=[4 * cm, 7 * cm, 5 * cm])
    tabla_header.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (0, 0), 14),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elementos.append(tabla_header)
    elementos.append(Spacer(1, 5 * mm))
    
    # --- DATOS DEL CLIENTE ---
    elementos.append(Paragraph("DATOS DEL CLIENTE", estilo_subtitulo))
    
    nombre_cliente = cliente.get("nombre", "-")
    rubro_cliente = cliente.get("rubro", "-")
    telefono_cliente = cliente.get("telefono", "-")
    contacto_cliente = cliente.get("contacto", "-")
    
    datos_cliente = [
        ["Cliente:", nombre_cliente, "Rubro:", rubro_cliente],
        ["Teléfono:", telefono_cliente, "Contacto:", contacto_cliente],
    ]
    
    tabla_cliente = Table(datos_cliente, colWidths=[2.5 * cm, 5 * cm, 2.5 * cm, 5 * cm])
    tabla_cliente.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_cliente)
    
    # --- DATOS DE LA OT ---
    maquina = ot.get("maquina", "-")
    descripcion = ot.get("descripcion_trabajo", "-")
    
    elementos.append(Spacer(1, 3 * mm))
    datos_ot = [
        ["Equipo/Máquina:", maquina],
        ["Trabajo:", descripcion],
    ]
    tabla_ot = Table(datos_ot, colWidths=[3.5 * cm, 12.5 * cm])
    tabla_ot.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_ot)
    
    # --- MANO DE OBRA ---
    items_mo = presupuesto.get("items_mano_obra") or []
    if items_mo:
        elementos.append(Paragraph("MANO DE OBRA", estilo_subtitulo))
        
        datos_mo = [["Categoría", "Descripción", "$/Hora", "Horas", "Subtotal"]]
        for item in items_mo:
            datos_mo.append([
                item.get("categoria", "-"),
                item.get("descripcion", "-"),
                _formatear_moneda(item.get("costo_hora", 0)),
                str(item.get("cantidad_horas", 0)),
                _formatear_moneda(item.get("subtotal", 0)),
            ])
        
        tabla_mo = Table(datos_mo, colWidths=[2 * cm, 6 * cm, 2.5 * cm, 2 * cm, 3 * cm])
        tabla_mo.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        elementos.append(tabla_mo)
    
    # --- MATERIALES ---
    items_mat = presupuesto.get("items_materiales") or []
    if items_mat:
        elementos.append(Paragraph("MATERIALES E INSUMOS", estilo_subtitulo))
        
        datos_mat = [["Denominación", "Unidad", "$/Unidad", "Cantidad", "Subtotal"]]
        for item in items_mat:
            datos_mat.append([
                item.get("denominacion", "-"),
                item.get("unidad", "-"),
                _formatear_moneda(item.get("costo_unitario", 0)),
                str(item.get("cantidad", 0)),
                _formatear_moneda(item.get("subtotal", 0)),
            ])
        
        tabla_mat = Table(datos_mat, colWidths=[5 * cm, 2 * cm, 2.5 * cm, 2 * cm, 3 * cm])
        tabla_mat.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        elementos.append(tabla_mat)
    
    # --- SERVICIOS DE TERCEROS ---
    items_serv = presupuesto.get("items_servicios") or []
    if items_serv:
        elementos.append(Paragraph("SERVICIOS DE TERCEROS", estilo_subtitulo))
        
        datos_serv = [["Descripción", "Monto"]]
        for item in items_serv:
            datos_serv.append([
                item.get("descripcion", "-"),
                _formatear_moneda(item.get("monto", 0)),
            ])
        
        tabla_serv = Table(datos_serv, colWidths=[12 * cm, 3.5 * cm])
        tabla_serv.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ]))
        elementos.append(tabla_serv)
    
    # --- TOTALES ---
    elementos.append(Spacer(1, 8 * mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elementos.append(Spacer(1, 3 * mm))
    
    otros_gastos = presupuesto.get("otros_gastos", 0) or 0
    total_costo = presupuesto.get("total_costo", 0) or 0
    porcentaje = presupuesto.get("porcentaje_ganancia", 0) or 0
    total_venta = presupuesto.get("total_venta", 0) or 0
    
    datos_totales = [
        ["Otros gastos (flete, envíos, etc.):", _formatear_moneda(otros_gastos)],
        ["TOTAL COSTO:", _formatear_moneda(total_costo)],
        [f"Margen ({porcentaje}%):", ""],
        ["TOTAL VENTA:", _formatear_moneda(total_venta)],
    ]
    
    tabla_totales = Table(datos_totales, colWidths=[12 * cm, 4 * cm])
    tabla_totales.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTSIZE", (0, 3), (-1, 3), 12),
        ("TEXTCOLOR", (0, 3), (-1, 3), colors.HexColor("#1a1a2e")),
        ("LINEABOVE", (0, 3), (-1, 3), 1, colors.HexColor("#1a1a2e")),
        ("TOPPADDING", (0, 3), (-1, 3), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_totales)
    
    # --- PIE ---
    elementos.append(Spacer(1, 15 * mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elementos.append(Spacer(1, 3 * mm))
    
    estilo_pie = ParagraphStyle(
        "PieKonmethal",
        parent=estilos["Normal"],
        fontSize=7,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    elementos.append(Paragraph(
        "KONMETHAL — Taller Metalúrgico Industrial | Presupuesto generado automáticamente",
        estilo_pie,
    ))
    
    # Construir PDF
    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
