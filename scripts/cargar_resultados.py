#!/usr/bin/env python3
"""
Script para cargar los resultados de MapReduce (part-00000)
en la base de datos PostgreSQL.
Matrícula: 125054487
Pregunta: Top 10 productos por ingreso total.
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values

def main():
    # Ubicación del archivo part-00000
    if len(sys.argv) > 1:
        ruta_part = sys.argv[1]
    else:
        # Rutas comunes: dentro del contenedor o en la máquina host
        if os.path.exists("/data/output/resultado/part-00000"):
            ruta_part = "/data/output/resultado/part-00000"
        elif os.path.exists("data/output/resultado/part-00000"):
            ruta_part = "data/output/resultado/part-00000"
        elif os.path.exists("../data/output/resultado/part-00000"):
            ruta_part = "../data/output/resultado/part-00000"
        else:
            ruta_part = "part-00000"

    print(f"=== Cargando resultados desde {ruta_part} ===")
    if not os.path.exists(ruta_part):
        print(f"Error: No se encontró el archivo de resultados en: {ruta_part}", file=sys.stderr)
        sys.exit(1)

    # Parámetros de conexión desde variables de entorno
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "ventas_db")
    db_user = os.getenv("POSTGRES_USER", "datamart")
    db_pass = os.environ["POSTGRES_PASSWORD"]

    print(f"Conectando a PostgreSQL en {db_host}:{db_port}/{db_name} con usuario {db_user}...")

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass
        )
        cur = conn.cursor()

        # Crear tabla si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resultados_top_productos (
                id SERIAL PRIMARY KEY,
                ranking INT,
                producto VARCHAR(50) UNIQUE NOT NULL,
                ingreso_total NUMERIC(15, 2) NOT NULL,
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Leer archivo part-00000
        registros = []
        with open(ruta_part, "r", encoding="utf-8") as f:
            ranking = 1
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                partes = linea.split("\t")
                if len(partes) >= 2:
                    producto = partes[0].strip()
                    try:
                        ingreso = float(partes[1].strip())
                        registros.append((ranking, producto, ingreso))
                        ranking += 1
                    except ValueError:
                        continue

        if not registros:
            print("Aviso: El archivo part-00000 no contenía registros válidos.")
            return

        # Insertar registros o actualizar si ya existen (UPSERT)
        upsert_query = """
            INSERT INTO resultados_top_productos (ranking, producto, ingreso_total)
            VALUES %s
            ON CONFLICT (producto) DO UPDATE 
            SET ranking = EXCLUDED.ranking,
                ingreso_total = EXCLUDED.ingreso_total,
                fecha_carga = CURRENT_TIMESTAMP;
        """
        execute_values(cur, upsert_query, registros)
        conn.commit()

        print(f"Éxito: Se cargaron/actualizaron {len(registros)} productos en 'resultados_top_productos'.")
        
        # Mostrar los registros cargados
        cur.execute("SELECT ranking, producto, ingreso_total FROM resultados_top_productos ORDER BY ranking ASC;")
        filas = cur.fetchall()
        print("\n=== REGISTROS EN BASE DE DATOS ===")
        print(f"{'Ranking':<8} {'Producto':<15} {'Ingreso Total':>15}")
        print("-" * 40)
        for r, p, total in filas:
            print(f"{r:<8} {p:<15} ${float(total):>14,.2f}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error conectando o insertando en la base de datos: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
