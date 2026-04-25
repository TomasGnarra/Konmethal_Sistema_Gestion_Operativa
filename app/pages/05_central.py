"""
Central — Vista completa del historial de OTs para el supervisor.
Permite ver, editar, cancelar y exportar todas las órdenes de trabajo.
"""

import io
from datetime import date, datetime
from typing import Optional

import httpx
import pandas as pd
import streamlit as st

from app.components.sidebar import render_sidebar
from app.utils.helpers import (
    ESTADOS_OT,
    ETAPAS_OT,
    calcular_atraso,
    formatear_fecha,
)
from app.utils.supabase_client import obtener_url_api

st.set_page_config(
    page_title="Central — Konmethal",
    page_icon="🗂️",
    layout="wide",
)
render_sidebar()

st.markdown("""
<style>
    h1 { color: #1A3A6B; }
    h2, h3 { color: #1F78C1; }
    [data-testid="stDataEditor"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ── Utilidades ──────────────────────────────────────────────────────────────

def _parsear_fecha(valor) -> Optional[date]:
    if not valor:
        return None
    if isinstance(valor, date):
        return valor
    try:
        return datetime.fromisoformat(str(valor)[:10]).date()
    except (ValueError, TypeError):
        return None


def _igual(a, b) -> bool:
    """Comparación segura que trata None, NaN y NaT como equivalentes."""
    try:
        if pd.isna(a) and pd.isna(b):
            return True
        if pd.isna(a) or pd.isna(b):
            return False
    except (TypeError, ValueError):
        pass
    return a == b


# ── Acceso a datos ──────────────────────────────────────────────────────────

def cargar_ots() -> list[dict]:
    url_api = obtener_url_api()
    resp = httpx.get(
        f"{url_api}/seguimiento/",
        params={"incluir_entregadas": True, "incluir_canceladas": True},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("ordenes_trabajo", [])


def patchear_ot(ot_id: str, campos: dict):
    url_api = obtener_url_api()
    resp = httpx.patch(
        f"{url_api}/seguimiento/{ot_id}",
        json=campos,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


# ── Construcción del DataFrame ──────────────────────────────────────────────

def construir_df(ots: list[dict]) -> pd.DataFrame:
    filas = []
    for ot in ots:
        cliente = ot.get("cliente") or {}
        presupuesto = ot.get("presupuesto") or {}
        diagnostico = ot.get("diagnostico") or {}
        estado = ot.get("estado", "")
        filas.append({
            "Cancelar": False,
            "OT": ot.get("id", ""),
            "Cliente": cliente.get("nombre") or "-",
            "Equipo": ot.get("maquina") or "-",
            "Descripción": ot.get("descripcion_trabajo") or "-",
            "Estado": estado,
            "Etapa": ot.get("etapa"),
            "Ingreso": _parsear_fecha(ot.get("fecha_ingreso")),
            "Entrega Prevista": _parsear_fecha(ot.get("fecha_entrega_prevista")),
            "Entrega Real": _parsear_fecha(ot.get("fecha_entrega_real")),
            "Hs Cotizadas": ot.get("horas_cotizadas"),
            "Hs Empleadas": ot.get("horas_empleadas"),
            "Cotización $": ot.get("monto_cotizacion"),
            "Total Venta $": presupuesto.get("total_venta"),
            "Estado Ppto.": presupuesto.get("estado") or "-",
            "Técnico": diagnostico.get("tecnico_responsable") or "-",
            "Atraso (días)": (
                calcular_atraso(ot.get("fecha_entrega_prevista"))
                if estado not in ("ENTREGADO", "CANCELADO") else 0
            ),
        })
    return pd.DataFrame(filas)


# ── Generación de archivos de exportación ───────────────────────────────────

def generar_excel(df: pd.DataFrame) -> bytes:
    df_export = df.drop(columns=["Cancelar"], errors="ignore")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Historial OTs")
    return buffer.getvalue()


def generar_csv_historial(df: pd.DataFrame) -> bytes:
    df_export = df.drop(columns=["Cancelar"], errors="ignore")
    return df_export.to_csv(index=False).encode("utf-8-sig")


def generar_csv_ot(ot: dict) -> bytes:
    """CSV detallado de una sola OT: todos los campos + items de presupuesto."""
    cliente = ot.get("cliente") or {}
    presupuesto = ot.get("presupuesto") or {}
    diagnostico = ot.get("diagnostico") or {}
    recepcion = ot.get("recepcion") or {}

    filas = []

    for campo, valor in [
        ("ID OT", ot.get("id")),
        ("Cliente", cliente.get("nombre")),
        ("Rubro", cliente.get("rubro")),
        ("Teléfono", cliente.get("telefono")),
        ("Contacto", cliente.get("contacto")),
        ("Equipo / Máquina", ot.get("maquina")),
        ("Descripción del trabajo", ot.get("descripcion_trabajo")),
        ("Estado", ot.get("estado")),
        ("Etapa", ot.get("etapa")),
        ("Fecha ingreso", formatear_fecha(ot.get("fecha_ingreso"))),
        ("Fecha entrega prevista", formatear_fecha(ot.get("fecha_entrega_prevista"))),
        ("Fecha entrega real", formatear_fecha(ot.get("fecha_entrega_real"))),
        ("Horas cotizadas", ot.get("horas_cotizadas")),
        ("Horas empleadas", ot.get("horas_empleadas")),
        ("Monto cotización", ot.get("monto_cotizacion")),
    ]:
        filas.append({"Sección": "OT", "Campo": campo, "Valor": valor or ""})

    if recepcion:
        for campo, valor in [
            ("Estado pieza", recepcion.get("estado_pieza")),
            ("Material base", recepcion.get("material_base")),
            ("Trabajo solicitado", recepcion.get("trabajo_solicitado")),
            ("Causa falla", recepcion.get("causa_falla")),
            ("Observaciones", recepcion.get("observaciones")),
        ]:
            filas.append({"Sección": "Recepción", "Campo": campo, "Valor": valor or ""})

    if diagnostico:
        for campo, valor in [
            ("Técnico responsable", diagnostico.get("tecnico_responsable")),
            ("Conclusión", diagnostico.get("conclusion")),
            ("Tipo falla", diagnostico.get("tipo_falla")),
            ("Dimensiones", diagnostico.get("dimensiones")),
            ("Notas", diagnostico.get("notas")),
        ]:
            filas.append({"Sección": "Diagnóstico", "Campo": campo, "Valor": valor or ""})

    if presupuesto:
        for campo, valor in [
            ("Estado presupuesto", presupuesto.get("estado")),
            ("Total costo", presupuesto.get("total_costo")),
            ("Total venta", presupuesto.get("total_venta")),
            ("% Ganancia", presupuesto.get("porcentaje_ganancia")),
            ("Otros gastos", presupuesto.get("otros_gastos")),
        ]:
            filas.append({"Sección": "Presupuesto", "Campo": campo, "Valor": valor or ""})

        for i, item in enumerate(presupuesto.get("items_mano_obra") or [], 1):
            filas.append({
                "Sección": "Mano de Obra",
                "Campo": f"MO {i} — Cat. {item.get('categoria', '')} · {item.get('cantidad_horas', '')} hs",
                "Valor": item.get("subtotal", ""),
            })
        for i, item in enumerate(presupuesto.get("items_materiales") or [], 1):
            filas.append({
                "Sección": "Materiales",
                "Campo": f"Mat {i} — {item.get('denominacion', '')} × {item.get('cantidad', '')}",
                "Valor": item.get("subtotal", ""),
            })
        for i, item in enumerate(presupuesto.get("items_servicios") or [], 1):
            filas.append({
                "Sección": "Servicios",
                "Campo": f"Serv {i} — {item.get('descripcion', '')}",
                "Valor": item.get("monto", ""),
            })

    return pd.DataFrame(filas).to_csv(index=False).encode("utf-8-sig")


# ── Página ──────────────────────────────────────────────────────────────────

st.title("🗂️ Central")
st.caption("Historial completo de órdenes de trabajo · Edición y exportación para supervisores.")

# Fila superior: actualizar + exportar
col_refresh, col_excel, col_csv = st.columns([2, 2, 2])
recargar = col_refresh.button("🔄 Actualizar datos", use_container_width=True)

if recargar or "central_ots" not in st.session_state:
    with st.spinner("Cargando historial completo..."):
        try:
            st.session_state.central_ots = cargar_ots()
            st.session_state.central_df_original = construir_df(st.session_state.central_ots)
            st.session_state.pop("central_confirmacion_cancelar", None)
        except Exception as e:
            st.error(f"No se pudieron cargar los datos: {e}")
            st.stop()

ots_raw: list[dict] = st.session_state.central_ots
df_original: pd.DataFrame = st.session_state.central_df_original

# ── Filtros ──────────────────────────────────────────────────────────────────

with st.expander("🔍 Filtros", expanded=False):
    fc1, fc2, fc3, fc4 = st.columns(4)

    estados_disponibles = sorted(df_original["Estado"].dropna().unique().tolist())
    filtro_estados = fc1.multiselect("Estado", options=estados_disponibles)

    clientes_disponibles = sorted(df_original["Cliente"].dropna().unique().tolist())
    filtro_cliente = fc2.selectbox("Cliente", options=["Todos"] + clientes_disponibles)

    filtro_desde = fc3.date_input("Ingreso desde", value=None)
    filtro_hasta = fc4.date_input("Ingreso hasta", value=None)

# Aplicar filtros
df_filtrado = df_original.copy()
if filtro_estados:
    df_filtrado = df_filtrado[df_filtrado["Estado"].isin(filtro_estados)]
if filtro_cliente != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Cliente"] == filtro_cliente]
if filtro_desde:
    df_filtrado = df_filtrado[
        df_filtrado["Ingreso"].apply(lambda d: d >= filtro_desde if d is not None else False)
    ]
if filtro_hasta:
    df_filtrado = df_filtrado[
        df_filtrado["Ingreso"].apply(lambda d: d <= filtro_hasta if d is not None else False)
    ]

df_filtrado = df_filtrado.reset_index(drop=True)

# Botones de exportación (usan df_filtrado)
with col_excel:
    st.download_button(
        "📥 Descargar Excel",
        data=generar_excel(df_filtrado),
        file_name=f"konmethal_historial_{date.today().isoformat()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
with col_csv:
    st.download_button(
        "📄 Descargar CSV",
        data=generar_csv_historial(df_filtrado),
        file_name=f"konmethal_historial_{date.today().isoformat()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown(
    f"**{len(df_filtrado)} órdenes de trabajo** · "
    "Editá Estado, Etapa, Entrega Prevista, Hs Empleadas o Cotización directamente en la tabla."
)

# ── Tabla editable ───────────────────────────────────────────────────────────

df_editor = st.data_editor(
    df_filtrado,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "Cancelar": st.column_config.CheckboxColumn(
            "Cancelar",
            help="Marcá para cancelar esta OT",
            default=False,
            width="small",
        ),
        "OT": st.column_config.TextColumn("OT", disabled=True, width="small"),
        "Cliente": st.column_config.TextColumn("Cliente", disabled=True),
        "Equipo": st.column_config.TextColumn("Equipo", disabled=True),
        "Descripción": st.column_config.TextColumn("Descripción", disabled=True, width="large"),
        "Estado": st.column_config.SelectboxColumn(
            "Estado",
            options=ESTADOS_OT,
            width="medium",
        ),
        "Etapa": st.column_config.SelectboxColumn(
            "Etapa",
            options=ETAPAS_OT,
            width="medium",
        ),
        "Ingreso": st.column_config.DateColumn("Ingreso", disabled=True, width="small"),
        "Entrega Prevista": st.column_config.DateColumn("Entrega Prevista", width="medium"),
        "Entrega Real": st.column_config.DateColumn("Entrega Real", disabled=True, width="medium"),
        "Hs Cotizadas": st.column_config.NumberColumn("Hs Cot.", disabled=True, format="%.1f"),
        "Hs Empleadas": st.column_config.NumberColumn("Hs Emp.", format="%.1f", min_value=0, step=0.5),
        "Cotización $": st.column_config.NumberColumn("Cotización $", format="$ %.2f", min_value=0),
        "Total Venta $": st.column_config.NumberColumn("Total Venta $", disabled=True, format="$ %.2f"),
        "Estado Ppto.": st.column_config.TextColumn("Estado Ppto.", disabled=True, width="medium"),
        "Técnico": st.column_config.TextColumn("Técnico", disabled=True),
        "Atraso (días)": st.column_config.NumberColumn("Atraso (días)", disabled=True, width="small"),
    },
    key="central_editor",
)

# ── Acciones ─────────────────────────────────────────────────────────────────

CAMPOS_EDITABLES = ["Estado", "Etapa", "Entrega Prevista", "Hs Empleadas", "Cotización $"]
CAMPO_A_API = {
    "Estado": "estado",
    "Etapa": "etapa",
    "Entrega Prevista": "fecha_entrega_prevista",
    "Hs Empleadas": "horas_empleadas",
    "Cotización $": "monto_cotizacion",
}

ca1, ca2, _ = st.columns([2, 2, 6])

# --- Guardar cambios ---
if ca1.button("💾 Guardar cambios", type="primary", use_container_width=True):
    cambios = []
    for i in range(len(df_filtrado)):
        ot_id = df_filtrado.iloc[i]["OT"]
        campos_modificados = {}
        for campo in CAMPOS_EDITABLES:
            val_orig = df_filtrado.iloc[i][campo]
            val_edit = df_editor.iloc[i][campo]
            if not _igual(val_orig, val_edit):
                campos_modificados[campo] = val_edit
        if campos_modificados:
            cambios.append({"ot_id": ot_id, "campos": campos_modificados})

    if not cambios:
        st.info("No se detectaron cambios.")
    else:
        errores = []
        guardados = 0
        for cambio in cambios:
            payload = {}
            for campo, valor in cambio["campos"].items():
                clave_api = CAMPO_A_API[campo]
                if campo == "Entrega Prevista":
                    try:
                        payload[clave_api] = valor.isoformat() if valor and not pd.isna(valor) else None
                    except (AttributeError, TypeError, ValueError):
                        payload[clave_api] = None
                elif valor is None or (isinstance(valor, float) and pd.isna(valor)):
                    payload[clave_api] = None
                else:
                    payload[clave_api] = valor
            try:
                patchear_ot(cambio["ot_id"], payload)
                guardados += 1
            except Exception as e:
                errores.append(f"{cambio['ot_id']}: {e}")

        if guardados:
            st.success(f"✅ {guardados} OT(s) actualizadas correctamente.")
        for err in errores:
            st.error(f"Error al guardar {err}")

        if not errores:
            st.session_state.central_ots = cargar_ots()
            st.session_state.central_df_original = construir_df(st.session_state.central_ots)
            st.rerun()

# --- Cancelar seleccionadas ---
seleccionadas = (
    df_editor[df_editor["Cancelar"] == True]["OT"].tolist()
    if "Cancelar" in df_editor.columns else []
)

if ca2.button(
    f"🚫 Cancelar ({len(seleccionadas)})" if seleccionadas else "🚫 Cancelar seleccionadas",
    disabled=not seleccionadas,
    use_container_width=True,
):
    st.session_state.central_confirmacion_cancelar = seleccionadas

if st.session_state.get("central_confirmacion_cancelar"):
    ids_pendientes = st.session_state.central_confirmacion_cancelar
    st.warning(
        f"⚠️ Estás por marcar como **CANCELADAS** las OTs: **{', '.join(ids_pendientes)}**. "
        "El estado quedará como CANCELADA (se puede revertir editando la tabla). ¿Confirmás?"
    )
    conf1, conf2, _ = st.columns([2, 2, 6])
    if conf1.button("✅ Sí, cancelar", type="primary"):
        errores_cancel = []
        for ot_id in ids_pendientes:
            try:
                patchear_ot(ot_id, {"estado": "CANCELADO"})
            except Exception as e:
                errores_cancel.append(f"{ot_id}: {e}")
        st.session_state.pop("central_confirmacion_cancelar", None)
        if not errores_cancel:
            st.success(f"OTs marcadas como CANCELADAS: {', '.join(ids_pendientes)}")
        for err in errores_cancel:
            st.error(f"Error: {err}")
        st.session_state.central_ots = cargar_ots()
        st.session_state.central_df_original = construir_df(st.session_state.central_ots)
        st.rerun()
    if conf2.button("❌ No, volver"):
        st.session_state.pop("central_confirmacion_cancelar", None)
        st.rerun()

# ── Descarga individual ───────────────────────────────────────────────────────

st.markdown("---")
st.subheader("📎 Descarga individual")

tab_por_ot, tab_por_cliente = st.tabs(["Por OT", "Por cliente"])

with tab_por_ot:
    ids_ot = [ot["id"] for ot in ots_raw]
    if ids_ot:
        ot_sel = st.selectbox("Seleccioná una OT", options=ids_ot, key="dl_ot_sel")
        ot_datos = next((o for o in ots_raw if o["id"] == ot_sel), None)
        if ot_datos:
            cliente_nombre = (ot_datos.get("cliente") or {}).get("nombre", "")
            st.caption(
                f"**{ot_sel}** · {cliente_nombre} · "
                f"{ot_datos.get('maquina', '-')} · Estado: {ot_datos.get('estado', '-')}"
            )
            st.download_button(
                f"📥 Descargar historial de {ot_sel}",
                data=generar_csv_ot(ot_datos),
                file_name=f"historial_{ot_sel}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No hay OTs disponibles.")

with tab_por_cliente:
    clientes_lista = sorted(
        {
            (ot.get("cliente_id"), (ot.get("cliente") or {}).get("nombre", "Sin nombre"))
            for ot in ots_raw
            if ot.get("cliente_id")
        },
        key=lambda x: x[1],
    )
    if clientes_lista:
        opciones = [f"{nombre}" for _, nombre in clientes_lista]
        cliente_sel_str = st.selectbox("Seleccioná un cliente", options=opciones, key="dl_cli_sel")
        idx = opciones.index(cliente_sel_str)
        cliente_id_sel, nombre_sel = clientes_lista[idx]
        ots_cliente = [o for o in ots_raw if o.get("cliente_id") == cliente_id_sel]
        df_cli = construir_df(ots_cliente)
        st.caption(f"{len(ots_cliente)} OTs encontradas para **{nombre_sel}**")
        st.download_button(
            f"📥 Descargar historial de {nombre_sel}",
            data=generar_csv_historial(df_cli),
            file_name=f"historial_{nombre_sel.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("No hay clientes disponibles.")
