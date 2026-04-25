"""
Konmethal — Sistema de Gestión Operativa
Punto de entrada principal de la aplicación Streamlit.
Configura la página, sidebar con navegación y muestra un resumen general.
"""

import streamlit as st
import httpx
import pandas as pd
from datetime import datetime, date

from app.utils.supabase_client import obtener_url_api
from app.utils.helpers import formatear_fecha, calcular_atraso
from app.components.sidebar import render_sidebar
from app.components.estado_badge import badge_estado

# --- Configuración de la página ---
st.set_page_config(
    page_title="Konmethal — Gestión Operativa",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Estilos Globales (Tema Konmethal) ---
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #1A3A6B;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #1F78C1;
        border: none;
        color: white;
        font-weight: bold;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1A3A6B;
    }
    h1, h2 { color: #1A3A6B; }
    h3     { color: #1F78C1; }
    [data-testid="metric-container"] {
        background-color: #F5F5F5;
        border-left: 4px solid #1F78C1;
        padding: 12px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
render_sidebar()

# --- Página de inicio / Dashboard ---
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
esperando_aprobacion = sum(1 for ot in ots if ot.get("estado") == "ESPERANDO_APROBACION")
en_ejecucion = sum(1 for ot in ots if ot.get("estado") == "EN_PROCESO")
demoradas_estado = sum(1 for ot in ots if ot.get("estado") == "DEMORADO")

# Metric 1: OTs Activas
col1.metric("🔧 OTs Activas", total_activas)

# Metric 2: Esperando Aprobación del Cliente
col2.metric("⏳ Esperando Aprobación", esperando_aprobacion)

# Metric 3: En Ejecución
col3.metric("🔨 En Ejecución", en_ejecucion)

# Metric 4: Demoradas
col4.metric("🔴 Demoradas", demoradas_estado, delta=f"-{demoradas_estado}" if demoradas_estado > 0 else None, delta_color="inverse")

# Alerta: OTs esperando aprobación hace más de 3 días
if esperando_aprobacion > 0:
    ots_esperando_hace_tiempo = []
    for ot in ots:
        if ot.get("estado") == "ESPERANDO_APROBACION" and ot.get("fecha_envio_presupuesto"):
            try:
                fecha_envio = datetime.fromisoformat(ot["fecha_envio_presupuesto"].replace('Z', '+00:00'))
                dias_esperando = (datetime.now(fecha_envio.tzinfo) - fecha_envio).days
                if dias_esperando > 3:
                    ots_esperando_hace_tiempo.append({
                        "id": ot["id"],
                        "dias": dias_esperando,
                        "cliente": ot.get("cliente", {}).get("nombre", "-") if ot.get("cliente") else "-"
                    })
            except (ValueError, TypeError):
                pass

    if ots_esperando_hace_tiempo:
        st.warning(
            f"⚠️ **{len(ots_esperando_hace_tiempo)} OT(s) esperando respuesta del cliente hace más de 3 días:**\n\n"
            + "\n".join([f"- **{ot['id']}** ({ot['cliente']}) — {ot['dias']} días" for ot in ots_esperando_hace_tiempo])
        )

st.divider()

st.subheader("Órdenes de Trabajo Activas")

if ots:
    # Preparar tabla HTML para soportar custom colores y badges
    html_table = """<table style="width:100%; border-collapse: collapse; font-size: 0.9em; font-family: sans-serif;">
<thead>
<tr style="background-color: #1A3A6B; color: #FFFFFF; text-align: left; border-bottom: 2px solid #ddd;">
<th style="padding: 12px; font-weight: bold;">NRO OT</th>
<th style="padding: 12px; font-weight: bold;">CLIENTE</th>
<th style="padding: 12px; font-weight: bold;">EQUIPO</th>
<th style="padding: 12px; font-weight: bold;">ESTADO</th>
<th style="padding: 12px; font-weight: bold;">ENTREGA PREVISTA</th>
<th style="padding: 12px; font-weight: bold;">DÍAS</th>
</tr>
</thead>
<tbody>"""
    
    for ot in sorted(ots, key=lambda x: x.get('fecha_entrega_prevista') or "9999-12-31"):
        nro = ot.get("id", "-")
        cliente = ot.get("cliente", {}).get("nombre", "-") if ot.get("cliente") else "-"
        equipo = ot.get("maquina", "-")
        estado = ot.get("estado", "-")
        
        f_entrega = ot.get("fecha_entrega_prevista")
        dias_restantes = -calcular_atraso(f_entrega) if f_entrega else None
        
        dt_str = formatear_fecha(f_entrega) if f_entrega else "No def."
        
        if dias_restantes is not None:
            if dias_restantes < 0:
                 dias_str = f'<span style="color: #E74C3C; font-weight: bold;">{dias_restantes}</span>'
            elif dias_restantes <= 3:
                 dias_str = f'<span style="color: #F39C12; font-weight: bold;">{dias_restantes}</span>'
            else:
                 dias_str = f'<span style="color: #27AE60; font-weight: bold;">{dias_restantes}</span>'
        else:
            dias_str = "-"
            
        badge = badge_estado(estado)
        
        row_html = f"""<tr style="border-bottom: 1px solid #ddd;">
<td style="padding: 12px; font-weight: 500;">{nro}</td>
<td style="padding: 12px;">{cliente}</td>
<td style="padding: 12px;">{equipo}</td>
<td style="padding: 12px;">{badge}</td>
<td style="padding: 12px;">{dt_str}</td>
<td style="padding: 12px;">{dias_str}</td>
</tr>"""
        html_table += row_html

    html_table += """</tbody>
</table>"""
    st.markdown(html_table, unsafe_allow_html=True)
else:
    st.success("✅ No hay órdenes de trabajo activas. ¡Todo al día!")

