"""
Aplicación principal FastAPI — Konmethal Sistema de Gestión Operativa.
Punto de entrada de la API, configuración de CORS y registro de routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import ot, presupuesto, seguimiento

app = FastAPI(
    title="Konmethal API",
    description="API del Sistema de Gestión Operativa de Konmethal — Taller Metalúrgico Industrial",
    version="1.0.0",
)

# --- CORS ---
# Permitir Streamlit local y Streamlit Cloud
origenes_permitidos = [
    "http://localhost:8501",
    "http://localhost:8502",
    "http://127.0.0.1:8501",
    "https://*.streamlit.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a los orígenes específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(ot.router)
app.include_router(presupuesto.router)
app.include_router(seguimiento.router)


# --- Health Check ---
@app.get("/", tags=["General"])
def health_check():
    """Endpoint de salud para verificar que la API está funcionando."""
    return {
        "estado": "ok",
        "servicio": "Konmethal API",
        "version": "1.0.0",
    }
