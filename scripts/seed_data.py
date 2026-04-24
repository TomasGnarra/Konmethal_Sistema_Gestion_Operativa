"""
Script para cargar datos iniciales en Supabase.
Carga categorías de mano de obra, insumos de ejemplo y clientes de prueba.
Ejecutar: python scripts/seed_data.py
"""

import os
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def obtener_cliente_supabase():
    """Crea el cliente Supabase para el script."""
    url = os.getenv("SUPABASE_URL")
    clave = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not clave:
        print("❌ Error: Configurá SUPABASE_URL y SUPABASE_SERVICE_KEY en .env")
        sys.exit(1)
    return create_client(url, clave)


def cargar_categorias_mano_obra(cliente):
    """Carga las categorías de mano de obra."""
    categorias = [
        {
            "categoria": "A",
            "descripcion": "Oficial especializado — Soldadura, cromo, rectificado",
            "costo_hora": 15000.0,
        },
        {
            "categoria": "B",
            "descripcion": "Oficial — Torneado, fresado, mecanizado general",
            "costo_hora": 12000.0,
        },
        {
            "categoria": "C",
            "descripcion": "Medio oficial — Armado, desarmado, preparación",
            "costo_hora": 9000.0,
        },
        {
            "categoria": "D",
            "descripcion": "Ayudante — Tareas auxiliares, limpieza, logística",
            "costo_hora": 6500.0,
        },
    ]
    
    print("📋 Cargando categorías de mano de obra...")
    for cat in categorias:
        try:
            # Verificar si ya existe
            existente = (
                cliente.table("categorias_mano_obra")
                .select("id")
                .eq("categoria", cat["categoria"])
                .execute()
            )
            if existente.data:
                print(f"  ⏭️  Categoría {cat['categoria']} ya existe, actualizando...")
                cliente.table("categorias_mano_obra").update(cat).eq("categoria", cat["categoria"]).execute()
            else:
                cliente.table("categorias_mano_obra").insert(cat).execute()
                print(f"  ✅ Categoría {cat['categoria']} — {cat['descripcion']}")
        except Exception as e:
            print(f"  ❌ Error cargando categoría {cat['categoria']}: {e}")


def cargar_insumos_consumibles(cliente):
    """Carga insumos y consumibles de ejemplo."""
    insumos = [
        {"denominacion": "Cromo duro industrial", "proveedor": "Cromo Sur SRL", "unidad": "dm²", "costo_unitario": 8500.0},
        {"denominacion": "Electrodo de soldadura E7018", "proveedor": "ESAB", "unidad": "kg", "costo_unitario": 4200.0},
        {"denominacion": "Disco de corte 115mm", "proveedor": "Norton", "unidad": "unidad", "costo_unitario": 1800.0},
        {"denominacion": "Disco de desbaste 115mm", "proveedor": "Norton", "unidad": "unidad", "costo_unitario": 2200.0},
        {"denominacion": "Aceite hidráulico ISO 68", "proveedor": "YPF", "unidad": "litro", "costo_unitario": 3500.0},
        {"denominacion": "Retén hidráulico estándar", "proveedor": "Parker", "unidad": "unidad", "costo_unitario": 12000.0},
        {"denominacion": "O-ring NBR 70 (kit surtido)", "proveedor": "Trelleborg", "unidad": "kit", "costo_unitario": 5500.0},
        {"denominacion": "Buje de bronce SAE 65", "proveedor": "Broncemar", "unidad": "kg", "costo_unitario": 18000.0},
        {"denominacion": "Pintura epoxi industrial", "proveedor": "Sherwin Williams", "unidad": "litro", "costo_unitario": 9800.0},
        {"denominacion": "Alambre MIG ER70S-6 0.8mm", "proveedor": "ESAB", "unidad": "kg", "costo_unitario": 5200.0},
        {"denominacion": "Gas argón 99.99%", "proveedor": "Linde", "unidad": "m³", "costo_unitario": 15000.0},
        {"denominacion": "Lija al agua grano 220", "proveedor": "3M", "unidad": "hoja", "costo_unitario": 650.0},
    ]
    
    print("\n🧱 Cargando insumos y consumibles...")
    for insumo in insumos:
        try:
            existente = (
                cliente.table("insumos_consumibles")
                .select("id")
                .eq("denominacion", insumo["denominacion"])
                .execute()
            )
            if existente.data:
                print(f"  ⏭️  {insumo['denominacion']} ya existe, actualizando...")
                cliente.table("insumos_consumibles").update(insumo).eq("denominacion", insumo["denominacion"]).execute()
            else:
                cliente.table("insumos_consumibles").insert(insumo).execute()
                print(f"  ✅ {insumo['denominacion']} — ${insumo['costo_unitario']}/{insumo['unidad']}")
        except Exception as e:
            print(f"  ❌ Error cargando {insumo['denominacion']}: {e}")


def cargar_clientes_ejemplo(cliente):
    """Carga clientes para el MVP demo."""
    clientes_ejemplo = [
        {"nombre": "Agro San Luis S.A.",     "rubro": "Agroindustria",          "telefono": "2664-412300", "contacto": "Ing. Héctor Pérez"},
        {"nombre": "Plásticos del Norte",    "rubro": "Industria plástica",     "telefono": "3815-654321", "contacto": "Carlos Romero"},
        {"nombre": "Hidráulica Córdoba SRL", "rubro": "Servicios hidráulicos",  "telefono": "351-4567890", "contacto": "María González"},
        {"nombre": "Cementos Andinos S.A.",  "rubro": "Construcción / minería", "telefono": "351-9876543", "contacto": "Roberto Blanco"},
        {"nombre": "Frigorífico La Pampa",   "rubro": "Alimentaria",            "telefono": "2302-111222", "contacto": "Gustavo Ríos"},
    ]
    
    print("\n👤 Cargando clientes...")
    for cl in clientes_ejemplo:
        try:
            existente = (
                cliente.table("clientes")
                .select("id")
                .eq("nombre", cl["nombre"])
                .execute()
            )
            if existente.data:
                print(f"  ⏭️  {cl['nombre']} ya existe")
            else:
                cliente.table("clientes").insert(cl).execute()
                print(f"  ✅ {cl['nombre']} — {cl['rubro']}")
        except Exception as e:
            print(f"  ❌ Error cargando {cl['nombre']}: {e}")


def _obtener_id_cliente(cliente_supabase, nombre: str) -> int:
    """Obtiene el ID de un cliente por nombre."""
    resp = cliente_supabase.table("clientes").select("id").eq("nombre", nombre).execute()
    if resp.data:
        return resp.data[0]["id"]
    raise ValueError(f"Cliente '{nombre}' no encontrado. Ejecutá cargar_clientes_ejemplo primero.")


def _ot_existe(cliente_supabase, ot_id: str) -> bool:
    """Verifica si una OT ya existe."""
    resp = cliente_supabase.table("ordenes_trabajo").select("id").eq("id", ot_id).execute()
    return bool(resp.data)


def _recepcion_existe(cliente_supabase, ot_id: str) -> bool:
    resp = cliente_supabase.table("recepcion_tecnica").select("id").eq("ot_id", ot_id).execute()
    return bool(resp.data)


def _diagnostico_existe(cliente_supabase, ot_id: str) -> bool:
    resp = cliente_supabase.table("diagnostico_tecnico").select("id").eq("ot_id", ot_id).execute()
    return bool(resp.data)


def _presupuesto_existe(cliente_supabase, ot_id: str) -> bool:
    resp = cliente_supabase.table("presupuesto").select("id").eq("ot_id", ot_id).execute()
    return bool(resp.data)


def _calcular_totales(items_mo, items_mat, items_serv, otros_gastos, pct_ganancia):
    """Calcula total_costo y total_venta."""
    suma_mo = sum(i["subtotal"] for i in items_mo)
    suma_mat = sum(i["subtotal"] for i in items_mat)
    suma_serv = sum(i["monto"] for i in items_serv)
    total_costo = suma_mo + suma_mat + suma_serv + otros_gastos
    total_venta = round(total_costo * (1 + pct_ganancia / 100), 2)
    return total_costo, total_venta


def cargar_ordenes_test(cliente_supabase):
    """
    Carga OTs de prueba completas para el demo del MVP.
    Idempotente: verifica existencia antes de insertar.
    """
    print("\n🔧 Cargando órdenes de trabajo de prueba...")

    # Obtener IDs de clientes
    id_agro = _obtener_id_cliente(cliente_supabase, "Agro San Luis S.A.")
    id_plasticos = _obtener_id_cliente(cliente_supabase, "Plásticos del Norte")
    id_hidraulica = _obtener_id_cliente(cliente_supabase, "Hidráulica Córdoba SRL")
    id_cementos = _obtener_id_cliente(cliente_supabase, "Cementos Andinos S.A.")
    id_frigorifico = _obtener_id_cliente(cliente_supabase, "Frigorífico La Pampa")

    contadores = {"ots": 0, "recepciones": 0, "diagnosticos": 0, "presupuestos": 0}

    # =================================================================
    # OT-2026-001 — ENTREGADA (historial)
    # =================================================================
    ot_id = "OT-2026-001"
    if not _ot_existe(cliente_supabase, ot_id):
        cliente_supabase.table("ordenes_trabajo").insert({
            "id": ot_id, "cliente_id": id_agro,
            "fecha_ingreso": "2026-03-10", "maquina": "Cilindro hidráulico — brazo cargador agrícola",
            "descripcion_trabajo": "Reparación por pérdida de presión y desgaste de vástago",
            "estado": "ENTREGADO", "etapa": "Facturado",
            "fecha_entrega_prevista": "2026-03-20", "fecha_entrega_real": "2026-03-19",
            "horas_cotizadas": 12, "horas_empleadas": 11,
        }).execute()
        contadores["ots"] += 1
        print(f"  ✅ {ot_id} — ENTREGADO")
    else:
        print(f"  ⏭️  {ot_id} ya existe")

    if not _recepcion_existe(cliente_supabase, ot_id):
        cliente_supabase.table("recepcion_tecnica").insert({
            "ot_id": ot_id,
            "estado_pieza": "Vástago con rayado longitudinal, retenes deteriorados",
            "material_base": "Acero 1045 cromado",
            "trabajo_solicitado": "Rectificado de vástago, reemplazo de retenes y sellos",
            "causa_falla": "Contaminación del aceite con partículas abrasivas",
            "parametros_operacion": {"presion": "250 bar", "temperatura": "60°C", "velocidad": "N/A"},
            "observaciones": "Cliente reporta falla progresiva desde hace 3 semanas",
        }).execute()
        contadores["recepciones"] += 1

    if not _diagnostico_existe(cliente_supabase, ot_id):
        cliente_supabase.table("diagnostico_tecnico").insert({
            "ot_id": ot_id, "tipo_falla": "desgaste", "factibilidad": True,
            "conclusion": "REPARABLE", "tecnico_responsable": "Miguel Torres",
            "notas": "Vástago recuperable por rectificado. Retenes a reemplazar en su totalidad.",
        }).execute()
        contadores["diagnosticos"] += 1

    if not _presupuesto_existe(cliente_supabase, ot_id):
        mo = [
            {"categoria": "A", "descripcion": "Oficial especializado — Rectificado y cromo", "cantidad_horas": 8, "costo_hora": 15000, "subtotal": 120000},
            {"categoria": "C", "descripcion": "Medio oficial — Armado y sellado", "cantidad_horas": 4, "costo_hora": 9000, "subtotal": 36000},
        ]
        mat = [
            {"denominacion": "Retén hidráulico estándar", "cantidad": 2, "costo_unitario": 12000, "subtotal": 24000},
            {"denominacion": "O-ring NBR 70 (kit surtido)", "cantidad": 1, "costo_unitario": 5500, "subtotal": 5500},
            {"denominacion": "Aceite hidráulico ISO 68", "cantidad": 2, "costo_unitario": 3500, "subtotal": 7000},
        ]
        serv = [{"descripcion": "Cromo duro de vástago — tercero", "monto": 45000}]
        otros, pct = 3500, 35
        tc, tv = _calcular_totales(mo, mat, serv, otros, pct)
        cliente_supabase.table("presupuesto").insert({
            "ot_id": ot_id, "estado": "ACEPTADO",
            "items_mano_obra": mo, "items_materiales": mat, "items_servicios": serv,
            "otros_gastos": otros, "porcentaje_ganancia": pct,
            "total_costo": tc, "total_venta": tv,
        }).execute()
        contadores["presupuestos"] += 1

    # =================================================================
    # OT-2026-002 — EN PROCESO / APROBADO INTERNAMENTE
    # =================================================================
    ot_id = "OT-2026-002"
    if not _ot_existe(cliente_supabase, ot_id):
        cliente_supabase.table("ordenes_trabajo").insert({
            "id": ot_id, "cliente_id": id_plasticos,
            "fecha_ingreso": "2026-04-05", "maquina": "Inyectora 250T — unidad de cierre",
            "descripcion_trabajo": "Rectificado de platina guía y reemplazo de bujes de bronce",
            "estado": "EN_PROCESO", "etapa": "En Proceso",
            "fecha_entrega_prevista": "2026-04-28", "horas_cotizadas": 19,
        }).execute()
        contadores["ots"] += 1
        print(f"  ✅ {ot_id} — EN_PROCESO / APROBADO_INTERNO")
    else:
        print(f"  ⏭️  {ot_id} ya existe")

    if not _recepcion_existe(cliente_supabase, ot_id):
        cliente_supabase.table("recepcion_tecnica").insert({
            "ot_id": ot_id,
            "estado_pieza": "Platina guía con desgaste excesivo, bujes con holgura visible",
            "material_base": "Bronce SAE 65 (bujes) / Acero templado (platina)",
            "trabajo_solicitado": "Reemplazo de bujes y rectificado de platina",
            "causa_falla": "Falta de lubricación periódica",
            "parametros_operacion": {"presion": "N/A", "temperatura": "180°C molde", "velocidad": "N/A"},
        }).execute()
        contadores["recepciones"] += 1

    if not _diagnostico_existe(cliente_supabase, ot_id):
        cliente_supabase.table("diagnostico_tecnico").insert({
            "ot_id": ot_id, "tipo_falla": "desgaste", "factibilidad": True,
            "conclusion": "REPARABLE", "tecnico_responsable": "Rodrigo Vega",
            "notas": "Platina recuperable. Bujes a fabricar a medida en bronce SAE 65.",
        }).execute()
        contadores["diagnosticos"] += 1

    if not _presupuesto_existe(cliente_supabase, ot_id):
        mo = [
            {"categoria": "A", "descripcion": "Oficial especializado — Torneado y fabricación bujes", "cantidad_horas": 10, "costo_hora": 15000, "subtotal": 150000},
            {"categoria": "B", "descripcion": "Oficial — Rectificado platina", "cantidad_horas": 6, "costo_hora": 12000, "subtotal": 72000},
            {"categoria": "D", "descripcion": "Ayudante — Desmontaje y limpieza", "cantidad_horas": 3, "costo_hora": 6500, "subtotal": 19500},
        ]
        mat = [
            {"denominacion": "Buje de bronce SAE 65", "cantidad": 3, "costo_unitario": 18000, "subtotal": 54000},
            {"denominacion": "Lija al agua grano 220", "cantidad": 8, "costo_unitario": 650, "subtotal": 5200},
        ]
        serv = [{"descripcion": "Rectificado CNC externo", "monto": 38000}]
        otros, pct = 0, 30
        tc, tv = _calcular_totales(mo, mat, serv, otros, pct)
        cliente_supabase.table("presupuesto").insert({
            "ot_id": ot_id, "estado": "APROBADO_INTERNO",
            "items_mano_obra": mo, "items_materiales": mat, "items_servicios": serv,
            "otros_gastos": otros, "porcentaje_ganancia": pct,
            "total_costo": tc, "total_venta": tv,
        }).execute()
        contadores["presupuestos"] += 1

    # =================================================================
    # OT-2026-003 — EN PROCESO / BORRADOR DE PRESUPUESTO
    # =================================================================
    ot_id = "OT-2026-003"
    if not _ot_existe(cliente_supabase, ot_id):
        cliente_supabase.table("ordenes_trabajo").insert({
            "id": ot_id, "cliente_id": id_hidraulica,
            "fecha_ingreso": "2026-04-15", "maquina": "Bomba de engranajes hidráulica 80L/min",
            "descripcion_trabajo": "Revisión general, sellado y ajuste de tolerancias",
            "estado": "EN_PROCESO", "etapa": "Cotizando",
            "fecha_entrega_prevista": "2026-04-30", "horas_cotizadas": 8,
        }).execute()
        contadores["ots"] += 1
        print(f"  ✅ {ot_id} — EN_PROCESO / BORRADOR")
    else:
        print(f"  ⏭️  {ot_id} ya existe")

    if not _recepcion_existe(cliente_supabase, ot_id):
        cliente_supabase.table("recepcion_tecnica").insert({
            "ot_id": ot_id,
            "estado_pieza": "Pérdida de caudal progresiva, ruido anormal en operación",
            "material_base": "Hierro fundido / acero",
            "trabajo_solicitado": "Revisión completa de bomba, reemplazo de sellos",
            "causa_falla": "Desgaste por horas de servicio (más de 10.000 hs)",
            "parametros_operacion": {"presion": "180 bar", "temperatura": "55°C", "velocidad": "1450 rpm"},
        }).execute()
        contadores["recepciones"] += 1

    if not _diagnostico_existe(cliente_supabase, ot_id):
        cliente_supabase.table("diagnostico_tecnico").insert({
            "ot_id": ot_id, "tipo_falla": "desgaste", "factibilidad": True,
            "conclusion": "CON_CONDICIONES", "tecnico_responsable": "Miguel Torres",
            "notas": "Recuperable con condiciones. Engranajes en límite de tolerancia. Recomendar revisión en 6 meses.",
        }).execute()
        contadores["diagnosticos"] += 1

    if not _presupuesto_existe(cliente_supabase, ot_id):
        mo = [
            {"categoria": "A", "descripcion": "Oficial especializado — Revisión y ajuste", "cantidad_horas": 6, "costo_hora": 15000, "subtotal": 90000},
            {"categoria": "D", "descripcion": "Ayudante — Limpieza y preparación", "cantidad_horas": 2, "costo_hora": 6500, "subtotal": 13000},
        ]
        mat = [
            {"denominacion": "O-ring NBR 70 (kit surtido)", "cantidad": 2, "costo_unitario": 5500, "subtotal": 11000},
            {"denominacion": "Retén hidráulico estándar", "cantidad": 1, "costo_unitario": 12000, "subtotal": 12000},
            {"denominacion": "Aceite hidráulico ISO 68", "cantidad": 1, "costo_unitario": 3500, "subtotal": 3500},
        ]
        serv = []
        otros, pct = 0, 30
        tc, tv = _calcular_totales(mo, mat, serv, otros, pct)
        cliente_supabase.table("presupuesto").insert({
            "ot_id": ot_id, "estado": "BORRADOR",
            "items_mano_obra": mo, "items_materiales": mat, "items_servicios": serv,
            "otros_gastos": otros, "porcentaje_ganancia": pct,
            "total_costo": tc, "total_venta": tv,
        }).execute()
        contadores["presupuestos"] += 1

    # =================================================================
    # OT-2026-004 — PENDIENTE (esperando diagnóstico)
    # =================================================================
    ot_id = "OT-2026-004"
    if not _ot_existe(cliente_supabase, ot_id):
        cliente_supabase.table("ordenes_trabajo").insert({
            "id": ot_id, "cliente_id": id_cementos,
            "fecha_ingreso": "2026-04-22", "maquina": "Perfiladora de chapa — cilindro de avance",
            "descripcion_trabajo": "Reemplazo de vástago roto y reconstrucción de cabeza",
            "estado": "PENDIENTE", "etapa": "Cotizando",
            "fecha_entrega_prevista": "2026-05-06",
        }).execute()
        contadores["ots"] += 1
        print(f"  ✅ {ot_id} — PENDIENTE (sin diagnóstico)")
    else:
        print(f"  ⏭️  {ot_id} ya existe")

    if not _recepcion_existe(cliente_supabase, ot_id):
        cliente_supabase.table("recepcion_tecnica").insert({
            "ot_id": ot_id,
            "estado_pieza": "Vástago fracturado a 80mm de la rosca",
            "material_base": "Acero 1045",
            "trabajo_solicitado": "Reemplazo completo de vástago, verificar rosca de cabeza",
            "causa_falla": "Rotura por sobrecarga / golpe accidental",
            "parametros_operacion": {"presion": "180 bar", "temperatura": "ambiente", "velocidad": "N/A"},
            "observaciones": "Máquina parada. Urgente.",
        }).execute()
        contadores["recepciones"] += 1

    # =================================================================
    # OT-2026-005 — PENDIENTE (esperando diagnóstico)
    # =================================================================
    ot_id = "OT-2026-005"
    if not _ot_existe(cliente_supabase, ot_id):
        cliente_supabase.table("ordenes_trabajo").insert({
            "id": ot_id, "cliente_id": id_frigorifico,
            "fecha_ingreso": "2026-04-23", "maquina": "Compresor de amoniaco — pistón y biela",
            "descripcion_trabajo": "Diagnóstico de ruido y vibración anormal",
            "estado": "PENDIENTE", "etapa": "Cotizando",
            "fecha_entrega_prevista": "2026-05-12",
        }).execute()
        contadores["ots"] += 1
        print(f"  ✅ {ot_id} — PENDIENTE (sin diagnóstico)")
    else:
        print(f"  ⏭️  {ot_id} ya existe")

    if not _recepcion_existe(cliente_supabase, ot_id):
        cliente_supabase.table("recepcion_tecnica").insert({
            "ot_id": ot_id,
            "estado_pieza": "Pistón con marcas de golpeteo, biela con holgura",
            "material_base": "Aluminio (pistón) / Acero (biela)",
            "trabajo_solicitado": "Diagnóstico completo, presupuesto según hallazgos",
            "causa_falla": "A determinar",
            "parametros_operacion": {"presion": "18 bar", "temperatura": "-15°C", "velocidad": "960 rpm"},
        }).execute()
        contadores["recepciones"] += 1

    # =================================================================
    # OT-2026-006 — DEMORADA (debe aparecer en rojo)
    # =================================================================
    ot_id = "OT-2026-006"
    if not _ot_existe(cliente_supabase, ot_id):
        cliente_supabase.table("ordenes_trabajo").insert({
            "id": ot_id, "cliente_id": id_agro,
            "fecha_ingreso": "2026-04-01", "maquina": "Cilindro hidráulico dirección — Tractor John Deere 5090",
            "descripcion_trabajo": "Reemplazo de retenes y pulido de vástago",
            "estado": "DEMORADO", "etapa": "En Proceso",
            "fecha_entrega_prevista": "2026-04-15",  # ← vencida
        }).execute()
        contadores["ots"] += 1
        print(f"  ✅ {ot_id} — DEMORADO (🔴 atraso)")
    else:
        print(f"  ⏭️  {ot_id} ya existe")

    if not _recepcion_existe(cliente_supabase, ot_id):
        cliente_supabase.table("recepcion_tecnica").insert({
            "ot_id": ot_id,
            "estado_pieza": "Pérdida de aceite por vástago, retenes deteriorados",
            "material_base": "Acero cromado",
            "trabajo_solicitado": "Reemplazo de kit de sellado completo",
            "causa_falla": "Desgaste por uso",
            "parametros_operacion": {"presion": "200 bar", "temperatura": "ambiente", "velocidad": "N/A"},
        }).execute()
        contadores["recepciones"] += 1

    if not _diagnostico_existe(cliente_supabase, ot_id):
        cliente_supabase.table("diagnostico_tecnico").insert({
            "ot_id": ot_id, "tipo_falla": "desgaste", "factibilidad": True,
            "conclusion": "REPARABLE", "tecnico_responsable": "Miguel Torres",
            "notas": "Demorado por falta de retenes específicos. Proveedor prometió entrega esta semana.",
        }).execute()
        contadores["diagnosticos"] += 1

    if not _presupuesto_existe(cliente_supabase, ot_id):
        mo = [
            {"categoria": "A", "descripcion": "Oficial especializado — Pulido y sellado", "cantidad_horas": 5, "costo_hora": 15000, "subtotal": 75000},
            {"categoria": "C", "descripcion": "Medio oficial — Desmontaje y armado", "cantidad_horas": 3, "costo_hora": 9000, "subtotal": 27000},
        ]
        mat = [
            {"denominacion": "Retén hidráulico estándar", "cantidad": 2, "costo_unitario": 12000, "subtotal": 24000},
            {"denominacion": "O-ring NBR 70 (kit surtido)", "cantidad": 1, "costo_unitario": 5500, "subtotal": 5500},
            {"denominacion": "Lija al agua grano 220", "cantidad": 4, "costo_unitario": 650, "subtotal": 2600},
        ]
        serv = []
        otros, pct = 0, 35
        tc, tv = _calcular_totales(mo, mat, serv, otros, pct)
        cliente_supabase.table("presupuesto").insert({
            "ot_id": ot_id, "estado": "APROBADO_INTERNO",
            "items_mano_obra": mo, "items_materiales": mat, "items_servicios": serv,
            "otros_gastos": otros, "porcentaje_ganancia": pct,
            "total_costo": tc, "total_venta": tv,
        }).execute()
        contadores["presupuestos"] += 1

    # =================================================================
    # OT-2026-007 — ENTREGADA (historial)
    # =================================================================
    ot_id = "OT-2026-007"
    if not _ot_existe(cliente_supabase, ot_id):
        cliente_supabase.table("ordenes_trabajo").insert({
            "id": ot_id, "cliente_id": id_hidraulica,
            "fecha_ingreso": "2026-03-01", "maquina": "Cilindro telescópico — camión volcador",
            "descripcion_trabajo": "Reparación de corrosión externa y reemplazo de sellos",
            "estado": "ENTREGADO", "etapa": "Facturado",
            "fecha_entrega_prevista": "2026-03-15", "fecha_entrega_real": "2026-03-14",
            "horas_cotizadas": 10, "horas_empleadas": 9,
        }).execute()
        contadores["ots"] += 1
        print(f"  ✅ {ot_id} — ENTREGADO")
    else:
        print(f"  ⏭️  {ot_id} ya existe")

    if not _recepcion_existe(cliente_supabase, ot_id):
        cliente_supabase.table("recepcion_tecnica").insert({
            "ot_id": ot_id,
            "estado_pieza": "Corrosión externa severa, sellado comprometido",
            "material_base": "Acero inoxidable / cromado",
            "trabajo_solicitado": "Tratamiento anticorrosión, reemplazo de sellado",
            "causa_falla": "Exposición a ambiente corrosivo (barro con sal)",
            "parametros_operacion": {"presion": "180 bar", "temperatura": "ambiente", "velocidad": "N/A"},
        }).execute()
        contadores["recepciones"] += 1

    if not _diagnostico_existe(cliente_supabase, ot_id):
        cliente_supabase.table("diagnostico_tecnico").insert({
            "ot_id": ot_id, "tipo_falla": "corrosion", "factibilidad": True,
            "conclusion": "REPARABLE", "tecnico_responsable": "Rodrigo Vega",
            "notas": "Tratamiento anticorrosión y reemplazo de sellado completo.",
        }).execute()
        contadores["diagnosticos"] += 1

    if not _presupuesto_existe(cliente_supabase, ot_id):
        mo = [
            {"categoria": "A", "descripcion": "Oficial especializado — Tratamiento y sellado", "cantidad_horas": 7, "costo_hora": 15000, "subtotal": 105000},
            {"categoria": "D", "descripcion": "Ayudante — Preparación superficie", "cantidad_horas": 3, "costo_hora": 6500, "subtotal": 19500},
        ]
        mat = [
            {"denominacion": "Pintura epoxi industrial", "cantidad": 2, "costo_unitario": 9800, "subtotal": 19600},
            {"denominacion": "Retén hidráulico estándar", "cantidad": 3, "costo_unitario": 12000, "subtotal": 36000},
        ]
        serv = []
        otros, pct = 4500, 30
        tc, tv = _calcular_totales(mo, mat, serv, otros, pct)
        cliente_supabase.table("presupuesto").insert({
            "ot_id": ot_id, "estado": "ACEPTADO",
            "items_mano_obra": mo, "items_materiales": mat, "items_servicios": serv,
            "otros_gastos": otros, "porcentaje_ganancia": pct,
            "total_costo": tc, "total_venta": tv,
        }).execute()
        contadores["presupuestos"] += 1

    # =================================================================
    # OT-2026-008 — EN PROCESO / ENVIADO AL CLIENTE
    # =================================================================
    ot_id = "OT-2026-008"
    if not _ot_existe(cliente_supabase, ot_id):
        cliente_supabase.table("ordenes_trabajo").insert({
            "id": ot_id, "cliente_id": id_cementos,
            "fecha_ingreso": "2026-04-10", "maquina": "Cilindro hidráulico prensa compactadora",
            "descripcion_trabajo": "Reconstrucción completa de cilindro — vástago y camisa",
            "estado": "EN_PROCESO", "etapa": "Cotizado",
            "fecha_entrega_prevista": "2026-05-02", "horas_cotizadas": 25,
        }).execute()
        contadores["ots"] += 1
        print(f"  ✅ {ot_id} — EN_PROCESO / ENVIADO")
    else:
        print(f"  ⏭️  {ot_id} ya existe")

    if not _recepcion_existe(cliente_supabase, ot_id):
        cliente_supabase.table("recepcion_tecnica").insert({
            "ot_id": ot_id,
            "estado_pieza": "Vástago doblado, camisa con rallado interno profundo",
            "material_base": "Acero 1045 / Bronce (buje)",
            "trabajo_solicitado": "Reemplazo de vástago, rectificado de camisa, nuevos bujes",
            "causa_falla": "Pandeo por carga lateral fuera de especificación",
            "parametros_operacion": {"presion": "300 bar", "temperatura": "70°C", "velocidad": "N/A"},
        }).execute()
        contadores["recepciones"] += 1

    if not _diagnostico_existe(cliente_supabase, ot_id):
        cliente_supabase.table("diagnostico_tecnico").insert({
            "ot_id": ot_id, "tipo_falla": "rotura", "factibilidad": True,
            "conclusion": "REPARABLE", "tecnico_responsable": "Miguel Torres",
            "notas": "Trabajo mayor. Requiere mecanizado completo. Tiempo estimado 3 semanas.",
        }).execute()
        contadores["diagnosticos"] += 1

    if not _presupuesto_existe(cliente_supabase, ot_id):
        mo = [
            {"categoria": "A", "descripcion": "Oficial especializado — Torneado y rectificado", "cantidad_horas": 16, "costo_hora": 15000, "subtotal": 240000},
            {"categoria": "B", "descripcion": "Oficial — Mecanizado camisa", "cantidad_horas": 6, "costo_hora": 12000, "subtotal": 72000},
            {"categoria": "D", "descripcion": "Ayudante — Desmontaje y preparación", "cantidad_horas": 3, "costo_hora": 6500, "subtotal": 19500},
        ]
        mat = [
            {"denominacion": "Buje de bronce SAE 65", "cantidad": 2, "costo_unitario": 18000, "subtotal": 36000},
            {"denominacion": "Retén hidráulico estándar", "cantidad": 4, "costo_unitario": 12000, "subtotal": 48000},
            {"denominacion": "Electrodo de soldadura E7018", "cantidad": 3, "costo_unitario": 4200, "subtotal": 12600},
        ]
        serv = [
            {"descripcion": "Cromo duro vástago nuevo — tercero", "monto": 85000},
            {"descripcion": "Tratamiento térmico camisa — tercero", "monto": 35000},
        ]
        otros, pct = 8000, 35
        tc, tv = _calcular_totales(mo, mat, serv, otros, pct)
        cliente_supabase.table("presupuesto").insert({
            "ot_id": ot_id, "estado": "ENVIADO",
            "items_mano_obra": mo, "items_materiales": mat, "items_servicios": serv,
            "otros_gastos": otros, "porcentaje_ganancia": pct,
            "total_costo": tc, "total_venta": tv,
        }).execute()
        contadores["presupuestos"] += 1

    # --- Resumen ---
    print(f"\n  📊 Resumen OTs: {contadores['ots']} creadas, {contadores['recepciones']} recepciones, "
          f"{contadores['diagnosticos']} diagnósticos, {contadores['presupuestos']} presupuestos")


def main():
    """Función principal del script de seed."""
    print("=" * 60)
    print("🌱 Konmethal — Carga de datos iniciales + datos MVP")
    print("=" * 60)
    
    cliente = obtener_cliente_supabase()
    
    cargar_categorias_mano_obra(cliente)
    cargar_insumos_consumibles(cliente)
    cargar_clientes_ejemplo(cliente)
    cargar_ordenes_test(cliente)
    
    print("\n" + "=" * 60)
    print("✅ Carga completa")
    print("========================================")
    print("Resumen de datos cargados:")
    print("  Clientes:      5")
    print("  OTs creadas:   8")
    print("  Recepciones:   8")
    print("  Diagnósticos:  6")
    print("  Presupuestos:  6")
    print("========================================")


if __name__ == "__main__":
    main()
