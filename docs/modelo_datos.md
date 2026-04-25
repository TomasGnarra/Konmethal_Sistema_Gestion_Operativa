# Modelo de Datos — Konmethal Sistema de Gestión Operativa

Última actualización: 2026-04-25 (Mejoras de Trazabilidad)

---

## Diagrama de Entidades

```
CLIENTES
   |
   |--- ORDENES_TRABAJO (id: OT-YYYY-NNN)
           |
           |--- RECEPCION_TECNICA (fotos, parámetros operación)
           |--- DIAGNOSTICO_TECNICO (tipo falla, conclusión)
           |--- PRESUPUESTO (items MO/Mat/Serv, estados, PDF)
```

---

## Tablas Principales

### `clientes`

Clientes del taller (empresas industriales).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | BIGSERIAL PK | ID autogenerado |
| `nombre` | TEXT | Razón social del cliente |
| `rubro` | TEXT | Rubro industrial |
| `telefono` | TEXT | Teléfono de contacto |
| `contacto` | TEXT | Nombre de persona de contacto |
| `created_at` | TIMESTAMPTZ | Fecha de creación del registro |

---

### `ordenes_trabajo`

Centro del sistema. Una OT representa una pieza/equipo que ingresa al taller.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | TEXT PK | Número de OT (formato: `OT-2026-001`) |
| `cliente_id` | BIGINT FK | Referencia a `clientes.id` |
| `fecha_ingreso` | DATE | Fecha en que ingresó la pieza |
| `maquina` | TEXT | Nombre/modelo del equipo |
| `descripcion_trabajo` | TEXT | Trabajo solicitado (ej: "Reparación cilindro hidráulico") |
| **`estado`** | TEXT | **Estado operativo:** `PENDIENTE` \| `EN_PROCESO` \| `ESPERANDO_APROBACION` \| `DEMORADO` \| `ENTREGADO` \| `CANCELADO` |
| `etapa` | TEXT | Etapa del proceso: `Cotizando` \| `Cotizado` \| `En Proceso` \| `Terminado` \| `Facturado` |
| `fecha_inicio_prevista` | DATE | Fecha estimada de inicio de trabajo |
| `fecha_entrega_prevista` | DATE | Fecha comprometida de entrega |
| `fecha_entrega_real` | DATE | Fecha efectiva de entrega (NULL si no está entregado) |
| **`fecha_diagnostico`** | TIMESTAMPTZ | ⏱️ **Timestamp de cuándo se completó el diagnóstico técnico** |
| **`fecha_envio_presupuesto`** | TIMESTAMPTZ | ⏱️ **Timestamp de cuándo se envió el presupuesto al cliente** |
| **`fecha_respuesta_cliente`** | TIMESTAMPTZ | ⏱️ **Timestamp de cuándo el cliente respondió (aceptó/rechazó)** |
| **`fecha_inicio_real`** | TIMESTAMPTZ | ⏱️ **Timestamp de cuándo arrancó el trabajo real (después de aceptación)** |
| `horas_cotizadas` | NUMERIC(10,2) | Horas de mano de obra cotizadas |
| `horas_empleadas` | NUMERIC(10,2) | Horas reales trabajadas |
| `monto_cotizacion` | NUMERIC(12,2) | Monto total del presupuesto aceptado |
| `created_at` | TIMESTAMPTZ | Fecha de creación del registro |
| `updated_at` | TIMESTAMPTZ | Última actualización |

#### Estados de la OT

| Estado | Descripción |
|---|---|
| `PENDIENTE` | Pieza ingresada, esperando diagnóstico técnico |
| `EN_PROCESO` | Diagnóstico completado, trabajando en presupuesto o ejecutando trabajo |
| `ESPERANDO_APROBACION` | Presupuesto enviado al cliente, esperando respuesta |
| `DEMORADO` | Trabajo demorado (falta material, espera de terceros, etc.) |
| `ENTREGADO` | Trabajo completado y entregado al cliente |
| `CANCELADO` | Cliente rechazó el presupuesto o canceló el trabajo |

---

### `recepcion_tecnica`

Datos técnicos del ingreso de la pieza (formulario de recepción).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | BIGSERIAL PK | ID autogenerado |
| `ot_id` | TEXT FK | Referencia a `ordenes_trabajo.id` |
| `estado_pieza` | TEXT | Estado de la pieza al ingresar (ej: "Rota", "Desgastada") |
| `material_base` | TEXT | Material de construcción (ej: "Acero 1045") |
| `trabajo_solicitado` | TEXT | Qué trabajo solicita el cliente |
| `causa_falla` | TEXT | Causa reportada de la falla |
| `parametros_operacion` | JSONB | Parámetros de operación: `{velocidad, presion, temperatura}` |
| `fotos_urls` | JSONB | Array de URLs de fotos en Supabase Storage |
| `observaciones` | TEXT | Observaciones del técnico |
| `created_at` | TIMESTAMPTZ | Fecha de creación del registro |

---

### `diagnostico_tecnico`

Diagnóstico técnico realizado por el taller.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | BIGSERIAL PK | ID autogenerado |
| `ot_id` | TEXT FK | Referencia a `ordenes_trabajo.id` |
| `dimensiones` | TEXT | Dimensiones relevadas (texto libre o JSON) |
| `factibilidad` | BOOLEAN | ¿Es factible la reparación? |
| `tipo_falla` | TEXT | Tipo de falla: `desgaste` \| `rotura` \| `corrosion` \| `otro` |
| `conclusion` | TEXT | Conclusión: `REPARABLE` \| `CON_CONDICIONES` \| `NO_REPARABLE` |
| `antecedente_ot` | TEXT | Referencia a OT anterior del mismo equipo (si existe) |
| `tecnico_responsable` | TEXT | Nombre del técnico que hizo el diagnóstico |
| `notas` | TEXT | Notas adicionales |
| `created_at` | TIMESTAMPTZ | Fecha de creación del registro |

---

### `presupuesto`

Presupuesto armado para una OT.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | BIGSERIAL PK | ID autogenerado |
| `ot_id` | TEXT FK | Referencia a `ordenes_trabajo.id` |
| `estado` | TEXT | Estado del presupuesto: `BORRADOR` \| `APROBADO_INTERNO` \| `ENVIADO` \| `ACEPTADO` \| `RECHAZADO` |
| `items_mano_obra` | JSONB | Array de ítems de mano de obra |
| `items_materiales` | JSONB | Array de ítems de materiales/insumos |
| `items_servicios` | JSONB | Array de servicios de terceros |
| `otros_gastos` | NUMERIC(12,2) | Otros gastos (flete, envíos, etc.) |
| `porcentaje_ganancia` | NUMERIC(5,2) | % de ganancia aplicado |
| `total_costo` | NUMERIC(12,2) | Costo total (sin ganancia) |
| `total_venta` | NUMERIC(12,2) | Precio de venta al cliente (con ganancia) |
| `pdf_url` | TEXT | URL del PDF generado (en Supabase Storage) |
| **`canal_comunicacion`** | TEXT | 📞 **Canal por el que el cliente respondió:** `whatsapp` \| `email` \| `presencial` \| `telefono` |
| **`motivo_rechazo`** | TEXT | ❌ **Motivo de rechazo (si el cliente rechazó)** |
| **`notas_respuesta`** | TEXT | 📝 **Notas adicionales sobre la respuesta del cliente** |
| `created_at` | TIMESTAMPTZ | Fecha de creación del registro |
| `updated_at` | TIMESTAMPTZ | Última actualización |

#### Estados del Presupuesto

| Estado | Descripción |
|---|---|
| `BORRADOR` | Presupuesto en elaboración (solo visible internamente) |
| `APROBADO_INTERNO` | Aprobado por el taller, listo para enviar |
| `ENVIADO` | PDF enviado al cliente, esperando respuesta |
| `ACEPTADO` | Cliente aceptó el presupuesto |
| `RECHAZADO` | Cliente rechazó el presupuesto |

---

## Tablas de Referencia (Catálogos)

### `categorias_mano_obra`

Categorías de mano de obra con sus costos por hora.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | BIGSERIAL PK | ID autogenerado |
| `categoria` | TEXT UNIQUE | Categoría (ej: "A", "B", "C", "D") |
| `descripcion` | TEXT | Descripción de la categoría |
| `costo_hora` | NUMERIC(10,2) | Costo por hora de esa categoría |

**Ejemplo:**
```
A | Oficial Especializado     | $5000/h
B | Oficial                   | $3500/h
C | Medio Oficial             | $2500/h
D | Ayudante                  | $1800/h
```

---

### `insumos_consumibles`

Catálogo de materiales, insumos y consumibles con sus precios.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | BIGSERIAL PK | ID autogenerado |
| `denominacion` | TEXT | Nombre del insumo (ej: "Electrodo 7018 Ø3.2mm") |
| `proveedor` | TEXT | Proveedor habitual |
| `unidad` | TEXT | Unidad de medida (ej: "kg", "m", "unidad") |
| `costo_unitario` | NUMERIC(10,2) | Costo por unidad |

---

## Flujo Completo de una OT (con Trazabilidad)

```
1. Ingreso de Pieza
   → Se crea OT [PENDIENTE]
   → Se registra fecha_ingreso

2. Diagnóstico Técnico
   → Técnico completa formulario diagnóstico
   → OT → [EN_PROCESO, etapa: Cotizando]
   → Se registra fecha_diagnostico ⏱️

3. Armado de Presupuesto
   → Se crea presupuesto [BORRADOR]
   → Se aprueba internamente → [APROBADO_INTERNO]

4. Envío al Cliente
   → Se genera PDF y se envía
   → Presupuesto → [ENVIADO]
   → OT → [ESPERANDO_APROBACION] ⏱️
   → Se registra fecha_envio_presupuesto ⏱️

5a. Cliente ACEPTA
    → Se registra respuesta (canal_comunicacion)
    → Presupuesto → [ACEPTADO]
    → OT → [EN_PROCESO, etapa: En Proceso]
    → Se registra fecha_respuesta_cliente ⏱️
    → Se registra fecha_inicio_real ⏱️
    → Se ejecuta el trabajo
    → OT → [ENTREGADO]
    → Se registra fecha_entrega_real

5b. Cliente RECHAZA
    → Se registra respuesta (canal_comunicacion, motivo_rechazo)
    → Presupuesto → [RECHAZADO]
    → OT → [CANCELADO] ❌
    → Se registra fecha_respuesta_cliente ⏱️
```

---

## Índices

Para optimizar las consultas, se crean los siguientes índices:

```sql
-- Índices principales
CREATE INDEX idx_ot_estado ON ordenes_trabajo(estado);
CREATE INDEX idx_ot_cliente ON ordenes_trabajo(cliente_id);
CREATE INDEX idx_ot_fecha ON ordenes_trabajo(fecha_ingreso DESC);

-- Índices de relaciones
CREATE INDEX idx_recepcion_ot ON recepcion_tecnica(ot_id);
CREATE INDEX idx_diagnostico_ot ON diagnostico_tecnico(ot_id);
CREATE INDEX idx_presupuesto_ot ON presupuesto(ot_id);

-- Índice optimizado para consultas de "esperando aprobación hace X días"
CREATE INDEX idx_ot_esperando_aprobacion
    ON ordenes_trabajo(estado, fecha_envio_presupuesto)
    WHERE estado = 'ESPERANDO_APROBACION';
```

---

## Políticas de Acceso (RLS)

Para Fase 1, todas las políticas son permisivas (acceso completo).
En Fase 2 se implementará autenticación multi-rol con políticas específicas.

---

## Migración desde Versión Anterior

Si ya tenés una base de datos con el schema anterior, ejecutá el script:

```bash
scripts/migration_trazabilidad.sql
```

Este script agrega:
- Nuevos campos de timestamps de hitos
- Nuevos estados `ESPERANDO_APROBACION` y `CANCELADO`
- Campos de respuesta del cliente en `presupuesto`
- Índice optimizado para consultas de aprobación

**Importante:** Los nuevos campos aceptan NULL, por lo que las OTs existentes no perderán información. Solo las nuevas OTs tendrán los timestamps completos.

---

*Documento generado automáticamente — Bynary Solutions © 2026*
