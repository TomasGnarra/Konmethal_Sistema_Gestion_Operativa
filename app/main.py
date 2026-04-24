"""
Konmethal — Sistema de Gestión Operativa
Punto de entrada principal de la aplicación Streamlit.
Configura la página, sidebar con navegación y muestra un resumen general.
"""

import streamlit as st
import httpx

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import formatear_fecha, calcular_atraso

# --- Configuración de la página ---
st.set_page_config(
    page_title="Konmethal — Gestión Operativa",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
with st.sidebar:
    st.title("🔧 Konmethal")
    st.caption("Sistema de Gestión Operativa")
    st.divider()
    st.markdown("""
    ### Navegación
    Usá el menú de páginas arriba ☝️ para acceder a:
    
    - 📋 **Recepción** — Ingreso de piezas
    - 🔬 **Diagnóstico** — Evaluación técnica
    - 💰 **Presupuesto** — Armado y aprobación
    - 📊 **Seguimiento** — Estado de trabajos
    """)
    st.divider()
    st.caption("Desarrollado por [Bynary Solutions](https://bynary.solutions)")

# --- Página de inicio ---
st.title("🔧 Konmethal — Gestión Operativa")
st.markdown("**Taller Metalúrgico Industrial** — Sistema de gestión de órdenes de trabajo")

st.divider()

# --- Resumen rápido ---
url_api = obtener_url_api()

try:
    respuesta = httpx.get(
        f"{url_api}/seguimiento/",
        params={"incluir_entregadas": False},
        timeout=10,
    )
    respuesta.raise_for_status()
    ots = respuesta.json().get("ordenes_trabajo", [])
    api_disponible = True
except Exception:
    ots = []
    api_disponible = False

if not api_disponible:
    st.warning(
        "⚠️ No se pudo conectar con la API. "
        "Verificá que FastAPI esté corriendo en la URL configurada."
    )
    st.code("uvicorn api.main:app --reload --port 8000", language="bash")
    st.stop()

# KPIs
st.subheader("📈 Resumen del Taller")

col1, col2, col3, col4 = st.columns(4)

total_activas = len(ots)
pendientes = sum(1 for ot in ots if ot.get("estado") == "PENDIENTE")
en_proceso = sum(1 for ot in ots if ot.get("estado") == "EN_PROCESO")
atrasadas = sum(
    1 for ot in ots
    if calcular_atraso(ot.get("fecha_entrega_prevista")) > 0
    and ot.get("estado") != "ENTREGADO"
)

col1.metric("🔧 OTs Activas", total_activas)
col2.metric("⏳ Pendientes", pendientes)
col3.metric("🔄 En Proceso", en_proceso)
col4.metric("🔴 Atrasadas", atrasadas)

st.divider()

# OTs que necesitan atención
if atrasadas > 0:
    st.subheader("⚠️ OTs con Atraso")
    for ot in ots:
        atraso = calcular_atraso(ot.get("fecha_entrega_prevista"))
        if atraso > 0 and ot.get("estado") != "ENTREGADO":
            nombre_cliente = ot.get("cliente", {}).get("nombre", "-") if ot.get("cliente") else "-"
            st.error(
                f"🔴 **{ot['id']}** — {nombre_cliente} — {ot.get('maquina', '-')} — "
                f"**{atraso} días de atraso** — Entrega prevista: {formatear_fecha(ot.get('fecha_entrega_prevista'))}"
            )

# OTs pendientes de diagnóstico
if pendientes > 0:
    st.subheader("📋 Pendientes de Diagnóstico")
    for ot in ots:
        if ot.get("estado") == "PENDIENTE":
            nombre_cliente = ot.get("cliente", {}).get("nombre", "-") if ot.get("cliente") else "-"
            st.info(
                f"⏳ **{ot['id']}** — {nombre_cliente} — {ot.get('maquina', '-')} — "
                f"Ingresó el {formatear_fecha(ot.get('fecha_ingreso'))}"
            )

# Si no hay nada urgente
if atrasadas == 0 and pendientes == 0 and en_proceso == 0:
    st.success("✅ No hay órdenes de trabajo activas. ¡Todo al día!")
elif atrasadas == 0:
    st.success("✅ No hay trabajos atrasados.")
