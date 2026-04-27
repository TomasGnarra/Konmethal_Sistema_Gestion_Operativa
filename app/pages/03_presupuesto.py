"""
Módulo 03 — Presupuesto (Panel General).
Vista de tabla con todas las OTs y sus presupuestos.
Permite ver, crear y editar presupuestos desde un panel centralizado.
"""

import streamlit as st
import httpx
import json

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import (
    formatear_moneda, formatear_fecha,
    calcular_resumen_presupuesto,
    obtener_info_estado_presupuesto
)
from app.components.sidebar import render_sidebar
from app.components.estado_badge import badge_estado


# =============================================================================
# FUNCIONES AUXILIARES DE RENDERIZADO
# =============================================================================

def renderizar_flujo_estados(estado_actual):
    """Renderiza el indicador visual de flujo de estados del presupuesto."""
    estados_flujo = [
        {"nombre": "Borrador", "key": "BORRADOR", "icono": "📝"},
        {"nombre": "Aprobado", "key": "APROBADO_INTERNO", "icono": "✅"},
        {"nombre": "Enviado", "key": "ENVIADO", "icono": "📤"},
        {"nombre": "Respuesta", "key": ["ACEPTADO", "RECHAZADO"], "icono": "📞"}
    ]

    cols = st.columns(len(estados_flujo))

    for idx, estado_info in enumerate(estados_flujo):
        with cols[idx]:
            # Determinar si este estado está completado
            if isinstance(estado_info["key"], list):
                completado = estado_actual in estado_info["key"]
                actual = estado_actual in estado_info["key"]
            else:
                # Lógica de flujo lineal
                if estado_actual is None:
                    completado = False
                    actual = False
                elif estado_info["key"] == "BORRADOR":
                    completado = estado_actual in ["BORRADOR", "APROBADO_INTERNO", "ENVIADO", "ACEPTADO", "RECHAZADO"]
                    actual = estado_actual == "BORRADOR"
                elif estado_info["key"] == "APROBADO_INTERNO":
                    completado = estado_actual in ["APROBADO_INTERNO", "ENVIADO", "ACEPTADO", "RECHAZADO"]
                    actual = estado_actual == "APROBADO_INTERNO"
                elif estado_info["key"] == "ENVIADO":
                    completado = estado_actual in ["ENVIADO", "ACEPTADO", "RECHAZADO"]
                    actual = estado_actual == "ENVIADO"
                else:
                    completado = False
                    actual = False

            # Color según estado
            if completado:
                color = "#27AE60"  # Verde
                opacity = "1.0"
            elif actual:
                color = "#3498DB"  # Azul
                opacity = "1.0"
            else:
                color = "#95A5A6"  # Gris
                opacity = "0.4"

            st.markdown(
                f"<div style='text-align: center; opacity: {opacity};'>"
                f"<div style='font-size: 2em;'>{estado_info['icono']}</div>"
                f"<div style='font-size: 0.9em; color: {color}; font-weight: bold;'>{estado_info['nombre']}</div>"
                f"</div>",
                unsafe_allow_html=True
            )


def renderizar_resumen_economico(presupuesto, items_mo, items_mat, items_serv, otros_gastos, pct_ganancia):
    """Renderiza el panel de resumen económico."""
    st.markdown("### 💰 Resumen Económico")

    resumen = calcular_resumen_presupuesto(
        items_mo, items_mat, items_serv, otros_gastos, pct_ganancia
    )
    total_costo = resumen["total_costo"]
    total_venta = resumen["total_venta"]
    suma_mo = resumen["total_mano_obra"]
    suma_mat = resumen["total_materiales"]
    suma_serv = resumen["total_servicios"]
    ganancia_neta = resumen["ganancia"]

    html_ticket = f"""<div style="background-color: #F5F5F5; border-top: 4px solid #1A3A6B; border-bottom: 4px solid #1A3A6B; padding: 15px 18px; border-radius: 4px; font-family: monospace; font-size: 0.98em; line-height: 1.45; color: #1C1C1C;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;"><span style="flex: 1 1 auto;">Mano de obra:</span> <span style="flex: 0 0 auto; white-space: nowrap; text-align: right;">{formatear_moneda(suma_mo)}</span></div>
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;"><span style="flex: 1 1 auto;">Materiales:</span> <span style="flex: 0 0 auto; white-space: nowrap; text-align: right;">{formatear_moneda(suma_mat)}</span></div>
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;"><span style="flex: 1 1 auto;">Servicios:</span> <span style="flex: 0 0 auto; white-space: nowrap; text-align: right;">{formatear_moneda(suma_serv)}</span></div>
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;"><span style="flex: 1 1 auto;">Otros gastos:</span> <span style="flex: 0 0 auto; white-space: nowrap; text-align: right;">{formatear_moneda(otros_gastos)}</span></div>
<hr style="border-top: 1px dashed #4A4A4A; margin: 10px 0;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;"><strong style="flex: 1 1 auto;">COSTO TOTAL:</strong> <strong style="flex: 0 0 auto; white-space: nowrap; text-align: right;">{formatear_moneda(total_costo)}</strong></div>
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px;"><span style="flex: 1 1 auto;">Margen sobre MO ({pct_ganancia}%):</span> <span style="flex: 0 0 auto; white-space: nowrap; text-align: right;">{formatear_moneda(ganancia_neta)}</span></div>
<hr style="border-top: 1px solid #1A3A6B; margin: 10px 0;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; font-size: 1.08em; font-weight: bold; color: #27AE60;"><span style="flex: 1 1 auto;">PRECIO VENTA:</span> <span style="flex: 0 0 auto; white-space: nowrap; text-align: right;">{formatear_moneda(total_venta)}</span></div>
</div>"""
    st.markdown(html_ticket, unsafe_allow_html=True)

    return total_costo, total_venta


def renderizar_acciones_disponibles(estado_pres, presupuesto, ot_id, url_api, tc, tv, items_mo, items_mat, items_serv):
    """Renderiza los botones de acción según el estado."""
    st.markdown("### ⚙️ Acciones")

    info_estado = obtener_info_estado_presupuesto(estado_pres)

    # Guardar Borrador
    if estado_pres in [None, "BORRADOR"]:
        if st.button("💾 Guardar Borrador", use_container_width=True, key=f"guardar_{ot_id}"):
            with st.spinner("Guardando..."):
                try:
                    datos = {
                        "ot_id": ot_id,
                        "items_mano_obra": items_mo,
                        "items_materiales": items_mat,
                        "items_servicios": items_serv,
                        "otros_gastos": st.session_state.get(f"form_otros_gastos_{ot_id}", 0.0),
                        "porcentaje_ganancia": st.session_state.get(f"form_pct_ganancia_{ot_id}", 30.0),
                        "total_costo": tc,
                        "total_venta": tv,
                    }
                    if presupuesto:
                        httpx.patch(f"{url_api}/presupuesto/{presupuesto['id']}", json=datos, timeout=15)
                        st.success("✅ Cambios guardados")
                    else:
                        httpx.post(f"{url_api}/presupuesto/", json=datos, timeout=15)
                        st.success("✅ Presupuesto creado como BORRADOR")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Aprobar Internamente
    if estado_pres == "BORRADOR":
        if st.button("✅ Aprobar Internamente", use_container_width=True, key=f"aprobar_{ot_id}"):
            try:
                httpx.post(f"{url_api}/presupuesto/{presupuesto['id']}/aprobar", timeout=10)
                st.success("✅ Presupuesto aprobado internamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Volver a Borrador
    if estado_pres == "APROBADO_INTERNO":
        if st.button("⬅️ Volver a Borrador", use_container_width=True, key=f"volver_{ot_id}"):
            try:
                datos = {"estado": "BORRADOR"}
                httpx.patch(f"{url_api}/presupuesto/{presupuesto['id']}", json=datos, timeout=10)
                st.success("✅ Presupuesto vuelto a BORRADOR")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # Generar PDF y Enviar
    if estado_pres == "APROBADO_INTERNO":
        if st.button("📄 Generar PDF y Enviar", type="primary", use_container_width=True, key=f"pdf_{ot_id}"):
            with st.spinner("Generando PDF..."):
                try:
                    resp = httpx.post(f"{url_api}/presupuesto/{presupuesto['id']}/generar-pdf", params={"ot_id": ot_id}, timeout=30)
                    if resp.headers.get("content-type", "").startswith("application/json"):
                        st.success("✅ PDF generado y presupuesto enviado")
                        st.info("La OT pasó a estado ESPERANDO_APROBACION")
                    else:
                        st.download_button("📥 Descargar PDF", data=resp.content, file_name=f"presupuesto_{ot_id}.pdf", mime="application/pdf")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Descargar PDF (si existe)
    if presupuesto and presupuesto.get("pdf_url"):
        st.markdown(f"📎 [Descargar PDF]({presupuesto['pdf_url']})", unsafe_allow_html=True)


def renderizar_tab_ver_presupuesto(presupuesto, diagnostico_info):
    """Tab 1: Vista de presupuesto en modo lectura."""
    if not presupuesto:
        st.info("⚠️ Aún no se creó un presupuesto para esta OT.")
        return

    # Resumen del diagnóstico
    if diagnostico_info:
        st.markdown("#### 📋 Resumen del Diagnóstico")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**Falla:** {diagnostico_info.get('tipo_falla') or '-'}")
        c2.markdown(f"**Factibilidad:** {'Sí' if diagnostico_info.get('factibilidad') else 'No'}")
        c3.markdown(f"**Conclusión:** {(diagnostico_info.get('conclusion') or '-').replace('_', ' ')}")
        st.divider()

    # Ítems Mano de Obra
    st.markdown("#### 👷 Mano de Obra")
    items_mo = presupuesto.get("items_mano_obra", [])
    if items_mo:
        for item in items_mo:
            st.markdown(
                f"• **{item.get('categoria')}** — {item.get('descripcion', '')} | "
                f"{item.get('cantidad_horas', 0)}h × {formatear_moneda(item.get('costo_hora', 0))} = "
                f"**{formatear_moneda(item.get('subtotal', 0))}**"
            )
    else:
        st.caption("Sin ítems de mano de obra")

    st.divider()

    # Ítems Materiales
    st.markdown("#### 🧱 Materiales e Insumos")
    items_mat = presupuesto.get("items_materiales", [])
    if items_mat:
        for item in items_mat:
            st.markdown(
                f"• **{item.get('denominacion')}** | "
                f"{item.get('cantidad', 0)} {item.get('unidad', '')} × {formatear_moneda(item.get('costo_unitario', 0))} = "
                f"**{formatear_moneda(item.get('subtotal', 0))}**"
            )
    else:
        st.caption("Sin ítems de materiales")

    st.divider()

    # Servicios de Terceros
    st.markdown("#### 🤝 Servicios de Terceros")
    items_serv = presupuesto.get("items_servicios", [])
    if items_serv:
        for item in items_serv:
            st.markdown(f"• **{item.get('descripcion')}** | Monto: **{formatear_moneda(item.get('monto', 0))}**")
    else:
        st.caption("Sin servicios de terceros")


def renderizar_tab_editar(presupuesto, categorias_mo, insumos, ot_id, items_mo, items_mat, items_serv):
    """Tab 2: Formulario de edición del presupuesto."""
    st.markdown("#### ✏️ Editar Presupuesto")

    # Mano de Obra
    st.subheader("👷 Mano de Obra")
    if categorias_mo:
        with st.container(border=True):
            opciones_cat = {f"{c['categoria']} — {c.get('descripcion', '')} (${c['costo_hora']}/h)": c for c in categorias_mo}
            c1, c2, c3 = st.columns([3, 1, 1])
            cat_seleccionada = c1.selectbox("Categoría", list(opciones_cat.keys()), key=f"cat_mo_{ot_id}")
            horas_mo = c2.number_input("Horas", min_value=0.5, value=1.0, step=0.5, key=f"h_mo_{ot_id}")
            c3.write("")
            c3.write("")
            if c3.button("➕ Agregar", key=f"btn_add_mo_{ot_id}"):
                cat = opciones_cat[cat_seleccionada]
                items_mo.append({
                    "categoria_id": cat["id"], "categoria": cat["categoria"],
                    "descripcion": cat.get("descripcion", ""), "costo_hora": cat["costo_hora"],
                    "cantidad_horas": horas_mo, "subtotal": round(cat["costo_hora"] * horas_mo, 2),
                })
                st.session_state[f"items_mo_{ot_id}"] = items_mo
                st.rerun()

    for i, item in enumerate(items_mo):
        st.markdown(f"**{item['categoria']}** — {item.get('descripcion', '')} | {item['cantidad_horas']}h × {formatear_moneda(item['costo_hora'])} = **{formatear_moneda(item['subtotal'])}**")
        if st.button("✕ Quitar", key=f"del_mo_{i}_{ot_id}"):
            items_mo.pop(i)
            st.session_state[f"items_mo_{ot_id}"] = items_mo
            st.rerun()

    st.divider()

    # Materiales
    st.subheader("🧱 Materiales e Insumos")
    if insumos:
        with st.container(border=True):
            busqueda = st.text_input("Buscar insumo...", key=f"busq_mat_{ot_id}")
            insumos_filtrados = [ins for ins in insumos if busqueda.lower() in ins["denominacion"].lower()]
            opciones_ins = {f"{ins['denominacion']} ({ins.get('unidad', '-')}) — ${ins['costo_unitario']}": ins for ins in insumos_filtrados}

            c1, c2, c3 = st.columns([3, 1, 1])
            if opciones_ins:
                ins_seleccionado = c1.selectbox("Material", list(opciones_ins.keys()), key=f"ins_mat_{ot_id}")
                cantidad_mat = c2.number_input("Cant.", min_value=0.1, value=1.0, step=0.5, key=f"c_mat_{ot_id}")
                c3.write("")
                c3.write("")
                if c3.button("➕ Agregar", key=f"btn_add_mat_{ot_id}"):
                    ins = opciones_ins[ins_seleccionado]
                    items_mat.append({
                        "insumo_id": ins["id"], "denominacion": ins["denominacion"],
                        "unidad": ins.get("unidad", "-"), "costo_unitario": ins["costo_unitario"],
                        "cantidad": cantidad_mat, "subtotal": round(ins["costo_unitario"] * cantidad_mat, 2),
                    })
                    st.session_state[f"items_mat_{ot_id}"] = items_mat
                    st.rerun()
            else:
                st.warning("No se encontraron resultados")

    for i, item in enumerate(items_mat):
        st.markdown(f"**{item['denominacion']}** | {item['cantidad']} {item.get('unidad', '')} × {formatear_moneda(item['costo_unitario'])} = **{formatear_moneda(item['subtotal'])}**")
        if st.button("✕ Quitar", key=f"del_mat_{i}_{ot_id}"):
            items_mat.pop(i)
            st.session_state[f"items_mat_{ot_id}"] = items_mat
            st.rerun()

    st.divider()

    # Servicios
    st.subheader("🤝 Servicios de Terceros")
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1, 1])
        desc_servicio = c1.text_input("Descripción", key=f"d_serv_{ot_id}")
        monto_servicio = c2.number_input("Monto ($)", min_value=0.0, step=100.0, key=f"m_serv_{ot_id}")
        c3.write("")
        c3.write("")
        if c3.button("➕ Agregar", key=f"btn_add_srv_{ot_id}"):
            if desc_servicio and monto_servicio > 0:
                items_serv.append({"descripcion": desc_servicio, "monto": monto_servicio})
                st.session_state[f"items_serv_{ot_id}"] = items_serv
                st.rerun()

    for i, item in enumerate(items_serv):
        st.markdown(f"**{item['descripcion']}** | Monto: **{formatear_moneda(item['monto'])}**")
        if st.button("✕ Quitar", key=f"del_serv_{i}_{ot_id}"):
            items_serv.pop(i)
            st.session_state[f"items_serv_{ot_id}"] = items_serv
            st.rerun()

    st.divider()

    # Variables finales
    st.subheader("📊 Variables Finales")
    st.number_input("Otros gastos (flete, envíos, etc.) $", min_value=0.0, step=100.0, key=f"form_otros_gastos_{ot_id}")
    st.number_input("% Ganancia", min_value=0.0, max_value=200.0, step=5.0, key=f"form_pct_ganancia_{ot_id}")


def renderizar_tab_respuesta_cliente(presupuesto, url_api):
    """Tab 3: Formulario de respuesta del cliente."""
    if presupuesto.get("canal_comunicacion"):
        # Ya se registró la respuesta
        st.markdown("### 📞 Respuesta del Cliente (Registrada)")

        estado_respuesta = "ACEPTADO ✅" if presupuesto.get("estado") == "ACEPTADO" else "RECHAZADO ❌"
        st.markdown(f"**Estado:** {estado_respuesta}")
        st.markdown(f"**Canal:** {presupuesto.get('canal_comunicacion', '-').capitalize()}")
        st.markdown(f"**Fecha respuesta:** {formatear_fecha(presupuesto.get('fecha_respuesta_cliente'))}")

        if presupuesto.get("motivo_rechazo"):
            st.markdown(f"**Motivo rechazo:** {presupuesto.get('motivo_rechazo')}")

        if presupuesto.get("notas_respuesta"):
            st.markdown(f"**Notas:** {presupuesto.get('notas_respuesta')}")
    else:
        # Formulario para registrar respuesta
        st.markdown("### 📞 Registrar Respuesta del Cliente")
        st.info("El presupuesto fue enviado. Registrá la respuesta del cliente.")

        with st.form(f"form_respuesta_cliente_{presupuesto['id']}"):
            col1, col2 = st.columns(2)

            with col1:
                respuesta_cliente = st.radio(
                    "¿El cliente aceptó el presupuesto?",
                    ["Aceptado", "Rechazado"],
                    horizontal=True
                )

                canal = st.selectbox(
                    "Canal de comunicación *",
                    ["", "whatsapp", "email", "presencial", "telefono"],
                    format_func=lambda x: x.capitalize() if x else "Seleccionar..."
                )

            with col2:
                motivo_rechazo = st.text_area(
                    "Motivo de rechazo" + (" *" if respuesta_cliente == "Rechazado" else " (opcional)"),
                    placeholder="¿Por qué rechazó el cliente?",
                    disabled=(respuesta_cliente == "Aceptado")
                )

                notas_respuesta = st.text_input(
                    "Notas adicionales (opcional)",
                    placeholder="Comentarios extras..."
                )

            submit_respuesta = st.form_submit_button("✅ Confirmar Respuesta del Cliente", type="primary", use_container_width=True)

            if submit_respuesta:
                errores = []
                if not canal:
                    errores.append("Seleccioná el canal de comunicación")
                if respuesta_cliente == "Rechazado" and not motivo_rechazo:
                    errores.append("El motivo de rechazo es obligatorio")

                if errores:
                    for error in errores:
                        st.warning(f"⚠️ {error}")
                else:
                    with st.spinner("Registrando respuesta..."):
                        try:
                            datos_respuesta = {
                                "aceptado": (respuesta_cliente == "Aceptado"),
                                "canal_comunicacion": canal,
                                "motivo_rechazo": motivo_rechazo if respuesta_cliente == "Rechazado" else None,
                                "notas_respuesta": notas_respuesta or None,
                            }

                            resp = httpx.post(
                                f"{url_api}/presupuesto/{presupuesto['id']}/respuesta-cliente",
                                json=datos_respuesta,
                                timeout=15
                            )
                            resp.raise_for_status()

                            if respuesta_cliente == "Aceptado":
                                st.success("✅ Presupuesto ACEPTADO registrado")
                            else:
                                st.warning("❌ Presupuesto RECHAZADO registrado")

                            st.rerun()
                        except httpx.HTTPStatusError as e:
                            detalle = e.response.json().get("detail", str(e))
                            st.error(f"❌ Error: {detalle}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def mostrar_pagina():
    """Página principal de presupuesto con vista de panel general."""
    render_sidebar()
    st.header("📋 Presupuesto — Panel General")
    st.markdown("Vista centralizada de todas las OTs con sus presupuestos.")
    st.divider()

    url_api = obtener_url_api()

    # Filtros
    with st.expander("🔍 Filtros de Búsqueda", expanded=True):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            filtro_estado_ot = st.multiselect(
                "Estados de OT a mostrar",
                ["PENDIENTE", "EN_PROCESO", "ESPERANDO_APROBACION", "DEMORADO", "ENTREGADO", "CANCELADO"],
                default=["EN_PROCESO", "ESPERANDO_APROBACION", "DEMORADO"]
            )

        with col_f2:
            filtro_estado_pres = st.multiselect(
                "Estados de Presupuesto",
                ["SIN_PRESUPUESTO", "BORRADOR", "APROBADO_INTERNO", "ENVIADO", "ACEPTADO", "RECHAZADO"],
                default=["BORRADOR", "APROBADO_INTERNO", "ENVIADO"]
            )

    # Cargar OTs según filtros
    try:
        todas_ots = []
        for estado in filtro_estado_ot:
            resp = httpx.get(f"{url_api}/ot/", params={"estado": estado}, timeout=10)
            resp.raise_for_status()
            todas_ots.extend(resp.json().get("ordenes_trabajo", []))
    except Exception as e:
        st.error(f"Error al cargar OTs: {str(e)}")
        todas_ots = []

    if not todas_ots:
        st.info("📭 No hay OTs con los filtros seleccionados.")
        return

    # Cargar presupuestos de todas las OTs
    presupuestos_map = {}
    for ot in todas_ots:
        try:
            resp = httpx.get(f"{url_api}/presupuesto/{ot['id']}", timeout=10)
            if resp.status_code == 200:
                presupuestos_map[ot['id']] = resp.json().get("presupuesto")
        except Exception:
            pass

    # Filtrar por estado de presupuesto
    ots_filtradas = []
    for ot in todas_ots:
        pres = presupuestos_map.get(ot['id'])
        estado_pres = pres.get("estado") if pres else "SIN_PRESUPUESTO"

        if estado_pres in filtro_estado_pres or (estado_pres is None and "SIN_PRESUPUESTO" in filtro_estado_pres):
            ots_filtradas.append(ot)

    if not ots_filtradas:
        st.info("📭 No hay OTs que cumplan con los filtros de presupuesto seleccionados.")
        return

    # Tabla resumen
    st.subheader(f"📊 Resumen de Presupuestos ({len(ots_filtradas)} OTs)")

    # Crear tabla HTML
    html_table = """<table style="width:100%; border-collapse: collapse; font-size: 0.9em; font-family: sans-serif;">
<thead>
<tr style="background-color: #1A3A6B; color: #FFFFFF; text-align: left; border-bottom: 2px solid #ddd;">
<th style="padding: 12px; font-weight: bold;">NRO OT</th>
<th style="padding: 12px; font-weight: bold;">CLIENTE</th>
<th style="padding: 12px; font-weight: bold;">EQUIPO</th>
<th style="padding: 12px; font-weight: bold;">ESTADO OT</th>
<th style="padding: 12px; font-weight: bold;">ESTADO PRESUPUESTO</th>
<th style="padding: 12px; font-weight: bold;">TOTAL VENTA</th>
</tr>
</thead>
<tbody>"""

    for ot in ots_filtradas:
        nro = ot.get("id", "-")
        cliente = ot.get("cliente", {}).get("nombre", "-") if ot.get("cliente") else "-"
        equipo = ot.get("maquina", "-")
        estado_ot = ot.get("estado", "-")

        pres = presupuestos_map.get(nro)
        if pres:
            estado_pres = pres.get("estado", "-")
            total_venta = formatear_moneda(pres.get("total_venta", 0.0))
            info_estado = obtener_info_estado_presupuesto(estado_pres)
            badge_pres = f"<span style='background-color: {info_estado['color']}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85em;'>{info_estado['icono']} {estado_pres}</span>"
        else:
            estado_pres = "SIN PRESUPUESTO"
            total_venta = "-"
            badge_pres = "<span style='background-color: #95A5A6; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 0.85em;'>📝 SIN PRESUPUESTO</span>"

        badge_ot = badge_estado(estado_ot)

        row_html = f"""<tr style="border-bottom: 1px solid #ddd;">
<td style="padding: 12px; font-weight: 500;">{nro}</td>
<td style="padding: 12px;">{cliente}</td>
<td style="padding: 12px;">{equipo}</td>
<td style="padding: 12px;">{badge_ot}</td>
<td style="padding: 12px;">{badge_pres}</td>
<td style="padding: 12px; font-weight: bold;">{total_venta}</td>
</tr>"""
        html_table += row_html

    html_table += """</tbody>
</table>"""
    st.markdown(html_table, unsafe_allow_html=True)

    st.divider()

    # Selector para ver detalles
    st.subheader("🔍 Ver/Editar Presupuesto")

    opciones_ot = {}
    for ot in ots_filtradas:
        cliente_nombre = ot.get('cliente', {}).get('nombre', 'Sin cliente') if ot.get('cliente') else 'Sin cliente'
        pres = presupuestos_map.get(ot['id'])
        estado_pres = pres.get("estado") if pres else "SIN PRES"
        label = f"{ot['id']} — {cliente_nombre} | {ot.get('maquina', '-')} [{estado_pres}]"
        opciones_ot[ot["id"]] = label

    opciones_select = ["Seleccionar..."] + list(opciones_ot.keys())
    seleccion_guardada = st.session_state.get("presupuesto_ot_seleccionada", "Seleccionar...")
    if seleccion_guardada not in opciones_select:
        seleccion_guardada = "Seleccionar..."
        st.session_state["presupuesto_ot_seleccionada"] = seleccion_guardada

    ot_seleccionada = st.selectbox(
        "Seleccionar OT para ver detalles y editar",
        opciones_select,
        index=opciones_select.index(seleccion_guardada),
        key="presupuesto_ot_seleccionada",
        format_func=lambda ot_key: "Seleccionar..." if ot_key == "Seleccionar..." else opciones_ot.get(ot_key, ot_key),
    )

    if ot_seleccionada == "Seleccionar...":
        st.info("👆 Seleccioná una OT de la lista para ver sus detalles y editar el presupuesto.")
        return

    ot_id = ot_seleccionada

    # Cargar datos completos de la OT seleccionada
    try:
        resp_ot = httpx.get(f"{url_api}/ot/{ot_id}", timeout=10)
        resp_ot.raise_for_status()
        datos_ot = resp_ot.json()
        ot_data = datos_ot.get("ot", {})
        diagnostico_info = datos_ot.get("diagnostico", {})
    except Exception as e:
        st.error(f"Error al cargar datos de la OT: {str(e)}")
        return

    presupuesto_existente = presupuestos_map.get(ot_id)
    estado_pres = presupuesto_existente.get("estado") if presupuesto_existente else None

    # Inicializar items en session_state por OT
    if f"items_mo_{ot_id}" not in st.session_state:
        if presupuesto_existente:
            st.session_state[f"items_mo_{ot_id}"] = presupuesto_existente.get("items_mano_obra", [])
            st.session_state[f"items_mat_{ot_id}"] = presupuesto_existente.get("items_materiales", [])
            st.session_state[f"items_serv_{ot_id}"] = presupuesto_existente.get("items_servicios", [])
            st.session_state[f"form_otros_gastos_{ot_id}"] = presupuesto_existente.get("otros_gastos", 0.0)
            st.session_state[f"form_pct_ganancia_{ot_id}"] = presupuesto_existente.get("porcentaje_ganancia", 30.0)
        else:
            st.session_state[f"items_mo_{ot_id}"] = []
            st.session_state[f"items_mat_{ot_id}"] = []
            st.session_state[f"items_serv_{ot_id}"] = []
            st.session_state[f"form_otros_gastos_{ot_id}"] = 0.0
            st.session_state[f"form_pct_ganancia_{ot_id}"] = 30.0

    items_mo = st.session_state[f"items_mo_{ot_id}"]
    items_mat = st.session_state[f"items_mat_{ot_id}"]
    items_serv = st.session_state[f"items_serv_{ot_id}"]
    otros_gastos = st.session_state.get(f"form_otros_gastos_{ot_id}", 0.0)
    pct_ganancia = st.session_state.get(f"form_pct_ganancia_{ot_id}", 30.0)

    # Header de OT
    st.markdown("---")
    cliente_nombre = ot_data.get('cliente', {}).get('nombre', '-') if ot_data.get('cliente') else '-'
    st.markdown(f"### 📋 {ot_id} — {cliente_nombre} | {ot_data.get('maquina', '-')}")

    col_ot, col_pres = st.columns(2)
    with col_ot:
        st.markdown(f"**Estado OT:** {badge_estado(ot_data.get('estado', '-'))}", unsafe_allow_html=True)
    with col_pres:
        info_estado = obtener_info_estado_presupuesto(estado_pres)
        st.markdown(
            f"**Estado Presupuesto:** <span style='background-color: {info_estado['color']}; "
            f"color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold;'>"
            f"{info_estado['icono']} {estado_pres or 'SIN PRESUPUESTO'}</span>",
            unsafe_allow_html=True
        )
        st.caption(info_estado['descripcion'])

    # Flujo de estados
    renderizar_flujo_estados(estado_pres)

    st.divider()

    # Layout principal: columnas
    col_contenido, col_resumen = st.columns([1.7, 1.3], gap="large")

    with col_resumen:
        tc, tv = renderizar_resumen_economico(presupuesto_existente, items_mo, items_mat, items_serv, otros_gastos, pct_ganancia)
        st.markdown("<br>", unsafe_allow_html=True)
        renderizar_acciones_disponibles(estado_pres, presupuesto_existente, ot_id, url_api, tc, tv, items_mo, items_mat, items_serv)

    with col_contenido:
        # Determinar tabs disponibles
        tabs_disponibles = []
        tab_funciones = []

        # Tab Ver Presupuesto
        if presupuesto_existente:
            tabs_disponibles.append("📄 Ver Presupuesto")
            tab_funciones.append(lambda: renderizar_tab_ver_presupuesto(presupuesto_existente, diagnostico_info))

        # Tab Editar
        info_estado = obtener_info_estado_presupuesto(estado_pres)
        if info_estado['puede_editar']:
            tabs_disponibles.append("✏️ Editar Presupuesto")

            # Cargar catálogos
            categorias_mo = []
            insumos = []
            try:
                resp_cat = httpx.get(f"{url_api}/presupuesto/catalogos/mano-obra", timeout=10)
                if resp_cat.status_code == 200:
                    categorias_mo = resp_cat.json().get("categorias", [])

                resp_ins = httpx.get(f"{url_api}/presupuesto/catalogos/insumos", timeout=10)
                if resp_ins.status_code == 200:
                    insumos = resp_ins.json().get("insumos", [])
            except Exception:
                pass

            tab_funciones.append(lambda: renderizar_tab_editar(presupuesto_existente, categorias_mo, insumos, ot_id, items_mo, items_mat, items_serv))

        # Tab Respuesta Cliente
        if estado_pres in ["ENVIADO", "ACEPTADO", "RECHAZADO"]:
            tabs_disponibles.append("📞 Respuesta Cliente")
            tab_funciones.append(lambda: renderizar_tab_respuesta_cliente(presupuesto_existente, url_api))

        # Renderizar tabs
        if len(tabs_disponibles) > 1:
            tabs_ui = st.tabs(tabs_disponibles)
            for idx, tab_fn in enumerate(tab_funciones):
                with tabs_ui[idx]:
                    tab_fn()
        elif len(tabs_disponibles) == 1:
            tab_funciones[0]()
        else:
            st.info("⚠️ Creá un presupuesto usando el botón 'Guardar Borrador' en el panel lateral.")


# --- Ejecutar página ---
if __name__ == "__main__":
    mostrar_pagina()
