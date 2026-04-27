import streamlit as st

def render_sidebar():
    """Renders the standard Konmethal sidebar with navigation links."""
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #1A3A6B;
            min-width: 17.5rem !important;
            max-width: 17.5rem !important;
        }
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] .stImage {
            padding-top: 0.5rem;
        }
        [data-testid="stAppViewContainer"] > .main .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-left: 2.5rem;
            padding-right: 2.5rem;
            padding-bottom: 2rem;
        }
        @media (max-width: 1200px) {
            [data-testid="stAppViewContainer"] > .main .block-container {
                padding-left: 1.5rem;
                padding-right: 1.5rem;
            }
        }
        @media (max-width: 992px) {
            [data-testid="stSidebar"] {
                min-width: auto !important;
                max-width: none !important;
            }
            [data-testid="stAppViewContainer"] > .main .block-container {
                padding-top: 1.25rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.image("Documentacion/logo.png", use_container_width=True)
        st.markdown("---")
        # In Streamlit, page_link requires the path relative to the script running, or just the file name if it's main.
        # Since this can be called from main.py or from pages/..., we use the absolute path relative to the app root.
        # The safest way is to use the labels and filenames defined by standard streamlit pages convention
        st.page_link("main.py",            label="Dashboard",             icon="🏠")
        st.page_link("pages/01_recepcion.py",   label="Recepción de Piezas",   icon="📥")
        st.page_link("pages/02_diagnostico.py", label="Diagnóstico Técnico",   icon="🔍")
        st.page_link("pages/03_presupuesto.py", label="Presupuesto",           icon="📋")
        st.page_link("pages/04_seguimiento.py", label="Seguimiento",           icon="📊")
        st.page_link("pages/05_central.py",     label="Central",               icon="🗂️")
        st.markdown("---")
        st.caption("Bynary Solutions · 2026")
