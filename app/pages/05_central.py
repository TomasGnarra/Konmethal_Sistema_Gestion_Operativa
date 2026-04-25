"""
Central — Home del Supervisor.
KPIs, gráficos, historial editable de OTs, clientes y gestión de costos.
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
    calcular_total_presupuesto,
    formatear_fecha,
    formatear_moneda,
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
    [data-testid="stSidebar"] { background-color: #1A3A6B; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    h1, h2 { color: #1A3A6B; }
    h3 { color: #1F78C1; }
    [data-testid="metric-container"] {
        background-color: #F5F5F5;
        border-left: 4px solid #1F78C1;
        padding: 12px;
        border-radius: 4px;
    }
    [data-testid="stDataEditor"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

url_api = obtener_url_api()


# ── Utilidades ───────────────────────────────────────────────────────────────

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
    try:
        if pd.isna(a) and pd.isna(b):
            return True
        if pd.isna(a) or pd.isna(b):
            return False
    except (TypeError, ValueError):
        pass
    return a == b


# ── Acceso a datos ───────────────────────────────────────────────────────────

def cargar_ots() -> list[dict]:
    resp = httpx.get(
        f"{url_api}/seguimiento/",
        params={"incluir_entregadas": True, "incluir_canceladas": True},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("ordenes_trabajo", [])


def cargar_catalogos() -> tuple[list[dict], list[dict]]:
    resp_mo = httpx.get(f"{url_api}/presupuesto/catalogos/mano-obra", timeout=10)
    resp_in = httpx.get(f"{url_api}/presupuesto/catalogos/insumos", timeout=10)
    mo = resp_mo.json().get("categorias", []) if resp_mo.status_code == 200 else []
    insumos = resp_in.json().get("insumos", []) if resp_in.status_code == 200 else []
    return mo, insumos


def patchear_ot(ot_id: str, campos: dict):
    resp = httpx.patch(f"{url_api}/seguimiento/{ot_id}", json=campos, timeout=15)
    resp.raise_for_status()
    return resp.json()


def patchear_categoria_mo(cat_id: int, campos: dict):
    resp = httpx.patch(f"{url_api}/presupuesto/catalogos/mano-obra/{cat_id}", json=campos, timeout=10)
    resp.raise_for_status()
    return resp.json()


def patchear_insumo(insumo_id: int, campos: dict):
    resp = httpx.patch(f"{url_api}/presupuesto/catalogos/insumos/{insumo_id}", json=campos, timeout=10)
    resp.raise_for_status()
    return resp.json()


def patchear_presupuesto(presupuesto_id: int, campos: dict):
    resp = httpx.patch(f"{url_api}/presupuesto/{presupuesto_id}", json=campos, timeout=15)
    resp.raise_for_status()
    return resp.json()


def crear_categoria_mo_api(datos: dict):
    resp = httpx.post(f"{url_api}/presupuesto/catalogos/mano-obra", json=datos, timeout=10)
    resp.raise_for_status()
    return resp.json()


def crear_insumo_api(datos: dict):
    resp = httpx.post(f"{url_api}/presupuesto/catalogos/insumos", json=datos, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ── Construcción del DataFrame de OTs ────────────────────────────────────────

def construir_df(ots: list[dict]) -> pd.DataFrame:
    filas = []
    for ot in ots:
        cliente     = ot.get("cliente") or {}
        presupuesto = ot.get("presupuesto") or {}
        diagnostico = ot.get("diagnostico") or {}
        estado      = ot.get("estado", "")
        filas.append({
            "Cancelar":          False,
            "OT":                ot.get("id", ""),
            "Cliente":           cliente.get("nombre") or "-",
            "Equipo":            ot.get("maquina") or "-",
            "Descripción":       ot.get("descripcion_trabajo") or "-",
            "Estado":            estado,
            "Etapa":             ot.get("etapa"),
            "Ingreso":           _parsear_fecha(ot.get("fecha_ingreso")),
            "Entrega Prevista":  _parsear_fecha(ot.get("fecha_entrega_prevista")),
            "Entrega Real":      _parsear_fecha(ot.get("fecha_entrega_real")),
            "Hs Cotizadas":      ot.get("horas_cotizadas"),
            "Hs Empleadas":      ot.get("horas_empleadas"),
            "Cotización $":      ot.get("monto_cotizacion"),
            "Total Venta $":     presupuesto.get("total_venta"),
            "Estado Ppto.":      presupuesto.get("estado") or "-",
            "Técnico":           diagnostico.get("tecnico_responsable") or "-",
            "Atraso (días)":     (
                calcular_atraso(ot.get("fecha_entrega_prevista"))
                if estado not in ("ENTREGADO", "CANCELADO") else 0
            ),
        })
    return pd.DataFrame(filas)


# ── Exportaciones ────────────────────────────────────────────────────────────

def generar_excel(df: pd.DataFrame) -> bytes:
    df_exp = df.drop(columns=["Cancelar"], errors="ignore")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_exp.to_excel(w, index=False, sheet_name="Historial OTs")
    return buf.getvalue()


def generar_csv(df: pd.DataFrame) -> bytes:
    return df.drop(columns=["Cancelar"], errors="ignore").to_csv(index=False).encode("utf-8-sig")


def generar_csv_ot(ot: dict) -> bytes:
    cliente     = ot.get("cliente") or {}
    presupuesto = ot.get("presupuesto") or {}
    diagnostico = ot.get("diagnostico") or {}
    recepcion   = ot.get("recepcion") or {}
    filas = []

    for campo, valor in [
        ("ID OT", ot.get("id")), ("Cliente", cliente.get("nombre")),
        ("Rubro", cliente.get("rubro")), ("Teléfono", cliente.get("telefono")),
        ("Equipo / Máquina", ot.get("maquina")), ("Descripción", ot.get("descripcion_trabajo")),
        ("Estado", ot.get("estado")), ("Etapa", ot.get("etapa")),
        ("Fecha ingreso", formatear_fecha(ot.get("fecha_ingreso"))),
        ("Entrega prevista", formatear_fecha(ot.get("fecha_entrega_prevista"))),
        ("Entrega real", formatear_fecha(ot.get("fecha_entrega_real"))),
        ("Hs cotizadas", ot.get("horas_cotizadas")), ("Hs empleadas", ot.get("horas_empleadas")),
        ("Monto cotización", ot.get("monto_cotizacion")),
    ]:
        filas.append({"Sección": "OT", "Campo": campo, "Valor": valor or ""})

    for campo, valor in [
        ("Estado pieza", recepcion.get("estado_pieza")),
        ("Material base", recepcion.get("material_base")),
        ("Trabajo solicitado", recepcion.get("trabajo_solicitado")),
        ("Causa falla", recepcion.get("causa_falla")),
        ("Observaciones", recepcion.get("observaciones")),
    ]:
        if valor:
            filas.append({"Sección": "Recepción", "Campo": campo, "Valor": valor})

    for campo, valor in [
        ("Técnico", diagnostico.get("tecnico_responsable")),
        ("Conclusión", diagnostico.get("conclusion")),
        ("Tipo falla", diagnostico.get("tipo_falla")),
        ("Notas", diagnostico.get("notas")),
    ]:
        if valor:
            filas.append({"Sección": "Diagnóstico", "Campo": campo, "Valor": valor})

    if presupuesto:
        filas.append({"Sección": "Presupuesto", "Campo": "Estado", "Valor": presupuesto.get("estado") or ""})
        filas.append({"Sección": "Presupuesto", "Campo": "Total venta", "Valor": presupuesto.get("total_venta") or ""})
        for i, item in enumerate(presupuesto.get("items_mano_obra") or [], 1):
            filas.append({"Sección": "MO", "Campo": f"MO {i} Cat.{item.get('categoria')} {item.get('cantidad_horas')}hs", "Valor": item.get("subtotal", "")})
        for i, item in enumerate(presupuesto.get("items_materiales") or [], 1):
            filas.append({"Sección": "Mat", "Campo": f"{item.get('denominacion')} x{item.get('cantidad')}", "Valor": item.get("subtotal", "")})

    return pd.DataFrame(filas).to_csv(index=False).encode("utf-8-sig")


# ── Carga inicial ────────────────────────────────────────────────────────────

st.title("🗂️ Central")
st.caption("Panel del supervisor · KPIs, historial completo, edición y gestión de costos.")

col_h, col_ref = st.columns([8, 2])
if col_ref.button("🔄 Actualizar", use_container_width=True) or "central_ots" not in st.session_state:
    with st.spinner("Cargando datos..."):
        try:
            st.session_state.central_ots = cargar_ots()
            st.session_state.central_df  = construir_df(st.session_state.central_ots)
            mo, insumos = cargar_catalogos()
            st.session_state.central_mo      = mo
            st.session_state.central_insumos = insumos
            st.session_state.pop("central_confirmacion_cancelar", None)
        except Exception as e:
            st.error(f"No se pudieron cargar los datos: {e}")
            st.stop()

ots_raw: list[dict]   = st.session_state.central_ots
df_original: pd.DataFrame = st.session_state.central_df
mano_obra: list[dict] = st.session_state.central_mo
insumos:   list[dict] = st.session_state.central_insumos

# ── TABS PRINCIPALES ─────────────────────────────────────────────────────────

tab_kpi, tab_ots, tab_clientes, tab_recursos, tab_detalle, tab_descargas = st.tabs([
    "📊 KPIs & Gráficos",
    "🗂️ Historial de OTs",
    "👥 Clientes",
    "⚙️ Costos & Recursos",
    "🔍 Detalle OT",
    "📥 Descargas",
])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: KPIs & GRÁFICOS
# ═══════════════════════════════════════════════════════════════════════════

with tab_kpi:
    ots_activas    = [o for o in ots_raw if o.get("estado") not in ("ENTREGADO", "CANCELADO")]
    ots_entregadas = [o for o in ots_raw if o.get("estado") == "ENTREGADO"]
    ots_canceladas = [o for o in ots_raw if o.get("estado") == "CANCELADO"]

    total_cotizado = sum(
        (o.get("presupuesto") or {}).get("total_venta", 0) or 0
        for o in ots_raw
        if (o.get("presupuesto") or {}).get("estado") in ("ENVIADO", "ACEPTADO", "RECHAZADO")
    )
    total_aprobado = sum(
        (o.get("presupuesto") or {}).get("total_venta", 0) or 0
        for o in ots_raw
        if (o.get("presupuesto") or {}).get("estado") == "ACEPTADO"
    )
    clientes_unicos = len({o.get("cliente_id") for o in ots_raw if o.get("cliente_id")})

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🔧 OTs Activas",       len(ots_activas),    f"{len(ots_raw)} total históricas")
    k2.metric("✅ Entregadas",         len(ots_entregadas))
    k3.metric("❌ Canceladas",         len(ots_canceladas))
    k4.metric("💰 Cotizado",           f"${total_cotizado:,.0f}", f"${total_aprobado:,.0f} aprobado")
    k5.metric("👥 Clientes atendidos", clientes_unicos)

    st.divider()

    gcol1, gcol2 = st.columns(2)

    with gcol1:
        st.markdown("**Distribución de estados (historial completo)**")
        if ots_raw:
            df_est = pd.DataFrame([o.get("estado", "?") for o in ots_raw], columns=["Estado"])
            cnt    = df_est["Estado"].value_counts().reset_index()
            cnt.columns = ["Estado", "Cantidad"]
            st.bar_chart(cnt, x="Estado", y="Cantidad", color="#1F78C1", use_container_width=True)
        else:
            st.info("Sin datos.")

    with gcol2:
        st.markdown("**OTs por cliente (top 10)**")
        if ots_raw:
            from collections import Counter
            cnt_cli = Counter(
                (o.get("cliente") or {}).get("nombre", "Sin cliente")
                for o in ots_raw
            )
            df_cli = pd.DataFrame(cnt_cli.most_common(10), columns=["Cliente", "OTs"])
            st.bar_chart(df_cli, x="Cliente", y="OTs", color="#1F78C1", use_container_width=True)
        else:
            st.info("Sin datos.")

    st.divider()

    gcol3, gcol4 = st.columns(2)

    with gcol3:
        st.markdown("**Evolución mensual de ingresos de OTs**")
        fechas_ing = [
            o.get("fecha_ingreso", "")[:7]
            for o in ots_raw if o.get("fecha_ingreso")
        ]
        if fechas_ing:
            from collections import Counter as C2
            por_mes = C2(fechas_ing)
            df_mes  = pd.DataFrame(sorted(por_mes.items()), columns=["Mes", "OTs"])
            st.line_chart(df_mes, x="Mes", y="OTs", use_container_width=True)
        else:
            st.info("Sin datos de fechas.")

    with gcol4:
        st.markdown("**Distribución de etapas (OTs activas)**")
        etapas = [o.get("etapa") or "Sin etapa" for o in ots_activas]
        if etapas:
            from collections import Counter as C3
            cnt_et = C3(etapas)
            df_et  = pd.DataFrame(cnt_et.most_common(), columns=["Etapa", "Cantidad"])
            st.bar_chart(df_et, x="Etapa", y="Cantidad", color="#F39C12", use_container_width=True)
        else:
            st.info("Sin OTs activas.")

    # Atrasadas
    st.divider()
    st.markdown("**OTs con atraso (estado activo)**")
    atrasadas = [
        o for o in ots_activas
        if calcular_atraso(o.get("fecha_entrega_prevista")) > 0
    ]
    if atrasadas:
        for ot in sorted(atrasadas, key=lambda x: calcular_atraso(x.get("fecha_entrega_prevista")), reverse=True):
            dias = calcular_atraso(ot.get("fecha_entrega_prevista"))
            cliente_n = (ot.get("cliente") or {}).get("nombre", "-")
            st.error(f"🔴 **{ot['id']}** · {cliente_n} · {ot.get('maquina', '-')} — **{dias} días** de atraso")
    else:
        st.success("✅ No hay OTs atrasadas.")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: HISTORIAL DE OTs (EDITABLE)
# ═══════════════════════════════════════════════════════════════════════════

with tab_ots:
    # Filtros
    with st.expander("🔍 Filtros", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        estados_disp  = sorted(df_original["Estado"].dropna().unique().tolist())
        filtro_estados = fc1.multiselect("Estado", options=estados_disp, key="f_est")
        clientes_disp  = sorted(df_original["Cliente"].dropna().unique().tolist())
        filtro_cliente = fc2.selectbox("Cliente", ["Todos"] + clientes_disp, key="f_cli")
        filtro_desde   = fc3.date_input("Ingreso desde", value=None, key="f_desde")
        filtro_hasta   = fc4.date_input("Ingreso hasta", value=None, key="f_hasta")

    df_filt = df_original.copy()
    if filtro_estados:
        df_filt = df_filt[df_filt["Estado"].isin(filtro_estados)]
    if filtro_cliente != "Todos":
        df_filt = df_filt[df_filt["Cliente"] == filtro_cliente]
    if filtro_desde:
        df_filt = df_filt[df_filt["Ingreso"].apply(lambda d: d >= filtro_desde if d else False)]
    if filtro_hasta:
        df_filt = df_filt[df_filt["Ingreso"].apply(lambda d: d <= filtro_hasta if d else False)]
    df_filt = df_filt.reset_index(drop=True)

    # Botones exportar
    ex1, ex2, _ = st.columns([2, 2, 6])
    ex1.download_button(
        "📥 Excel", data=generar_excel(df_filt),
        file_name=f"konmethal_{date.today().isoformat()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    ex2.download_button(
        "📄 CSV", data=generar_csv(df_filt),
        file_name=f"konmethal_{date.today().isoformat()}.csv",
        mime="text/csv", use_container_width=True,
    )

    st.markdown(f"**{len(df_filt)} órdenes** · Editá Estado, Etapa, Entrega Prevista, Hs Empleadas o Cotización directamente.")

    df_editor = st.data_editor(
        df_filt,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Cancelar":         st.column_config.CheckboxColumn("Cancelar", default=False, width="small"),
            "OT":               st.column_config.TextColumn("OT", disabled=True, width="small"),
            "Cliente":          st.column_config.TextColumn("Cliente", disabled=True),
            "Equipo":           st.column_config.TextColumn("Equipo", disabled=True),
            "Descripción":      st.column_config.TextColumn("Descripción", disabled=True, width="large"),
            "Estado":           st.column_config.SelectboxColumn("Estado", options=ESTADOS_OT, width="medium"),
            "Etapa":            st.column_config.SelectboxColumn("Etapa", options=ETAPAS_OT, width="medium"),
            "Ingreso":          st.column_config.DateColumn("Ingreso", disabled=True, width="small"),
            "Entrega Prevista": st.column_config.DateColumn("Entrega Prevista", width="medium"),
            "Entrega Real":     st.column_config.DateColumn("Entrega Real", disabled=True, width="medium"),
            "Hs Cotizadas":     st.column_config.NumberColumn("Hs Cot.", disabled=True, format="%.1f"),
            "Hs Empleadas":     st.column_config.NumberColumn("Hs Emp.", format="%.1f", min_value=0, step=0.5),
            "Cotización $":     st.column_config.NumberColumn("Cotización $", format="$ %.2f", min_value=0),
            "Total Venta $":    st.column_config.NumberColumn("Total Venta $", disabled=True, format="$ %.2f"),
            "Estado Ppto.":     st.column_config.TextColumn("Estado Ppto.", disabled=True, width="medium"),
            "Técnico":          st.column_config.TextColumn("Técnico", disabled=True),
            "Atraso (días)":    st.column_config.NumberColumn("Atraso (días)", disabled=True, width="small"),
        },
        key="central_editor",
    )

    CAMPOS_EDITABLES = ["Estado", "Etapa", "Entrega Prevista", "Hs Empleadas", "Cotización $"]
    CAMPO_A_API = {
        "Estado": "estado", "Etapa": "etapa",
        "Entrega Prevista": "fecha_entrega_prevista",
        "Hs Empleadas": "horas_empleadas", "Cotización $": "monto_cotizacion",
    }

    ac1, ac2, _ = st.columns([2, 2, 6])

    if ac1.button("💾 Guardar cambios", type="primary", use_container_width=True):
        cambios = []
        for i in range(len(df_filt)):
            ot_id = df_filt.iloc[i]["OT"]
            mods  = {}
            for campo in CAMPOS_EDITABLES:
                if not _igual(df_filt.iloc[i][campo], df_editor.iloc[i][campo]):
                    mods[campo] = df_editor.iloc[i][campo]
            if mods:
                cambios.append({"ot_id": ot_id, "mods": mods})

        if not cambios:
            st.info("No se detectaron cambios.")
        else:
            errores, guardados = [], 0
            for c in cambios:
                payload = {}
                for campo, valor in c["mods"].items():
                    clave = CAMPO_A_API[campo]
                    if campo == "Entrega Prevista":
                        try:
                            payload[clave] = valor.isoformat() if valor and not pd.isna(valor) else None
                        except (AttributeError, TypeError):
                            payload[clave] = None
                    elif valor is None or (isinstance(valor, float) and pd.isna(valor)):
                        payload[clave] = None
                    else:
                        payload[clave] = valor
                try:
                    patchear_ot(c["ot_id"], payload)
                    guardados += 1
                except Exception as e:
                    errores.append(f"{c['ot_id']}: {e}")

            if guardados:
                st.success(f"✅ {guardados} OT(s) actualizadas.")
            for err in errores:
                st.error(f"Error: {err}")
            if not errores:
                st.session_state.central_ots = cargar_ots()
                st.session_state.central_df  = construir_df(st.session_state.central_ots)
                st.rerun()

    seleccionadas = (
        df_editor[df_editor["Cancelar"] == True]["OT"].tolist()
        if "Cancelar" in df_editor.columns else []
    )
    if ac2.button(
        f"🚫 Cancelar ({len(seleccionadas)})" if seleccionadas else "🚫 Cancelar seleccionadas",
        disabled=not seleccionadas, use_container_width=True,
    ):
        st.session_state.central_confirmacion_cancelar = seleccionadas

    if st.session_state.get("central_confirmacion_cancelar"):
        ids_pend = st.session_state.central_confirmacion_cancelar
        st.warning(
            f"⚠️ Marcando como **CANCELADAS**: **{', '.join(ids_pend)}**. ¿Confirmás?"
        )
        cc1, cc2, _ = st.columns([2, 2, 6])
        if cc1.button("✅ Sí, cancelar", type="primary"):
            for ot_id in ids_pend:
                try:
                    patchear_ot(ot_id, {"estado": "CANCELADO"})
                except Exception as e:
                    st.error(f"Error cancelando {ot_id}: {e}")
            st.session_state.pop("central_confirmacion_cancelar", None)
            st.session_state.central_ots = cargar_ots()
            st.session_state.central_df  = construir_df(st.session_state.central_ots)
            st.rerun()
        if cc2.button("❌ No, volver"):
            st.session_state.pop("central_confirmacion_cancelar", None)
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: CLIENTES
# ═══════════════════════════════════════════════════════════════════════════

with tab_clientes:
    st.subheader("Ranking de Clientes")

    clientes_dict: dict = {}
    for ot in ots_raw:
        c_id = ot.get("cliente_id")
        if not c_id:
            continue
        c_nombre = (ot.get("cliente") or {}).get("nombre", "-")
        if c_id not in clientes_dict:
            clientes_dict[c_id] = {
                "Cliente": c_nombre, "Total OTs": 0,
                "Activas": 0, "Entregadas": 0, "Canceladas": 0,
                "Facturación Aprobada": 0.0,
            }
        clientes_dict[c_id]["Total OTs"] += 1
        estado_ot = ot.get("estado", "")
        if estado_ot not in ("ENTREGADO", "CANCELADO"):
            clientes_dict[c_id]["Activas"] += 1
        elif estado_ot == "ENTREGADO":
            clientes_dict[c_id]["Entregadas"] += 1
        elif estado_ot == "CANCELADO":
            clientes_dict[c_id]["Canceladas"] += 1
        ppto = ot.get("presupuesto") or {}
        if ppto.get("estado") == "ACEPTADO":
            clientes_dict[c_id]["Facturación Aprobada"] += ppto.get("total_venta") or 0.0

    if clientes_dict:
        df_cli = pd.DataFrame(clientes_dict.values()).sort_values("Facturación Aprobada", ascending=False)
        df_cli["Facturación Aprobada"] = df_cli["Facturación Aprobada"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_cli, use_container_width=True, hide_index=True)
    else:
        st.info("Sin clientes registrados.")

    st.divider()
    st.subheader("Historial por cliente")
    clientes_lista = sorted(
        {(ot.get("cliente_id"), (ot.get("cliente") or {}).get("nombre", "Sin nombre"))
         for ot in ots_raw if ot.get("cliente_id")},
        key=lambda x: x[1],
    )
    if clientes_lista:
        opciones = [nombre for _, nombre in clientes_lista]
        cli_sel = st.selectbox("Cliente", opciones, key="cli_hist_sel")
        idx = opciones.index(cli_sel)
        cli_id_sel, cli_nombre_sel = clientes_lista[idx]
        ots_cli = [o for o in ots_raw if o.get("cliente_id") == cli_id_sel]
        df_cli_hist = construir_df(ots_cli).drop(columns=["Cancelar"], errors="ignore")
        st.caption(f"{len(ots_cli)} OTs para **{cli_nombre_sel}**")
        st.dataframe(df_cli_hist, use_container_width=True, hide_index=True)
        st.download_button(
            f"📥 Descargar historial de {cli_nombre_sel}",
            data=generar_csv(construir_df(ots_cli)),
            file_name=f"historial_{cli_nombre_sel.replace(' ', '_')}.csv",
            mime="text/csv",
        )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: COSTOS & RECURSOS (EDITABLE)
# ═══════════════════════════════════════════════════════════════════════════

with tab_recursos:
    col_mo, col_ins = st.columns(2)

    # ── Mano de obra ──────────────────────────────────────────────────────

    with col_mo:
        st.subheader("Mano de Obra — Costos/hora")
        if mano_obra:
            df_mo_orig = pd.DataFrame([
                {"id": m["id"], "Categoría": m.get("categoria", ""),
                 "Descripción": m.get("descripcion") or "", "$/hora": m.get("costo_hora", 0.0)}
                for m in mano_obra
            ])
            df_mo_ed = st.data_editor(
                df_mo_orig,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "id":          st.column_config.NumberColumn("id", disabled=True, width="small"),
                    "Categoría":   st.column_config.TextColumn("Cat.", disabled=True, width="small"),
                    "Descripción": st.column_config.TextColumn("Descripción"),
                    "$/hora":      st.column_config.NumberColumn("$/hora", format="$ %.2f", min_value=0, step=0.5),
                },
                key="editor_mo",
            )
            if st.button("💾 Guardar Mano de Obra", type="primary", use_container_width=True):
                errores_mo, guardados_mo = [], 0
                for i in range(len(df_mo_orig)):
                    orig_desc  = df_mo_orig.iloc[i]["Descripción"]
                    orig_costo = df_mo_orig.iloc[i]["$/hora"]
                    edit_desc  = df_mo_ed.iloc[i]["Descripción"]
                    edit_costo = df_mo_ed.iloc[i]["$/hora"]
                    if orig_desc != edit_desc or not _igual(orig_costo, edit_costo):
                        cat_id = int(df_mo_orig.iloc[i]["id"])
                        try:
                            patchear_categoria_mo(cat_id, {"descripcion": edit_desc, "costo_hora": float(edit_costo)})
                            guardados_mo += 1
                        except Exception as e:
                            errores_mo.append(f"Cat {cat_id}: {e}")
                if guardados_mo:
                    st.success(f"✅ {guardados_mo} categoría(s) actualizadas.")
                    mo_r, _ = cargar_catalogos()
                    st.session_state.central_mo = mo_r
                elif not errores_mo:
                    st.info("Sin cambios detectados.")
                for err in errores_mo:
                    st.error(err)
        else:
            st.info("No hay categorías de mano de obra cargadas.")

    # ── Insumos ───────────────────────────────────────────────────────────

    with col_ins:
        st.subheader("Insumos / Consumibles — Precios")

        busqueda_ins = st.text_input("🔍 Buscar insumo", key="busq_ins", placeholder="Denominación…")

        insumos_filtrados = [
            i for i in insumos
            if not busqueda_ins or busqueda_ins.lower() in (i.get("denominacion") or "").lower()
        ]

        if insumos_filtrados:
            df_ins_orig = pd.DataFrame([
                {"id": i["id"], "Denominación": i.get("denominacion", ""),
                 "Proveedor": i.get("proveedor") or "", "Unidad": i.get("unidad") or "",
                 "Costo unit.": i.get("costo_unitario", 0.0)}
                for i in insumos_filtrados
            ])
            df_ins_ed = st.data_editor(
                df_ins_orig,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                column_config={
                    "id":           st.column_config.NumberColumn("id", disabled=True, width="small"),
                    "Denominación": st.column_config.TextColumn("Denominación"),
                    "Proveedor":    st.column_config.TextColumn("Proveedor"),
                    "Unidad":       st.column_config.TextColumn("Unidad", width="small"),
                    "Costo unit.":  st.column_config.NumberColumn("Costo unit.", format="$ %.2f", min_value=0, step=0.01),
                },
                key="editor_ins",
            )
            if st.button("💾 Guardar Insumos", type="primary", use_container_width=True):
                errores_ins, guardados_ins = [], 0
                for i in range(len(df_ins_orig)):
                    cambios_ins = {}
                    for col_df, campo_api in [
                        ("Denominación", "denominacion"), ("Proveedor", "proveedor"),
                        ("Unidad", "unidad"), ("Costo unit.", "costo_unitario"),
                    ]:
                        v_orig = df_ins_orig.iloc[i][col_df]
                        v_edit = df_ins_ed.iloc[i][col_df]
                        if not _igual(v_orig, v_edit):
                            cambios_ins[campo_api] = v_edit
                    if cambios_ins:
                        ins_id = int(df_ins_orig.iloc[i]["id"])
                        try:
                            patchear_insumo(ins_id, cambios_ins)
                            guardados_ins += 1
                        except Exception as e:
                            errores_ins.append(f"Insumo {ins_id}: {e}")
                if guardados_ins:
                    st.success(f"✅ {guardados_ins} insumo(s) actualizados.")
                    _, insumos_r = cargar_catalogos()
                    st.session_state.central_insumos = insumos_r
                elif not errores_ins:
                    st.info("Sin cambios detectados.")
                for err in errores_ins:
                    st.error(err)
        else:
            st.info("No hay insumos que coincidan con la búsqueda.")

    # ── Crear nuevos registros de catálogo ────────────────────────────────

    st.divider()
    st.subheader("Agregar al catálogo")
    form_col_mo, form_col_ins = st.columns(2)

    with form_col_mo:
        st.markdown("**Nueva categoría de Mano de Obra**")
        with st.form("form_crear_cat_mo", clear_on_submit=True):
            nueva_cat_letra = st.text_input("Categoría (ej: E, F…)", max_chars=10)
            nueva_cat_desc  = st.text_input("Descripción")
            nueva_cat_costo = st.number_input("Costo/hora ($)", min_value=0.0, step=0.5)
            submitted_mo = st.form_submit_button("➕ Crear Categoría", type="primary", use_container_width=True)
        if submitted_mo:
            if not nueva_cat_letra.strip():
                st.error("La categoría es obligatoria.")
            else:
                try:
                    crear_categoria_mo_api({
                        "categoria":   nueva_cat_letra.strip().upper(),
                        "descripcion": nueva_cat_desc.strip() or None,
                        "costo_hora":  nueva_cat_costo,
                    })
                    st.success(f"✅ Categoría '{nueva_cat_letra.strip().upper()}' creada.")
                    mo_r, _ = cargar_catalogos()
                    st.session_state.central_mo = mo_r
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with form_col_ins:
        st.markdown("**Nuevo insumo / consumible**")
        with st.form("form_crear_insumo", clear_on_submit=True):
            nuevo_ins_denom  = st.text_input("Denominación")
            nuevo_ins_prov   = st.text_input("Proveedor (opcional)")
            nuevo_ins_unidad = st.text_input("Unidad (kg, m, u…)")
            nuevo_ins_costo  = st.number_input("Costo unitario ($)", min_value=0.0, step=0.01)
            submitted_ins = st.form_submit_button("➕ Crear Insumo", type="primary", use_container_width=True)
        if submitted_ins:
            if not nuevo_ins_denom.strip():
                st.error("La denominación es obligatoria.")
            else:
                try:
                    crear_insumo_api({
                        "denominacion":   nuevo_ins_denom.strip(),
                        "proveedor":      nuevo_ins_prov.strip() or None,
                        "unidad":         nuevo_ins_unidad.strip() or None,
                        "costo_unitario": nuevo_ins_costo,
                    })
                    st.success(f"✅ Insumo '{nuevo_ins_denom.strip()}' creado.")
                    _, insumos_r = cargar_catalogos()
                    st.session_state.central_insumos = insumos_r
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: DETALLE OT
# ═══════════════════════════════════════════════════════════════════════════

with tab_detalle:
    st.subheader("Detalle y Edición de OT")

    if not ots_raw:
        st.info("Sin OTs disponibles.")
    else:
        labels_ot = []
        for ot in ots_raw:
            cli = (ot.get("cliente") or {}).get("nombre", "-")
            labels_ot.append(f"{ot['id']} — {cli} | {ot.get('maquina', '-')} [{ot.get('estado', '-')}]")
        mapa_label_ot = dict(zip(labels_ot, ots_raw))

        label_sel = st.selectbox(
            "Seleccioná una OT",
            ["— Seleccionar —"] + labels_ot,
            key="det_ot_sel",
        )

        ot_det = mapa_label_ot.get(label_sel)

        if ot_det is None:
            st.info("Seleccioná una OT para ver su detalle completo.")
        else:
            ot_id_det = ot_det["id"]
            pres_det  = ot_det.get("presupuesto") or {}
            rec_det   = ot_det.get("recepcion") or {}
            diag_det  = ot_det.get("diagnostico") or {}
            cli_det   = (ot_det.get("cliente") or {}).get("nombre", "-")

            st.markdown(f"### OT {ot_id_det} — {cli_det}")
            st.divider()

            col_izq, col_der = st.columns([3, 2])

            # ── Columna izquierda ─────────────────────────────────────────

            with col_izq:
                with st.expander("📋 Datos de la OT (editable)", expanded=True):
                    d1, d2 = st.columns(2)
                    nuevo_estado_det = d1.selectbox(
                        "Estado",
                        ESTADOS_OT,
                        index=ESTADOS_OT.index(ot_det["estado"]) if ot_det.get("estado") in ESTADOS_OT else 0,
                        key=f"det_est_{ot_id_det}",
                    )
                    nueva_etapa_det = d2.selectbox(
                        "Etapa",
                        ETAPAS_OT,
                        index=ETAPAS_OT.index(ot_det["etapa"]) if ot_det.get("etapa") in ETAPAS_OT else 0,
                        key=f"det_etapa_{ot_id_det}",
                    )
                    nueva_desc_det = st.text_area(
                        "Descripción del trabajo",
                        value=ot_det.get("descripcion_trabajo") or "",
                        key=f"det_desc_{ot_id_det}",
                    )
                    f1, f2 = st.columns(2)
                    fp_det = ot_det.get("fecha_entrega_prevista")
                    fr_det = ot_det.get("fecha_entrega_real")
                    nueva_fp_det = f1.date_input(
                        "Entrega prevista",
                        value=date.fromisoformat(fp_det[:10]) if fp_det else None,
                        key=f"det_fp_{ot_id_det}",
                    )
                    nueva_fr_det = f2.date_input(
                        "Entrega real",
                        value=date.fromisoformat(fr_det[:10]) if fr_det else None,
                        key=f"det_fr_{ot_id_det}",
                    )
                    h1, h2 = st.columns(2)
                    nuevas_hc_det = h1.number_input(
                        "Hs cotizadas",
                        value=float(ot_det.get("horas_cotizadas") or 0),
                        min_value=0.0,
                        step=0.5,
                        key=f"det_hc_{ot_id_det}",
                    )
                    nuevas_he_det = h2.number_input(
                        "Hs empleadas",
                        value=float(ot_det.get("horas_empleadas") or 0),
                        min_value=0.0,
                        step=0.5,
                        key=f"det_he_{ot_id_det}",
                    )
                    if st.button("💾 Guardar datos de OT", key=f"det_save_ot_{ot_id_det}", type="primary"):
                        payload_ot = {}
                        if nuevo_estado_det != ot_det.get("estado"):
                            payload_ot["estado"] = nuevo_estado_det
                        if nueva_etapa_det != ot_det.get("etapa"):
                            payload_ot["etapa"] = nueva_etapa_det
                        desc_orig = ot_det.get("descripcion_trabajo") or ""
                        if nueva_desc_det != desc_orig:
                            payload_ot["descripcion_trabajo"] = nueva_desc_det
                        if nueva_fp_det and nueva_fp_det.isoformat() != (fp_det or "")[:10]:
                            payload_ot["fecha_entrega_prevista"] = nueva_fp_det.isoformat()
                        if nueva_fr_det and nueva_fr_det.isoformat() != (fr_det or "")[:10]:
                            payload_ot["fecha_entrega_real"] = nueva_fr_det.isoformat()
                        if nuevas_hc_det != float(ot_det.get("horas_cotizadas") or 0):
                            payload_ot["horas_cotizadas"] = nuevas_hc_det
                        if nuevas_he_det != float(ot_det.get("horas_empleadas") or 0):
                            payload_ot["horas_empleadas"] = nuevas_he_det
                        if payload_ot:
                            try:
                                patchear_ot(ot_id_det, payload_ot)
                                st.success("✅ OT actualizada.")
                                st.session_state.central_ots = cargar_ots()
                                st.session_state.central_df  = construir_df(st.session_state.central_ots)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                        else:
                            st.info("Sin cambios detectados.")

                with st.expander("📥 Recepción Técnica (solo lectura)", expanded=False):
                    if rec_det:
                        st.markdown(f"**Estado pieza:** {rec_det.get('estado_pieza', '-')}")
                        st.markdown(f"**Material base:** {rec_det.get('material_base', '-')}")
                        st.markdown(f"**Trabajo solicitado:** {rec_det.get('trabajo_solicitado', '-')}")
                        st.markdown(f"**Causa de falla:** {rec_det.get('causa_falla', '-')}")
                        if rec_det.get("observaciones"):
                            st.markdown(f"**Observaciones:** {rec_det['observaciones']}")
                    else:
                        st.caption("Sin recepción registrada.")

                with st.expander("🔍 Diagnóstico Técnico (solo lectura)", expanded=False):
                    if diag_det:
                        st.markdown(f"**Técnico:** {diag_det.get('tecnico_responsable', '-')}")
                        st.markdown(f"**Conclusión:** {diag_det.get('conclusion', '-')}")
                        st.markdown(f"**Tipo falla:** {diag_det.get('tipo_falla', '-')}")
                        st.markdown(f"**Factibilidad:** {'Sí' if diag_det.get('factibilidad') else 'No'}")
                        if diag_det.get("notas"):
                            st.markdown(f"**Notas:** {diag_det['notas']}")
                    else:
                        st.caption("Sin diagnóstico registrado.")

            # ── Columna derecha: Presupuesto ──────────────────────────────

            with col_der:
                st.markdown("#### 💰 Presupuesto")
                pres_id = pres_det.get("id")

                clave_mo   = f"det_items_mo_{ot_id_det}"
                clave_mat  = f"det_items_mat_{ot_id_det}"
                clave_serv = f"det_items_serv_{ot_id_det}"

                if clave_mo not in st.session_state:
                    st.session_state[clave_mo]   = list(pres_det.get("items_mano_obra") or [])
                    st.session_state[clave_mat]  = list(pres_det.get("items_materiales") or [])
                    st.session_state[clave_serv] = list(pres_det.get("items_servicios") or [])

                items_mo_det   = st.session_state[clave_mo]
                items_mat_det  = st.session_state[clave_mat]
                items_serv_det = st.session_state[clave_serv]

                # Mano de obra
                st.markdown("**Mano de Obra**")
                for i, item in enumerate(items_mo_det):
                    cols_mo = st.columns([5, 1])
                    cols_mo[0].markdown(
                        f"{item.get('categoria', '-')} — {item.get('descripcion', '')} | "
                        f"{item.get('cantidad_horas', 0)}h × {formatear_moneda(item.get('costo_hora', 0))}"
                    )
                    if cols_mo[1].button("✕", key=f"det_del_mo_{i}_{ot_id_det}"):
                        items_mo_det.pop(i)
                        st.session_state[clave_mo] = items_mo_det
                        st.rerun()

                with st.expander("➕ Agregar Mano de Obra"):
                    opciones_cat = {
                        f"{c['categoria']} — {c.get('descripcion', '')} (${c['costo_hora']}/h)": c
                        for c in mano_obra
                    }
                    if opciones_cat:
                        cat_sel = st.selectbox("Categoría", list(opciones_cat.keys()), key=f"det_cat_{ot_id_det}")
                        horas_add = st.number_input("Horas", min_value=0.5, value=1.0, step=0.5, key=f"det_hmo_{ot_id_det}")
                        if st.button("Agregar MO", key=f"det_btn_mo_{ot_id_det}"):
                            cat = opciones_cat[cat_sel]
                            items_mo_det.append({
                                "categoria_id":   cat["id"],
                                "categoria":      cat["categoria"],
                                "descripcion":    cat.get("descripcion", ""),
                                "costo_hora":     cat["costo_hora"],
                                "cantidad_horas": horas_add,
                                "subtotal":       round(cat["costo_hora"] * horas_add, 2),
                            })
                            st.session_state[clave_mo] = items_mo_det
                            st.rerun()
                    else:
                        st.caption("Sin categorías de MO disponibles.")

                st.divider()

                # Materiales
                st.markdown("**Materiales**")
                for i, item in enumerate(items_mat_det):
                    cols_mat = st.columns([5, 1])
                    cols_mat[0].markdown(
                        f"{item.get('denominacion', '-')} | "
                        f"{item.get('cantidad', 0)} {item.get('unidad', '')} × "
                        f"{formatear_moneda(item.get('costo_unitario', 0))}"
                    )
                    if cols_mat[1].button("✕", key=f"det_del_mat_{i}_{ot_id_det}"):
                        items_mat_det.pop(i)
                        st.session_state[clave_mat] = items_mat_det
                        st.rerun()

                with st.expander("➕ Agregar Material"):
                    busq_mat = st.text_input("Buscar insumo", key=f"det_busq_mat_{ot_id_det}")
                    ins_filt = [
                        ins for ins in insumos
                        if not busq_mat or busq_mat.lower() in (ins.get("denominacion") or "").lower()
                    ]
                    opciones_ins = {
                        f"{ins['denominacion']} ({ins.get('unidad', '-')}) ${ins['costo_unitario']}": ins
                        for ins in ins_filt
                    }
                    if opciones_ins:
                        ins_sel  = st.selectbox("Insumo", list(opciones_ins.keys()), key=f"det_ins_{ot_id_det}")
                        cant_add = st.number_input("Cantidad", min_value=0.1, value=1.0, step=0.5, key=f"det_cmat_{ot_id_det}")
                        if st.button("Agregar Material", key=f"det_btn_mat_{ot_id_det}"):
                            ins = opciones_ins[ins_sel]
                            items_mat_det.append({
                                "insumo_id":    ins["id"],
                                "denominacion": ins["denominacion"],
                                "unidad":       ins.get("unidad", "-"),
                                "costo_unitario": ins["costo_unitario"],
                                "cantidad":     cant_add,
                                "subtotal":     round(ins["costo_unitario"] * cant_add, 2),
                            })
                            st.session_state[clave_mat] = items_mat_det
                            st.rerun()
                    else:
                        st.caption("Sin insumos que coincidan con la búsqueda.")

                st.divider()

                # Servicios de terceros
                st.markdown("**Servicios de Terceros**")
                for i, item in enumerate(items_serv_det):
                    cols_srv = st.columns([5, 1])
                    cols_srv[0].markdown(f"{item.get('descripcion', '-')} | {formatear_moneda(item.get('monto', 0))}")
                    if cols_srv[1].button("✕", key=f"det_del_serv_{i}_{ot_id_det}"):
                        items_serv_det.pop(i)
                        st.session_state[clave_serv] = items_serv_det
                        st.rerun()

                with st.expander("➕ Agregar Servicio"):
                    desc_srv  = st.text_input("Descripción", key=f"det_desc_srv_{ot_id_det}")
                    monto_srv = st.number_input("Monto ($)", min_value=0.0, step=100.0, key=f"det_monto_srv_{ot_id_det}")
                    if st.button("Agregar Servicio", key=f"det_btn_srv_{ot_id_det}"):
                        if desc_srv and monto_srv > 0:
                            items_serv_det.append({"descripcion": desc_srv, "monto": monto_srv})
                            st.session_state[clave_serv] = items_serv_det
                            st.rerun()
                        else:
                            st.warning("Ingresá descripción y monto mayor a 0.")

                st.divider()

                # Totales y guardar
                otros_gastos_det = st.number_input(
                    "Otros gastos ($)", min_value=0.0, step=100.0,
                    value=float(pres_det.get("otros_gastos") or 0),
                    key=f"det_og_{ot_id_det}",
                )
                pct_gan_det = st.number_input(
                    "% Ganancia", min_value=0.0, max_value=500.0, step=5.0,
                    value=float(pres_det.get("porcentaje_ganancia") or 0),
                    key=f"det_pct_{ot_id_det}",
                )

                tc_det, tv_det = calcular_total_presupuesto(
                    items_mo_det, items_mat_det, items_serv_det, otros_gastos_det, pct_gan_det
                )
                st.markdown(f"**Costo total: {formatear_moneda(tc_det)}**")
                st.markdown(f"**Precio venta: {formatear_moneda(tv_det)}**")

                if st.button("💾 Guardar Presupuesto", key=f"det_save_pres_{ot_id_det}", type="primary", use_container_width=True):
                    if not pres_id:
                        st.warning("Esta OT aún no tiene presupuesto. Crealo desde el módulo 03 — Presupuesto.")
                    else:
                        payload_pres = {
                            "items_mano_obra":    items_mo_det,
                            "items_materiales":   items_mat_det,
                            "items_servicios":    items_serv_det,
                            "otros_gastos":       otros_gastos_det,
                            "porcentaje_ganancia": pct_gan_det,
                            "total_costo":        tc_det,
                            "total_venta":        tv_det,
                        }
                        try:
                            patchear_presupuesto(pres_id, payload_pres)
                            st.success("✅ Presupuesto guardado.")
                            st.session_state.central_ots = cargar_ots()
                            st.session_state.central_df  = construir_df(st.session_state.central_ots)
                            for k in [clave_mo, clave_mat, clave_serv]:
                                st.session_state.pop(k, None)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al guardar presupuesto: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 6: DESCARGAS INDIVIDUALES
# ═══════════════════════════════════════════════════════════════════════════

with tab_descargas:
    st.subheader("Descarga individual por OT")
    ids_ot = [ot["id"] for ot in ots_raw]
    if ids_ot:
        ot_sel_id = st.selectbox("Seleccioná una OT", ids_ot, key="dl_ot")
        ot_datos  = next((o for o in ots_raw if o["id"] == ot_sel_id), None)
        if ot_datos:
            cli_n = (ot_datos.get("cliente") or {}).get("nombre", "")
            st.caption(f"**{ot_sel_id}** · {cli_n} · {ot_datos.get('maquina', '-')} · {ot_datos.get('estado', '-')}")
            st.download_button(
                f"📥 Descargar {ot_sel_id}",
                data=generar_csv_ot(ot_datos),
                file_name=f"historial_{ot_sel_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("Sin OTs disponibles.")
