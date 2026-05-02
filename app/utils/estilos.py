import streamlit as st


def inyectar_estilos():
    """
    Inyecta CSS centralizado para la aplicación Konmethal.
    Debe llamarse una sola vez desde sidebar.py en el inicio.
    """
    css = """
    <style>
    * {
        box-sizing: border-box;
    }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: #0D1B2A;
        width: 17.5rem !important;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF;
    }

    [data-testid="stSidebar"] .stImage {
        padding-top: 0.5rem;
    }

    [data-testid="stSidebarNav"] a {
        text-decoration: none;
        color: #FFFFFF;
    }

    [data-testid="stSidebarNav"] a:hover {
        background-color: #1A2F4E;
        border-radius: 4px;
    }

    /* MAIN CONTAINER - FONDO NEGRO */
    [data-testid="stAppViewContainer"] {
        background-color: #0A0E27;
    }

    [data-testid="stAppViewContainer"] .block-container {
        max-width: 1500px;
        padding: 2rem 2.5rem;
        background-color: #0A0E27;
    }

    body {
        background-color: #0A0E27;
        color: #FFFFFF;
    }

    @media (max-width: 1200px) {
        [data-testid="stAppViewContainer"] .block-container {
            padding: 1.5rem 1.5rem;
        }
    }

    @media (max-width: 992px) {
        [data-testid="stAppViewContainer"] .block-container {
            padding: 1rem 1.25rem;
        }
    }

    /* TIPOGRAFÍA */
    h1, h2 {
        color: #FFFFFF;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    h1 {
        font-size: 1.8rem;
        margin-bottom: 0.25rem;
    }

    h2 {
        font-size: 1.4rem;
        border-bottom: 1px solid #2A3A5A;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }

    h3 {
        color: #5EB3FF;
        font-weight: 600;
        font-size: 1.1rem;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    h4, h5, h6 {
        color: #FFFFFF;
        font-weight: 600;
    }

    p, li, td {
        color: #E0E0E0;
        font-size: 0.95rem;
    }

    small, .caption {
        color: #A0A0A0;
        font-size: 0.85rem;
    }

    /* BOTONES */
    .stButton > button[kind="primary"] {
        background-color: #1B6CA8;
        border: none;
        border-radius: 6px;
        color: #FFFFFF;
        font-weight: 600;
        padding: 0.55rem 1.5rem;
        font-size: 0.9rem;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #2E86C1;
    }

    .stButton > button[kind="secondary"] {
        border: 1px solid #3A5A7A;
        border-radius: 6px;
        color: #E0E0E0;
        background-color: #1A2744;
    }

    .stButton > button[kind="secondary"]:hover {
        border-color: #5EB3FF;
        color: #5EB3FF;
    }

    /* MÉTRICAS */
    [data-testid="metric-container"] {
        background-color: #1A2744;
        border-left: 4px solid #1B6CA8;
        border-radius: 6px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }

    [data-testid="metric-container"] > div:first-child {
        color: #A0A0A0;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    [data-testid="metric-container"] > div:nth-child(2) {
        color: #FFFFFF;
        font-weight: 700;
        font-size: 2rem;
    }

    /* INPUTS Y SELECTORES */
    .stSelectbox, .stTextInput, .stNumberInput, .stDateInput {
        border: 1px solid #3A5A7A !important;
        border-radius: 6px !important;
        background-color: #1A2744 !important;
    }

    input, select, textarea {
        border: 1px solid #3A5A7A !important;
        border-radius: 6px !important;
        background-color: #1A2744 !important;
        color: #E0E0E0 !important;
        padding: 0.6rem !important;
    }

    input::placeholder, select::placeholder, textarea::placeholder {
        color: #666666 !important;
    }

    input:focus, select:focus, textarea:focus {
        border-color: #5EB3FF !important;
        box-shadow: 0 0 0 3px rgba(94, 179, 255, 0.2) !important;
    }

    /* EXPANDERS */
    .streamlit-expanderHeader {
        border: 1px solid #3A5A7A;
        border-radius: 6px;
        background-color: #1A2744;
        padding: 0.85rem 1rem;
        font-weight: 600;
        color: #FFFFFF;
    }

    .streamlit-expanderHeader:hover {
        background-color: #233652;
        border-color: #5EB3FF;
    }

    /* TABS */
    [role="tablist"] {
        border-bottom: 2px solid #2A3A5A !important;
    }

    [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.9rem;
        color: #A0A0A0;
        background-color: transparent;
        border-bottom: 2px solid transparent !important;
        padding: 0.8rem 1.2rem !important;
    }

    [data-baseweb="tab"]:hover {
        background-color: #1A2744;
    }

    [aria-selected="true"] {
        color: #5EB3FF !important;
        background-color: transparent !important;
        border-bottom: 2px solid #5EB3FF !important;
    }

    /* TABLES - HTML */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1.5rem 0;
    }

    table thead {
        background-color: #0D1B2A;
        color: #FFFFFF;
    }

    table th {
        padding: 0.75rem 1rem;
        text-align: left;
        font-weight: 600;
        font-size: 0.9rem;
        border: none;
    }

    table td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #2A3A5A;
        color: #E0E0E0;
        font-size: 0.9rem;
    }

    table tbody tr:nth-child(even) {
        background-color: #141B35;
    }

    table tbody tr:hover {
        background-color: #1A2744;
    }

    /* BADGES - Estados */
    .badge-pendiente {
        background-color: #4A3F1F;
        color: #FFD699;
        border: 1px solid #6B5A2F;
        border-radius: 8px;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-en-proceso {
        background-color: #1A3A5A;
        color: #5EB3FF;
        border: 1px solid #2A5A7A;
        border-radius: 8px;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-demorado {
        background-color: #5A2A2A;
        color: #FF9999;
        border: 1px solid #7A4A4A;
        border-radius: 8px;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-entregado {
        background-color: #2A4A2A;
        color: #99FF99;
        border: 1px solid #4A6A4A;
        border-radius: 8px;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-borrador {
        background-color: #3A3A3A;
        color: #CCCCCC;
        border: 1px solid #5A5A5A;
        border-radius: 8px;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-aprobado {
        background-color: #2A4A2A;
        color: #99FF99;
        border: 1px solid #4A6A4A;
        border-radius: 8px;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-aceptado {
        background-color: #2A4A2A;
        color: #99FF99;
        border: 1px solid #4A6A4A;
        border-radius: 8px;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .badge-rechazado {
        background-color: #5A2A2A;
        color: #FF9999;
        border: 1px solid #7A4A4A;
        border-radius: 8px;
        padding: 0.4rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* CARD TÉCNICA */
    .card-tecnica {
        background-color: #1A2744;
        border-left: 4px solid #1B6CA8;
        border-radius: 6px;
        padding: 1.25rem;
        margin: 1.5rem 0;
        font-size: 0.9rem;
        color: #E0E0E0;
    }

    .card-tecnica h3 {
        color: #FFFFFF;
        margin-top: 0;
        font-size: 1rem;
    }

    /* MESSAGES */
    .stError, .stWarning, .stInfo, .stSuccess {
        border-radius: 6px;
        border-left: 4px solid;
    }

    .stError {
        border-left-color: #FF6B6B;
        background-color: #3A1A1A;
        color: #FFB3B3;
    }

    .stWarning {
        border-left-color: #FFB84D;
        background-color: #3A2A1A;
        color: #FFD699;
    }

    .stInfo {
        border-left-color: #5EB3FF;
        background-color: #1A2A4A;
        color: #B3D9FF;
    }

    .stSuccess {
        border-left-color: #66CC66;
        background-color: #1A3A1A;
        color: #99FF99;
    }

    /* CONTAINER CON BORDER */
    [data-testid="element-container"] .container {
        border: 1px solid #3A5A7A;
        border-radius: 6px;
        padding: 1rem;
        background-color: #1A2744;
    }

    /* DATAFRAME */
    [data-testid="stDataEditor"] {
        border-radius: 6px;
        border: 1px solid #3A5A7A;
    }

    /* RADIO BUTTONS Y CHECKBOXES */
    [data-testid="stCheckbox"] label {
        color: #E0E0E0;
    }

    [data-testid="stRadio"] label {
        color: #E0E0E0;
    }

    [data-baseweb="radio"] {
        color: #E0E0E0;
    }

    /* DIVIDER */
    hr {
        border-color: #2A3A5A;
    }

    /* OCULTAR LÍNEAS VERTICALES */
    [data-testid="stVerticalBlock"] {
        border: none !important;
    }

    .stVerticalBlock {
        border: none !important;
    }

    /* OCULTAR SEPARADORES VISUALES */
    [class*="vertical"] {
        border: none !important;
    }

    /* TEXT AREA PLACEHOLDER */
    textarea::placeholder {
        color: #666666 !important;
    }

    /* SELECTBOX DROPDOWN */
    [data-baseweb="select"] {
        color: #E0E0E0;
    }

    /* MULTISELECT */
    [data-testid="stMultiSelect"] {
        color: #E0E0E0;
    }

    /* NUMBER INPUT */
    [data-testid="stNumberInput"] input {
        color: #E0E0E0 !important;
    }

    /* DATE INPUT */
    [data-testid="stDateInput"] input {
        color: #E0E0E0 !important;
    }

    /* ENLACES */
    a {
        color: #5EB3FF;
        text-decoration: none;
    }

    a:hover {
        color: #7ECBFF;
        text-decoration: underline;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
