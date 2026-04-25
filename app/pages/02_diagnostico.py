"""
Módulo 02 — Diagnóstico Técnico.
Permite al técnico registrar el diagnóstico detallado y realizar
la estimación de horas, materiales y servicios.
"""

import streamlit as st
import httpx
import json
from datetime import date

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import (
    formatear_fecha, formatear_moneda,
    TIPOS_FALLA, CONCLUSIONES_DIAGNOSTICO,
)
from app.components.sidebar import render_sidebar
from app.components.estado_badge import badge_estado


def mostrar_pagina():
    """Página principal de diagnóstico técnico."""
    render_sidebar()
    st.header("🔍 Diagnóstico Técnico y Estimación")
    st.markdown("Revisión técnica, validaciones, horas estimadas e insumos para el Presupuesto.")
    st.divider()
    
    url_api = obtener_url_api()
    
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
        
    col_lista, col_detalle = st.columns([1, 2], gap="large")
    
    with col_lista:
        st.subheader("OTs Pendientes")
        opciones_ot = []
        for ot in ots:
            f_ing = ot.get('fecha_ingreso')
            ingreso_dt = date.fromisoformat(f_ing) if f_ing else date.today()
            dias_ingreso = (date.today() - ingreso_dt).days
            alerta = " ⚠️" if dias_ingreso > 5 else ""
            cliente_nombre = ot.get('cliente', {}).get('nombre', '-') if ot.get('cliente') else '-'
            label = f"{ot['id']} | {cliente_nombre} | {ot.get('maquina', '-')} ({dias_ingreso}d){alerta}"
            opciones_ot.append({"id": ot["id"], "label": label})
            
        selec_label = st.radio("Seleccioná la OT a diagnosticar:", [o["label"] for o in opciones_ot], label_visibility="collapsed")
        ot_id_seleccionada = next(o["id"] for o in opciones_ot if o["label"] == selec_label)

    # Inicializar estado para estimaciones de la OT actual
    if st.session_state.get("diag_ot_actual") != ot_id_seleccionada:
        st.session_state.diag_ot_actual = ot_id_seleccionada
        st.session_state.diag_items_mo = []
        st.session_state.diag_items_mat = []
        st.session_state.diag_items_serv = []
        
    # Cargar catálogos
    categorias_mo = []
    insumos = []
    try:
        categorias_mo = httpx.get(f"{url_api}/presupuesto/catalogos/mano-obra", timeout=10).json().get("categorias", [])
        insumos = httpx.get(f"{url_api}/presupuesto/catalogos/insumos", timeout=10).json().get("insumos", [])
    except Exception:
        pass
        
    with col_detalle:
        try:
            resp_ot = httpx.get(f"{url_api}/ot/{ot_id_seleccionada}", timeout=10)
            resp_ot.raise_for_status()
            datos_ot = resp_ot.json()
            ot = datos_ot.get("ot", {})
            recepcion = datos_ot.get("recepcion", {})
            cliente = datos_ot.get("cliente", {})
        except Exception as e:
            st.error(f"Error al cargar datos: {str(e)}")
            return
            
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
        
        try:
            resp_hist = httpx.get(f"{url_api}/ot/{ot_id_seleccionada}/historial", timeout=10)
            historial = resp_hist.json().get("historial", []) if resp_hist.status_code == 200 else []
        except Exception:
            historial = []
            
        if historial:
            with st.expander("📜 Ver historial del cliente (Últimas OTs)"):
                for ot_hist in historial[:3]:
                    st.markdown(f"- **{ot_hist['id']}** ({formatear_fecha(ot_hist.get('fecha_ingreso'))}) | {ot_hist.get('maquina', '-')} | Estado: {ot_hist.get('estado', '-')}")

        st.markdown("### 📝 Formulario de Diagnóstico")
        
        c1, c2 = st.columns(2)
        with c1:
            factibilidad = st.radio("¿Es factible la reparación?", ["Sí", "No"], horizontal=True)
            tipo_falla = st.selectbox("Tipo de falla principal", [""] + TIPOS_FALLA, format_func=lambda x: x.capitalize() if x else "Seleccionar...")
            dimensiones = st.text_area("Dimensiones relevadas", placeholder="Ej: Diámetro ext: 120mm, Largo: 500mm", height=68)
            
        with c2:
            conclusion = st.selectbox("Conclusión del diagnóstico *", [""] + CONCLUSIONES_DIAGNOSTICO, format_func=lambda x: x.replace("_", " ") if x else "Seleccionar...")
            tecnico_responsable = st.text_input("Técnico responsable *", placeholder="Nombre del técnico")
            antecedente_ot = st.text_input("OT antecedente (si existe)", placeholder="Ej: OT-2025-042")
            
        # Detalles avanzados
        with st.expander("🔬 Especificaciones de Falla y Recuperación (Según Formulario)"):
            c_det1, c_det2 = st.columns(2)
            esfuerzo = c_det1.selectbox("Esfuerzo dominante", ["", "Tracción", "Compresión", "Flexión", "Torsión", "Impacto"])
            naturaleza = c_det2.selectbox("Naturaleza de falla", ["", "Fatiga", "Rotura Frágil", "Impacto", "Concentración de tensiones", "Falla Térmica", "Corrosión/Erosión"])
            requiere_end = st.multiselect("Ensayos No Destructivos (END) requeridos", ["Líquidos Penetrantes", "Partículas Magnetizables", "Ultrasonido"])
            requiere_tt = st.checkbox("Requiere Tratamiento Térmico (Precalentamiento/Alivio)")

        notas = st.text_area("Notas técnicas adicionales", placeholder="Observaciones extras...")
        
        st.divider()
        st.markdown("### 🛠️ Estimación de Trabajos e Insumos")
        
        tab_mo, tab_mat, tab_serv = st.tabs(["👷 Mano de Obra", "🧱 Insumos", "🤝 Servicios Ext."])
        
        with tab_mo:
            if categorias_mo:
                opc_mo = {f"{c['categoria']} (${c['costo_hora']}/h)": c for c in categorias_mo}
                cc1, cc2, cc3 = st.columns([3, 1, 1])
                cat_sel = cc1.selectbox("Categoría", list(opc_mo.keys()), key="d_cat_mo")
                horas_mo = cc2.number_input("Horas", min_value=0.5, value=1.0, step=0.5, key="d_h_mo")
                cc3.write("")
                cc3.write("")
                if cc3.button("➕ Agregar", key="btn_d_mo"):
                    cat = opc_mo[cat_sel]
                    st.session_state.diag_items_mo.append({
                        "categoria_id": cat["id"], "categoria": cat["categoria"],
                        "descripcion": cat.get("descripcion", ""), "costo_hora": cat["costo_hora"],
                        "cantidad_horas": horas_mo, "subtotal": round(cat["costo_hora"] * horas_mo, 2),
                    })
                    st.rerun()
                    
            for i, item in enumerate(st.session_state.diag_items_mo):
                st.markdown(f"**{item['categoria']}** | {item['cantidad_horas']}h × {formatear_moneda(item['costo_hora'])} = **{formatear_moneda(item['subtotal'])}**")
                if st.button("✕ Quitar", key=f"d_del_mo_{i}"):
                    st.session_state.diag_items_mo.pop(i)
                    st.rerun()
                    
        with tab_mat:
            if insumos:
                busqueda = st.text_input("Buscar insumo...")
                ins_fil = [ins for ins in insumos if busqueda.lower() in ins["denominacion"].lower()]
                opc_ins = {f"{ins['denominacion']} — ${ins['costo_unitario']}": ins for ins in ins_fil}
                cc1, cc2, cc3 = st.columns([3, 1, 1])
                if opc_ins:
                    ins_sel = cc1.selectbox("Insumo", list(opc_ins.keys()), key="d_ins")
                    cant_mat = cc2.number_input("Cant.", min_value=0.1, value=1.0, step=0.5, key="d_c_mat")
                    cc3.write("")
                    cc3.write("")
                    if cc3.button("➕ Agregar", key="btn_d_mat"):
                        ins = opc_ins[ins_sel]
                        st.session_state.diag_items_mat.append({
                            "insumo_id": ins["id"], "denominacion": ins["denominacion"],
                            "unidad": ins.get("unidad", "-"), "costo_unitario": ins["costo_unitario"],
                            "cantidad": cant_mat, "subtotal": round(ins["costo_unitario"] * cant_mat, 2),
                        })
                        st.rerun()
                        
            for i, item in enumerate(st.session_state.diag_items_mat):
                st.markdown(f"**{item['denominacion']}** | {item['cantidad']} × {formatear_moneda(item['costo_unitario'])} = **{formatear_moneda(item['subtotal'])}**")
                if st.button("✕ Quitar", key=f"d_del_mat_{i}"):
                    st.session_state.diag_items_mat.pop(i)
                    st.rerun()
                    
        with tab_serv:
            cc1, cc2, cc3 = st.columns([3, 1, 1])
            desc_srv = cc1.text_input("Descripción", key="d_desc_srv")
            monto_srv = cc2.number_input("Monto Estimado ($)", min_value=0.0, step=100.0, key="d_m_srv")
            cc3.write("")
            cc3.write("")
            if cc3.button("➕ Agregar", key="btn_d_srv"):
                if desc_srv and monto_srv > 0:
                    st.session_state.diag_items_serv.append({"descripcion": desc_srv, "monto": monto_srv})
                    st.rerun()
                    
            for i, item in enumerate(st.session_state.diag_items_serv):
                st.markdown(f"**{item['descripcion']}** | Monto: **{formatear_moneda(item['monto'])}**")
                if st.button("✕ Quitar", key=f"d_del_srv_{i}"):
                    st.session_state.diag_items_serv.pop(i)
                    st.rerun()
                    
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Finalizar Diagnóstico y Estimación", type="primary", use_container_width=True):
            errores = []
            if not conclusion:
                errores.append("Seleccioná la conclusión del diagnóstico")
            if not tecnico_responsable:
                errores.append("Ingresá el técnico responsable")
                
            if errores:
                for error in errores:
                    st.warning(f"⚠️ {error}")
                return
                
            with st.spinner("Guardando diagnóstico y presupuesto..."):
                try:
                    # Preparar JSON de detalles extra en notas
                    detalles_tecnicos = {
                        "esfuerzo_dominante": esfuerzo,
                        "naturaleza_falla": naturaleza,
                        "requiere_end": requiere_end,
                        "requiere_tratamiento_termico": requiere_tt,
                        "notas_adicionales": notas
                    }
                    
                    datos_diagnostico = {
                        "ot_id": ot_id_seleccionada,
                        "dimensiones": dimensiones or None,
                        "factibilidad": factibilidad == "Sí",
                        "tipo_falla": tipo_falla or None,
                        "conclusion": conclusion,
                        "antecedente_ot": antecedente_ot or None,
                        "tecnico_responsable": tecnico_responsable,
                        "notas": json.dumps(detalles_tecnicos, ensure_ascii=False),
                    }
                    
                    # Guardar diagnóstico
                    httpx.post(f"{url_api}/ot/{ot_id_seleccionada}/diagnostico", json=datos_diagnostico, timeout=15).raise_for_status()
                    
                    # Armar presupuesto
                    tc = sum(i["subtotal"] for i in st.session_state.diag_items_mo) + \
                         sum(i["subtotal"] for i in st.session_state.diag_items_mat) + \
                         sum(i["monto"] for i in st.session_state.diag_items_serv)
                         
                    datos_presupuesto = {
                        "ot_id": ot_id_seleccionada,
                        "items_mano_obra": st.session_state.diag_items_mo,
                        "items_materiales": st.session_state.diag_items_mat,
                        "items_servicios": st.session_state.diag_items_serv,
                        "otros_gastos": 0.0,
                        "porcentaje_ganancia": 0.0,
                        "total_costo": tc,
                        "total_venta": 0.0,
                    }
                    
                    # Intentar actualizar o crear
                    resp_pres_exist = httpx.get(f"{url_api}/presupuesto/{ot_id_seleccionada}", timeout=10)
                    if resp_pres_exist.status_code == 200:
                        pres_id = resp_pres_exist.json().get("presupuesto", {}).get("id")
                        if pres_id:
                            httpx.patch(f"{url_api}/presupuesto/{pres_id}", json=datos_presupuesto, timeout=15)
                    else:
                        httpx.post(f"{url_api}/presupuesto/", json=datos_presupuesto, timeout=15)
                    
                    st.success(f"✅ Diagnóstico y estimación guardados para OT **{ot_id_seleccionada}**")
                    st.info("La OT está lista para Presupuestar.")
                    st.rerun()
                    
                except httpx.HTTPStatusError as e:
                    detalle = e.response.json().get("detail", str(e))
                    st.error(f"❌ Error: {detalle}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {str(e)}")


if __name__ == "__main__":
    mostrar_pagina()
