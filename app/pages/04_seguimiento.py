"""
Módulo 04 — Seguimiento de Trabajos.
Vista tabla de todas las OTs activas con indicadores de atraso,
filtros por estado/cliente/fecha, y detalle expandido.
"""

import streamlit as st
import httpx
import pandas as pd
from datetime import date

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import (
    formatear_fecha,
    formatear_moneda,
    calcular_atraso,
    ESTADOS_OT,
    ETAPAS_OT,
)
from app.components.sidebar import render_sidebar
from app.components.estado_badge import badge_estado


def mostrar_pagina():
    """Página principal de seguimiento de trabajos."""
    render_sidebar()
    
    # KPIs en el título
    st.header("📊 Seguimiento de Trabajos")
    
    url_api = obtener_url_api()
    
    # --- Cargar clientes para el filtro ---
    try:
        resp_clientes = httpx.get(f"{url_api}/seguimiento/clientes", timeout=10)
        resp_clientes.raise_for_status()
        clientes = resp_clientes.json().get("clientes", [])
        opciones_clientes = {"Todos": None}
        opciones_clientes.update({c["nombre"]: c["id"] for c in clientes})
    except Exception:
        opciones_clientes = {"Todos": None}
    
    # --- Filtros Inline ---
    with st.container():
        fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns([2, 2, 2, 2, 1])
        
        with fcol1:
            filtro_estado = st.selectbox("Estado", ["Todos"] + ESTADOS_OT, label_visibility="collapsed")
        with fcol2:
            filtro_cliente = st.selectbox("Cliente", list(opciones_clientes.keys()), label_visibility="collapsed")
        with fcol3:
            fecha_desde = st.date_input("Desde", value=None, label_visibility="collapsed")
        with fcol4:
            fecha_hasta = st.date_input("Hasta", value=None, label_visibility="collapsed")
        with fcol5:
            # En vez de un botón buscar, usamos checkbox para las entregadas o lo disparamos automático
            incluir_entregadas = st.checkbox("Entregadas", value=False)
            
    st.divider()
    
    # --- Cargar OTs ---
    try:
        params = {"incluir_entregadas": incluir_entregadas}
        if filtro_estado != "Todos":
            params["estado"] = filtro_estado
        if filtro_cliente != "Todos":
            params["cliente_id"] = opciones_clientes[filtro_cliente]
        # El backend actual quizás no soporte filtros de fecha_desde/hasta, pero los mandamos o filtramos en memoria
        
        respuesta = httpx.get(f"{url_api}/seguimiento/", params=params, timeout=15)
        respuesta.raise_for_status()
        ots = respuesta.json().get("ordenes_trabajo", [])
        
        # Filtro de fechas en memoria si fuera necesario
        if fecha_desde:
            ots = [ot for ot in ots if ot.get('fecha_ingreso') and date.fromisoformat(ot.get('fecha_ingreso')) >= fecha_desde]
        if fecha_hasta:
            ots = [ot for ot in ots if ot.get('fecha_ingreso') and date.fromisoformat(ot.get('fecha_ingreso')) <= fecha_hasta]
            
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        ots = []
    
    # Actualizar Subtítulo con contadores
    total_activas = len(ots)
    demoradas = sum(1 for ot in ots if ot.get("estado") == "DEMORADO")
    st.markdown(f"**{total_activas} activas · {demoradas} demoradas**")
    
    if not ots:
        st.info("📭 No hay órdenes de trabajo para mostrar con los filtros actuales.")
        return
        
    # --- Lista Columnar estilo Tabla ---
    # Header de la tabla "virtual"
    h1, h2, h3, h4, h5, h6 = st.columns([1.5, 3, 3, 2, 2, 1])
    h1.markdown("**NRO OT**")
    h2.markdown("**CLIENTE**")
    h3.markdown("**EQUIPO**")
    h4.markdown("**ESTADO**")
    h5.markdown("**DÍAS**")
    h6.markdown("**ACCIÓN**")
    st.markdown("<hr style='margin: 0.5em 0;'/>", unsafe_allow_html=True)
    
    ot_seleccionada = None
    
    for ot in sorted(ots, key=lambda x: x.get('fecha_entrega_prevista') or "9999-12-31"):
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 3, 3, 2, 2, 1])
        c1.markdown(f"**{ot.get('id', '-')}**")
        c2.markdown(ot.get("cliente", {}).get("nombre", "-") if ot.get("cliente") else "-")
        c3.markdown(ot.get("maquina", "-"))
        
        # Badge Estado
        c4.markdown(badge_estado(ot.get("estado", "-")), unsafe_allow_html=True)
        
        # Días
        f_entrega = ot.get("fecha_entrega_prevista")
        dias = -calcular_atraso(f_entrega) if f_entrega else None
        if dias is not None:
             if dias < 0:
                  c5.markdown(f"<span style='color: #E74C3C; font-weight: bold;'>{dias} (Atrasado)</span>", unsafe_allow_html=True)
             elif dias <= 3:
                  c5.markdown(f"<span style='color: #F39C12; font-weight: bold;'>{dias}</span>", unsafe_allow_html=True)
             else:
                  c5.markdown(f"<span style='color: #27AE60; font-weight: bold;'>{dias}</span>", unsafe_allow_html=True)
        else:
             c5.markdown("-")
             
        # Botón detalle
        if c6.button("Ver", key=f"btn_ver_{ot['id']}", use_container_width=True):
            ot_seleccionada = ot
            
        st.markdown("<hr style='margin: 0.2em 0;'/>", unsafe_allow_html=True)
    
    # --- Panel de Detalle (Si hay OT seleccionada o por defecto mostramos algo) ---
    if ot_seleccionada:
        st.markdown("### 📋 Detalles de la Orden")
        st.info(f"**Viendo Detalle: {ot_seleccionada['id']} — {ot_seleccionada.get('cliente', {}).get('nombre', '-')}**")
        
        tab_rec, tab_diag, tab_pres, tab_acc = st.tabs([
            "📥 Recepción", "🔍 Diagnóstico", "💰 Presupuesto", "⚙️ Acciones"
        ])
        
        with tab_rec:
            st.markdown(f"**Máquina/Equipo:** {ot_seleccionada.get('maquina', '-')}")
            st.markdown(f"**Trabajo a realizar:** {ot_seleccionada.get('descripcion_trabajo', '-')}")
            st.markdown(f"**Fecha ingreso:** {formatear_fecha(ot_seleccionada.get('fecha_ingreso'))}")
            st.markdown(f"**Entrega prevista:** {formatear_fecha(ot_seleccionada.get('fecha_entrega_prevista'))}")
            recepcion = ot_seleccionada.get("recepcion")
            if recepcion:
                st.markdown("---")
                st.markdown("#### Datos Técnicos de Ingreso")
                rc1, rc2 = st.columns(2)
                rc1.markdown(f"**Estado de la pieza:** {recepcion.get('estado_pieza', '-')}")
                rc1.markdown(f"**Causa de falla:** {recepcion.get('causa_falla', '-')}")
                rc2.markdown(f"**Material base:** {recepcion.get('material_base', '-')}")
                if recepcion.get("observaciones"):
                     st.markdown(f"**Observaciones:** {recepcion['observaciones']}")
            else:
                st.info("Sin datos técnicos de recepción registrados.")
                
        with tab_diag:
            diagnostico = ot_seleccionada.get("diagnostico")
            if diagnostico:
                st.markdown(f"**Conclusión:** {diagnostico.get('conclusion', '-')}")
                st.markdown(f"**Tipo falla:** {diagnostico.get('tipo_falla', '-')}")
                st.markdown(f"**Factibilidad:** {'Sí' if diagnostico.get('factibilidad') else 'No'}")
                st.markdown(f"**Técnico:** {diagnostico.get('tecnico_responsable', '-')}")
                if diagnostico.get("dimensiones"):
                    st.markdown(f"**Dimensiones:** {diagnostico['dimensiones']}")
                if diagnostico.get("notas"):
                    st.markdown(f"**Notas:** {diagnostico['notas']}")
            else:
                st.warning("⚠️ Sin diagnóstico registrado.")
                
        with tab_pres:
            presupuesto = ot_seleccionada.get("presupuesto")
            if presupuesto:
                st.markdown(f"**Estado Presupuesto:** {badge_estado(presupuesto.get('estado', '-'))}", unsafe_allow_html=True)
                st.markdown(f"**Costo Interno:** {formatear_moneda(presupuesto.get('total_costo'))}")
                st.markdown(f"<h3 style='color: #27AE60;'>Total Venta: {formatear_moneda(presupuesto.get('total_venta'))}</h3>", unsafe_allow_html=True)
                if presupuesto.get("pdf_url"):
                    st.markdown(f"📎 [**Descargar PDF de Presupuesto**]({presupuesto['pdf_url']})")
                
                mo_items = presupuesto.get("items_mano_obra", [])
                mat_items = presupuesto.get("items_materiales", [])
                
                if mo_items or mat_items:
                    with st.expander("Ver desglose de ítems"):
                        st.markdown("**Mano de Obra:**")
                        for i in mo_items:
                            st.markdown(f" - {i['descripcion']} (Hs: {i.get('horas', i.get('cantidad_horas', '-'))}) -> **{formatear_moneda(i.get('subtotal', 0))}**")
                        st.markdown("**Materiales:**")
                        for m in mat_items:
                            st.markdown(f" - {m['denominacion']} (Cant: {m.get('cantidad', '-')}) -> **{formatear_moneda(m.get('subtotal', 0))}**")
            else:
                st.warning("⚠️ Sin presupuesto registrado.")
                
        with tab_acc:
            st.markdown("### Cambiar Estado y Etapa")
            ac1, ac2 = st.columns(2)
            with ac1:
                nuevo_estado = st.selectbox(
                    "Nuevo Estado:",
                    ESTADOS_OT,
                    index=ESTADOS_OT.index(ot_seleccionada["estado"]) if ot_seleccionada.get("estado") in ESTADOS_OT else 0
                )
            with ac2:
                etapa_actual = ot_seleccionada.get("etapa", ETAPAS_OT[0])
                nueva_etapa = st.selectbox(
                    "Nueva Etapa:",
                    ETAPAS_OT,
                    index=ETAPAS_OT.index(etapa_actual) if etapa_actual in ETAPAS_OT else 0
                )
            
            if st.button("💾 Guardar Cambios de Estado", kind="primary"):
                try:
                    datos_actualizar = {}
                    if nuevo_estado != ot_seleccionada.get("estado"):
                        datos_actualizar["estado"] = nuevo_estado
                    if nueva_etapa != ot_seleccionada.get("etapa"):
                        datos_actualizar["etapa"] = nueva_etapa
                    
                    if nuevo_estado == "ENTREGADO" and ot_seleccionada.get("estado") != "ENTREGADO":
                        datos_actualizar["fecha_entrega_real"] = date.today().isoformat()
                    
                    if datos_actualizar:
                        resp = httpx.patch(
                            f"{url_api}/seguimiento/{ot_seleccionada['id']}",
                            json=datos_actualizar,
                            timeout=10,
                        )
                        resp.raise_for_status()
                        st.success(f"✅ OT {ot_seleccionada['id']} actualizada correctamente.")
                        st.rerun()
                    else:
                        st.info("No detectamos cambios para guardar.")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")


# --- Ejecutar página ---
if __name__ == "__main__":
    mostrar_pagina()

