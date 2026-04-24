import streamlit as st

COLORES_ESTADO = {
    "PENDIENTE":        {"bg": "#FEF3CD", "texto": "#856404", "borde": "#FFDA6A"},
    "EN_PROCESO":       {"bg": "#DBEAFE", "texto": "#1A3A6B", "borde": "#93C5FD"},
    "DEMORADO":         {"bg": "#F8D7DA", "texto": "#842029", "borde": "#F1AEB5"},
    "ENTREGADO":        {"bg": "#D1E7DD", "texto": "#0A3622", "borde": "#A3CFBB"},
    "BORRADOR":         {"bg": "#E2E3E5", "texto": "#41464B", "borde": "#C4C8CB"},
    "APROBADO_INTERNO": {"bg": "#D1E7DD", "texto": "#0A3622", "borde": "#A3CFBB"},
    "ENVIADO":          {"bg": "#DBEAFE", "texto": "#1A3A6B", "borde": "#93C5FD"},
    "ACEPTADO":         {"bg": "#D1E7DD", "texto": "#0A3622", "borde": "#A3CFBB"},
    "RECHAZADO":        {"bg": "#F8D7DA", "texto": "#842029", "borde": "#F1AEB5"},
}

def badge_estado(estado: str) -> str:
    """Retorna HTML de un badge coloreado según el estado."""
    c = COLORES_ESTADO.get(estado, {"bg": "#eee", "texto": "#333", "borde": "#ccc"})
    return (
        f'<span style="background:{c["bg"]};color:{c["texto"]};'
        f'border:1px solid {c["borde"]};padding:3px 10px;'
        f'border-radius:12px;font-size:0.82em;font-weight:600;">'
        f'{estado}</span>'
    )
