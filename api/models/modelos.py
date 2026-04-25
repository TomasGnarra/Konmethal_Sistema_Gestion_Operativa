"""
Modelos Pydantic para todas las entidades del sistema Konmethal.
Definen la estructura de request/response de la API FastAPI.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


# =====================================================================
# CLIENTE
# =====================================================================

class ClienteBase(BaseModel):
    """Campos base de un cliente."""
    nombre: str
    rubro: Optional[str] = None
    telefono: Optional[str] = None
    contacto: Optional[str] = None


class ClienteCrear(ClienteBase):
    """Modelo para crear un cliente."""
    pass


class Cliente(ClienteBase):
    """Modelo completo de un cliente."""
    id: int
    created_at: Optional[str] = None


# =====================================================================
# RECEPCIÓN TÉCNICA
# =====================================================================

class ParametrosOperacion(BaseModel):
    """Parámetros de operación de la pieza."""
    velocidad: Optional[str] = None
    presion: Optional[str] = None
    temperatura: Optional[str] = None


class RecepcionTecnicaCrear(BaseModel):
    """Modelo para crear una recepción técnica."""
    estado_pieza: Optional[str] = None
    material_base: Optional[str] = None
    trabajo_solicitado: Optional[str] = None
    causa_falla: Optional[str] = None
    parametros_operacion: Optional[dict] = None
    fotos_urls: Optional[list[str]] = Field(default_factory=list)
    observaciones: Optional[str] = None


class RecepcionTecnica(RecepcionTecnicaCrear):
    """Modelo completo de recepción técnica."""
    id: int
    ot_id: str
    created_at: Optional[str] = None


# =====================================================================
# ORDEN DE TRABAJO
# =====================================================================

class OrdenTrabajoCrear(BaseModel):
    """Modelo para crear una OT con recepción incluida."""
    # Datos de la OT
    cliente_id: int
    maquina: Optional[str] = None
    descripcion_trabajo: Optional[str] = None
    fecha_inicio_prevista: Optional[str] = None
    fecha_entrega_prevista: Optional[str] = None
    horas_cotizadas: Optional[float] = None
    # Datos de recepción técnica
    recepcion: RecepcionTecnicaCrear


class OrdenTrabajoActualizar(BaseModel):
    """Modelo para actualizar una OT."""
    estado: Optional[str] = None
    etapa: Optional[str] = None
    fecha_inicio_prevista: Optional[str] = None
    fecha_entrega_prevista: Optional[str] = None
    fecha_entrega_real: Optional[str] = None
    fecha_diagnostico: Optional[str] = None
    fecha_envio_presupuesto: Optional[str] = None
    fecha_respuesta_cliente: Optional[str] = None
    fecha_inicio_real: Optional[str] = None
    horas_cotizadas: Optional[float] = None
    horas_empleadas: Optional[float] = None
    monto_cotizacion: Optional[float] = None


class OrdenTrabajo(BaseModel):
    """Modelo completo de una orden de trabajo."""
    id: str
    cliente_id: int
    fecha_ingreso: Optional[str] = None
    maquina: Optional[str] = None
    descripcion_trabajo: Optional[str] = None
    estado: str = "PENDIENTE"
    etapa: Optional[str] = None
    fecha_inicio_prevista: Optional[str] = None
    fecha_entrega_prevista: Optional[str] = None
    fecha_entrega_real: Optional[str] = None
    fecha_diagnostico: Optional[str] = None
    fecha_envio_presupuesto: Optional[str] = None
    fecha_respuesta_cliente: Optional[str] = None
    fecha_inicio_real: Optional[str] = None
    horas_cotizadas: Optional[float] = None
    horas_empleadas: Optional[float] = None
    monto_cotizacion: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# =====================================================================
# DIAGNÓSTICO TÉCNICO
# =====================================================================

class DiagnosticoCrear(BaseModel):
    """Modelo para crear un diagnóstico técnico."""
    ot_id: str
    dimensiones: Optional[str] = None
    factibilidad: Optional[bool] = None
    tipo_falla: Optional[str] = None  # desgaste | rotura | corrosion | otro
    conclusion: Optional[str] = None  # REPARABLE | CON_CONDICIONES | NO_REPARABLE
    antecedente_ot: Optional[str] = None
    tecnico_responsable: Optional[str] = None
    notas: Optional[str] = None


class DiagnosticoTecnico(DiagnosticoCrear):
    """Modelo completo de diagnóstico técnico."""
    id: int
    created_at: Optional[str] = None


# =====================================================================
# PRESUPUESTO — ITEMS
# =====================================================================

class ItemManoObra(BaseModel):
    """Ítem de mano de obra en un presupuesto."""
    categoria_id: int
    categoria: str  # A, B, C, D
    descripcion: Optional[str] = None
    costo_hora: float
    cantidad_horas: float
    subtotal: float


class ItemMaterial(BaseModel):
    """Ítem de material/insumo en un presupuesto."""
    insumo_id: Optional[int] = None
    denominacion: str
    unidad: Optional[str] = None
    costo_unitario: float
    cantidad: float
    subtotal: float


class ItemServicio(BaseModel):
    """Ítem de servicio de terceros en un presupuesto."""
    descripcion: str
    monto: float


# =====================================================================
# PRESUPUESTO
# =====================================================================

class PresupuestoCrear(BaseModel):
    """Modelo para crear un presupuesto."""
    ot_id: str
    items_mano_obra: list[dict] = Field(default_factory=list)
    items_materiales: list[dict] = Field(default_factory=list)
    items_servicios: list[dict] = Field(default_factory=list)
    otros_gastos: float = 0.0
    porcentaje_ganancia: float = 0.0
    total_costo: float = 0.0
    total_venta: float = 0.0


class PresupuestoActualizar(BaseModel):
    """Modelo para actualizar un presupuesto."""
    items_mano_obra: Optional[list[dict]] = None
    items_materiales: Optional[list[dict]] = None
    items_servicios: Optional[list[dict]] = None
    otros_gastos: Optional[float] = None
    porcentaje_ganancia: Optional[float] = None
    total_costo: Optional[float] = None
    total_venta: Optional[float] = None
    estado: Optional[str] = None
    canal_comunicacion: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    notas_respuesta: Optional[str] = None


class Presupuesto(BaseModel):
    """Modelo completo de presupuesto."""
    id: int
    ot_id: str
    estado: str = "BORRADOR"
    items_mano_obra: Optional[list] = None
    items_materiales: Optional[list] = None
    items_servicios: Optional[list] = None
    otros_gastos: Optional[float] = 0.0
    porcentaje_ganancia: Optional[float] = 0.0
    total_costo: Optional[float] = 0.0
    total_venta: Optional[float] = 0.0
    pdf_url: Optional[str] = None
    canal_comunicacion: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    notas_respuesta: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RespuestaClientePresupuesto(BaseModel):
    """Modelo para registrar la respuesta del cliente a un presupuesto."""
    aceptado: bool
    canal_comunicacion: str  # whatsapp | email | presencial | telefono
    motivo_rechazo: Optional[str] = None  # obligatorio si aceptado=False
    notas_respuesta: Optional[str] = None


# =====================================================================
# TABLAS DE REFERENCIA
# =====================================================================

class CategoriaManoObra(BaseModel):
    """Categoría de mano de obra."""
    id: int
    categoria: str
    descripcion: Optional[str] = None
    costo_hora: float


class InsumoConsumible(BaseModel):
    """Insumo o consumible."""
    id: int
    denominacion: str
    proveedor: Optional[str] = None
    unidad: Optional[str] = None
    costo_unitario: float


# =====================================================================
# RESPUESTAS EXPANDIDAS
# =====================================================================

class OTConDetalle(BaseModel):
    """OT con todos sus datos relacionados (para seguimiento)."""
    id: str
    cliente_id: int
    fecha_ingreso: Optional[str] = None
    maquina: Optional[str] = None
    descripcion_trabajo: Optional[str] = None
    estado: str
    etapa: Optional[str] = None
    fecha_inicio_prevista: Optional[str] = None
    fecha_entrega_prevista: Optional[str] = None
    fecha_entrega_real: Optional[str] = None
    fecha_diagnostico: Optional[str] = None
    fecha_envio_presupuesto: Optional[str] = None
    fecha_respuesta_cliente: Optional[str] = None
    fecha_inicio_real: Optional[str] = None
    horas_cotizadas: Optional[float] = None
    horas_empleadas: Optional[float] = None
    monto_cotizacion: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Relaciones
    cliente: Optional[dict] = None
    recepcion: Optional[dict] = None
    diagnostico: Optional[dict] = None
    presupuesto: Optional[dict] = None
