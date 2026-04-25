"""
Router de Órdenes de Trabajo.
Endpoints para crear, consultar y actualizar OTs.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from api.db.supabase import (
    crear_cliente,
    crear_ot,
    crear_recepcion,
    crear_diagnostico,
    obtener_clientes,
    obtener_cliente_por_id,
    obtener_ot_por_id,
    obtener_recepcion_por_ot,
    obtener_diagnostico_por_ot,
    obtener_historial_ots_cliente,
    obtener_siguiente_numero_ot,
    listar_ots,
    actualizar_ot,
)
from api.models.modelos import (
    OrdenTrabajoCrear,
    OrdenTrabajoActualizar,
    DiagnosticoCrear,
    ClienteCrear,
)

router = APIRouter(prefix="/ot", tags=["Órdenes de Trabajo"])


@router.post("/")
def crear_orden_trabajo(datos: OrdenTrabajoCrear):
    """
    Crea una nueva Orden de Trabajo junto con su recepción técnica.
    Genera automáticamente el número de OT con formato OT-AÑO-NRO.
    """
    try:
        # Generar número de OT
        anio = datetime.now().year
        ultimo = obtener_siguiente_numero_ot(anio)
        ot_id = f"OT-{anio}-{ultimo + 1:03d}"
        
        # Crear la OT
        datos_ot = {
            "id": ot_id,
            "cliente_id": datos.cliente_id,
            "fecha_ingreso": datetime.now().date().isoformat(),
            "maquina": datos.maquina,
            "descripcion_trabajo": datos.descripcion_trabajo,
            "estado": "PENDIENTE",
            "etapa": "Cotizando",
            "fecha_inicio_prevista": datos.fecha_inicio_prevista,
            "fecha_entrega_prevista": datos.fecha_entrega_prevista,
            "horas_cotizadas": datos.horas_cotizadas,
        }
        ot_creada = crear_ot(datos_ot)
        
        # Crear la recepción técnica
        datos_recepcion = {
            "ot_id": ot_id,
            "estado_pieza": datos.recepcion.estado_pieza,
            "material_base": datos.recepcion.material_base,
            "trabajo_solicitado": datos.recepcion.trabajo_solicitado,
            "causa_falla": datos.recepcion.causa_falla,
            "parametros_operacion": datos.recepcion.parametros_operacion,
            "fotos_urls": datos.recepcion.fotos_urls,
            "observaciones": datos.recepcion.observaciones,
        }
        recepcion_creada = crear_recepcion(datos_recepcion)
        
        return {
            "mensaje": f"Orden de trabajo {ot_id} creada exitosamente",
            "ot": ot_creada,
            "recepcion": recepcion_creada,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la OT: {str(e)}")


@router.get("/")
def listar_ordenes_trabajo(
    estado: str = None,
    cliente_id: int = None,
):
    """Lista OTs con filtros opcionales."""
    try:
        ots = listar_ots(estado=estado, cliente_id=cliente_id)
        return {"ordenes_trabajo": ots}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar OTs: {str(e)}")


@router.get("/{ot_id}")
def obtener_orden_trabajo(ot_id: str):
    """Obtiene una OT por su ID con sus datos relacionados."""
    try:
        ot = obtener_ot_por_id(ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {ot_id} no encontrada")
        
        recepcion = obtener_recepcion_por_ot(ot_id)
        diagnostico = obtener_diagnostico_por_ot(ot_id)
        cliente = obtener_cliente_por_id(ot["cliente_id"]) if ot.get("cliente_id") else None
        
        return {
            "ot": ot,
            "recepcion": recepcion,
            "diagnostico": diagnostico,
            "cliente": cliente,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener OT: {str(e)}")


@router.patch("/{ot_id}")
def actualizar_orden_trabajo(ot_id: str, datos: OrdenTrabajoActualizar):
    """Actualiza campos de una OT (estado, etapa, fechas, etc.)."""
    try:
        ot = obtener_ot_por_id(ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {ot_id} no encontrada")
        
        # Solo incluir campos que se proporcionaron
        campos_actualizar = {k: v for k, v in datos.model_dump().items() if v is not None}
        
        if not campos_actualizar:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        
        ot_actualizada = actualizar_ot(ot_id, campos_actualizar)
        return {"mensaje": f"OT {ot_id} actualizada", "ot": ot_actualizada}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar OT: {str(e)}")


@router.post("/{ot_id}/diagnostico")
def crear_diagnostico_tecnico(ot_id: str, datos: DiagnosticoCrear):
    """
    Crea un diagnóstico técnico para una OT.
    Actualiza el estado de la OT a EN_PROCESO y etapa a Cotizando.
    """
    try:
        ot = obtener_ot_por_id(ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {ot_id} no encontrada")
        
        # Crear diagnóstico
        datos_diagnostico = datos.model_dump()
        datos_diagnostico["ot_id"] = ot_id
        diagnostico = crear_diagnostico(datos_diagnostico)

        # Actualizar estado de la OT y registrar timestamp del diagnóstico
        actualizar_ot(ot_id, {
            "estado": "EN_PROCESO",
            "etapa": "Cotizando",
            "fecha_diagnostico": datetime.now().isoformat()
        })
        
        return {
            "mensaje": f"Diagnóstico creado para OT {ot_id}",
            "diagnostico": diagnostico,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear diagnóstico: {str(e)}")


@router.get("/{ot_id}/historial")
def obtener_historial(ot_id: str):
    """Obtiene el historial de OTs del mismo cliente."""
    try:
        ot = obtener_ot_por_id(ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {ot_id} no encontrada")
        
        historial = obtener_historial_ots_cliente(ot["cliente_id"], ot_actual=ot_id)
        return {"historial": historial}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener historial: {str(e)}")


# --- Endpoints auxiliares de clientes ---

@router.get("/clientes/lista")
def listar_clientes():
    """Lista todos los clientes."""
    try:
        clientes = obtener_clientes()
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar clientes: {str(e)}")


@router.post("/clientes/crear")
def crear_nuevo_cliente(datos: ClienteCrear):
    """Crea un nuevo cliente."""
    try:
        cliente = crear_cliente(datos.model_dump())
        return {"mensaje": "Cliente creado exitosamente", "cliente": cliente}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear cliente: {str(e)}")
