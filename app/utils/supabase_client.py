"""
Cliente Supabase singleton para el frontend Streamlit.
Se usa para operaciones simples de lectura (selectores, listas).
Las operaciones complejas de negocio van por la API FastAPI.
"""

import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


@st.cache_resource
def obtener_cliente_supabase() -> Client:
    """
    Retorna una instancia singleton del cliente Supabase.
    Primero intenta leer desde Streamlit secrets (producción),
    si no, lee desde variables de entorno (.env local).
    """
    try:
        # Intentar leer desde Streamlit secrets (Streamlit Cloud)
        url = st.secrets["SUPABASE_URL"]
        clave = st.secrets["SUPABASE_ANON_KEY"]
    except (KeyError, FileNotFoundError):
        # Fallback a variables de entorno (.env local)
        url = os.getenv("SUPABASE_URL")
        clave = os.getenv("SUPABASE_ANON_KEY")

    if not url or not clave:
        raise ValueError(
            "No se encontraron las credenciales de Supabase. "
            "Configurá SUPABASE_URL y SUPABASE_ANON_KEY en .env o en Streamlit secrets."
        )

    return create_client(url, clave)


def obtener_url_api() -> str:
    """Retorna la URL base de la API FastAPI."""
    try:
        return st.secrets["API_BASE_URL"]
    except (KeyError, FileNotFoundError):
        return os.getenv("API_BASE_URL", "http://localhost:8000")
