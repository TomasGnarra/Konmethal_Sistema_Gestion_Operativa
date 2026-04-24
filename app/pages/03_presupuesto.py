"""
Módulo 03 — Presupuesto.
Armado de presupuestos con ítems de mano de obra, materiales, servicios de terceros.
Flujo de aprobación: BORRADOR → APROBADO_INTERNO → ENVIADO (con PDF).
"""

import streamlit as st
import httpx

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import formatear_moneda, calcular_total_presupuesto
from app.components.sidebar import render_sidebar
from app.components.estado_badge import badge_estado


def renderizar_resumen(ot_id, pres_existente):
    """Renderiza el ticket de resumen a la derecha."""
    suma_mo = sum(i["subtotal"] for i in st.session_state.items_mo)
    suma_mat = sum(i["subtotal"] for i in st.session_state.items_mat)
    suma_serv = sum(i["monto"] for i in st.session_state.items_serv)
    
    otros_gastos = st.session_state.get("form_otros_gastos", pres_existente.get("otros_gastos", 0.0) if pres_existente else 0.0)
    pct_ganancia = st.session_state.get("form_pct_ganancia", pres_existente.get("porcentaje_ganancia", 30.0) if pres_existente else 30.0)
    
    tc, tv = calcular_total_presupuesto(
        st.session_state.items_mo,
        st.session_state.items_mat,
        st.session_state.items_serv,
        otros_gastos,
        pct_ganancia
    )
    
    ganancia_neta = tc * (pct_ganancia / 100)
    
    st.markdown("### 📋 Resumen Económico")
    
    if pres_existente:
        st.markdown(f"**Estado:** {badge_estado(pres_existente.get('estado', 'BORRADOR'))}", unsafe_allow_html=True)
    else:
        st.markdown(f"**Estado:** {badge_estado('NUEVO')}", unsafe_allow_html=True)
        
    html_ticket = f"""
    <div style="background-color: #F5F5F5; border-top: 4px solid #1A3A6B; border-bottom: 4px solid #1A3A6B; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 1.1em; color: #1C1C1C;">
        <div style="display: flex; justify-content: space-between;"><span>Mano de obra:</span> <span>{formatear_moneda(suma_mo)}</span></div>
        <div style="display: flex; justify-content: space-between;"><span>Materiales:</span> <span>{formatear_moneda(suma_mat)}</span></div>
        <div style="display: flex; justify-content: space-between;"><span>Servicios:</span> <span>{formatear_moneda(suma_serv)}</span></div>
        <div style="display: flex; justify-content: space-between;"><span>Otros gastos:</span> <span>{formatear_moneda(otros_gastos)}</span></div>
        <hr style="border-top: 1px dashed #4A4A4A; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between;"><strong>COSTO TOTAL:</strong> <strong>{formatear_moneda(tc)}</strong></div>
        <div style="display: flex; justify-content: space-between;"><span>Ganancia {pct_ganancia}%:</span> <span>{formatear_moneda(ganancia_neta)}</span></div>
        <hr style="border-top: 1px solid #1A3A6B; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; font-size: 1.2M; font-weight: bold; color: #27AE60;"><span>PRECIO VENTA:</span> <span>{formatear_moneda(tv)}</span></div>
    </div>
    """
    st.markdown(html_ticket, unsafe_allow_html=True)
    return tc, tv


def mostrar_pagina():
    """Página principal de presupuesto."""
    render_sidebar()
    st.header("📋 Presupuesto")
    st.markdown("Armá el presupuesto para una OT. El resumen económico se actualizará al agregar ítems.")
    st.divider()
    
    url_api = obtener_url_api()
    
    # --- Inicializar session_state ---
    if "items_mo" not in st.session_state:
        st.session_state.items_mo = []
    if "items_mat" not in st.session_state:
        st.session_state.items_mat = []
    if "items_serv" not in st.session_state:
        st.session_state.items_serv = []
    
    # --- Cargar OTs en proceso ---
    try:
        respuesta = httpx.get(f"{url_api}/ot/", params={"estado": "EN_PROCESO"}, timeout=10)
        respuesta.raise_for_status()
        ots = respuesta.json().get("ordenes_trabajo", [])
    except Exception as e:
        st.error(f"Error al cargar OTs: {str(e)}")
        ots = []
    
    if not ots:
        st.info("📭 No hay OTs en proceso que necesiten presupuesto.")
        return
    
    # --- Selector de OT ---
    opciones_ot = {f"{ot['id']} — {ot.get('maquina', 'Sin equipo')}": ot["id"] for ot in ots}
    ot_seleccionada = st.selectbox("Seleccionar Orden de Trabajo", [""] + list(opciones_ot.keys()), index=0)
    
    if not ot_seleccionada:
        return
    
    ot_id = opciones_ot[ot_seleccionada]
    
    # --- Verificar si ya existe presupuesto ---
    presupuesto_existente = None
    try:
        resp = httpx.get(f"{url_api}/presupuesto/{ot_id}", timeout=10)
        if resp.status_code == 200:
            presupuesto_existente = resp.json().get("presupuesto")
    except Exception:
        pass
        
    # Cambio centralizado para resetear items si cambió de OT
    if st.session_state.get("ot_actual") != ot_id:
        st.session_state.ot_actual = ot_id
        if presupuesto_existente:
            st.session_state.items_mo = presupuesto_existente.get("items_mano_obra", [])
            st.session_state.items_mat = presupuesto_existente.get("items_materiales", [])
            st.session_state.items_serv = presupuesto_existente.get("items_servicios", [])
            st.session_state.form_otros_gastos = presupuesto_existente.get("otros_gastos", 0.0)
            st.session_state.form_pct_ganancia = presupuesto_existente.get("porcentaje_ganancia", 30.0)
        else:
            st.session_state.items_mo = []
            st.session_state.items_mat = []
            st.session_state.items_serv = []
            st.session_state.form_otros_gastos = 0.0
            st.session_state.form_pct_ganancia = 30.0
            
    if presupuesto_existente and presupuesto_existente.get("estado") == "ENVIADO":
        st.success("✅ El presupuesto ya fue enviado al cliente.")
        if presupuesto_existente.get("pdf_url"):
            st.markdown(f"📎 [Descargar PDF]({presupuesto_existente['pdf_url']})")
        return
    
    # --- Cargar catálogos ---
    categorias_mo = []
    insumos = []
    try:
        resp_cat = httpx.get(f"{url_api}/presupuesto/catalogos/mano-obra", timeout=10)
        if resp_cat.status_code == 200:
            categorias_mo = resp_cat.json().get("categorias", [])
    except Exception:
        pass
    
    try:
        resp_ins = httpx.get(f"{url_api}/presupuesto/catalogos/insumos", timeout=10)
        if resp_ins.status_code == 200:
            insumos = resp_ins.json().get("insumos", [])
    except Exception:
        pass
    
    st.divider()
    
    # --- LAYOUT DE DOS COLUMNAS ---
    col_izq, col_der = st.columns([2, 1], gap="large")
    
    with col_der:
        tc, tv = renderizar_resumen(ot_id, presupuesto_existente)
        
        st.markdown("<br>", unsafe_allow_html=True)
        # --- BOTONES DE FLUJO ---
        st.markdown("#### ⚙️ Acciones")
        
        estado_actual = presupuesto_existente.get("estado") if presupuesto_existente else None
        
        btn_borrador = st.button("💾 Guardar Borrador", use_container_width=True)
        btn_aprobar = st.button(
            "✅ Aprobar Internamente", 
            use_container_width=True,
            disabled=not presupuesto_existente or estado_actual in ["APROBADO_INTERNO", "ENVIADO"]
        )
        btn_enviar = st.button(
            "📄 Generar PDF y Enviar", 
            kind="primary", 
            use_container_width=True,
            disabled=not presupuesto_existente or estado_actual != "APROBADO_INTERNO"
        )
        
        # Handlers
        if btn_borrador:
            with st.spinner("Guardando..."):
                datos = {
                    "ot_id": ot_id,
                    "items_mano_obra": st.session_state.items_mo,
                    "items_materiales": st.session_state.items_mat,
                    "items_servicios": st.session_state.items_serv,
                    "otros_gastos": st.session_state.get("form_otros_gastos", 0.0),
                    "porcentaje_ganancia": st.session_state.get("form_pct_ganancia", 30.0),
                    "total_costo": tc,
                    "total_venta": tv,
                }
                if presupuesto_existente:
                    httpx.patch(f"{url_api}/presupuesto/{presupuesto_existente['id']}", json=datos, timeout=15)
                else:
                    httpx.post(f"{url_api}/presupuesto/", json=datos, timeout=15)
                st.success("Guardado como BORRADOR")
                st.rerun()
                
        if btn_aprobar and presupuesto_existente:
            httpx.post(f"{url_api}/presupuesto/{presupuesto_existente['id']}/aprobar", timeout=10)
            st.success("Aprobado internamente")
            st.rerun()
            
        if btn_enviar and presupuesto_existente:
            resp = httpx.post(f"{url_api}/presupuesto/{presupuesto_existente['id']}/generar-pdf", params={"ot_id": ot_id}, timeout=30)
            if resp.headers.get("content-type", "").startswith("application/json"):
                st.success("Enviado (PDF subido)")
            else:
                st.download_button("📥 Descargar PDF generado", data=resp.content, file_name=f"presupuesto_{ot_id}.pdf", mime="application/pdf")
            st.rerun()

    
    with col_izq:
        # ==================================
        # MANO DE OBRA
        # ==================================
        st.subheader("👷 Mano de Obra")
        if categorias_mo:
            with st.container(border=True):
                opciones_cat = {f"{c['categoria']} — {c.get('descripcion', '')} (${c['costo_hora']}/h)": c for c in categorias_mo}
                c1, c2, c3 = st.columns([3, 1, 1])
                cat_seleccionada = c1.selectbox("Categoría", list(opciones_cat.keys()), key="cat_mo")
                horas_mo = c2.number_input("Horas", min_value=0.5, value=1.0, step=0.5, key="h_mo")
                c3.write("")
                c3.write("")
                if c3.button("➕ Agregar"):
                    cat = opciones_cat[cat_seleccionada]
                    st.session_state.items_mo.append({
                        "categoria_id": cat["id"], "categoria": cat["categoria"],
                        "descripcion": cat.get("descripcion", ""), "costo_hora": cat["costo_hora"],
                        "cantidad_horas": horas_mo, "subtotal": round(cat["costo_hora"] * horas_mo, 2),
                    })
                    st.rerun()
                    
        for i, item in enumerate(st.session_state.items_mo):
            st.markdown(f"**{item['categoria']}** — {item.get('descripcion', '')} | {item['cantidad_horas']}h × {formatear_moneda(item['costo_hora'])} = **{formatear_moneda(item['subtotal'])}**")
            if st.button("✕ Quitar", key=f"del_mo_{i}", help="Eliminar ítem"):
                st.session_state.items_mo.pop(i)
                st.rerun()

        st.divider()
        
        # ==================================
        # MATERIALES
        # ==================================
        st.subheader("🧱 Materiales e Insumos")
        if insumos:
            with st.container(border=True):
                # Búsqueda filtrada rápida
                busqueda = st.text_input("Buscar insumo...")
                insumos_filtrados = [ins for ins in insumos if busqueda.lower() in ins["denominacion"].lower()]
                
                opciones_ins = {f"{ins['denominacion']} ({ins.get('unidad', '-')}) — ${ins['costo_unitario']}": ins for ins in insumos_filtrados}
                
                c1, c2, c3 = st.columns([3, 1, 1])
                if opciones_ins:
                    ins_seleccionado = c1.selectbox("Material encontrado", list(opciones_ins.keys()), key="ins_mat")
                    cantidad_mat = c2.number_input("Cant.", min_value=0.1, value=1.0, step=0.5, key="c_mat")
                    c3.write("")
                    c3.write("")
                    if c3.button("➕ Agregar", key="btn_add_mat"):
                        ins = opciones_ins[ins_seleccionado]
                        st.session_state.items_mat.append({
                            "insumo_id": ins["id"], "denominacion": ins["denominacion"],
                            "unidad": ins.get("unidad", "-"), "costo_unitario": ins["costo_unitario"],
                            "cantidad": cantidad_mat, "subtotal": round(ins["costo_unitario"] * cantidad_mat, 2),
                        })
                        st.rerun()
                else:
                    st.warning("No se encontraron resultados.")
        
        for i, item in enumerate(st.session_state.items_mat):
            st.markdown(f"**{item['denominacion']}** | {item['cantidad']} × {formatear_moneda(item['costo_unitario'])} = **{formatear_moneda(item['subtotal'])}**")
            if st.button("✕ Quitar", key=f"del_mat_{i}"):
                st.session_state.items_mat.pop(i)
                st.rerun()

        st.divider()
        
        # ==================================
        # SERVICIOS
        # ==================================
        st.subheader("🤝 Servicios de Terceros")
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            desc_servicio = c1.text_input("Descripción", key="d_serv")
            monto_servicio = c2.number_input("Monto ($)", min_value=0.0, step=100.0, key="m_serv")
            c3.write("")
            c3.write("")
            if c3.button("➕ Agregar", key="btn_add_srv"):
                if desc_servicio and monto_servicio > 0:
                    st.session_state.items_serv.append({"descripcion": desc_servicio, "monto": monto_servicio})
                    st.rerun()
                    
        for i, item in enumerate(st.session_state.items_serv):
            st.markdown(f"**{item['descripcion']}** | Monto: **{formatear_moneda(item['monto'])}**")
            if st.button("✕ Quitar", key=f"del_serv_{i}"):
                st.session_state.items_serv.pop(i)
                st.rerun()

        st.divider()
        
        # ==================================
        # VARIABLES GLOBALES
        # ==================================
        st.subheader("📊 Variables Finales")
        c1, c2 = st.columns(2)
        
        # Usamos on_change o pasamos directo a session_state
        st.number_input(
            "Otros gastos (flete, envíos, etc.) $", 
            min_value=0.0, 
            step=100.0, 
            key="form_otros_gastos",
        )
        st.number_input(
            "% Ganancia", 
            min_value=0.0, max_value=200.0, step=5.0, 
            key="form_pct_ganancia"
        )
        

# --- Ejecutar página ---
if __name__ == "__main__":
    mostrar_pagina()

