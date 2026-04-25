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
    calcular_atraso,
    construir_timeline,
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

        # --- Timeline de Hitos ---
        st.markdown("#### 📅 Timeline de la Orden")
        timeline_eventos = construir_timeline(ot_seleccionada, ot_seleccionada.get("presupuesto"))

        if timeline_eventos:
            # Renderizar timeline horizontal
            num_eventos = len(timeline_eventos)
            cols = st.columns(num_eventos)

            for idx, evento in enumerate(timeline_eventos):
                with cols[idx]:
                    # Icono y estado
                    if evento["completado"]:
                        st.markdown(
                            f"<div style='text-align: center; font-size: 2em;'>{evento['icono']}</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<div style='text-align: center; font-weight: bold; color: {evento['color']};'>{evento['titulo']}</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<div style='text-align: center; font-size: 0.85em; color: #7F8C8D;'>{formatear_fecha(evento['fecha'])}</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div style='text-align: center; font-size: 2em; opacity: 0.4;'>{evento['icono']}</div>",
                            unsafe_allow_html=True
                        )
                        st.markdown(
                            f"<div style='text-align: center; font-style: italic; color: {evento['color']};'>{evento['titulo']}</div>",
                            unsafe_allow_html=True
                        )
                        if evento.get('fecha'):
                            st.markdown(
                                f"<div style='text-align: center; font-size: 0.85em; color: #95A5A6;'>{formatear_fecha(evento['fecha'])}</div>",
                                unsafe_allow_html=True
                            )
        else:
            st.info("Sin hitos registrados aún.")

        st.divider()

        # --- Panel operativo ---
        nombre_cliente = ot_seleccionada.get("cliente", {}).get("nombre", "-") if ot_seleccionada.get("cliente") else "-"
        st.markdown(f"#### Actualización Operativa")
        st.info(
            f"**Equipo:** {ot_seleccionada.get('maquina', '-')} · "
            f"**Ingreso:** {formatear_fecha(ot_seleccionada.get('fecha_ingreso'))} · "
            f"**Etapa actual:** {ot_seleccionada.get('etapa', '-')}"
        )

        # Estado y Etapa
        ac1, ac2 = st.columns(2)
        nuevo_estado = ac1.selectbox(
            "Estado",
            ESTADOS_OT,
            index=ESTADOS_OT.index(ot_seleccionada["estado"]) if ot_seleccionada.get("estado") in ESTADOS_OT else 0,
            key=f"seg_estado_{ot_seleccionada['id']}",
        )
        etapa_actual = ot_seleccionada.get("etapa", ETAPAS_OT[0])
        nueva_etapa = ac2.selectbox(
            "Etapa",
            ETAPAS_OT,
            index=ETAPAS_OT.index(etapa_actual) if etapa_actual in ETAPAS_OT else 0,
            key=f"seg_etapa_{ot_seleccionada['id']}",
        )

        # Fechas y horas
        fc1, fc2, fc3 = st.columns(3)
        fp_actual = ot_seleccionada.get("fecha_entrega_prevista")
        fr_actual = ot_seleccionada.get("fecha_entrega_real")

        nueva_fecha_prevista = fc1.date_input(
            "Entrega prevista",
            value=date.fromisoformat(fp_actual[:10]) if fp_actual else None,
            key=f"seg_fp_{ot_seleccionada['id']}",
        )
        nueva_fecha_real = fc2.date_input(
            "Entrega real",
            value=date.fromisoformat(fr_actual[:10]) if fr_actual else None,
            key=f"seg_fr_{ot_seleccionada['id']}",
        )
        nuevas_horas = fc3.number_input(
            "Hs empleadas",
            value=float(ot_seleccionada.get("horas_empleadas") or 0),
            min_value=0.0,
            step=0.5,
            key=f"seg_hs_{ot_seleccionada['id']}",
        )

        if st.button("💾 Guardar Cambios", type="primary", key=f"seg_save_{ot_seleccionada['id']}"):
            try:
                datos_actualizar = {}
                if nuevo_estado != ot_seleccionada.get("estado"):
                    datos_actualizar["estado"] = nuevo_estado
                if nueva_etapa != ot_seleccionada.get("etapa"):
                    datos_actualizar["etapa"] = nueva_etapa
                if nueva_fecha_prevista and nueva_fecha_prevista.isoformat() != (fp_actual or "")[:10]:
                    datos_actualizar["fecha_entrega_prevista"] = nueva_fecha_prevista.isoformat()
                if nueva_fecha_real and nueva_fecha_real.isoformat() != (fr_actual or "")[:10]:
                    datos_actualizar["fecha_entrega_real"] = nueva_fecha_real.isoformat()
                elif nuevo_estado == "ENTREGADO" and ot_seleccionada.get("estado") != "ENTREGADO" and not nueva_fecha_real:
                    datos_actualizar["fecha_entrega_real"] = date.today().isoformat()
                he_actual = float(ot_seleccionada.get("horas_empleadas") or 0)
                if nuevas_horas != he_actual:
                    datos_actualizar["horas_empleadas"] = nuevas_horas

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
                    st.info("No hay cambios para guardar.")
            except Exception as e:
                st.error(f"❌ Error al guardar: {str(e)}")


# --- Ejecutar página ---
if __name__ == "__main__":
    mostrar_pagina()

