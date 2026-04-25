"""
Router de Seguimiento de Trabajos.
Endpoints para visualizar y actualizar el estado de las OTs activas.
"""

from fastapi import APIRouter, HTTPException

from api.db.supabase import (
    obtener_ots_con_detalle,
    actualizar_ot,
    obtener_ot_por_id,
    obtener_clientes,
)
from api.models.modelos import OrdenTrabajoActualizar

router = APIRouter(prefix="/seguimiento", tags=["Seguimiento"])


@router.get("/")
def listar_ots_seguimiento(
    estado: str = None,
    cliente_id: int = None,
    incluir_entregadas: bool = False,
    incluir_canceladas: bool = False,
):
    """
    Lista OTs con datos expandidos para la vista de seguimiento.
    Por defecto excluye las OTs entregadas y canceladas.
    """
    try:
        solo_activas = not incluir_entregadas
        ots = obtener_ots_con_detalle(
            solo_activas=solo_activas,
            estado=estado,
            cliente_id=cliente_id,
            incluir_canceladas=incluir_canceladas,
        )
        return {"ordenes_trabajo": ots}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener seguimiento: {str(e)}",
        )


@router.patch("/{ot_id}")
def actualizar_estado_seguimiento(ot_id: str, datos: OrdenTrabajoActualizar):
    """
    Actualiza rápidamente el estado/etapa de una OT desde la vista de seguimiento.
    """
    try:
        ot = obtener_ot_por_id(ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {ot_id} no encontrada")
        
        campos = {k: v for k, v in datos.model_dump().items() if v is not None}
        if not campos:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        
        ot_actualizada = actualizar_ot(ot_id, campos)
        return {"mensaje": f"OT {ot_id} actualizada", "ot": ot_actualizada}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar OT: {str(e)}",
        )


@router.get("/clientes")
def listar_clientes_seguimiento():
    """Lista clientes para el filtro de seguimiento."""
    try:
        clientes = obtener_clientes()
        return {"clientes": clientes}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener clientes: {str(e)}",
        )
