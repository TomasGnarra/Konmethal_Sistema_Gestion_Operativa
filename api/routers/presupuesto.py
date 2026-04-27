"""
Router de Presupuestos.
Endpoints para crear, actualizar, aprobar y generar PDF de presupuestos.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.db.supabase import (
    crear_presupuesto,
    obtener_presupuesto_por_ot,
    actualizar_presupuesto,
    obtener_cliente,
    obtener_ot_por_id,
    obtener_cliente_por_id,
    actualizar_ot,
    obtener_categorias_mano_obra,
    obtener_insumos_consumibles,
    actualizar_categoria_mo,
    actualizar_insumo,
    crear_categoria_mo,
    crear_insumo_consumible,
    subir_archivo_storage,
)
from api.models.modelos import (
    PresupuestoCrear,
    PresupuestoActualizar,
    RespuestaClientePresupuesto,
    CategoriaManoObraActualizar,
    InsumoActualizar,
    CategoriaManoObraCrear,
    InsumoConsumibleCrear,
)
from api.services.pdf_service import generar_pdf_presupuesto
from app.utils.helpers import calcular_total_presupuesto

router = APIRouter(prefix="/presupuesto", tags=["Presupuestos"])


def recalcular_totales_presupuesto(datos_presupuesto: dict) -> dict:
    """Normaliza totales de presupuesto en base a los ítems y variables finales."""
    total_costo, total_venta = calcular_total_presupuesto(
        datos_presupuesto.get("items_mano_obra", []) or [],
        datos_presupuesto.get("items_materiales", []) or [],
        datos_presupuesto.get("items_servicios", []) or [],
        datos_presupuesto.get("otros_gastos", 0.0) or 0.0,
        datos_presupuesto.get("porcentaje_ganancia", 0.0) or 0.0,
    )
    datos_presupuesto["total_costo"] = total_costo
    datos_presupuesto["total_venta"] = total_venta
    return datos_presupuesto


@router.post("/")
def crear_nuevo_presupuesto(datos: PresupuestoCrear):
    """Crea un nuevo presupuesto en estado BORRADOR."""
    try:
        # Verificar que la OT existe
        ot = obtener_ot_por_id(datos.ot_id)
        if not ot:
            raise HTTPException(status_code=404, detail=f"OT {datos.ot_id} no encontrada")
        
        datos_presupuesto = recalcular_totales_presupuesto(datos.model_dump())
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
        
        campos_recalculo = {
            "items_mano_obra",
            "items_materiales",
            "items_servicios",
            "otros_gastos",
            "porcentaje_ganancia",
        }

        if campos_recalculo.intersection(campos):
            presupuesto_actual = None
            try:
                cliente = obtener_cliente()
                resp_pres = cliente.table("presupuesto").select("*").eq("id", presupuesto_id).execute()
                if resp_pres.data:
                    presupuesto_actual = resp_pres.data[0]
            except Exception:
                presupuesto_actual = None

            base = presupuesto_actual or {}
            datos_recalculados = {
                "items_mano_obra": campos.get("items_mano_obra", base.get("items_mano_obra", [])),
                "items_materiales": campos.get("items_materiales", base.get("items_materiales", [])),
                "items_servicios": campos.get("items_servicios", base.get("items_servicios", [])),
                "otros_gastos": campos.get("otros_gastos", base.get("otros_gastos", 0.0)),
                "porcentaje_ganancia": campos.get("porcentaje_ganancia", base.get("porcentaje_ganancia", 0.0)),
            }
            campos.update(recalcular_totales_presupuesto(datos_recalculados))

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

        # Actualizar OT: cambiar a ESPERANDO_APROBACION y registrar timestamp
        actualizar_ot(ot_id, {
            "estado": "ESPERANDO_APROBACION",
            "etapa": "Cotizado",
            "fecha_envio_presupuesto": datetime.now().isoformat()
        })
        
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


@router.post("/{presupuesto_id}/respuesta-cliente")
def registrar_respuesta_cliente(presupuesto_id: int, datos: RespuestaClientePresupuesto):
    """
    Registra la respuesta del cliente a un presupuesto ENVIADO.

    Si aceptado:
    - Presupuesto → ACEPTADO
    - OT → EN_PROCESO, etapa "En Proceso", registra fecha_respuesta_cliente y fecha_inicio_real

    Si rechazado:
    - Presupuesto → RECHAZADO
    - OT → CANCELADO, registra fecha_respuesta_cliente
    """
    try:
        # Buscar presupuesto por ID
        # Nota: necesitamos una forma de obtener presupuesto por ID, no solo por OT
        # Por ahora, vamos a hacer una query directa en la función
        cliente = obtener_cliente()
        resp_pres = cliente.table("presupuesto").select("*").eq("id", presupuesto_id).execute()

        if not resp_pres.data or len(resp_pres.data) == 0:
            raise HTTPException(status_code=404, detail=f"Presupuesto {presupuesto_id} no encontrado")

        presupuesto = resp_pres.data[0]
        ot_id = presupuesto["ot_id"]

        # Validar que el presupuesto esté en estado ENVIADO
        if presupuesto["estado"] != "ENVIADO":
            raise HTTPException(
                status_code=400,
                detail=f"El presupuesto debe estar en estado ENVIADO. Estado actual: {presupuesto['estado']}"
            )

        # Validar que si es rechazo, haya motivo
        if not datos.aceptado and not datos.motivo_rechazo:
            raise HTTPException(
                status_code=400,
                detail="El motivo de rechazo es obligatorio cuando el cliente rechaza"
            )

        # Actualizar presupuesto
        nuevo_estado_presupuesto = "ACEPTADO" if datos.aceptado else "RECHAZADO"
        actualizar_presupuesto(presupuesto_id, {
            "estado": nuevo_estado_presupuesto,
            "canal_comunicacion": datos.canal_comunicacion,
            "motivo_rechazo": datos.motivo_rechazo,
            "notas_respuesta": datos.notas_respuesta,
        })

        # Actualizar OT según la respuesta
        timestamp_respuesta = datetime.now().isoformat()

        if datos.aceptado:
            # Cliente aceptó → OT vuelve a EN_PROCESO, arranca trabajo real
            actualizar_ot(ot_id, {
                "estado": "EN_PROCESO",
                "etapa": "En Proceso",
                "fecha_respuesta_cliente": timestamp_respuesta,
                "fecha_inicio_real": timestamp_respuesta,
            })
            mensaje = f"Cliente ACEPTÓ el presupuesto. OT {ot_id} pasó a EN_PROCESO."
        else:
            # Cliente rechazó → OT cancelada
            actualizar_ot(ot_id, {
                "estado": "CANCELADO",
                "fecha_respuesta_cliente": timestamp_respuesta,
            })
            mensaje = f"Cliente RECHAZÓ el presupuesto. OT {ot_id} pasó a CANCELADO."

        return {
            "mensaje": mensaje,
            "presupuesto_id": presupuesto_id,
            "ot_id": ot_id,
            "estado_presupuesto": nuevo_estado_presupuesto,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar respuesta del cliente: {str(e)}")


# --- Catálogos ---

@router.get("/catalogos/mano-obra")
def listar_categorias_mo():
    """Lista todas las categorías de mano de obra con sus costos."""
    try:
        categorias = obtener_categorias_mano_obra()
        return {"categorias": categorias}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener categorías: {str(e)}")


@router.patch("/catalogos/mano-obra/{categoria_id}")
def actualizar_categoria_mano_obra(categoria_id: int, datos: CategoriaManoObraActualizar):
    """Actualiza el costo/hora o descripción de una categoría de mano de obra."""
    try:
        campos = {k: v for k, v in datos.model_dump().items() if v is not None}
        if not campos:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        resultado = actualizar_categoria_mo(categoria_id, campos)
        return {"mensaje": f"Categoría {categoria_id} actualizada", "categoria": resultado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar categoría: {str(e)}")


@router.get("/catalogos/insumos")
def listar_insumos(busqueda: str = None):
    """Lista insumos/consumibles, con búsqueda opcional por denominación."""
    try:
        insumos = obtener_insumos_consumibles(busqueda=busqueda)
        return {"insumos": insumos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener insumos: {str(e)}")


@router.patch("/catalogos/insumos/{insumo_id}")
def actualizar_insumo_catalogo(insumo_id: int, datos: InsumoActualizar):
    """Actualiza precio u otros campos de un insumo/consumible."""
    try:
        campos = {k: v for k, v in datos.model_dump().items() if v is not None}
        if not campos:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        resultado = actualizar_insumo(insumo_id, campos)
        return {"mensaje": f"Insumo {insumo_id} actualizado", "insumo": resultado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar insumo: {str(e)}")


@router.post("/catalogos/mano-obra")
def crear_categoria_mano_obra(datos: CategoriaManoObraCrear):
    """Crea una nueva categoría de mano de obra en el catálogo."""
    try:
        resultado = crear_categoria_mo(datos.model_dump())
        return {"mensaje": "Categoría creada", "categoria": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear categoría: {str(e)}")


@router.post("/catalogos/insumos")
def crear_insumo_catalogo(datos: InsumoConsumibleCrear):
    """Crea un nuevo insumo/consumible en el catálogo."""
    try:
        resultado = crear_insumo_consumible(datos.model_dump())
        return {"mensaje": "Insumo creado", "insumo": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear insumo: {str(e)}")
