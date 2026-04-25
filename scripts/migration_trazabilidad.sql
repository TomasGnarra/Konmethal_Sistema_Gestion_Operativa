-- =====================================================================
-- Migración: Mejoras de Trazabilidad
-- Fecha: 2026-04-25
-- Descripción: Agrega estados ESPERANDO_APROBACION y CANCELADO,
--              timestamps de hitos, y campos de respuesta del cliente
-- =====================================================================

-- IMPORTANTE: Ejecutar este script en el SQL Editor de Supabase
-- si ya tenés tablas creadas. Si estás creando la DB desde cero,
-- usá scripts/schema.sql en su lugar.

-- -------------------------------------------------------------------
-- PASO 1: Agregar nuevos campos a ordenes_trabajo
-- -------------------------------------------------------------------

-- Campos de timestamps de hitos
ALTER TABLE ordenes_trabajo
ADD COLUMN IF NOT EXISTS fecha_diagnostico TIMESTAMPTZ;

ALTER TABLE ordenes_trabajo
ADD COLUMN IF NOT EXISTS fecha_envio_presupuesto TIMESTAMPTZ;

ALTER TABLE ordenes_trabajo
ADD COLUMN IF NOT EXISTS fecha_respuesta_cliente TIMESTAMPTZ;

ALTER TABLE ordenes_trabajo
ADD COLUMN IF NOT EXISTS fecha_inicio_real TIMESTAMPTZ;

-- Actualizar constraint de estado para incluir nuevos valores
ALTER TABLE ordenes_trabajo
DROP CONSTRAINT IF EXISTS ordenes_trabajo_estado_check;

ALTER TABLE ordenes_trabajo
ADD CONSTRAINT ordenes_trabajo_estado_check
CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'ESPERANDO_APROBACION', 'DEMORADO', 'ENTREGADO', 'CANCELADO'));

-- -------------------------------------------------------------------
-- PASO 2: Agregar nuevos campos a presupuesto
-- -------------------------------------------------------------------

ALTER TABLE presupuesto
ADD COLUMN IF NOT EXISTS canal_comunicacion TEXT;

ALTER TABLE presupuesto
ADD COLUMN IF NOT EXISTS motivo_rechazo TEXT;

ALTER TABLE presupuesto
ADD COLUMN IF NOT EXISTS notas_respuesta TEXT;

-- Agregar constraint para canal_comunicacion
ALTER TABLE presupuesto
ADD CONSTRAINT presupuesto_canal_comunicacion_check
CHECK (canal_comunicacion IS NULL OR canal_comunicacion IN ('whatsapp', 'email', 'presencial', 'telefono'));

-- -------------------------------------------------------------------
-- PASO 3: Crear índice optimizado para "esperando aprobación"
-- -------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_ot_esperando_aprobacion
    ON ordenes_trabajo(estado, fecha_envio_presupuesto)
    WHERE estado = 'ESPERANDO_APROBACION';

-- -------------------------------------------------------------------
-- VERIFICACIÓN
-- -------------------------------------------------------------------

-- Verificar que los campos se agregaron correctamente
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ordenes_trabajo'
  AND column_name IN ('fecha_diagnostico', 'fecha_envio_presupuesto', 'fecha_respuesta_cliente', 'fecha_inicio_real')
ORDER BY column_name;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'presupuesto'
  AND column_name IN ('canal_comunicacion', 'motivo_rechazo', 'notas_respuesta')
ORDER BY column_name;

-- Verificar constraints
SELECT constraint_name, check_clause
FROM information_schema.check_constraints
WHERE constraint_name IN ('ordenes_trabajo_estado_check', 'presupuesto_canal_comunicacion_check');

-- Verificar índices
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('ordenes_trabajo', 'presupuesto')
  AND indexname LIKE '%esperando%';
