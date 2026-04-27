"""
Funciones utilitarias generales para el sistema Konmethal.
Generación de NRO OT, formateo de fechas, cálculos de presupuesto.
"""

from datetime import date, datetime
from typing import Optional


def _a_float(valor) -> float:
    """Convierte valores numéricos o strings a float de forma tolerante."""
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        normalizado = valor.strip().replace("$", "").replace(".", "").replace(",", ".")
        try:
            return float(normalizado)
        except ValueError:
            return 0.0
    return 0.0


def generar_numero_ot(anio: int, ultimo_numero: int) -> str:
    """
    Genera el siguiente número de OT con formato OT-AÑO-NRO.
    
    Args:
        anio: Año actual (ej: 2026)
        ultimo_numero: Último número secuencial usado en el año
    
    Returns:
        Número de OT formateado (ej: "OT-2026-001")
    """
    siguiente = ultimo_numero + 1
    return f"OT-{anio}-{siguiente:03d}"


def formatear_fecha(fecha: Optional[date]) -> str:
    """
    Formatea una fecha al formato dd/mm/yyyy argentino.
    
    Args:
        fecha: Fecha a formatear (date o datetime)
    
    Returns:
        String formateado o "-" si la fecha es None
    """
    if fecha is None:
        return "-"
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha).date()
        except ValueError:
            return fecha
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    return fecha.strftime("%d/%m/%Y")


def calcular_total_presupuesto(
    items_mano_obra: list,
    items_materiales: list,
    items_servicios: list,
    otros_gastos: float,
    porcentaje_ganancia: float,
) -> tuple[float, float]:
    """
    Calcula el total de costo y venta de un presupuesto.
    
    Args:
        items_mano_obra: Lista de dicts con 'subtotal'
        items_materiales: Lista de dicts con 'subtotal'
        items_servicios: Lista de dicts con 'monto'
        otros_gastos: Monto de otros gastos (flete, etc.)
        porcentaje_ganancia: Porcentaje de ganancia (ej: 30 para 30%)
    
    Returns:
        Tupla (total_costo, total_venta)
    """
    resumen = calcular_resumen_presupuesto(
        items_mano_obra,
        items_materiales,
        items_servicios,
        otros_gastos,
        porcentaje_ganancia,
    )
    return resumen["total_costo"], resumen["total_venta"]


def calcular_resumen_presupuesto(
    items_mano_obra: list,
    items_materiales: list,
    items_servicios: list,
    otros_gastos: float,
    porcentaje_ganancia: float,
) -> dict:
    """
    Calcula el resumen económico completo del presupuesto.

    Regla comercial:
    - El margen de ganancia se aplica únicamente sobre la mano de obra.
    """
    total_mo = sum(_a_float(item.get("subtotal", 0)) for item in items_mano_obra)
    total_mat = sum(_a_float(item.get("subtotal", 0)) for item in items_materiales)
    total_serv = sum(_a_float(item.get("monto", 0)) for item in items_servicios)

    otros_gastos = _a_float(otros_gastos)
    porcentaje_ganancia = _a_float(porcentaje_ganancia)

    ganancia = total_mo * (porcentaje_ganancia / 100)
    total_costo = total_mo + total_mat + total_serv + otros_gastos
    total_venta = total_costo + ganancia

    return {
        "total_mano_obra": round(total_mo, 2),
        "total_materiales": round(total_mat, 2),
        "total_servicios": round(total_serv, 2),
        "otros_gastos": round(otros_gastos or 0.0, 2),
        "porcentaje_ganancia": round(porcentaje_ganancia or 0.0, 2),
        "ganancia": round(ganancia, 2),
        "total_costo": round(total_costo, 2),
        "total_venta": round(total_venta, 2),
    }


def calcular_atraso(fecha_prevista: Optional[str]) -> int:
    """
    Calcula los días de atraso respecto a la fecha de entrega prevista.
    
    Args:
        fecha_prevista: Fecha de entrega prevista en formato ISO
    
    Returns:
        Días de atraso (positivo si está atrasado, 0 si no)
    """
    if not fecha_prevista:
        return 0
    try:
        if isinstance(fecha_prevista, str):
            fecha = datetime.fromisoformat(fecha_prevista).date()
        elif isinstance(fecha_prevista, datetime):
            fecha = fecha_prevista.date()
        elif isinstance(fecha_prevista, date):
            fecha = fecha_prevista
        else:
            return 0
        
        diferencia = (date.today() - fecha).days
        return max(0, diferencia)
    except (ValueError, TypeError):
        return 0


def formatear_moneda(monto: Optional[float]) -> str:
    """
    Formatea un monto como moneda argentina.
    
    Args:
        monto: Monto a formatear
    
    Returns:
        String formateado (ej: "$ 1.250,00") o "-" si es None
    """
    if monto is None:
        return "-"
    # Formato argentino: punto para miles, coma para decimales
    entero = int(monto)
    decimales = int(round((monto - entero) * 100))
    entero_str = f"{entero:,}".replace(",", ".")
    return f"$ {entero_str},{decimales:02d}"


# Constantes del sistema
ESTADOS_OT = ["PENDIENTE", "EN_PROCESO", "ESPERANDO_APROBACION", "DEMORADO", "ENTREGADO", "CANCELADO"]
ETAPAS_OT = ["Cotizando", "Cotizado", "En Proceso", "Terminado", "Facturado"]
ESTADOS_PRESUPUESTO = ["BORRADOR", "APROBADO_INTERNO", "ENVIADO", "ACEPTADO", "RECHAZADO"]
TIPOS_FALLA = ["desgaste", "rotura", "corrosion", "otro"]
CONCLUSIONES_DIAGNOSTICO = ["REPARABLE", "CON_CONDICIONES", "NO_REPARABLE"]


def construir_timeline(ot: dict, presupuesto: Optional[dict] = None) -> list[dict]:
    """
    Construye un timeline de hitos de una OT basado en las fechas registradas.

    Args:
        ot: Diccionario con los datos de la OT
        presupuesto: Diccionario opcional con los datos del presupuesto

    Returns:
        Lista de eventos ordenados cronológicamente, cada uno con:
        - titulo: str
        - fecha: str (ISO format)
        - completado: bool
        - icono: str
        - color: str
    """
    eventos = []

    # 1. Recepcionado (siempre presente)
    if ot.get("fecha_ingreso"):
        eventos.append({
            "titulo": "Recepcionado",
            "fecha": ot["fecha_ingreso"],
            "completado": True,
            "icono": "📥",
            "color": "#27AE60"
        })

    # 2. Diagnóstico completado
    if ot.get("fecha_diagnostico"):
        eventos.append({
            "titulo": "Diagnóstico completado",
            "fecha": ot["fecha_diagnostico"],
            "completado": True,
            "icono": "🔍",
            "color": "#27AE60"
        })

    # 3. Presupuesto enviado
    if ot.get("fecha_envio_presupuesto"):
        eventos.append({
            "titulo": "Presupuesto enviado",
            "fecha": ot["fecha_envio_presupuesto"],
            "completado": True,
            "icono": "📄",
            "color": "#27AE60"
        })

    # 4. Respuesta del cliente
    if ot.get("fecha_respuesta_cliente"):
        canal = presupuesto.get("canal_comunicacion", "").capitalize() if presupuesto else ""
        canal_str = f" ({canal})" if canal else ""

        # Determinar si fue aceptado o rechazado
        if ot.get("estado") == "CANCELADO":
            titulo = f"Cliente rechazó{canal_str}"
            icono = "❌"
            color = "#E74C3C"
        else:
            titulo = f"Cliente aceptó{canal_str}"
            icono = "✅"
            color = "#27AE60"

        eventos.append({
            "titulo": titulo,
            "fecha": ot["fecha_respuesta_cliente"],
            "completado": True,
            "icono": icono,
            "color": color
        })

    # 5. Trabajo iniciado
    if ot.get("fecha_inicio_real"):
        eventos.append({
            "titulo": "Trabajo iniciado",
            "fecha": ot["fecha_inicio_real"],
            "completado": True,
            "icono": "🔧",
            "color": "#27AE60"
        })

    # 6. Entregado
    if ot.get("fecha_entrega_real"):
        eventos.append({
            "titulo": "Entregado",
            "fecha": ot["fecha_entrega_real"],
            "completado": True,
            "icono": "✅",
            "color": "#27AE60"
        })
    elif ot.get("estado") in ["EN_PROCESO", "ESPERANDO_APROBACION", "DEMORADO"]:
        # Mostrar como pendiente si no está entregado ni cancelado
        eventos.append({
            "titulo": "Entrega pendiente",
            "fecha": ot.get("fecha_entrega_prevista", ""),
            "completado": False,
            "icono": "⏳",
            "color": "#95A5A6"
        })

    # Ordenar por fecha
    eventos_con_fecha = [e for e in eventos if e["fecha"]]
    eventos_sin_fecha = [e for e in eventos if not e["fecha"]]

    eventos_ordenados = sorted(eventos_con_fecha, key=lambda x: x["fecha"])

    return eventos_ordenados + eventos_sin_fecha


def obtener_info_estado_presupuesto(estado):
    """
    Retorna metadata sobre un estado de presupuesto.

    Args:
        estado: Estado del presupuesto (None si no existe)

    Returns:
        dict con:
        - descripcion: str
        - acciones_disponibles: list[str]
        - puede_editar: bool
        - color: str (hex)
        - icono: str (emoji)
    """
    info = {
        None: {
            "descripcion": "Sin presupuesto creado",
            "acciones_disponibles": ["crear"],
            "puede_editar": True,
            "color": "#95A5A6",
            "icono": "📝"
        },
        "BORRADOR": {
            "descripcion": "Presupuesto en elaboración (interno)",
            "acciones_disponibles": ["editar", "aprobar", "eliminar"],
            "puede_editar": True,
            "color": "#F39C12",
            "icono": "📄"
        },
        "APROBADO_INTERNO": {
            "descripcion": "Aprobado internamente, listo para enviar",
            "acciones_disponibles": ["enviar_pdf", "volver_borrador"],
            "puede_editar": False,
            "color": "#3498DB",
            "icono": "✅"
        },
        "ENVIADO": {
            "descripcion": "PDF enviado al cliente, esperando respuesta",
            "acciones_disponibles": ["registrar_respuesta", "ver_pdf"],
            "puede_editar": False,
            "color": "#9B59B6",
            "icono": "📤"
        },
        "ACEPTADO": {
            "descripcion": "Cliente aceptó el presupuesto",
            "acciones_disponibles": ["ver_pdf", "ver_respuesta"],
            "puede_editar": False,
            "color": "#27AE60",
            "icono": "✅"
        },
        "RECHAZADO": {
            "descripcion": "Cliente rechazó el presupuesto",
            "acciones_disponibles": ["ver_pdf", "ver_motivo"],
            "puede_editar": False,
            "color": "#E74C3C",
            "icono": "❌"
        }
    }
    return info.get(estado, info[None])
