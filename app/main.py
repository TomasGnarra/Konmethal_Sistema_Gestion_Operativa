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
        params={"incluir_entregadas": True},
        timeout=10,
    )
    respuesta.raise_for_status()
    ots_totales = respuesta.json().get("ordenes_trabajo", [])
    api_disponible = True
except Exception:
    ots_totales = []
    api_disponible = False

try:
    resp_insumos = httpx.get(f"{url_api}/presupuesto/catalogos/insumos", timeout=10)
    insumos = resp_insumos.json().get("insumos", []) if resp_insumos.status_code == 200 else []
except Exception:
    insumos = []

try:
    resp_mo = httpx.get(f"{url_api}/presupuesto/catalogos/mano-obra", timeout=10)
    mano_obra = resp_mo.json().get("categorias", []) if resp_mo.status_code == 200 else []
except Exception:
    mano_obra = []

if not api_disponible:
    st.warning(
        "⚠️ No se pudo conectar con la API. "
        "Verificá que FastAPI esté corriendo en la URL configurada."
    )
    st.code("uvicorn api.main:app --reload --port 8000", language="bash")
    st.stop()

# Procesamiento de métricas
ots_activas = [ot for ot in ots_totales if ot.get("estado") != "ENTREGADO" and ot.get("estado") != "CANCELADO"]
pendientes = sum(1 for ot in ots_activas if ot.get("estado") == "PENDIENTE")
esperando_aprobacion = sum(1 for ot in ots_activas if ot.get("estado") == "ESPERANDO_APROBACION")
en_ejecucion = sum(1 for ot in ots_activas if ot.get("estado") == "EN_PROCESO")
demoradas_estado = sum(1 for ot in ots_activas if ot.get("estado") == "DEMORADO")

clientes_unicos = len(set(ot.get("cliente_id") for ot in ots_totales if ot.get("cliente_id")))

presupuesto_total_cotizado = sum(
    ot.get("presupuesto", {}).get("total_venta", 0) 
    for ot in ots_totales if ot.get("presupuesto") and ot.get("presupuesto", {}).get("estado") in ["ENVIADO", "ACEPTADO", "RECHAZADO"]
)
presupuesto_total_aprobado = sum(
    ot.get("presupuesto", {}).get("total_venta", 0) 
    for ot in ots_totales if ot.get("presupuesto") and ot.get("presupuesto", {}).get("estado") == "ACEPTADO"
)

st.subheader("📈 Centro de Control Operativo")

tab_resumen, tab_historial, tab_clientes, tab_recursos = st.tabs([
    "📊 Resumen General", 
    "🗂️ Historial de Trabajos", 
    "👥 Clientes",
    "⚙️ Mano de Obra e Insumos"
])

with tab_resumen:
    # Fila 1: KPIs Principales
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🔧 OTs Activas", len(ots_activas), f"{len(ots_totales)} Históricas")
    col2.metric("👥 Clientes Atendidos", clientes_unicos)
    col3.metric("📦 Insumos Registrados", len(insumos))
    col4.metric("💰 Presupuesto Aprobado", f"${presupuesto_total_aprobado:,.2f}", f"${presupuesto_total_cotizado:,.2f} Cotizado")

    st.divider()

    # Fila 2: Gráficos y Detalles
    col_grafico, col_alertas = st.columns([2, 1])

    with col_grafico:
        st.markdown("**Distribución de Estados (OTs Activas)**")
        if ots_activas:
            df_estados = pd.DataFrame([ot.get("estado", "Desconocido") for ot in ots_activas], columns=["Estado"])
            conteo_estados = df_estados["Estado"].value_counts().reset_index()
            conteo_estados.columns = ["Estado", "Cantidad"]
            st.bar_chart(conteo_estados, x="Estado", y="Cantidad", color="#1F78C1", use_container_width=True)
        else:
            st.info("No hay OTs activas para graficar.")

    with col_alertas:
        st.markdown("**Alertas del Sistema**")
        
        # Demoradas
        if demoradas_estado > 0:
            st.error(f"🔴 **{demoradas_estado} OT(s)** en estado DEMORADO.")
        else:
            st.success("✅ Ninguna OT demorada.")

        # Esperando Aprobación hace tiempo
        if esperando_aprobacion > 0:
            ots_esperando_hace_tiempo = []
            for ot in ots_activas:
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
                    f"⚠️ **{len(ots_esperando_hace_tiempo)} OT(s) esperando respuesta > 3 días:**\n"
                    + "\n".join([f"- {ot['id']} ({ot['cliente']})" for ot in ots_esperando_hace_tiempo])
                )
            else:
                 st.info("ℹ️ OTs esperando respuesta están dentro del plazo (<= 3 días).")
        
        # OTs en Proceso
        st.info(f"🔨 **{en_ejecucion} OT(s)** actualmente en proceso.")

    st.divider()

    st.markdown("**Órdenes de Trabajo Activas**")

    if ots_activas:
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
        
        for ot in sorted(ots_activas, key=lambda x: x.get('fecha_entrega_prevista') or "9999-12-31"):
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

with tab_historial:
    st.markdown("### Buscador Histórico de Trabajos")
    
    col_f1, col_f2 = st.columns(2)
    estados_disponibles = ["Todos"] + sorted(list(set(ot.get("estado", "") for ot in ots_totales if ot.get("estado"))))
    clientes_disponibles = ["Todos"] + sorted(list(set(ot.get("cliente", {}).get("nombre", "Sin cliente") for ot in ots_totales if ot.get("cliente"))))
    
    filtro_estado = col_f1.selectbox("Filtrar por Estado", estados_disponibles)
    filtro_cliente = col_f2.selectbox("Filtrar por Cliente", clientes_disponibles)
    
    datos_tabla = []
    for ot in sorted(ots_totales, key=lambda x: x.get('fecha_ingreso') or "", reverse=True):
        cliente_nombre = ot.get("cliente", {}).get("nombre", "-") if ot.get("cliente") else "-"
        
        if filtro_estado != "Todos" and ot.get("estado") != filtro_estado:
            continue
        if filtro_cliente != "Todos" and cliente_nombre != filtro_cliente:
            continue
            
        datos_tabla.append({
            "OT": ot.get("id"),
            "Cliente": cliente_nombre,
            "Equipo": ot.get("maquina", "-"),
            "Estado": ot.get("estado", "-"),
            "Fecha Ingreso": formatear_fecha(ot.get("fecha_ingreso")) if ot.get("fecha_ingreso") else "-",
            "Entrega Real": formatear_fecha(ot.get("fecha_entrega_real")) if ot.get("fecha_entrega_real") else "Pendiente",
            "Cotizado": f"${ot.get('presupuesto', {}).get('total_venta', 0):,.2f}" if ot.get("presupuesto") else "No cotizado"
        })
        
    df_ots = pd.DataFrame(datos_tabla)
    
    if not df_ots.empty:
        st.dataframe(
            df_ots,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No se encontraron órdenes de trabajo con los filtros seleccionados.")

with tab_clientes:
    st.markdown("### Ranking de Clientes")
    clientes_dict = {}
    for ot in ots_totales:
        c_id = ot.get("cliente_id")
        if not c_id:
            continue
            
        c_nombre = ot.get("cliente", {}).get("nombre", "-")
        if c_id not in clientes_dict:
            clientes_dict[c_id] = {"Cliente": c_nombre, "Total OTs": 0, "Facturación Aprobada": 0.0}
            
        clientes_dict[c_id]["Total OTs"] += 1
        
        if ot.get("presupuesto") and ot.get("presupuesto", {}).get("estado") == "ACEPTADO":
            clientes_dict[c_id]["Facturación Aprobada"] += ot.get("presupuesto").get("total_venta", 0.0)
            
    df_clientes = pd.DataFrame(clientes_dict.values())
    if not df_clientes.empty:
        df_clientes = df_clientes.sort_values(by="Facturación Aprobada", ascending=False)
        st.dataframe(
            df_clientes.style.format({"Facturación Aprobada": "${:,.2f}"}),
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("No hay clientes registrados en el historial.")

with tab_recursos:
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.markdown("### Categorías de Mano de Obra")
        if mano_obra:
            df_mo = pd.DataFrame(mano_obra)
            cols_mo = ["categoria", "descripcion", "costo_hora"]
            df_mo = df_mo[[c for c in cols_mo if c in df_mo.columns]]
            df_mo = df_mo.rename(columns={"categoria": "Categoría", "descripcion": "Descripción", "costo_hora": "Costo/Hora"})
            if "Costo/Hora" in df_mo.columns:
                 st.dataframe(
                     df_mo.style.format({"Costo/Hora": "${:,.2f}"}), 
                     use_container_width=True, 
                     hide_index=True
                 )
            else:
                 st.dataframe(df_mo, use_container_width=True, hide_index=True)
        else:
            st.info("No hay categorías de mano de obra cargadas en el sistema.")
            
    with col_r2:
        st.markdown("### Catálogo de Insumos")
        if insumos:
            df_insumos = pd.DataFrame(insumos)
            # Mostrar solo columnas clave si existen
            cols_to_show = ["denominacion", "proveedor", "costo_unitario"]
            df_insumos = df_insumos[[c for c in cols_to_show if c in df_insumos.columns]]
            df_insumos = df_insumos.rename(columns={"denominacion": "Denominación", "proveedor": "Proveedor", "costo_unitario": "Costo"})
            if "Costo" in df_insumos.columns:
                 st.dataframe(
                     df_insumos.style.format({"Costo": "${:,.2f}"}), 
                     use_container_width=True, 
                     hide_index=True
                 )
            else:
                 st.dataframe(df_insumos, use_container_width=True, hide_index=True)
        else:
            st.info("No hay insumos cargados en el sistema.")

