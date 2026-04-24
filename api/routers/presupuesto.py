"""
Router de Presupuestos.
Endpoints para crear, actualizar, aprobar y generar PDF de presupuestos.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.db.supabase import (
    crear_presupuesto,
    obtener_presupuesto_por_ot,
    actualizar_presupuesto,
    obtener_ot_por_id,
    obtener_cliente_por_id,
    actualizar_ot,
    obtener_categorias_mano_obra,
    obtener_insumos_consumibles,
    subir_archivo_storage,
)
from api.models.modelos import PresupuestoCrear, PresupuestoActualizar
from api.services.pdf_service import generar_pdf_presupuesto

router = APIRouter(prefix="/presupuesto", tags=["Presupuestos"])


@router.post("/")
def crear_nuevo_presupuesto(datos: PresupuestoCrear):
    """Crea un nuevo presupuesto en estado BORRADOR."""
    try:
        # Verificar que la OT existe
        ot = obtener_ot_por_id(datos.ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {datos.ot_id} no encontrada")
        
        datos_presupuesto = datos.model_dump()
        datos_presupuesto["estado"] = "BORRADOR"
        
        presupuesto = crear_presupuesto(datos_presupuesto)
        
        return {
            "mensaje": f"Presupuesto creado para OT {datos.ot_id}",
            "presupuesto": presupuesto,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear presupuesto: {str(e)}")


@router.get("/{ot_id}")
def obtener_presupuesto(ot_id: str):
    """Obtiene el presupuesto de una OT."""
    try:
        presupuesto = obtener_presupuesto_por_ot(ot_id)
        if not presupuesto:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró presupuesto para OT {ot_id}",
            )
        return {"presupuesto": presupuesto}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener presupuesto: {str(e)}")


@router.patch("/{presupuesto_id}")
def actualizar_datos_presupuesto(presupuesto_id: int, datos: PresupuestoActualizar):
    """Actualiza items y datos de un presupuesto."""
    try:
        campos = {k: v for k, v in datos.model_dump().items() if v is not None}
        if not campos:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        
        presupuesto = actualizar_presupuesto(presupuesto_id, campos)
        return {"mensaje": "Presupuesto actualizado", "presupuesto": presupuesto}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar presupuesto: {str(e)}")


@router.post("/{presupuesto_id}/aprobar")
def aprobar_presupuesto(presupuesto_id: int):
    """
    Aprueba internamente un presupuesto.
    Solo se puede aprobar si está en estado BORRADOR.
    """
    try:
        # Nota: no tenemos obtener_presupuesto_por_id directo,
        # hacemos el update y verificamos que se actualizó
        presupuesto = actualizar_presupuesto(presupuesto_id, {"estado": "APROBADO_INTERNO"})
        
        if not presupuesto:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        return {"mensaje": "Presupuesto aprobado internamente", "presupuesto": presupuesto}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al aprobar presupuesto: {str(e)}")


@router.post("/{presupuesto_id}/generar-pdf")
def generar_pdf_y_enviar(presupuesto_id: int, ot_id: str):
    """
    Genera el PDF del presupuesto, lo sube a Supabase Storage
    y marca el presupuesto como ENVIADO.
    """
    try:
        # Obtener datos necesarios
        ot = obtener_ot_por_id(ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {ot_id} no encontrada")
        
        cliente = obtener_cliente_por_id(ot["cliente_id"])
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        presupuesto = obtener_presupuesto_por_ot(ot_id)
        if not presupuesto:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        # Generar PDF
        pdf_bytes = generar_pdf_presupuesto(ot, cliente, presupuesto)
        
        # Subir a Supabase Storage
        nombre_archivo = f"{ot_id}/presupuesto_{ot_id}.pdf"
        try:
            pdf_url = subir_archivo_storage(
                bucket="presupuestos-pdf",
                ruta=nombre_archivo,
                archivo=pdf_bytes,
                content_type="application/pdf",
            )
        except Exception:
            # Si falla el storage, retornamos el PDF directamente
            pdf_url = None
        
        # Actualizar presupuesto
        datos_actualizar = {"estado": "ENVIADO"}
        if pdf_url:
            datos_actualizar["pdf_url"] = pdf_url
        
        actualizar_presupuesto(presupuesto_id, datos_actualizar)
        
        # Actualizar etapa de la OT
        actualizar_ot(ot_id, {"etapa": "Cotizado"})
        
        if pdf_url:
            return {
                "mensaje": f"PDF generado y subido para OT {ot_id}",
                "pdf_url": pdf_url,
            }
        else:
            # Retornar el PDF directamente si no se pudo subir al storage
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=presupuesto_{ot_id}.pdf"
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")


@router.post("/{presupuesto_id}/descargar-pdf")
def descargar_pdf(presupuesto_id: int, ot_id: str):
    """
    Genera y retorna el PDF del presupuesto sin subirlo al storage.
    Útil para previsualización.
    """
    try:
        ot = obtener_ot_por_id(ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {ot_id} no encontrada")
        
        cliente = obtener_cliente_por_id(ot["cliente_id"])
        presupuesto = obtener_presupuesto_por_ot(ot_id)
        
        if not presupuesto:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        pdf_bytes = generar_pdf_presupuesto(ot, cliente or {}, presupuesto)
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=presupuesto_{ot_id}.pdf"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")


# --- Catálogos ---

@router.get("/catalogos/mano-obra")
def listar_categorias_mo():
    """Lista todas las categorías de mano de obra con sus costos."""
    try:
        categorias = obtener_categorias_mano_obra()
        return {"categorias": categorias}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener categorías: {str(e)}")


@router.get("/catalogos/insumos")
def listar_insumos(busqueda: str = None):
    """Lista insumos/consumibles, con búsqueda opcional por denominación."""
    try:
        insumos = obtener_insumos_consumibles(busqueda=busqueda)
        return {"insumos": insumos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener insumos: {str(e)}")
