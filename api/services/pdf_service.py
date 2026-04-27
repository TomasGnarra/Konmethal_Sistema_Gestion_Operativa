"""
Servicio de generacion de PDF de presupuesto con ReportLab.
Genera un PDF profesional con el detalle del presupuesto para enviar al cliente.
"""

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from app.utils.helpers import calcular_resumen_presupuesto


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


def _estilo_tabla_detalle(color_primario: colors.Color) -> TableStyle:
    """Estilo base para tablas de detalle."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), color_primario),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D7E2")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])


def _texto_celda(texto, estilo):
    """Crea una celda Paragraph para permitir saltos de línea limpios."""
    return Paragraph(str(texto or "-"), estilo)


def generar_pdf_presupuesto(ot: dict, cliente: dict, presupuesto: dict) -> bytes:
    """
    Genera un PDF de presupuesto listo para enviar al cliente.

    Regla comercial:
    - El margen de ganancia se aplica unicamente sobre la mano de obra.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
    )

    color_primario = colors.HexColor("#123B6D")
    color_secundario = colors.HexColor("#1F78C1")
    color_acento = colors.HexColor("#1E9E63")
    color_fondo = colors.HexColor("#F4F7FB")
    color_borde = colors.HexColor("#D8E0EA")
    color_texto = colors.HexColor("#2B2B2B")

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloKonmethal",
        parent=estilos["Title"],
        fontSize=22,
        leading=24,
        textColor=color_primario,
        spaceAfter=1 * mm,
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloKonmethal",
        parent=estilos["Heading2"],
        fontSize=11,
        leading=13,
        textColor=color_primario,
        spaceBefore=6 * mm,
        spaceAfter=2 * mm,
    )
    estilo_normal = ParagraphStyle(
        "NormalKonmethal",
        parent=estilos["Normal"],
        fontSize=9,
        leading=12,
        textColor=color_texto,
    )
    estilo_celda = ParagraphStyle(
        "CeldaKonmethal",
        parent=estilo_normal,
        fontSize=8.5,
        leading=10,
        wordWrap="CJK",
    )
    estilo_celda_derecha = ParagraphStyle(
        "CeldaDerechaKonmethal",
        parent=estilo_celda,
        alignment=TA_RIGHT,
    )
    estilo_derecha = ParagraphStyle(
        "DerechaKonmethal",
        parent=estilos["Normal"],
        fontSize=9,
        leading=12,
        textColor=color_texto,
        alignment=TA_RIGHT,
    )
    estilo_centrado = ParagraphStyle(
        "CentradoKonmethal",
        parent=estilos["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER,
    )
    items_mo = presupuesto.get("items_mano_obra") or []
    items_mat = presupuesto.get("items_materiales") or []
    items_serv = presupuesto.get("items_servicios") or []
    otros_gastos = presupuesto.get("otros_gastos", 0.0) or 0.0
    porcentaje = presupuesto.get("porcentaje_ganancia", 0.0) or 0.0

    resumen = calcular_resumen_presupuesto(
        items_mo,
        items_mat,
        items_serv,
        otros_gastos,
        porcentaje,
    )

    fecha_hoy = _formatear_fecha(date.today())
    ot_id = ot.get("id", "-")
    nombre_cliente = cliente.get("nombre", "-")
    rubro_cliente = cliente.get("rubro", "-")
    telefono_cliente = cliente.get("telefono", "-")
    contacto_cliente = cliente.get("contacto", "-")
    maquina = ot.get("maquina", "-")
    descripcion = ot.get("descripcion_trabajo", "-")

    elementos = []

    elementos.append(Paragraph("KONMETHAL", estilo_titulo))
    elementos.append(Paragraph("Soluciones metalurgicas para la industria", estilo_normal))
    elementos.append(Spacer(1, 3 * mm))

    header = Table(
        [
            [
                Paragraph("PRESUPUESTO DE REPARACION", estilo_subtitulo),
                Paragraph(f"<b>Fecha:</b> {fecha_hoy}", estilo_derecha),
            ],
            [
                Paragraph(f"<b>Orden de trabajo:</b> {ot_id}", estilo_normal),
                Paragraph("<b>Validez:</b> sujeta a confirmacion comercial", estilo_derecha),
            ],
        ],
        colWidths=[10.6 * cm, 5.2 * cm],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color_fondo),
        ("BOX", (0, 0), (-1, -1), 0.75, color_borde),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, color_borde),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(header)
    elementos.append(Spacer(1, 5 * mm))

    elementos.append(Paragraph("DATOS DEL CLIENTE", estilo_subtitulo))
    tabla_cliente = Table(
        [
            ["Cliente", nombre_cliente, "Rubro", rubro_cliente],
            ["Telefono", telefono_cliente, "Contacto", contacto_cliente],
        ],
        colWidths=[2.4 * cm, 5.7 * cm, 2.2 * cm, 5.5 * cm],
    )
    tabla_cliente.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.5, color_borde),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, color_borde),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_cliente)

    elementos.append(Spacer(1, 3 * mm))
    elementos.append(Paragraph("DETALLE DEL TRABAJO", estilo_subtitulo))
    tabla_ot = Table(
        [
            ["Equipo / Maquina", maquina],
            ["Trabajo solicitado", descripcion],
        ],
        colWidths=[3.8 * cm, 12.0 * cm],
    )
    tabla_ot.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.5, color_borde),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, color_borde),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_ot)

    if items_mo:
        elementos.append(Paragraph("MANO DE OBRA", estilo_subtitulo))
        datos_mo = [["Categoria", "Descripcion", "$ / Hora", "Horas", "Subtotal"]]
        for item in items_mo:
            datos_mo.append([
                _texto_celda(item.get("categoria", "-"), estilo_celda),
                _texto_celda(item.get("descripcion", "-"), estilo_celda),
                _texto_celda(_formatear_moneda(item.get("costo_hora", 0)), estilo_celda_derecha),
                _texto_celda(str(item.get("cantidad_horas", 0)), estilo_celda_derecha),
                _texto_celda(_formatear_moneda(item.get("subtotal", 0)), estilo_celda_derecha),
            ])
        tabla_mo = Table(datos_mo, colWidths=[1.6 * cm, 7.1 * cm, 2.3 * cm, 1.6 * cm, 3.2 * cm])
        estilo_mo = _estilo_tabla_detalle(color_primario)
        estilo_mo.add("ALIGN", (2, 1), (-1, -1), "RIGHT")
        tabla_mo.setStyle(estilo_mo)
        elementos.append(tabla_mo)

    if items_mat:
        elementos.append(Paragraph("MATERIALES E INSUMOS", estilo_subtitulo))
        datos_mat = [["Denominacion", "Unidad", "$ / Unidad", "Cantidad", "Subtotal"]]
        for item in items_mat:
            datos_mat.append([
                _texto_celda(item.get("denominacion", "-"), estilo_celda),
                _texto_celda(item.get("unidad", "-"), estilo_celda),
                _texto_celda(_formatear_moneda(item.get("costo_unitario", 0)), estilo_celda_derecha),
                _texto_celda(str(item.get("cantidad", 0)), estilo_celda_derecha),
                _texto_celda(_formatear_moneda(item.get("subtotal", 0)), estilo_celda_derecha),
            ])
        tabla_mat = Table(datos_mat, colWidths=[5.9 * cm, 1.5 * cm, 2.5 * cm, 1.8 * cm, 3.1 * cm])
        estilo_mat = _estilo_tabla_detalle(color_primario)
        estilo_mat.add("ALIGN", (2, 1), (-1, -1), "RIGHT")
        tabla_mat.setStyle(estilo_mat)
        elementos.append(tabla_mat)

    if items_serv:
        elementos.append(Paragraph("SERVICIOS DE TERCEROS", estilo_subtitulo))
        datos_serv = [["Descripcion", "Monto"]]
        for item in items_serv:
            datos_serv.append([
                _texto_celda(item.get("descripcion", "-"), estilo_celda),
                _texto_celda(_formatear_moneda(item.get("monto", 0)), estilo_celda_derecha),
            ])
        tabla_serv = Table(datos_serv, colWidths=[12.2 * cm, 3.6 * cm])
        estilo_serv = _estilo_tabla_detalle(color_primario)
        estilo_serv.add("ALIGN", (1, 1), (1, -1), "RIGHT")
        tabla_serv.setStyle(estilo_serv)
        elementos.append(tabla_serv)

    elementos.append(Spacer(1, 7 * mm))
    elementos.append(HRFlowable(width="100%", thickness=0.7, color=color_borde))
    elementos.append(Spacer(1, 4 * mm))

    elementos.append(Paragraph("RESUMEN ECONOMICO", estilo_subtitulo))
    tabla_resumen = Table(
        [
            ["Mano de obra + margen", _formatear_moneda(resumen["total_mano_obra"] + resumen["ganancia"])],
            ["Mano de obra", _formatear_moneda(resumen["total_mano_obra"])],
            ["Materiales e insumos", _formatear_moneda(resumen["total_materiales"])],
            ["Servicios de terceros", _formatear_moneda(resumen["total_servicios"])],
            ["Otros gastos", _formatear_moneda(resumen["otros_gastos"])],
            ["Costo total", _formatear_moneda(resumen["total_costo"])],
            [f"Margen sobre mano de obra ({resumen['porcentaje_ganancia']}%)", _formatear_moneda(resumen["ganancia"])],
            ["PRECIO FINAL", _formatear_moneda(resumen["total_venta"])],
        ],
        colWidths=[11.1 * cm, 4.7 * cm],
    )
    tabla_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 4), color_fondo),
        ("BACKGROUND", (0, 5), (-1, 6), colors.white),
        ("BACKGROUND", (0, 7), (-1, 7), colors.HexColor("#EAF7F0")),
        ("BOX", (0, 0), (-1, -1), 0.75, color_borde),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, color_borde),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 5), (-1, 6), "Helvetica-Bold"),
        ("FONTNAME", (0, 7), (-1, 7), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 7), (-1, 7), color_acento),
        ("FONTSIZE", (0, 0), (-1, 6), 9.5),
        ("FONTSIZE", (0, 7), (-1, 7), 13),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    elementos.append(tabla_resumen)

    elementos.append(Spacer(1, 3 * mm))
    elementos.append(
        Paragraph(
            "Nota: el margen de ganancia se calcula sobre la mano de obra. "
            "Los materiales, servicios y otros gastos se incorporan al costo directo del trabajo.",
            estilo_centrado,
        )
    )

    elementos.append(Spacer(1, 12 * mm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=color_secundario))
    elementos.append(Spacer(1, 3 * mm))
    elementos.append(Paragraph("KONMETHAL | Presupuesto generado automaticamente", estilo_centrado))

    doc.build(elementos)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
