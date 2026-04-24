"""
Módulo 02 — Diagnóstico Técnico.
Permite al técnico seleccionar una OT pendiente, revisar la recepción,
registrar el diagnóstico y ver historial del mismo cliente/equipo.
"""

import streamlit as st
import httpx

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import (
    formatear_fecha,
    TIPOS_FALLA,
    CONCLUSIONES_DIAGNOSTICO,
)


def mostrar_pagina():
    """Página principal de diagnóstico técnico."""
    st.header("🔬 Diagnóstico Técnico")
    st.markdown("Seleccioná una OT pendiente para registrar el diagnóstico.")
    
    url_api = obtener_url_api()
    
    # --- Cargar OTs pendientes ---
    try:
        respuesta = httpx.get(f"{url_api}/ot/", params={"estado": "PENDIENTE"}, timeout=10)
        respuesta.raise_for_status()
        ots = respuesta.json().get("ordenes_trabajo", [])
    except Exception as e:
        st.error(f"Error al cargar OTs: {str(e)}")
        ots = []
    
    if not ots:
        st.info("📭 No hay órdenes de trabajo pendientes de diagnóstico.")
        return
    
    # --- Selector de OT ---
    opciones_ot = {f"{ot['id']} — {ot.get('maquina', 'Sin equipo')}": ot["id"] for ot in ots}
    ot_seleccionada_label = st.selectbox(
        "Seleccionar Orden de Trabajo",
        options=list(opciones_ot.keys()),
    )
    
    if not ot_seleccionada_label:
        return
    
    ot_id = opciones_ot[ot_seleccionada_label]
    
    # --- Cargar datos de la OT ---
    try:
        respuesta = httpx.get(f"{url_api}/ot/{ot_id}", timeout=10)
        respuesta.raise_for_status()
        datos_ot = respuesta.json()
    except Exception as e:
        st.error(f"Error al cargar datos de la OT: {str(e)}")
        return
    
    ot = datos_ot.get("ot", {})
    recepcion = datos_ot.get("recepcion", {})
    cliente = datos_ot.get("cliente", {})
    
    # --- Resumen de recepción ---
    st.subheader("📋 Resumen de Recepción")
    
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**OT:** {ot.get('id', '-')}")
            st.markdown(f"**Cliente:** {cliente.get('nombre', '-')}")
            st.markdown(f"**Fecha ingreso:** {formatear_fecha(ot.get('fecha_ingreso'))}")
        with col2:
            st.markdown(f"**Máquina:** {ot.get('maquina', '-')}")
            st.markdown(f"**Trabajo:** {ot.get('descripcion_trabajo', '-')}")
            st.markdown(f"**Material:** {recepcion.get('material_base', '-') if recepcion else '-'}")
        with col3:
            st.markdown(f"**Estado pieza:** {recepcion.get('estado_pieza', '-') if recepcion else '-'}")
            st.markdown(f"**Causa falla:** {recepcion.get('causa_falla', '-') if recepcion else '-'}")
            if recepcion and recepcion.get("parametros_operacion"):
                params = recepcion["parametros_operacion"]
                st.markdown(f"**Parámetros:** V={params.get('velocidad', '-')} | P={params.get('presion', '-')} | T={params.get('temperatura', '-')}")
        
        if recepcion and recepcion.get("observaciones"):
            st.markdown(f"**Observaciones:** {recepcion['observaciones']}")
    
    st.divider()
    
    # --- Formulario de diagnóstico ---
    st.subheader("🔍 Diagnóstico")
    
    col1, col2 = st.columns(2)
    with col1:
        dimensiones = st.text_area(
            "Dimensiones relevadas",
            placeholder="Ej: Diámetro exterior: 120mm, Interior: 80mm, Largo: 500mm",
        )
        factibilidad = st.radio(
            "¿Es factible la reparación?",
            ["Sí", "No"],
            horizontal=True,
        )
        tipo_falla = st.selectbox(
            "Tipo de falla detectada",
            [""] + TIPOS_FALLA,
            format_func=lambda x: x.capitalize() if x else "Seleccionar...",
        )
    with col2:
        conclusion = st.selectbox(
            "Conclusión del diagnóstico *",
            [""] + CONCLUSIONES_DIAGNOSTICO,
            format_func=lambda x: x.replace("_", " ") if x else "Seleccionar...",
        )
        tecnico_responsable = st.text_input(
            "Técnico responsable *",
            placeholder="Nombre del técnico",
        )
        antecedente_ot = st.text_input(
            "OT antecedente (si existe)",
            placeholder="Ej: OT-2025-042",
        )
    
    notas = st.text_area(
        "Notas técnicas",
        placeholder="Observaciones adicionales del diagnóstico...",
    )
    
    st.divider()
    
    # --- Historial del cliente ---
    st.subheader("📜 Historial de OTs del cliente")
    
    try:
        resp_historial = httpx.get(f"{url_api}/ot/{ot_id}/historial", timeout=10)
        resp_historial.raise_for_status()
        historial = resp_historial.json().get("historial", [])
    except Exception:
        historial = []
    
    if historial:
        for ot_hist in historial:
            with st.expander(
                f"{ot_hist['id']} — {ot_hist.get('maquina', '-')} — "
                f"Estado: {ot_hist.get('estado', '-')}"
            ):
                st.markdown(f"**Fecha ingreso:** {formatear_fecha(ot_hist.get('fecha_ingreso'))}")
                st.markdown(f"**Trabajo:** {ot_hist.get('descripcion_trabajo', '-')}")
                st.markdown(f"**Estado:** {ot_hist.get('estado', '-')} | **Etapa:** {ot_hist.get('etapa', '-')}")
    else:
        st.info("No hay OTs anteriores para este cliente.")
    
    st.divider()
    
    # --- Botón guardar ---
    if st.button("💾 Guardar Diagnóstico", type="primary", use_container_width=True):
        # Validaciones
        errores = []
        if not conclusion:
            errores.append("Seleccioná la conclusión del diagnóstico")
        if not tecnico_responsable:
            errores.append("Ingresá el técnico responsable")
        
        if errores:
            for error in errores:
                st.error(f"⚠️ {error}")
            return
        
        with st.spinner("Guardando diagnóstico..."):
            try:
                datos_diagnostico = {
                    "ot_id": ot_id,
                    "dimensiones": dimensiones or None,
                    "factibilidad": factibilidad == "Sí",
                    "tipo_falla": tipo_falla or None,
                    "conclusion": conclusion,
                    "antecedente_ot": antecedente_ot or None,
                    "tecnico_responsable": tecnico_responsable,
                    "notas": notas or None,
                }
                
                respuesta = httpx.post(
                    f"{url_api}/ot/{ot_id}/diagnostico",
                    json=datos_diagnostico,
                    timeout=15,
                )
                respuesta.raise_for_status()
                
                st.success(f"✅ Diagnóstico guardado para OT **{ot_id}**")
                st.info("La OT pasó a estado **EN_PROCESO** y etapa **Cotizando**.")
                st.rerun()
                
            except httpx.HTTPStatusError as e:
                detalle = e.response.json().get("detail", str(e))
                st.error(f"❌ Error: {detalle}")
            except Exception as e:
                st.error(f"❌ Error de conexión: {str(e)}")


# --- Ejecutar página ---
mostrar_pagina()
