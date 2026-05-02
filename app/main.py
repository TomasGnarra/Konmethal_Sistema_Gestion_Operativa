"""
Konmethal — Dashboard Operativo
Vista para operarios: OTs activas, alertas, detalle por OT.
"""

import sys
from pathlib import Path

root_path = str(Path(__file__).resolve().parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st
import httpx
import json
from datetime import datetime, date

from app.utils.supabase_client import obtener_url_api, obtener_cliente_supabase_admin
from app.utils.helpers import formatear_fecha, calcular_atraso, construir_timeline
from app.components.sidebar import render_sidebar
from app.components.estado_badge import badge_estado

st.set_page_config(
    page_title="Konmethal — Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1A3A6B; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    .stButton > button[kind="primary"] {
        background-color: #1F78C1; border: none; color: white; font-weight: bold;
    }
    .stButton > button[kind="primary"]:hover { background-color: #1A3A6B; }
    h1, h2 { color: #1A3A6B; }
    h3 { color: #1F78C1; }
    [data-testid="metric-container"] {
        background-color: #F5F5F5;
        border-left: 4px solid #1F78C1;
        padding: 12px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

render_sidebar()

st.title("🔧 Dashboard Operativo")
st.caption("Estado actual del taller · Órdenes activas y alertas del día.")

url_api = obtener_url_api()

# ── Carga de datos ──────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def cargar_ots_activas(url: str) -> list[dict]:
    resp = httpx.get(
        f"{url}/seguimiento/",
        params={"incluir_entregadas": False, "incluir_canceladas": False},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("ordenes_trabajo", [])

col_titulo, col_refresh = st.columns([8, 2])
if col_refresh.button("🔄 Actualizar", use_container_width=True):
    st.cache_data.clear()

try:
    with st.spinner("Cargando OTs activas..."):
        ots = cargar_ots_activas(url_api)
except Exception as e:
    st.warning(
        "⚠️ No se pudo conectar con la API. "
        "Verificá que FastAPI esté corriendo en la URL configurada."
    )
    st.code("uvicorn api.main:app --reload --port 8000", language="bash")
    st.stop()

# ── Métricas ────────────────────────────────────────────────────────────────

pendientes        = [ot for ot in ots if ot.get("estado") == "PENDIENTE"]
en_proceso        = [ot for ot in ots if ot.get("estado") == "EN_PROCESO"]
demoradas         = [ot for ot in ots if ot.get("estado") == "DEMORADO"]
esp_aprobacion    = [ot for ot in ots if ot.get("estado") == "ESPERANDO_APROBACION"]

hoy = date.today()

def _dias_restantes(ot: dict) -> int | None:
    f = ot.get("fecha_entrega_prevista")
    if not f:
        return None
    try:
        return (datetime.fromisoformat(f[:10]).date() - hoy).days
    except (ValueError, TypeError):
        return None

atrasadas = [ot for ot in ots if (_dias_restantes(ot) or 1) < 0]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("🔧 OTs Activas",          len(ots))
m2.metric("📋 Pendientes",           len(pendientes))
m3.metric("⚙️ En Proceso",          len(en_proceso))
m4.metric("⏳ Esp. Aprobación",      len(esp_aprobacion))
m5.metric("🔴 Atrasadas",           len(atrasadas), delta_color="inverse")

st.divider()

# ── Alertas ─────────────────────────────────────────────────────────────────

alertas = []

for ot in demoradas:
    alertas.append(("error", f"🔴 **{ot['id']}** ({(ot.get('cliente') or {}).get('nombre', '-')}) — Estado DEMORADO"))

for ot in atrasadas:
    if ot.get("estado") not in ("DEMORADO",):
        dias = abs(_dias_restantes(ot) or 0)
        alertas.append(("error", f"🔴 **{ot['id']}** — Atrasada **{dias} días** (entrega: {formatear_fecha(ot.get('fecha_entrega_prevista'))})"))

for ot in esp_aprobacion:
    f_envio = ot.get("fecha_envio_presupuesto")
    if f_envio:
        try:
            fecha_envio = datetime.fromisoformat(f_envio.replace("Z", "+00:00"))
            dias_esp = (datetime.now(fecha_envio.tzinfo) - fecha_envio).days
            if dias_esp > 3:
                alertas.append(("warning", f"⚠️ **{ot['id']}** esperando respuesta del cliente hace **{dias_esp} días**"))
        except (ValueError, TypeError):
            pass

if alertas:
    with st.expander(f"🚨 {len(alertas)} alerta(s) activa(s)", expanded=True):
        for tipo, msg in alertas:
            if tipo == "error":
                st.error(msg)
            else:
                st.warning(msg)
else:
    st.success("✅ Sin alertas activas. ¡Todo en orden!")

st.divider()

# ── Tabla de OTs activas ─────────────────────────────────────────────────────

st.subheader("📋 Órdenes de Trabajo Activas")

if not ots:
    st.info("No hay órdenes de trabajo activas en este momento.")
    st.stop()

# Filtro rápido por estado
estados_presentes = sorted({ot.get("estado", "") for ot in ots if ot.get("estado")})
filtro = st.multiselect(
    "Filtrar por estado",
    options=estados_presentes,
    default=[],
    label_visibility="collapsed",
    placeholder="Filtrar por estado…",
)
ots_filtradas = [ot for ot in ots if not filtro or ot.get("estado") in filtro]
ots_ordenadas = sorted(ots_filtradas, key=lambda x: x.get("fecha_entrega_prevista") or "9999-12-31")

html_table = """<table style="width:100%;border-collapse:collapse;font-size:0.9em;font-family:sans-serif;">
<thead><tr style="background:#1A3A6B;color:#FFF;text-align:left;border-bottom:2px solid #ddd;">
<th style="padding:10px;">NRO OT</th>
<th style="padding:10px;">CLIENTE</th>
<th style="padding:10px;">EQUIPO</th>
<th style="padding:10px;">ESTADO</th>
<th style="padding:10px;">ETAPA</th>
<th style="padding:10px;">ENTREGA PREV.</th>
<th style="padding:10px;">DÍAS</th>
</tr></thead><tbody>"""

for ot in ots_ordenadas:
    nro     = ot.get("id", "-")
    cliente = (ot.get("cliente") or {}).get("nombre", "-")
    equipo  = ot.get("maquina", "-")
    estado  = ot.get("estado", "-")
    etapa   = ot.get("etapa") or "-"
    f_ent   = ot.get("fecha_entrega_prevista")
    dias    = _dias_restantes(ot)

    dt_str = formatear_fecha(f_ent) if f_ent else "No def."
    if dias is not None:
        if dias < 0:
            dias_str = f'<span style="color:#E74C3C;font-weight:bold;">{dias}d</span>'
        elif dias <= 3:
            dias_str = f'<span style="color:#F39C12;font-weight:bold;">{dias}d</span>'
        else:
            dias_str = f'<span style="color:#27AE60;font-weight:bold;">{dias}d</span>'
    else:
        dias_str = "-"

    html_table += f"""<tr style="border-bottom:1px solid #ddd;">
<td style="padding:10px;font-weight:500;">{nro}</td>
<td style="padding:10px;">{cliente}</td>
<td style="padding:10px;">{equipo}</td>
<td style="padding:10px;">{badge_estado(estado)}</td>
<td style="padding:10px;">{etapa}</td>
<td style="padding:10px;">{dt_str}</td>
<td style="padding:10px;">{dias_str}</td>
</tr>"""

html_table += "</tbody></table>"
st.markdown(html_table, unsafe_allow_html=True)

st.divider()

# ── Detalle expandible por OT ────────────────────────────────────────────────

st.subheader("🔍 Detalle de OT")
ids_ot = [ot["id"] for ot in ots_ordenadas]

if ids_ot:
    ot_sel_id = st.selectbox("Seleccioná una OT para ver el detalle", options=ids_ot)
    ot_sel = next((o for o in ots if o["id"] == ot_sel_id), None)

    if ot_sel:
        cliente_d   = ot_sel.get("cliente") or {}
        recepcion   = ot_sel.get("recepcion") or {}
        diagnostico = ot_sel.get("diagnostico") or {}
        presupuesto = ot_sel.get("presupuesto") or {}

        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**OT:** {ot_sel.get('id')}")
        c1.markdown(f"**Cliente:** {cliente_d.get('nombre', '-')}")
        c1.markdown(f"**Equipo:** {ot_sel.get('maquina', '-')}")
        c2.markdown(f"**Estado:** {badge_estado(ot_sel.get('estado', '-'))}", unsafe_allow_html=True)
        c2.markdown(f"**Etapa:** {ot_sel.get('etapa') or '-'}")
        c2.markdown(f"**Ingreso:** {formatear_fecha(ot_sel.get('fecha_ingreso'))}")
        c3.markdown(f"**Entrega prev.:** {formatear_fecha(ot_sel.get('fecha_entrega_prevista'))}")
        c3.markdown(f"**Entrega real:** {formatear_fecha(ot_sel.get('fecha_entrega_real'))}")
        c3.markdown(f"**Técnico:** {diagnostico.get('tecnico_responsable') or '-'}")

        fotos = recepcion.get("fotos_urls") or []
        if isinstance(fotos, str):
            try:
                fotos = json.loads(fotos) if fotos else []
            except (json.JSONDecodeError, TypeError):
                fotos = [fotos] if fotos else []
        with st.expander("📷 Ver foto de la pieza"):
            fotos_validas = [f for f in fotos if f] if isinstance(fotos, list) else []
            if fotos_validas:
                cols = st.columns(min(len(fotos_validas), 5))
                for i, url in enumerate(fotos_validas[:5]):
                    cols[i].image(url, width=200)
            else:
                st.markdown(
                    '<div style="border: 2px dashed #3A5A7A; border-radius: 6px; padding: 30px; text-align: center; color: #8899AA;">📷 Sin foto</div>',
                    unsafe_allow_html=True
                )

        tab_rec, tab_diag, tab_ppto, tab_timeline = st.tabs([
            "📥 Recepción", "🔍 Diagnóstico", "📋 Presupuesto", "📅 Timeline"
        ])

        with tab_rec:
            if recepcion:
                r1, r2 = st.columns(2)
                r1.markdown(f"**Estado de la pieza:** {recepcion.get('estado_pieza') or '-'}")
                r1.markdown(f"**Material base:** {recepcion.get('material_base') or '-'}")
                r1.markdown(f"**Causa de falla:** {recepcion.get('causa_falla') or '-'}")
                r2.markdown(f"**Trabajo solicitado:** {recepcion.get('trabajo_solicitado') or '-'}")
                r2.markdown(f"**Observaciones:** {recepcion.get('observaciones') or '-'}")

                fotos = recepcion.get("fotos_urls") or []
                if isinstance(fotos, str):
                    try:
                        fotos = json.loads(fotos) if fotos else []
                    except (json.JSONDecodeError, TypeError):
                        fotos = [fotos] if fotos else []
                fotos_validas = [f for f in fotos if f]

                if fotos_validas:
                    st.markdown("**Fotos:**")
                    cols_fotos = st.columns(min(len(fotos_validas), 4))
                    for i, url in enumerate(fotos_validas[:4]):
                        cols_fotos[i].image(url, use_container_width=True)
            else:
                st.info("Sin datos de recepción.")

            st.markdown("---")
            st.markdown("**Agregar foto:**")
            archivo = st.file_uploader(
                "Subir foto de la pieza",
                type=["jpg", "jpeg", "png"],
                key=f"upload_foto_{ot_sel_id}",
                label_visibility="collapsed",
            )
            if archivo and st.button("📤 Subir foto", key=f"btn_subir_foto_{ot_sel_id}"):
                with st.spinner("Subiendo foto..."):
                    try:
                        from datetime import datetime as _dt
                        sb_admin = obtener_cliente_supabase_admin()
                        nombre = f"{ot_sel_id}/{_dt.now().strftime('%Y%m%d_%H%M%S')}_{archivo.name}"
                        sb_admin.storage.from_("fotos-piezas").upload(
                            nombre, archivo.getvalue(), {"content-type": archivo.type, "upsert": "true"}
                        )
                        url_publica = sb_admin.storage.from_("fotos-piezas").get_public_url(nombre)
                        fotos_actuales = recepcion.get("fotos_urls") or []
                        if isinstance(fotos_actuales, str):
                            try:
                                fotos_actuales = json.loads(fotos_actuales) if fotos_actuales else []
                            except (json.JSONDecodeError, TypeError):
                                fotos_actuales = [fotos_actuales] if fotos_actuales else []
                        fotos_nuevas = [f for f in fotos_actuales if f] + [url_publica]
                        sb_admin.table("recepcion_tecnica").update({"fotos_urls": fotos_nuevas}).eq("ot_id", ot_sel_id).execute()
                        st.success("✅ Foto subida correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al subir foto: {e}")

        with tab_diag:
            if diagnostico:
                d1, d2 = st.columns(2)
                d1.markdown(f"**Conclusión:** {diagnostico.get('conclusion') or '-'}")
                d1.markdown(f"**Tipo de falla:** {diagnostico.get('tipo_falla') or '-'}")
                d1.markdown(f"**Factibilidad:** {'Sí' if diagnostico.get('factibilidad') else 'No'}")
                d2.markdown(f"**Dimensiones:** {diagnostico.get('dimensiones') or '-'}")
                d2.markdown(f"**Notas:** {diagnostico.get('notas') or '-'}")
                if diagnostico.get("antecedente_ot"):
                    st.info(f"Antecedente: OT {diagnostico['antecedente_ot']}")
            else:
                st.info("Sin diagnóstico registrado.")

        with tab_ppto:
            if presupuesto:
                p1, p2 = st.columns(2)
                p1.markdown(f"**Estado:** {presupuesto.get('estado') or '-'}")
                p1.markdown(f"**Total costo:** ${presupuesto.get('total_costo') or 0:,.2f}")
                p2.markdown(f"**% Ganancia:** {presupuesto.get('porcentaje_ganancia') or 0}%")
                p2.markdown(f"**Total venta:** ${presupuesto.get('total_venta') or 0:,.2f}")

                items_mo  = presupuesto.get("items_mano_obra") or []
                items_mat = presupuesto.get("items_materiales") or []
                items_srv = presupuesto.get("items_servicios") or []

                if items_mo:
                    st.markdown("**Mano de obra:**")
                    for item in items_mo:
                        st.markdown(f"- Cat. {item.get('categoria')} · {item.get('cantidad_horas')} hs → ${item.get('subtotal', 0):,.2f}")
                if items_mat:
                    st.markdown("**Materiales:**")
                    for item in items_mat:
                        st.markdown(f"- {item.get('denominacion')} × {item.get('cantidad')} → ${item.get('subtotal', 0):,.2f}")
                if items_srv:
                    st.markdown("**Servicios:**")
                    for item in items_srv:
                        st.markdown(f"- {item.get('descripcion')} → ${item.get('monto', 0):,.2f}")

                if presupuesto.get("pdf_url"):
                    st.link_button("📄 Ver PDF", presupuesto["pdf_url"])
            else:
                st.info("Sin presupuesto registrado.")

        with tab_timeline:
            eventos = construir_timeline(ot_sel, presupuesto)
            if eventos:
                for ev in eventos:
                    icono    = ev.get("icono", "•")
                    titulo   = ev.get("titulo", "")
                    fecha    = formatear_fecha(ev.get("fecha"))
                    color    = ev.get("color", "#95A5A6")
                    opacidad = "1" if ev.get("completado") else "0.5"
                    st.markdown(
                        f'<div style="display:flex;align-items:center;margin:6px 0;opacity:{opacidad};">'
                        f'<span style="font-size:1.2em;margin-right:10px;">{icono}</span>'
                        f'<span style="color:{color};font-weight:bold;margin-right:8px;">{titulo}</span>'
                        f'<span style="color:#666;font-size:0.85em;">{fecha}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No hay hitos registrados para esta OT.")
