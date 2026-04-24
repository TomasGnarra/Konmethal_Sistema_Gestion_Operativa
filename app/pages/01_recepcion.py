"""
Módulo 01 — Recepción de Piezas.
Formulario para registrar el ingreso de piezas al taller.
Crea la OT y su recepción técnica asociada.
"""

import streamlit as st
import httpx

from app.utils.supabase_client import obtener_url_api
from app.components.sidebar import render_sidebar


def mostrar_pagina():
    """Página principal de recepción de piezas."""
    render_sidebar()
    st.header("📥 Recepción de Piezas")
    st.markdown("Nueva Orden de Trabajo")
    st.divider()
    
    # Manejar estado post-guardado
    if st.session_state.get("recepcion_exitosa"):
        ot_id = st.session_state.recepcion_ot_id
        st.success(f"✅ OT **{ot_id}** creada correctamente")
        st.info("La orden quedó en estado PENDIENTE. El técnico puede iniciar el diagnóstico.")
        if st.button("Registrar otra OT", use_container_width=True):
            st.session_state.recepcion_exitosa = False
            st.session_state.recepcion_ot_id = None
            st.rerun()
        return

    url_api = obtener_url_api()
    
    # --- Cargar clientes ---
    try:
        respuesta = httpx.get(f"{url_api}/ot/clientes/lista", timeout=10)
        respuesta.raise_for_status()
        clientes = respuesta.json().get("clientes", [])
    except Exception as e:
        st.error(f"Error al cargar clientes: {str(e)}")
        clientes = []
    
    # === SECCIÓN: DATOS DEL CLIENTE ===
    with st.expander("👤 Datos del Cliente", expanded=True):
        opcion_cliente = st.radio(
            "Seleccionar cliente",
            ["Cliente existente", "Crear nuevo cliente"],
            horizontal=True,
            label_visibility="collapsed",
        )
        
        cliente_id = None
        nuevo_nombre, nuevo_telefono, nuevo_rubro, nuevo_contacto = "", "", "", ""
        
        if opcion_cliente == "Cliente existente":
            if clientes:
                opciones = {c["nombre"]: c["id"] for c in clientes}
                nombre_seleccionado = st.selectbox(
                    "Cliente",
                    options=[""] + list(opciones.keys()),
                    index=0,
                )
                if nombre_seleccionado:
                    cliente_id = opciones[nombre_seleccionado]
            else:
                st.info("No hay clientes registrados. Creá uno nuevo.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                nuevo_nombre = st.text_input("Nombre del cliente *", key="nuevo_nombre")
                nuevo_telefono = st.text_input("Teléfono", key="nuevo_telefono")
            with c2:
                nuevo_rubro = st.text_input("Rubro", key="nuevo_rubro")
                nuevo_contacto = st.text_input("Persona de contacto", key="nuevo_contacto")

    # === SECCIÓN: DATOS DEL EQUIPO ===
    with st.expander("🔧 Datos del Equipo", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            maquina = st.text_input("Máquina / Equipo *", placeholder="Ej: Cilindro hidráulico Cat 320")
            descripcion_trabajo = st.text_area("Descripción del trabajo solicitado *", placeholder="Describí brevemente el trabajo que solicita el cliente...")
        with c2:
            fecha_inicio = st.date_input("Fecha inicio prevista", value=None)
            fecha_entrega = st.date_input("Fecha entrega prevista", value=None)

    # === SECCIÓN: ESTADO DE LA PIEZA ===
    with st.expander("🔍 Estado de la Pieza al Ingreso", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            estado_pieza = st.selectbox("Estado general", ["", "Bueno", "Regular", "Malo", "Muy dañado"])
            material_base = st.text_input("Material base", placeholder="Ej: Acero SAE 4140")
            causa_falla = st.text_input("Causa de falla reportada", placeholder="Ej: Desgaste por uso")
        with c2:
            trabajo_solicitado = st.text_input("Trabajo solicitado (técnico)", placeholder="Ej: Recromado y rectificado")
            
        st.markdown("**Parámetros de operación**")
        p1, p2, p3 = st.columns(3)
        velocidad = p1.text_input("Velocidad", placeholder="1500 RPM")
        presion = p2.text_input("Presión", placeholder="250 bar")
        temperatura = p3.text_input("Temperatura", placeholder="80°C")

    # === SECCIÓN: OBSERVACIONES Y FOTOS ===
    with st.expander("📷 Observaciones y Fotos"):
        observaciones = st.text_area("Observaciones adicionales", placeholder="Notas adicionales...")
        fotos = st.file_uploader("Subir fotos (opcional)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Botón guardar ---
    if st.button("💾 Registrar Orden de Trabajo", type="primary", use_container_width=True):
        # Validaciones
        errores = []
        if opcion_cliente == "Cliente existente" and not cliente_id:
            errores.append("Seleccioná un cliente existente o creá uno nuevo.")
        if opcion_cliente == "Crear nuevo cliente" and not nuevo_nombre:
            errores.append("Ingresá el nombre del nuevo cliente.")
        if not maquina:
            errores.append("Ingresá la máquina/equipo.")
        if not descripcion_trabajo:
            errores.append("Ingresá la descripción del trabajo solicitado.")
            
        if errores:
            for error in errores:
                st.warning(f"⚠️ {error}")
            return
            
        with st.spinner("Guardando..."):
            try:
                # Crear cliente si es necesario
                if opcion_cliente == "Crear nuevo cliente":
                    datos_cliente = {
                        "nombre": nuevo_nombre,
                        "rubro": nuevo_rubro or None,
                        "telefono": nuevo_telefono or None,
                        "contacto": nuevo_contacto or None,
                    }
                    resp_cliente = httpx.post(f"{url_api}/ot/clientes/crear", json=datos_cliente, timeout=10)
                    resp_cliente.raise_for_status()
                    cliente_id = resp_cliente.json()["cliente"]["id"]
                
                # Crear la OT con recepción
                datos_ot = {
                    "cliente_id": cliente_id,
                    "maquina": maquina,
                    "descripcion_trabajo": descripcion_trabajo,
                    "fecha_inicio_prevista": fecha_inicio.isoformat() if fecha_inicio else None,
                    "fecha_entrega_prevista": fecha_entrega.isoformat() if fecha_entrega else None,
                    "recepcion": {
                        "estado_pieza": estado_pieza or None,
                        "material_base": material_base or None,
                        "trabajo_solicitado": trabajo_solicitado or None,
                        "causa_falla": causa_falla or None,
                        "parametros_operacion": {
                            "velocidad": velocidad or None,
                            "presion": presion or None,
                            "temperatura": temperatura or None,
                        },
                        "fotos_urls": [],
                        "observaciones": observaciones or None,
                    },
                }
                
                respuesta = httpx.post(f"{url_api}/ot/", json=datos_ot, timeout=15)
                respuesta.raise_for_status()
                resultado = respuesta.json()
                
                ot_id = resultado["ot"]["id"]
                
                st.session_state.recepcion_exitosa = True
                st.session_state.recepcion_ot_id = ot_id
                st.rerun()
                    
            except httpx.HTTPStatusError as e:
                detalle = e.response.json().get("detail", str(e))
                st.error(f"❌ Error al crear la OT: {detalle}")
            except Exception as e:
                st.error(f"❌ Error de conexión: {str(e)}")


if __name__ == "__main__":
    mostrar_pagina()
