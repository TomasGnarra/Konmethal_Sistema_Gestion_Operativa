"""
Módulo 02 — Diagnóstico Técnico.
Permite al técnico seleccionar una OT pendiente, revisar la recepción,
registrar el diagnóstico y ver historial del mismo cliente/equipo.
"""

import streamlit as st
import httpx
from datetime import date

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import (
    formatear_fecha,
    calcular_atraso,
    TIPOS_FALLA,
    CONCLUSIONES_DIAGNOSTICO,
)
from app.components.sidebar import render_sidebar
from app.components.estado_badge import badge_estado


def mostrar_pagina():
    """Página principal de diagnóstico técnico."""
    render_sidebar()
    st.header("🔍 Diagnóstico Técnico")
    st.markdown("Revisión técnica de ingreso para Órdenes de Trabajo.")
    st.divider()
    
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
        
    # --- LAYOUT SPLIT: Lado Izquierdo (Lista) | Lado Derecho (Detalle Formulario) ---
    col_lista, col_detalle = st.columns([1, 2], gap="large")
    
    with col_lista:
        st.subheader("OTs Pendientes")
        
        # Selección via selectbox / radio
        opciones_ot = []
        for ot in ots:
            f_ing = ot.get('fecha_ingreso')
            ingreso_dt = date.fromisoformat(f_ing) if f_ing else date.today()
            dias_ingreso = (date.today() - ingreso_dt).days
            
            # Badge visual en texto para la lista
            alerta = " ⚠️" if dias_ingreso > 5 else ""
            cliente_nombre = ot.get('cliente', {}).get('nombre', '-') if ot.get('cliente') else '-'
            label = f"{ot['id']} | {cliente_nombre} | {ot.get('maquina', '-')} ({dias_ingreso}d){alerta}"
            
            opciones_ot.append({
                "id": ot["id"],
                "label": label,
                "dias": dias_ingreso
            })
            
        selec_label = st.radio(
            "Seleccioná la OT a diagnosticar:", 
            [o["label"] for o in opciones_ot],
            label_visibility="collapsed"
        )
        
        # Extraer el ID seleccionado
        ot_id_seleccionada = next(o["id"] for o in opciones_ot if o["label"] == selec_label)
        
    with col_detalle:
        # Cargar datos completos de la OT seleccionada
        try:
            resp_ot = httpx.get(f"{url_api}/ot/{ot_id_seleccionada}", timeout=10)
            resp_ot.raise_for_status()
            datos_ot = resp_ot.json()
            ot = datos_ot.get("ot", {})
            recepcion = datos_ot.get("recepcion", {})
            cliente = datos_ot.get("cliente", {})
        except Exception as e:
            st.error(f"Error al cargar datos de la OT: {str(e)}")
            return
            
        # --- Tarjeta Resumen Recepción ---
        st.markdown("### 📋 Resumen de Recepción")
        recepcion_html = f"""<div style="background-color: #F5F5F5; border-left: 4px solid #E74C3C; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
<div style="font-size: 1.1em; font-weight: bold; color: #1A3A6B; margin-bottom: 5px;">
{ot.get('id', '-')} · {cliente.get('nombre', '-')}
</div>
<div style="margin-bottom: 5px;">
<strong>Equipo:</strong> {ot.get('maquina', '-')} — {ot.get('descripcion_trabajo', '-')}
</div>
<div style="margin-bottom: 5px;">
<strong>Ingreso:</strong> {formatear_fecha(ot.get('fecha_ingreso'))} · <strong>Entrega prevista:</strong> {formatear_fecha(ot.get('fecha_entrega_prevista'))}
</div>
<div>
<strong>Estado pieza:</strong> {recepcion.get('estado_pieza', '-')} | <strong>Falla reportada:</strong> {recepcion.get('causa_falla', '-')}
</div>
</div>"""
        st.markdown(recepcion_html, unsafe_allow_html=True)
        
        # --- Historial ---
        try:
            resp_hist = httpx.get(f"{url_api}/ot/{ot_id_seleccionada}/historial", timeout=10)
            historial = resp_hist.json().get("historial", []) if resp_hist.status_code == 200 else []
        except Exception:
            historial = []
            
        if historial:
            with st.expander("📜 Ver historial del cliente (Últimas OTs)"):
                for ot_hist in historial[:3]:
                    st.markdown(f"- **{ot_hist['id']}** ({formatear_fecha(ot_hist.get('fecha_ingreso'))}) | {ot_hist.get('maquina', '-')} | Estado: {ot_hist.get('estado', '-')}")

        # --- Formulario de diagnóstico ---
        st.markdown("### 📝 Formulario de Diagnóstico")
        
        c1, c2 = st.columns(2)
        with c1:
            factibilidad = st.radio("¿Es factible la reparación?", ["Sí", "No"], horizontal=True)
            tipo_falla = st.selectbox(
                "Tipo de falla detectada",
                [""] + TIPOS_FALLA,
                format_func=lambda x: x.capitalize() if x else "Seleccionar..."
            )
            dimensiones = st.text_area(
                "Dimensiones relevadas",
                placeholder="Ej: Diámetro exterior: 120mm, Largo: 500mm",
                height=100
            )
            
        with c2:
            conclusion = st.selectbox(
                "Conclusión del diagnóstico *",
                [""] + CONCLUSIONES_DIAGNOSTICO,
                format_func=lambda x: x.replace("_", " ") if x else "Seleccionar..."
            )
            tecnico_responsable = st.text_input("Técnico responsable *", placeholder="Nombre del técnico")
            antecedente_ot = st.text_input("OT antecedente (si existe)", placeholder="Ej: OT-2025-042")
            
        notas = st.text_area("Notas técnicas adicionales", placeholder="Observaciones extras del técnico...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Guardar Diagnóstico", type="primary", use_container_width=True):
            errores = []
            if not conclusion:
                errores.append("Seleccioná la conclusión del diagnóstico")
            if not tecnico_responsable:
                errores.append("Ingresá el técnico responsable")
                
            if errores:
                for error in errores:
                    st.warning(f"⚠️ {error}")
                return
                
            with st.spinner("Guardando diagnóstico..."):
                try:
                    datos_diagnostico = {
                        "ot_id": ot_id_seleccionada,
                        "dimensiones": dimensiones or None,
                        "factibilidad": factibilidad == "Sí",
                        "tipo_falla": tipo_falla or None,
                        "conclusion": conclusion,
                        "antecedente_ot": antecedente_ot or None,
                        "tecnico_responsable": tecnico_responsable,
                        "notas": notas or None,
                    }
                    
                    respuesta = httpx.post(f"{url_api}/ot/{ot_id_seleccionada}/diagnostico", json=datos_diagnostico, timeout=15)
                    respuesta.raise_for_status()
                    
                    st.success(f"✅ Diagnóstico guardado para OT **{ot_id_seleccionada}**")
                    st.info("La OT pasó a estado **EN_PROCESO** y etapa **Cotizando**.")
                    st.rerun()
                    
                except httpx.HTTPStatusError as e:
                    detalle = e.response.json().get("detail", str(e))
                    st.error(f"❌ Error: {detalle}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {str(e)}")


if __name__ == "__main__":
    mostrar_pagina()
