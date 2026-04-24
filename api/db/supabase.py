"""
Funciones de acceso a Supabase para el backend FastAPI.
Centraliza todas las operaciones CRUD contra la base de datos.
"""

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# --- Cliente Supabase (singleton a nivel módulo) ---

_cliente: Optional[Client] = None


def obtener_cliente() -> Client:
    """Retorna el cliente Supabase singleton para la API."""
    global _cliente
    if _cliente is None:
        url = os.getenv("SUPABASE_URL")
        clave = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        if not url or not clave:
            raise ValueError(
                "No se encontraron las credenciales de Supabase. "
                "Configurá SUPABASE_URL y SUPABASE_SERVICE_KEY en .env"
            )
        _cliente = create_client(url, clave)
    return _cliente


# =====================================================================
# CLIENTES
# =====================================================================

def obtener_clientes() -> list[dict]:
    """Retorna todos los clientes ordenados por nombre."""
    cliente = obtener_cliente()
    respuesta = cliente.table("clientes").select("*").order("nombre").execute()
    return respuesta.data or []


def obtener_cliente_por_id(cliente_id: int) -> Optional[dict]:
    """Retorna un cliente por su ID."""
    cliente = obtener_cliente()
    respuesta = cliente.table("clientes").select("*").eq("id", cliente_id).execute()
    datos = respuesta.data
    return datos[0] if datos else None


def crear_cliente(datos: dict) -> dict:
    """Crea un nuevo cliente y retorna el registro creado."""
    cliente = obtener_cliente()
    respuesta = cliente.table("clientes").insert(datos).execute()
    return respuesta.data[0]


# =====================================================================
# ÓRDENES DE TRABAJO
# =====================================================================

def obtener_siguiente_numero_ot(anio: int) -> int:
    """
    Obtiene el último número secuencial de OT para un año dado.
    Retorna 0 si no hay OTs en ese año.
    """
    cliente = obtener_cliente()
    prefijo = f"OT-{anio}-"
    respuesta = (
        cliente.table("ordenes_trabajo")
        .select("id")
        .like("id", f"{prefijo}%")
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    datos = respuesta.data
    if not datos:
        return 0
    # Extraer el número del ID (ej: "OT-2026-005" → 5)
    ultimo_id = datos[0]["id"]
    try:
        return int(ultimo_id.split("-")[-1])
    except (ValueError, IndexError):
        return 0


def crear_ot(datos: dict) -> dict:
    """Crea una nueva orden de trabajo."""
    cliente = obtener_cliente()
    respuesta = cliente.table("ordenes_trabajo").insert(datos).execute()
    return respuesta.data[0]


def obtener_ot_por_id(ot_id: str) -> Optional[dict]:
    """Retorna una OT por su ID."""
    cliente = obtener_cliente()
    respuesta = cliente.table("ordenes_trabajo").select("*").eq("id", ot_id).execute()
    datos = respuesta.data
    return datos[0] if datos else None


def listar_ots(
    estado: Optional[str] = None,
    cliente_id: Optional[int] = None,
    solo_activas: bool = False,
) -> list[dict]:
    """
    Lista órdenes de trabajo con filtros opcionales.
    
    Args:
        estado: Filtrar por estado específico
        cliente_id: Filtrar por cliente
        solo_activas: Si True, excluye ENTREGADO
    """
    cliente = obtener_cliente()
    consulta = cliente.table("ordenes_trabajo").select("*")
    
    if estado:
        consulta = consulta.eq("estado", estado)
    if cliente_id:
        consulta = consulta.eq("cliente_id", cliente_id)
    if solo_activas:
        consulta = consulta.neq("estado", "ENTREGADO")
    
    respuesta = consulta.order("created_at", desc=True).execute()
    return respuesta.data or []


def actualizar_ot(ot_id: str, datos: dict) -> dict:
    """Actualiza campos de una OT."""
    cliente = obtener_cliente()
    datos["updated_at"] = datetime.now().isoformat()
    respuesta = (
        cliente.table("ordenes_trabajo")
        .update(datos)
        .eq("id", ot_id)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else {}


# =====================================================================
# RECEPCIÓN TÉCNICA
# =====================================================================

def crear_recepcion(datos: dict) -> dict:
    """Crea un registro de recepción técnica."""
    cliente = obtener_cliente()
    respuesta = cliente.table("recepcion_tecnica").insert(datos).execute()
    return respuesta.data[0]


def obtener_recepcion_por_ot(ot_id: str) -> Optional[dict]:
    """Retorna la recepción técnica de una OT."""
    cliente = obtener_cliente()
    respuesta = (
        cliente.table("recepcion_tecnica")
        .select("*")
        .eq("ot_id", ot_id)
        .execute()
    )
    datos = respuesta.data
    return datos[0] if datos else None


# =====================================================================
# DIAGNÓSTICO TÉCNICO
# =====================================================================

def crear_diagnostico(datos: dict) -> dict:
    """Crea un registro de diagnóstico técnico."""
    cliente = obtener_cliente()
    respuesta = cliente.table("diagnostico_tecnico").insert(datos).execute()
    return respuesta.data[0]


def obtener_diagnostico_por_ot(ot_id: str) -> Optional[dict]:
    """Retorna el diagnóstico técnico de una OT."""
    cliente = obtener_cliente()
    respuesta = (
        cliente.table("diagnostico_tecnico")
        .select("*")
        .eq("ot_id", ot_id)
        .execute()
    )
    datos = respuesta.data
    return datos[0] if datos else None


def obtener_historial_ots_cliente(cliente_id: int, ot_actual: Optional[str] = None) -> list[dict]:
    """
    Retorna OTs anteriores del mismo cliente (para historial en diagnóstico).
    Excluye la OT actual si se proporciona.
    """
    cliente = obtener_cliente()
    consulta = (
        cliente.table("ordenes_trabajo")
        .select("*")
        .eq("cliente_id", cliente_id)
        .order("created_at", desc=True)
        .limit(10)
    )
    if ot_actual:
        consulta = consulta.neq("id", ot_actual)
    
    respuesta = consulta.execute()
    return respuesta.data or []


# =====================================================================
# PRESUPUESTO
# =====================================================================

def crear_presupuesto(datos: dict) -> dict:
    """Crea un nuevo presupuesto."""
    cliente = obtener_cliente()
    respuesta = cliente.table("presupuesto").insert(datos).execute()
    return respuesta.data[0]


def obtener_presupuesto_por_ot(ot_id: str) -> Optional[dict]:
    """Retorna el presupuesto de una OT."""
    cliente = obtener_cliente()
    respuesta = (
        cliente.table("presupuesto")
        .select("*")
        .eq("ot_id", ot_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    datos = respuesta.data
    return datos[0] if datos else None


def actualizar_presupuesto(presupuesto_id: int, datos: dict) -> dict:
    """Actualiza campos de un presupuesto."""
    cliente = obtener_cliente()
    datos["updated_at"] = datetime.now().isoformat()
    respuesta = (
        cliente.table("presupuesto")
        .update(datos)
        .eq("id", presupuesto_id)
        .execute()
    )
    return respuesta.data[0] if respuesta.data else {}


# =====================================================================
# TABLAS DE REFERENCIA
# =====================================================================

def obtener_categorias_mano_obra() -> list[dict]:
    """Retorna todas las categorías de mano de obra."""
    cliente = obtener_cliente()
    respuesta = (
        cliente.table("categorias_mano_obra")
        .select("*")
        .order("categoria")
        .execute()
    )
    return respuesta.data or []


def obtener_insumos_consumibles(busqueda: Optional[str] = None) -> list[dict]:
    """
    Retorna insumos/consumibles, opcionalmente filtrados por búsqueda.
    
    Args:
        busqueda: Texto para filtrar por denominación (búsqueda parcial)
    """
    cliente = obtener_cliente()
    consulta = cliente.table("insumos_consumibles").select("*")
    
    if busqueda:
        consulta = consulta.ilike("denominacion", f"%{busqueda}%")
    
    respuesta = consulta.order("denominacion").execute()
    return respuesta.data or []


# =====================================================================
# SUPABASE STORAGE
# =====================================================================

def subir_archivo_storage(bucket: str, ruta: str, archivo: bytes, content_type: str = "application/octet-stream") -> str:
    """
    Sube un archivo a Supabase Storage y retorna la URL pública.
    
    Args:
        bucket: Nombre del bucket (ej: "fotos-piezas", "presupuestos-pdf")
        ruta: Ruta dentro del bucket (ej: "OT-2026-001/foto1.jpg")
        archivo: Contenido del archivo en bytes
        content_type: Tipo MIME del archivo
    
    Returns:
        URL pública del archivo subido
    """
    cliente = obtener_cliente()
    cliente.storage.from_(bucket).upload(
        path=ruta,
        file=archivo,
        file_options={"content-type": content_type},
    )
    # Obtener URL pública
    url_publica = cliente.storage.from_(bucket).get_public_url(ruta)
    return url_publica


# =====================================================================
# CONSULTAS EXPANDIDAS (para seguimiento)
# =====================================================================

def obtener_ots_con_detalle(
    solo_activas: bool = True,
    estado: Optional[str] = None,
    cliente_id: Optional[int] = None,
) -> list[dict]:
    """
    Retorna OTs con datos expandidos de cliente, recepción, diagnóstico y presupuesto.
    Ideal para la vista de seguimiento.
    """
    ots = listar_ots(estado=estado, cliente_id=cliente_id, solo_activas=solo_activas)
    
    resultado = []
    for ot in ots:
        # Obtener datos relacionados
        cliente_datos = obtener_cliente_por_id(ot.get("cliente_id")) if ot.get("cliente_id") else None
        recepcion = obtener_recepcion_por_ot(ot["id"])
        diagnostico = obtener_diagnostico_por_ot(ot["id"])
        presupuesto = obtener_presupuesto_por_ot(ot["id"])
        
        ot_expandida = {
            **ot,
            "cliente": cliente_datos,
            "recepcion": recepcion,
            "diagnostico": diagnostico,
            "presupuesto": presupuesto,
        }
        resultado.append(ot_expandida)
    
    return resultado
