"""
Módulo 01 — Recepción de Piezas.
Formulario para registrar el ingreso de piezas al taller.
Crea la OT y su recepción técnica asociada.
"""

import streamlit as st
import httpx

from app.utils.supabase_client import obtener_url_api


def mostrar_pagina():
    """Página principal de recepción de piezas."""
    st.header("📋 Recepción de Piezas")
    st.markdown("Registrá el ingreso de una nueva pieza al taller.")
    
    url_api = obtener_url_api()
    
    # --- Cargar clientes ---
    try:
        respuesta = httpx.get(f"{url_api}/ot/clientes/lista", timeout=10)
        respuesta.raise_for_status()
        clientes = respuesta.json().get("clientes", [])
    except Exception as e:
        st.error(f"Error al cargar clientes: {str(e)}")
        clientes = []
    
    # --- Selector de cliente o crear nuevo ---
    st.subheader("👤 Cliente")
    
    opcion_cliente = st.radio(
        "Seleccionar cliente",
        ["Cliente existente", "Crear nuevo cliente"],
        horizontal=True,
        label_visibility="collapsed",
    )
    
    cliente_id = None
    
    if opcion_cliente == "Cliente existente":
        if clientes:
            opciones = {c["nombre"]: c["id"] for c in clientes}
            nombre_seleccionado = st.selectbox(
                "Cliente",
                options=list(opciones.keys()),
                placeholder="Seleccioná un cliente...",
            )
            if nombre_seleccionado:
                cliente_id = opciones[nombre_seleccionado]
        else:
            st.info("No hay clientes registrados. Creá uno nuevo.")
    else:
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_nombre = st.text_input("Nombre del cliente *", key="nuevo_nombre")
                nuevo_telefono = st.text_input("Teléfono", key="nuevo_telefono")
            with col2:
                nuevo_rubro = st.text_input("Rubro", key="nuevo_rubro")
                nuevo_contacto = st.text_input("Persona de contacto", key="nuevo_contacto")
    
    st.divider()
    
    # --- Datos de la OT ---
    st.subheader("🔧 Datos del Trabajo")
    
    col1, col2 = st.columns(2)
    with col1:
        maquina = st.text_input("Máquina / Equipo *", placeholder="Ej: Cilindro hidráulico Cat 320")
        descripcion_trabajo = st.text_area(
            "Descripción del trabajo solicitado *",
            placeholder="Describí brevemente el trabajo que solicita el cliente...",
        )
    with col2:
        fecha_inicio = st.date_input("Fecha inicio prevista", value=None)
        fecha_entrega = st.date_input("Fecha entrega prevista", value=None)
    
    st.divider()
    
    # --- Recepción técnica ---
    st.subheader("🔍 Recepción Técnica")
    
    col1, col2 = st.columns(2)
    with col1:
        estado_pieza = st.selectbox(
            "Estado de la pieza al ingreso",
            ["", "Bueno", "Regular", "Malo", "Muy dañado"],
            index=0,
        )
        material_base = st.text_input("Material base", placeholder="Ej: Acero SAE 4140")
        causa_falla = st.text_input("Causa de falla reportada", placeholder="Ej: Desgaste por uso")
    with col2:
        trabajo_solicitado = st.text_input(
            "Trabajo solicitado (técnico)",
            placeholder="Ej: Recromado y rectificado",
        )
        observaciones = st.text_area("Observaciones", placeholder="Notas adicionales...")
    
    # Parámetros de operación
    st.markdown("**Parámetros de operación**")
    col1, col2, col3 = st.columns(3)
    with col1:
        velocidad = st.text_input("Velocidad", placeholder="Ej: 1500 RPM")
    with col2:
        presion = st.text_input("Presión", placeholder="Ej: 250 bar")
    with col3:
        temperatura = st.text_input("Temperatura", placeholder="Ej: 80°C")
    
    st.divider()
    
    # --- Fotos ---
    st.subheader("📷 Fotos de la pieza")
    fotos = st.file_uploader(
        "Subir fotos (opcional)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )
    
    st.divider()
    
    # --- Botón guardar ---
    if st.button("💾 Guardar Recepción y Crear OT", type="primary", use_container_width=True):
        # Validaciones
        errores = []
        
        if opcion_cliente == "Cliente existente" and not cliente_id:
            errores.append("Seleccioná un cliente")
        if opcion_cliente == "Crear nuevo cliente" and not nuevo_nombre:
            errores.append("Ingresá el nombre del nuevo cliente")
        if not maquina:
            errores.append("Ingresá la máquina/equipo")
        if not descripcion_trabajo:
            errores.append("Ingresá la descripción del trabajo")
        
        if errores:
            for error in errores:
                st.error(f"⚠️ {error}")
            return
        
        with st.spinner("Guardando..."):
            try:
                # Si es cliente nuevo, crearlo primero
                if opcion_cliente == "Crear nuevo cliente":
                    datos_cliente = {
                        "nombre": nuevo_nombre,
                        "rubro": nuevo_rubro or None,
                        "telefono": nuevo_telefono or None,
                        "contacto": nuevo_contacto or None,
                    }
                    resp_cliente = httpx.post(
                        f"{url_api}/ot/clientes/crear",
                        json=datos_cliente,
                        timeout=10,
                    )
                    resp_cliente.raise_for_status()
                    cliente_id = resp_cliente.json()["cliente"]["id"]
                
                # Subir fotos si hay (las URLs se agregan después)
                fotos_urls = []
                # Nota: las fotos se suben vía la API o directamente.
                # Por ahora las dejamos como placeholder.
                
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
                        "fotos_urls": fotos_urls,
                        "observaciones": observaciones or None,
                    },
                }
                
                respuesta = httpx.post(
                    f"{url_api}/ot/",
                    json=datos_ot,
                    timeout=15,
                )
                respuesta.raise_for_status()
                resultado = respuesta.json()
                
                ot_id = resultado["ot"]["id"]
                st.success(f"✅ Orden de Trabajo **{ot_id}** creada exitosamente!")
                st.balloons()
                
                # Mostrar resumen
                with st.expander("📄 Ver resumen de la OT", expanded=True):
                    st.markdown(f"""
                    - **Nro OT:** {ot_id}
                    - **Cliente ID:** {cliente_id}
                    - **Máquina:** {maquina}
                    - **Trabajo:** {descripcion_trabajo}
                    - **Estado:** PENDIENTE
                    """)
                    
            except httpx.HTTPStatusError as e:
                detalle = e.response.json().get("detail", str(e))
                st.error(f"❌ Error al crear la OT: {detalle}")
            except Exception as e:
                st.error(f"❌ Error de conexión: {str(e)}")


# --- Ejecutar página ---
mostrar_pagina()
