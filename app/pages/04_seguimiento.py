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


def mostrar_pagina():
    """Página principal de seguimiento de trabajos."""
    st.header("📊 Seguimiento de Trabajos")
    st.markdown("Vista general de todas las órdenes de trabajo activas.")
    
    url_api = obtener_url_api()
    
    # --- Filtros ---
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_estado = st.selectbox(
                "Filtrar por estado",
                ["Todos"] + ESTADOS_OT,
            )
        
        with col2:
            # Cargar clientes para el filtro
            try:
                resp_clientes = httpx.get(f"{url_api}/seguimiento/clientes", timeout=10)
                resp_clientes.raise_for_status()
                clientes = resp_clientes.json().get("clientes", [])
                opciones_clientes = {"Todos": None}
                opciones_clientes.update({c["nombre"]: c["id"] for c in clientes})
            except Exception:
                opciones_clientes = {"Todos": None}
            
            filtro_cliente = st.selectbox("Filtrar por cliente", list(opciones_clientes.keys()))
        
        with col3:
            incluir_entregadas = st.checkbox("Incluir entregadas", value=False)
    
    # --- Cargar OTs ---
    try:
        params = {"incluir_entregadas": incluir_entregadas}
        if filtro_estado != "Todos":
            params["estado"] = filtro_estado
        if filtro_cliente != "Todos":
            params["cliente_id"] = opciones_clientes[filtro_cliente]
        
        respuesta = httpx.get(f"{url_api}/seguimiento/", params=params, timeout=15)
        respuesta.raise_for_status()
        ots = respuesta.json().get("ordenes_trabajo", [])
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        ots = []
    
    if not ots:
        st.info("📭 No hay órdenes de trabajo para mostrar con los filtros actuales.")
        return
    
    # --- KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_ots = len(ots)
    pendientes = sum(1 for ot in ots if ot.get("estado") == "PENDIENTE")
    en_proceso = sum(1 for ot in ots if ot.get("estado") == "EN_PROCESO")
    atrasadas = sum(1 for ot in ots if calcular_atraso(ot.get("fecha_entrega_prevista")) > 0 and ot.get("estado") != "ENTREGADO")
    
    col1.metric("Total OTs", total_ots)
    col2.metric("Pendientes", pendientes)
    col3.metric("En Proceso", en_proceso)
    col4.metric("⚠️ Atrasadas", atrasadas)
    
    st.divider()
    
    # --- Tabla de OTs ---
    for ot in ots:
        atraso = calcular_atraso(ot.get("fecha_entrega_prevista"))
        esta_atrasada = atraso > 0 and ot.get("estado") != "ENTREGADO"
        
        # Color del indicador
        if ot.get("estado") == "ENTREGADO":
            icono = "✅"
        elif esta_atrasada:
            icono = "🔴"
        elif ot.get("estado") == "DEMORADO":
            icono = "🟡"
        else:
            icono = "🟢"
        
        nombre_cliente = ot.get("cliente", {}).get("nombre", "-") if ot.get("cliente") else "-"
        
        # Encabezado del expander
        titulo = (
            f"{icono} **{ot['id']}** | {nombre_cliente} | "
            f"{ot.get('maquina', '-')} | {ot.get('estado', '-')} | "
            f"{ot.get('etapa', '-')}"
        )
        if esta_atrasada:
            titulo += f" | ⏰ {atraso} días de atraso"
        
        with st.expander(titulo):
            # --- Detalle de la OT ---
            tab1, tab2, tab3, tab4 = st.tabs(
                ["📋 General", "🔍 Recepción", "🔬 Diagnóstico", "💰 Presupuesto"]
            )
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Nro OT:** {ot['id']}")
                    st.markdown(f"**Cliente:** {nombre_cliente}")
                    st.markdown(f"**Máquina:** {ot.get('maquina', '-')}")
                    st.markdown(f"**Trabajo:** {ot.get('descripcion_trabajo', '-')}")
                with col2:
                    st.markdown(f"**Fecha ingreso:** {formatear_fecha(ot.get('fecha_ingreso'))}")
                    st.markdown(f"**Entrega prevista:** {formatear_fecha(ot.get('fecha_entrega_prevista'))}")
                    st.markdown(f"**Entrega real:** {formatear_fecha(ot.get('fecha_entrega_real'))}")
                    if ot.get("horas_cotizadas") or ot.get("horas_empleadas"):
                        st.markdown(
                            f"**Horas:** {ot.get('horas_cotizadas', '-')} cotizadas / "
                            f"{ot.get('horas_empleadas', '-')} empleadas"
                        )
            
            with tab2:
                recepcion = ot.get("recepcion")
                if recepcion:
                    st.markdown(f"**Estado pieza:** {recepcion.get('estado_pieza', '-')}")
                    st.markdown(f"**Material base:** {recepcion.get('material_base', '-')}")
                    st.markdown(f"**Trabajo solicitado:** {recepcion.get('trabajo_solicitado', '-')}")
                    st.markdown(f"**Causa falla:** {recepcion.get('causa_falla', '-')}")
                    if recepcion.get("observaciones"):
                        st.markdown(f"**Observaciones:** {recepcion['observaciones']}")
                else:
                    st.info("Sin datos de recepción.")
            
            with tab3:
                diagnostico = ot.get("diagnostico")
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
                    st.info("Sin diagnóstico registrado.")
            
            with tab4:
                presupuesto = ot.get("presupuesto")
                if presupuesto:
                    st.markdown(f"**Estado:** {presupuesto.get('estado', '-')}")
                    st.markdown(f"**Total costo:** {formatear_moneda(presupuesto.get('total_costo'))}")
                    st.markdown(f"**Total venta:** {formatear_moneda(presupuesto.get('total_venta'))}")
                    if presupuesto.get("pdf_url"):
                        st.markdown(f"📎 [Ver PDF]({presupuesto['pdf_url']})")
                else:
                    st.info("Sin presupuesto registrado.")
            
            # --- Actualizar estado/etapa ---
            st.markdown("---")
            st.markdown("**Actualizar estado:**")
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                nuevo_estado = st.selectbox(
                    "Estado",
                    ESTADOS_OT,
                    index=ESTADOS_OT.index(ot["estado"]) if ot.get("estado") in ESTADOS_OT else 0,
                    key=f"estado_{ot['id']}",
                )
            with col2:
                etapa_actual = ot.get("etapa", ETAPAS_OT[0])
                nuevo_etapa = st.selectbox(
                    "Etapa",
                    ETAPAS_OT,
                    index=ETAPAS_OT.index(etapa_actual) if etapa_actual in ETAPAS_OT else 0,
                    key=f"etapa_{ot['id']}",
                )
            with col3:
                st.write("")
                st.write("")
                if st.button("💾 Actualizar", key=f"btn_act_{ot['id']}"):
                    try:
                        datos_actualizar = {}
                        if nuevo_estado != ot.get("estado"):
                            datos_actualizar["estado"] = nuevo_estado
                        if nuevo_etapa != ot.get("etapa"):
                            datos_actualizar["etapa"] = nuevo_etapa
                        
                        # Si se marca como entregado, registrar fecha
                        if nuevo_estado == "ENTREGADO" and ot.get("estado") != "ENTREGADO":
                            datos_actualizar["fecha_entrega_real"] = date.today().isoformat()
                        
                        if datos_actualizar:
                            resp = httpx.patch(
                                f"{url_api}/seguimiento/{ot['id']}",
                                json=datos_actualizar,
                                timeout=10,
                            )
                            resp.raise_for_status()
                            st.success(f"✅ OT {ot['id']} actualizada")
                            st.rerun()
                        else:
                            st.info("No hay cambios para guardar.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")


# --- Ejecutar página ---
mostrar_pagina()
