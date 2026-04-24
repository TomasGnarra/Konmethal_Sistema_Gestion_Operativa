# CLAUDE.md — Konmethal Sistema de Gestión Operativa

Este archivo le da contexto completo a Claude Code sobre el proyecto.
Leelo entero antes de tocar cualquier archivo.

---

## Qué es este proyecto

Sistema de gestión operativa para **Konmethal** (taller metalúrgico industrial).
Reemplaza formularios en papel y planillas Excel por una app web interna.

Desarrollado por **Bynary Solutions** (bynary.solutions).

### Flujo principal del negocio

```
Ingresa pieza → Recepción (OT) → Diagnóstico técnico
→ Presupuesto (borrador interno → aprobación → PDF al cliente)
→ Ejecución → Seguimiento → Entrega
```

### Volumen esperado
- 2 a 5 órdenes de trabajo nuevas por día
- 2 a 3 usuarios simultáneos (admin + técnicos)
- No es una app de alto tráfico — priorizar simplicidad sobre optimización prematura

---

## Stack tecnológico

| Capa | Tecnología | Notas |
|---|---|---|
| Frontend / App | **Streamlit** | UI principal, multi-página |
| Backend / API | **FastAPI** | Lógica de negocio, generación de PDF |
| Base de datos | **Supabase (PostgreSQL)** | ORM via `supabase-py` |
| Storage | **Supabase Storage** | PDFs generados, fotos de piezas |
| PDF | **ReportLab** | Generación de presupuestos |
| Hosting app | **Streamlit Cloud** | Deploy desde GitHub |
| Hosting API | **Render** | Free tier, se duerme sin uso |
| Control versiones | **GitHub** | CI/CD automático |

### Dependencias principales (requirements.txt)
```
streamlit
fastapi
uvicorn
supabase
reportlab
python-dotenv
httpx
pillow
```

---

## Estructura del repositorio

```
/
├── CLAUDE.md                  ← este archivo
├── README.md
├── requirements.txt
├── .env.example               ← variables de entorno requeridas (sin valores reales)
├── .gitignore
│
├── app/                       ← Streamlit frontend
│   ├── main.py                ← entrada principal, navegación entre páginas
│   ├── pages/
│   │   ├── 01_recepcion.py    ← módulo recepción de piezas
│   │   ├── 02_diagnostico.py  ← módulo diagnóstico técnico
│   │   ├── 03_presupuesto.py  ← módulo armado de presupuesto
│   │   └── 04_seguimiento.py  ← módulo seguimiento de trabajos
│   ├── components/            ← widgets reutilizables de Streamlit
│   └── utils/
│       ├── supabase_client.py ← cliente Supabase singleton
│       └── helpers.py         ← funciones utilitarias generales
│
├── api/                       ← FastAPI backend
│   ├── main.py                ← app FastAPI, definición de rutas
│   ├── routers/
│   │   ├── ot.py              ← endpoints órdenes de trabajo
│   │   ├── presupuesto.py     ← endpoints presupuesto + PDF
│   │   └── seguimiento.py     ← endpoints seguimiento
│   ├── models/                ← modelos Pydantic
│   ├── services/
│   │   └── pdf_service.py     ← generación PDF con ReportLab
│   └── db/
│       └── supabase.py        ← funciones de acceso a Supabase
│
├── docs/
│   ├── formularios/           ← formularios originales del cliente (referencia)
│   └── modelo_datos.md        ← esquema de base de datos documentado
│
└── scripts/
    └── seed_data.py           ← datos iniciales (categorías MO, insumos)
```

---

## Modelo de datos (Supabase / PostgreSQL)

### Tablas principales

```sql
-- Clientes
clientes (id, nombre, rubro, telefono, contacto, created_at)

-- Órdenes de trabajo (centro del sistema)
ordenes_trabajo (
  id,                    -- ej: "OT-2026-001"
  cliente_id,            -- FK clientes
  fecha_ingreso,
  maquina,               -- nombre/modelo del equipo
  descripcion_trabajo,
  estado,                -- PENDIENTE | EN_PROCESO | DEMORADO | ENTREGADO
  etapa,                 -- Cotizando | Cotizado | En Proceso | Terminado | Facturado
  fecha_inicio_prevista,
  fecha_entrega_prevista,
  fecha_entrega_real,
  horas_cotizadas,
  horas_empleadas,
  monto_cotizacion,
  created_at, updated_at
)

-- Recepción técnica
recepcion_tecnica (
  id, ot_id,             -- FK ordenes_trabajo
  estado_pieza,
  material_base,
  trabajo_solicitado,
  causa_falla,
  parametros_operacion,  -- JSON: {velocidad, presion, temperatura}
  fotos_urls,            -- JSON array de URLs en Supabase Storage
  observaciones,
  created_at
)

-- Diagnóstico técnico
diagnostico_tecnico (
  id, ot_id,
  dimensiones,           -- texto libre o JSON
  factibilidad,          -- bool
  tipo_falla,            -- enum: desgaste | rotura | corrosion | otro
  conclusion,            -- REPARABLE | CON_CONDICIONES | NO_REPARABLE
  antecedente_ot,        -- referencia a OT anterior si existe
  tecnico_responsable,
  notas,
  created_at
)

-- Presupuesto
presupuesto (
  id, ot_id,
  estado,                -- BORRADOR | APROBADO_INTERNO | ENVIADO | ACEPTADO | RECHAZADO
  items_mano_obra,       -- JSON array
  items_materiales,      -- JSON array
  items_servicios,       -- JSON array (terceros, manual)
  otros_gastos,          -- decimal (flete, etc, manual)
  porcentaje_ganancia,   -- decimal
  total_costo,
  total_venta,
  pdf_url,               -- URL en Supabase Storage
  created_at, updated_at
)

-- Tablas de referencia (precios actualizables)
categorias_mano_obra (id, categoria, descripcion, costo_hora)
insumos_consumibles (id, denominacion, proveedor, unidad, costo_unitario)
```

---

## Módulos — comportamiento esperado

### 1. Recepción de Piezas (`01_recepcion.py`)
- Formulario con los campos del `FORMULARIO_Recepción_Técnica.docx` (ver `/docs/formularios/`)
- Al guardar: genera número de OT automático, crea registro en `ordenes_trabajo` y `recepcion_tecnica`
- Permite subir fotos → van a Supabase Storage
- Estado inicial de la OT: `PENDIENTE`

### 2. Diagnóstico Técnico (`02_diagnostico.py`)
- Lista OTs en estado `PENDIENTE`, el técnico selecciona una
- Formulario simplificado basado en `FORMULARIO_Diagnóstico_Técnico.docx`
- Al guardar: crea registro en `diagnostico_tecnico`, cambia estado OT a `EN_PROCESO`
- Muestra historial de OTs anteriores del mismo cliente/equipo

### 3. Presupuesto (`03_presupuesto.py`)
- Seleccionar OT con diagnóstico completado
- **Mano de obra**: selector de categoría (A/B/C/D) + horas → calcula automático desde tabla `categorias_mano_obra`
- **Materiales**: búsqueda en `insumos_consumibles` + cantidad → calcula automático
- **Servicios de terceros**: entrada manual (descripción + monto)
- **Otros gastos**: campo manual (flete, etc)
- **% Ganancia**: configurable, se aplica sobre el total de costos
- Flujo de aprobación:
  1. Guardar como `BORRADOR` (solo visible internamente)
  2. Botón "Aprobar internamente" → estado `APROBADO_INTERNO`
  3. Botón "Generar PDF y Enviar" → genera PDF, sube a Storage, estado `ENVIADO`
- El PDF sigue el layout del `EJ__PRESUPUESTO_FINAL.xlsx` (ver `/docs/formularios/`)

### 4. Seguimiento de Trabajos (`04_seguimiento.py`)
- Vista tipo tabla/kanban de todas las OTs activas
- Columnas: OT | Cliente | Equipo | Estado | Etapa | Fecha entrega | Atraso
- Indicador visual de atraso (rojo si fecha_entrega_prevista < hoy y no está entregado)
- Filtros: por estado, por cliente, por fecha
- Click en OT → ver detalle completo

---

## Variables de entorno requeridas

```env
# .env (nunca commitear, usar .env.example sin valores)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...   # solo para operaciones admin
API_BASE_URL=http://localhost:8000   # en prod: URL de Render
```

---

## Convenciones de código

### Idioma
- **Todo en español**: código, variables, funciones, clases, comentarios, docstrings y UI

### Naming
```python
# Variables y funciones: snake_case en español
orden_trabajo = obtener_ot_por_id(ot_id)

# Clases: PascalCase
class OrdenTrabajo(BaseModel):
    ...

# Constantes: UPPER_SNAKE_CASE
ESTADOS_OT = ["PENDIENTE", "EN_PROCESO", "DEMORADO", "ENTREGADO"]

# Archivos: snake_case en español
# servicio_pdf.py, cliente_supabase.py
```

### Streamlit — reglas
- Cada página es un archivo independiente en `app/pages/`
- Usar `st.session_state` para estado entre reruns, no variables globales
- Siempre manejar errores de Supabase con try/except y mostrar `st.error()` al usuario
- No hacer llamadas a Supabase directamente desde las páginas — usar funciones de `app/utils/`

### FastAPI — reglas
- Siempre usar modelos Pydantic para request/response
- Endpoints retornan JSON, nunca HTML
- Errores: usar `HTTPException` con códigos apropiados
- No lógica de negocio en los routers — delegarla a `services/`

### Supabase
- Un solo cliente singleton en `app/utils/supabase_client.py`
- No hardcodear IDs ni valores de tablas de referencia — siempre traerlos de la DB
- Usar `.execute()` y verificar `data` antes de procesar respuesta

---

## Archivos de referencia en `/docs/formularios/`

| Archivo | Qué representa |
|---|---|
| `FORMULARIO_Recepción_Técnica.docx` | Campos del formulario de recepción |
| `FORMULARIO_Diagnóstico_Técnico.docx` | Campos del formulario de diagnóstico |
| `ESQUEMA_PRESUPESTO.xlsx` | Estructura del presupuesto |
| `EJ__PRESUPUESTO_FINAL.xlsx` | Ejemplo de presupuesto final (layout del PDF) |
| `COSTO_MANO_DE_OBRA_EJ_.xlsx` | Tabla de categorías y costos de mano de obra |
| `INSUMOS-CONSUMIBLES-ACT.xlsx` | Tabla de insumos y consumibles con precios |
| `PLANILLA_DE_SEGUIMEINTO_EJ_.xlsx` | Ejemplo de seguimiento de trabajos |
| `SEGUIMIENTO_DE_TRABAJOS.xlsm` | Planilla de seguimiento con macros |

**Cuando necesites implementar algo, revisá primero estos archivos para respetar la lógica y estructura que ya usa el cliente.**

---

## Qué NO hacer

- ❌ No usar `st.experimental_*` (APIs deprecadas de Streamlit)
- ❌ No hardcodear strings de conexión a Supabase — siempre desde `.env`
- ❌ No crear lógica de negocio duplicada entre Streamlit y FastAPI
- ❌ No commitear archivos `.env` con valores reales
- ❌ No over-engineerear — el cliente tiene 2-5 OTs/día, no necesita queues ni workers async complejos
- ❌ No agregar dependencias sin actualizar `requirements.txt`
- ❌ No romper el flujo de aprobación del presupuesto (borrador → aprobado interno → enviado)

---

## Comandos útiles

```bash
# Correr Streamlit en desarrollo
streamlit run app/main.py

# Correr FastAPI en desarrollo
uvicorn api.main:app --reload --port 8000

# Instalar dependencias
pip install -r requirements.txt

# Cargar datos iniciales (categorías MO e insumos)
python scripts/seed_data.py
```

---

## Contexto del cliente

**Konmethal** es un taller metalúrgico industrial en Argentina.
Reparan piezas industriales: cilindros hidráulicos, inyectoras, perfiladoras, bombas, etc.
El historial de reparaciones es su activo más valioso — el sistema debe preservarlo.

**Usuarios del sistema:**
- **Admin / dueño**: acceso completo, aprueba presupuestos
- **Técnicos**: cargan recepción, diagnóstico y actualizan seguimiento

Por ahora no hay autenticación multi-rol implementada (Fase 2).
En Fase 1: un solo login compartido es suficiente.

---

*Última actualización: Abril 2026 — Bynary Solutions*
