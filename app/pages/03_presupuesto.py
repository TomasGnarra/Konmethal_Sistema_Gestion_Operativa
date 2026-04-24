"""
Módulo 03 — Presupuesto.
Armado de presupuestos con ítems de mano de obra, materiales, servicios de terceros.
Flujo de aprobación: BORRADOR → APROBADO_INTERNO → ENVIADO (con PDF).
"""

import streamlit as st
import httpx

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import formatear_moneda, calcular_total_presupuesto


def mostrar_pagina():
    """Página principal de presupuesto."""
    st.header("💰 Presupuesto")
    st.markdown("Armá el presupuesto para una OT con diagnóstico completo.")
    
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
    ot_seleccionada = st.selectbox("Seleccionar Orden de Trabajo", list(opciones_ot.keys()))
    
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
    
    if presupuesto_existente:
        estado_pres = presupuesto_existente.get("estado", "BORRADOR")
        st.info(f"📄 Esta OT ya tiene un presupuesto en estado **{estado_pres}**.")
        
        if estado_pres == "ENVIADO":
            st.success("✅ El presupuesto ya fue enviado al cliente.")
            if presupuesto_existente.get("pdf_url"):
                st.markdown(f"📎 [Descargar PDF]({presupuesto_existente['pdf_url']})")
            return
        
        # Cargar items existentes al session_state si no fueron cargados
        if not st.session_state.items_mo and presupuesto_existente.get("items_mano_obra"):
            st.session_state.items_mo = presupuesto_existente["items_mano_obra"]
        if not st.session_state.items_mat and presupuesto_existente.get("items_materiales"):
            st.session_state.items_mat = presupuesto_existente["items_materiales"]
        if not st.session_state.items_serv and presupuesto_existente.get("items_servicios"):
            st.session_state.items_serv = presupuesto_existente["items_servicios"]
    
    # --- Cargar catálogos ---
    categorias_mo = []
    insumos = []
    try:
        resp_cat = httpx.get(f"{url_api}/presupuesto/catalogos/mano-obra", timeout=10)
        if resp_cat.status_code == 200:
            categorias_mo = resp_cat.json().get("categorias", [])
    except Exception:
        st.warning("No se pudieron cargar las categorías de mano de obra.")
    
    try:
        resp_ins = httpx.get(f"{url_api}/presupuesto/catalogos/insumos", timeout=10)
        if resp_ins.status_code == 200:
            insumos = resp_ins.json().get("insumos", [])
    except Exception:
        st.warning("No se pudieron cargar los insumos.")
    
    st.divider()
    
    # =====================================================================
    # SECCIÓN: MANO DE OBRA
    # =====================================================================
    st.subheader("👷 Mano de Obra")
    
    if categorias_mo:
        with st.container(border=True):
            opciones_cat = {
                f"Cat. {c['categoria']} — {c.get('descripcion', '')} (${c['costo_hora']}/h)": c
                for c in categorias_mo
            }
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                cat_seleccionada = st.selectbox(
                    "Categoría",
                    list(opciones_cat.keys()),
                    key="cat_mo_select",
                )
            with col2:
                horas_mo = st.number_input("Horas", min_value=0.5, value=1.0, step=0.5, key="horas_mo")
            with col3:
                st.write("")
                st.write("")
                if st.button("➕ Agregar MO", key="btn_agregar_mo"):
                    cat = opciones_cat[cat_seleccionada]
                    item = {
                        "categoria_id": cat["id"],
                        "categoria": cat["categoria"],
                        "descripcion": cat.get("descripcion", ""),
                        "costo_hora": cat["costo_hora"],
                        "cantidad_horas": horas_mo,
                        "subtotal": round(cat["costo_hora"] * horas_mo, 2),
                    }
                    st.session_state.items_mo.append(item)
                    st.rerun()
    
    # Mostrar items de MO
    if st.session_state.items_mo:
        for i, item in enumerate(st.session_state.items_mo):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
            col1.write(f"Cat. {item['categoria']} — {item.get('descripcion', '')}")
            col2.write(f"{item['cantidad_horas']}h × {formatear_moneda(item['costo_hora'])}")
            col3.write(f"**{formatear_moneda(item['subtotal'])}**")
            if col4.button("🗑️", key=f"del_mo_{i}"):
                st.session_state.items_mo.pop(i)
                st.rerun()
    
    st.divider()
    
    # =====================================================================
    # SECCIÓN: MATERIALES
    # =====================================================================
    st.subheader("🧱 Materiales e Insumos")
    
    if insumos:
        with st.container(border=True):
            opciones_ins = {
                f"{ins['denominacion']} ({ins.get('unidad', '-')}) — ${ins['costo_unitario']}": ins
                for ins in insumos
            }
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                ins_seleccionado = st.selectbox(
                    "Insumo / Material",
                    list(opciones_ins.keys()),
                    key="ins_select",
                )
            with col2:
                cantidad_mat = st.number_input("Cantidad", min_value=0.1, value=1.0, step=0.5, key="cant_mat")
            with col3:
                st.write("")
                st.write("")
                if st.button("➕ Agregar Material", key="btn_agregar_mat"):
                    ins = opciones_ins[ins_seleccionado]
                    item = {
                        "insumo_id": ins["id"],
                        "denominacion": ins["denominacion"],
                        "unidad": ins.get("unidad", "-"),
                        "costo_unitario": ins["costo_unitario"],
                        "cantidad": cantidad_mat,
                        "subtotal": round(ins["costo_unitario"] * cantidad_mat, 2),
                    }
                    st.session_state.items_mat.append(item)
                    st.rerun()
    
    # Mostrar items de materiales
    if st.session_state.items_mat:
        for i, item in enumerate(st.session_state.items_mat):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 0.5])
            col1.write(f"{item['denominacion']} ({item.get('unidad', '-')})")
            col2.write(f"{item['cantidad']} × {formatear_moneda(item['costo_unitario'])}")
            col3.write(f"**{formatear_moneda(item['subtotal'])}**")
            if col4.button("🗑️", key=f"del_mat_{i}"):
                st.session_state.items_mat.pop(i)
                st.rerun()
    
    st.divider()
    
    # =====================================================================
    # SECCIÓN: SERVICIOS DE TERCEROS
    # =====================================================================
    st.subheader("🤝 Servicios de Terceros")
    
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            desc_servicio = st.text_input("Descripción del servicio", key="desc_serv")
        with col2:
            monto_servicio = st.number_input("Monto ($)", min_value=0.0, value=0.0, step=100.0, key="monto_serv")
        with col3:
            st.write("")
            st.write("")
            if st.button("➕ Agregar Servicio", key="btn_agregar_serv"):
                if desc_servicio and monto_servicio > 0:
                    item = {
                        "descripcion": desc_servicio,
                        "monto": monto_servicio,
                    }
                    st.session_state.items_serv.append(item)
                    st.rerun()
    
    # Mostrar items de servicios
    if st.session_state.items_serv:
        for i, item in enumerate(st.session_state.items_serv):
            col1, col2, col3 = st.columns([3, 1, 0.5])
            col1.write(item["descripcion"])
            col2.write(f"**{formatear_moneda(item['monto'])}**")
            if col3.button("🗑️", key=f"del_serv_{i}"):
                st.session_state.items_serv.pop(i)
                st.rerun()
    
    st.divider()
    
    # =====================================================================
    # OTROS GASTOS Y GANANCIA
    # =====================================================================
    st.subheader("📊 Totales")
    
    col1, col2 = st.columns(2)
    with col1:
        otros_gastos = st.number_input(
            "Otros gastos (flete, envíos, etc.) $",
            min_value=0.0,
            value=presupuesto_existente.get("otros_gastos", 0.0) if presupuesto_existente else 0.0,
            step=100.0,
        )
    with col2:
        porcentaje_ganancia = st.number_input(
            "% Ganancia",
            min_value=0.0,
            max_value=200.0,
            value=presupuesto_existente.get("porcentaje_ganancia", 30.0) if presupuesto_existente else 30.0,
            step=5.0,
        )
    
    # Calcular totales
    total_costo, total_venta = calcular_total_presupuesto(
        st.session_state.items_mo,
        st.session_state.items_mat,
        st.session_state.items_serv,
        otros_gastos,
        porcentaje_ganancia,
    )
    
    # Resumen
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Costo", formatear_moneda(total_costo))
        with col2:
            st.metric("Total Venta", formatear_moneda(total_venta))
    
    st.divider()
    
    # =====================================================================
    # BOTONES DE ACCIÓN
    # =====================================================================
    col1, col2, col3 = st.columns(3)
    
    with col1:
        guardar_borrador = st.button("💾 Guardar Borrador", use_container_width=True)
    with col2:
        aprobar = st.button(
            "✅ Aprobar Internamente",
            use_container_width=True,
            disabled=not presupuesto_existente,
        )
    with col3:
        generar_pdf = st.button(
            "📄 Generar PDF y Enviar",
            type="primary",
            use_container_width=True,
            disabled=not presupuesto_existente or (
                presupuesto_existente and presupuesto_existente.get("estado") not in ["APROBADO_INTERNO"]
            ),
        )
    
    # --- Guardar borrador ---
    if guardar_borrador:
        with st.spinner("Guardando borrador..."):
            try:
                datos = {
                    "ot_id": ot_id,
                    "items_mano_obra": st.session_state.items_mo,
                    "items_materiales": st.session_state.items_mat,
                    "items_servicios": st.session_state.items_serv,
                    "otros_gastos": otros_gastos,
                    "porcentaje_ganancia": porcentaje_ganancia,
                    "total_costo": total_costo,
                    "total_venta": total_venta,
                }
                
                if presupuesto_existente:
                    # Actualizar existente
                    resp = httpx.patch(
                        f"{url_api}/presupuesto/{presupuesto_existente['id']}",
                        json=datos,
                        timeout=15,
                    )
                else:
                    # Crear nuevo
                    resp = httpx.post(f"{url_api}/presupuesto/", json=datos, timeout=15)
                
                resp.raise_for_status()
                st.success("✅ Presupuesto guardado como BORRADOR")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # --- Aprobar internamente ---
    if aprobar and presupuesto_existente:
        with st.spinner("Aprobando presupuesto..."):
            try:
                resp = httpx.post(
                    f"{url_api}/presupuesto/{presupuesto_existente['id']}/aprobar",
                    timeout=10,
                )
                resp.raise_for_status()
                st.success("✅ Presupuesto aprobado internamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # --- Generar PDF ---
    if generar_pdf and presupuesto_existente:
        with st.spinner("Generando PDF..."):
            try:
                resp = httpx.post(
                    f"{url_api}/presupuesto/{presupuesto_existente['id']}/generar-pdf",
                    params={"ot_id": ot_id},
                    timeout=30,
                )
                resp.raise_for_status()
                
                # Si retornó JSON con URL
                if resp.headers.get("content-type", "").startswith("application/json"):
                    resultado = resp.json()
                    st.success(f"✅ PDF generado y presupuesto marcado como ENVIADO")
                    if resultado.get("pdf_url"):
                        st.markdown(f"📎 [Descargar PDF]({resultado['pdf_url']})")
                else:
                    # Retornó el PDF directamente
                    st.success("✅ PDF generado")
                    st.download_button(
                        "📥 Descargar PDF",
                        data=resp.content,
                        file_name=f"presupuesto_{ot_id}.pdf",
                        mime="application/pdf",
                    )
                
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


# --- Ejecutar página ---
mostrar_pagina()
