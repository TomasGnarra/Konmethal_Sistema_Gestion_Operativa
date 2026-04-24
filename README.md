# Konmethal — Sistema de Gestión Operativa

Sistema de gestión de órdenes de trabajo para **Konmethal**, taller metalúrgico industrial.

Desarrollado por **Bynary Solutions**.

## Stack

- **Frontend:** Streamlit (multi-página)
- **Backend:** FastAPI
- **Base de datos:** Supabase (PostgreSQL)
- **PDF:** ReportLab
- **Deploy:** Streamlit Cloud + Render

## Instalación

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd Konmethal_Sistema_Gestion_Operativa

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Supabase

# 4. Crear tablas en Supabase
# Ejecutar el SQL en scripts/schema.sql en tu proyecto Supabase

# 5. Cargar datos iniciales
python scripts/seed_data.py
```

## Uso

```bash
# Terminal 1 — API FastAPI
uvicorn api.main:app --reload --port 8000

# Terminal 2 — App Streamlit
streamlit run app/main.py
```

## Estructura

```
app/          → Frontend Streamlit (páginas + utilidades)
api/          → Backend FastAPI (routers + modelos + servicios)
scripts/      → Scripts de utilidad (seed, schema)
Documentacion/→ Documentos de referencia del cliente
```

## Flujo de negocio

```
Ingresa pieza → Recepción (OT) → Diagnóstico técnico
→ Presupuesto (borrador → aprobación → PDF) → Seguimiento → Entrega
```

## Licencia

Propietario — Bynary Solutions © 2026
