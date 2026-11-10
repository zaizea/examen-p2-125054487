#!/usr/bin/env python3
"""
API REST en Flask para exponer y gestionar los resultados de MapReduce.
Matrícula: 125054487
Pregunta: Top 10 productos por ingreso total.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuración de base de datos desde variables de entorno
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "ventas_db")
DB_USER = os.getenv("POSTGRES_USER", "datamart")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "datamart_secure_pass")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resultados_top_productos (
                id SERIAL PRIMARY KEY,
                ranking INT,
                producto VARCHAR(50) UNIQUE NOT NULL,
                ingreso_total NUMERIC(15, 2) NOT NULL,
                fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Tabla 'resultados_top_productos' verificada/inicializada.")
    except Exception as e:
        print(f"Advertencia al inicializar BD: {e}")

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "ok",
        "servicio": "API de Resultados - DataMart",
        "matricula": os.getenv("MATRICULA", "125054487"),
        "pregunta": "Top 10 productos por ingreso total en todo el año",
        "clave": "producto",
        "endpoints": {
            "GET /resultados": "Listar todos los productos en el Top",
            "GET /resultados/<clave>": "Filtrar por código de producto (ej: ABA-0030)",
            "POST /resultados": "Registrar un nuevo producto (JSON: producto, ingreso_total, ranking)",
            "PUT /resultados/<clave>": "Actualizar ingreso o ranking de un producto",
            "DELETE /resultados/<clave>": "Eliminar un producto del registro"
        }
    })

# 1. GET /resultados -> Todos los registros
@app.route("/resultados", methods=["GET"])
def obtener_todos():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, ranking, producto, CAST(ingreso_total AS FLOAT) as ingreso_total, fecha_carga FROM resultados_top_productos ORDER BY ranking ASC, ingreso_total DESC;")
        filas = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({
            "total_registros": len(filas),
            "resultados": filas
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. GET /resultados/<clave> -> Filtro por la clave de la pregunta (producto)
@app.route("/resultados/<clave>", methods=["GET"])
def obtener_por_producto(clave):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, ranking, producto, CAST(ingreso_total AS FLOAT) as ingreso_total, fecha_carga FROM resultados_top_productos WHERE UPPER(producto) = UPPER(%s);", (clave.strip(),))
        fila = cur.fetchone()
        cur.close()
        conn.close()

        if fila:
            return jsonify(fila), 200
        else:
            return jsonify({"mensaje": f"Producto '{clave}' no encontrado en resultados"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. POST /resultados -> Insertar nuevo registro (CRUD escritura)
@app.route("/resultados", methods=["POST"])
def crear_resultado():
    datos = request.get_json(silent=True) or {}
    producto = datos.get("producto")
    ingreso_total = datos.get("ingreso_total")
    ranking = datos.get("ranking", None)

    if not producto or ingreso_total is None:
        return jsonify({"error": "Los campos 'producto' e 'ingreso_total' son obligatorios"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO resultados_top_productos (ranking, producto, ingreso_total)
            VALUES (%s, %s, %s)
            RETURNING id, ranking, producto, CAST(ingreso_total AS FLOAT) as ingreso_total, fecha_carga;
        """, (ranking, producto.strip().upper(), float(ingreso_total)))
        nuevo = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"mensaje": "Producto creado exitosamente", "datos": nuevo}), 201
    except psycopg2.IntegrityError:
        return jsonify({"error": f"El producto '{producto}' ya existe en la base de datos"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. PUT /resultados/<clave> -> Actualizar un registro existente
@app.route("/resultados/<clave>", methods=["PUT"])
def actualizar_resultado(clave):
    datos = request.get_json(silent=True) or {}
    ingreso_total = datos.get("ingreso_total")
    ranking = datos.get("ranking")

    if ingreso_total is None and ranking is None:
        return jsonify({"error": "Debe proporcionar al menos 'ingreso_total' o 'ranking' para actualizar"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar si existe
        cur.execute("SELECT id FROM resultados_top_productos WHERE UPPER(producto) = UPPER(%s);", (clave.strip(),))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": f"Producto '{clave}' no encontrado"}), 404

        if ingreso_total is not None and ranking is not None:
            cur.execute("""
                UPDATE resultados_top_productos
                SET ingreso_total = %s, ranking = %s, fecha_carga = CURRENT_TIMESTAMP
                WHERE UPPER(producto) = UPPER(%s)
                RETURNING id, ranking, producto, CAST(ingreso_total AS FLOAT) as ingreso_total, fecha_carga;
            """, (float(ingreso_total), ranking, clave.strip()))
        elif ingreso_total is not None:
            cur.execute("""
                UPDATE resultados_top_productos
                SET ingreso_total = %s, fecha_carga = CURRENT_TIMESTAMP
                WHERE UPPER(producto) = UPPER(%s)
                RETURNING id, ranking, producto, CAST(ingreso_total AS FLOAT) as ingreso_total, fecha_carga;
            """, (float(ingreso_total), clave.strip()))
        else:
            cur.execute("""
                UPDATE resultados_top_productos
                SET ranking = %s, fecha_carga = CURRENT_TIMESTAMP
                WHERE UPPER(producto) = UPPER(%s)
                RETURNING id, ranking, producto, CAST(ingreso_total AS FLOAT) as ingreso_total, fecha_carga;
            """, (ranking, clave.strip()))

        actualizado = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"mensaje": "Producto actualizado", "datos": actualizado}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5. DELETE /resultados/<clave> -> Eliminar un registro
@app.route("/resultados/<clave>", methods=["DELETE"])
def eliminar_resultado(clave):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM resultados_top_productos WHERE UPPER(producto) = UPPER(%s) RETURNING id, producto;", (clave.strip(),))
        eliminado = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        if eliminado:
            return jsonify({"mensaje": f"Producto '{clave}' eliminado exitosamente"}), 200
        else:
            return jsonify({"error": f"Producto '{clave}' no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    puerto = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)
