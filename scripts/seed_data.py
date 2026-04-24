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
    """Carga clientes de ejemplo."""
    clientes_ejemplo = [
        {
            "nombre": "Aceros Zapla S.A.",
            "rubro": "Siderurgia",
            "telefono": "0388-4221234",
            "contacto": "Ing. Carlos Mendoza",
        },
        {
            "nombre": "Minera Aguilar",
            "rubro": "Minería",
            "telefono": "0388-4915678",
            "contacto": "Roberto Figueroa",
        },
    ]
    
    print("\n👤 Cargando clientes de ejemplo...")
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


def main():
    """Función principal del script de seed."""
    print("=" * 60)
    print("🌱 Konmethal — Carga de datos iniciales")
    print("=" * 60)
    
    cliente = obtener_cliente_supabase()
    
    cargar_categorias_mano_obra(cliente)
    cargar_insumos_consumibles(cliente)
    cargar_clientes_ejemplo(cliente)
    
    print("\n" + "=" * 60)
    print("✅ Carga de datos iniciales completada")
    print("=" * 60)


if __name__ == "__main__":
    main()
