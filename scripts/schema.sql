-- =====================================================================
-- Konmethal — Schema de Base de Datos
-- Ejecutar en el SQL Editor de Supabase
-- =====================================================================

-- Habilitar la extensión para UUIDs si no está habilitada
-- (Supabase la tiene por defecto)

-- -------------------------------------------------------------------
-- CLIENTES
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id BIGSERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    rubro TEXT,
    telefono TEXT,
    contacto TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------------
-- ÓRDENES DE TRABAJO
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ordenes_trabajo (
    id TEXT PRIMARY KEY,              -- formato: "OT-2026-001"
    cliente_id BIGINT REFERENCES clientes(id),
    fecha_ingreso DATE DEFAULT CURRENT_DATE,
    maquina TEXT,
    descripcion_trabajo TEXT,
    estado TEXT DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'EN_PROCESO', 'ESPERANDO_APROBACION', 'DEMORADO', 'ENTREGADO', 'CANCELADO')),
    etapa TEXT CHECK (etapa IN ('Cotizando', 'Cotizado', 'En Proceso', 'Terminado', 'Facturado')),
    fecha_inicio_prevista DATE,
    fecha_entrega_prevista DATE,
    fecha_entrega_real DATE,
    fecha_diagnostico TIMESTAMPTZ,           -- cuándo se completó el diagnóstico
    fecha_envio_presupuesto TIMESTAMPTZ,     -- cuándo se envió el PDF al cliente
    fecha_respuesta_cliente TIMESTAMPTZ,     -- cuándo respondió el cliente
    fecha_inicio_real TIMESTAMPTZ,           -- cuándo arrancó el trabajo real
    horas_cotizadas NUMERIC(10,2),
    horas_empleadas NUMERIC(10,2),
    monto_cotizacion NUMERIC(12,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------------
-- RECEPCIÓN TÉCNICA
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recepcion_tecnica (
    id BIGSERIAL PRIMARY KEY,
    ot_id TEXT REFERENCES ordenes_trabajo(id) ON DELETE CASCADE,
    estado_pieza TEXT,
    material_base TEXT,
    trabajo_solicitado TEXT,
    causa_falla TEXT,
    parametros_operacion JSONB,       -- {velocidad, presion, temperatura}
    fotos_urls JSONB DEFAULT '[]',    -- array de URLs
    observaciones TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------------
-- DIAGNÓSTICO TÉCNICO
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS diagnostico_tecnico (
    id BIGSERIAL PRIMARY KEY,
    ot_id TEXT REFERENCES ordenes_trabajo(id) ON DELETE CASCADE,
    dimensiones TEXT,
    factibilidad BOOLEAN,
    tipo_falla TEXT CHECK (tipo_falla IN ('desgaste', 'rotura', 'corrosion', 'otro')),
    conclusion TEXT CHECK (conclusion IN ('REPARABLE', 'CON_CONDICIONES', 'NO_REPARABLE')),
    antecedente_ot TEXT,
    tecnico_responsable TEXT,
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------------
-- PRESUPUESTO
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS presupuesto (
    id BIGSERIAL PRIMARY KEY,
    ot_id TEXT REFERENCES ordenes_trabajo(id) ON DELETE CASCADE,
    estado TEXT DEFAULT 'BORRADOR' CHECK (estado IN ('BORRADOR', 'APROBADO_INTERNO', 'ENVIADO', 'ACEPTADO', 'RECHAZADO')),
    items_mano_obra JSONB DEFAULT '[]',
    items_materiales JSONB DEFAULT '[]',
    items_servicios JSONB DEFAULT '[]',
    otros_gastos NUMERIC(12,2) DEFAULT 0,
    porcentaje_ganancia NUMERIC(5,2) DEFAULT 0,
    total_costo NUMERIC(12,2) DEFAULT 0,
    total_venta NUMERIC(12,2) DEFAULT 0,
    pdf_url TEXT,
    canal_comunicacion TEXT CHECK (canal_comunicacion IS NULL OR canal_comunicacion IN ('whatsapp', 'email', 'presencial', 'telefono')),
    motivo_rechazo TEXT,
    notas_respuesta TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- -------------------------------------------------------------------
-- CATEGORÍAS DE MANO DE OBRA
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias_mano_obra (
    id BIGSERIAL PRIMARY KEY,
    categoria TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    costo_hora NUMERIC(10,2) NOT NULL
);

-- -------------------------------------------------------------------
-- INSUMOS Y CONSUMIBLES
-- -------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS insumos_consumibles (
    id BIGSERIAL PRIMARY KEY,
    denominacion TEXT NOT NULL,
    proveedor TEXT,
    unidad TEXT,
    costo_unitario NUMERIC(10,2) NOT NULL
);

-- -------------------------------------------------------------------
-- ÍNDICES
-- -------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_ot_estado ON ordenes_trabajo(estado);
CREATE INDEX IF NOT EXISTS idx_ot_cliente ON ordenes_trabajo(cliente_id);
CREATE INDEX IF NOT EXISTS idx_ot_fecha ON ordenes_trabajo(fecha_ingreso DESC);
CREATE INDEX IF NOT EXISTS idx_recepcion_ot ON recepcion_tecnica(ot_id);
CREATE INDEX IF NOT EXISTS idx_diagnostico_ot ON diagnostico_tecnico(ot_id);
CREATE INDEX IF NOT EXISTS idx_presupuesto_ot ON presupuesto(ot_id);
-- Optimización para consultas de "esperando aprobación hace X días"
CREATE INDEX IF NOT EXISTS idx_ot_esperando_aprobacion
    ON ordenes_trabajo(estado, fecha_envio_presupuesto)
    WHERE estado = 'ESPERANDO_APROBACION';

-- -------------------------------------------------------------------
-- RLS (Row Level Security) — deshabilitado para Fase 1
-- En Fase 2 se agregará autenticación multi-rol
-- -------------------------------------------------------------------
-- Por ahora permitir acceso completo via service_key
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE ordenes_trabajo ENABLE ROW LEVEL SECURITY;
ALTER TABLE recepcion_tecnica ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostico_tecnico ENABLE ROW LEVEL SECURITY;
ALTER TABLE presupuesto ENABLE ROW LEVEL SECURITY;
ALTER TABLE categorias_mano_obra ENABLE ROW LEVEL SECURITY;
ALTER TABLE insumos_consumibles ENABLE ROW LEVEL SECURITY;

-- Políticas permisivas para Fase 1 (acceso completo)
CREATE POLICY "Acceso completo clientes" ON clientes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Acceso completo ordenes" ON ordenes_trabajo FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Acceso completo recepcion" ON recepcion_tecnica FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Acceso completo diagnostico" ON diagnostico_tecnico FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Acceso completo presupuesto" ON presupuesto FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Acceso completo categorias_mo" ON categorias_mano_obra FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Acceso completo insumos" ON insumos_consumibles FOR ALL USING (true) WITH CHECK (true);
