"""
Funciones utilitarias generales para el sistema Konmethal.
Generación de NRO OT, formateo de fechas, cálculos de presupuesto.
"""

from datetime import date, datetime
from typing import Optional


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
    total_mo = sum(item.get("subtotal", 0) for item in items_mano_obra)
    total_mat = sum(item.get("subtotal", 0) for item in items_materiales)
    total_serv = sum(item.get("monto", 0) for item in items_servicios)
    
    total_costo = total_mo + total_mat + total_serv + otros_gastos
    total_venta = total_costo * (1 + porcentaje_ganancia / 100)
    
    return round(total_costo, 2), round(total_venta, 2)


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
ESTADOS_OT = ["PENDIENTE", "EN_PROCESO", "DEMORADO", "ENTREGADO"]
ETAPAS_OT = ["Cotizando", "Cotizado", "En Proceso", "Terminado", "Facturado"]
ESTADOS_PRESUPUESTO = ["BORRADOR", "APROBADO_INTERNO", "ENVIADO", "ACEPTADO", "RECHAZADO"]
TIPOS_FALLA = ["desgaste", "rotura", "corrosion", "otro"]
CONCLUSIONES_DIAGNOSTICO = ["REPARABLE", "CON_CONDICIONES", "NO_REPARABLE"]
