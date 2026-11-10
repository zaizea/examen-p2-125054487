#!/usr/bin/env python3
"""
Script secuencial para resolver la pregunta de negocio:
Matrícula: 125054487 (dígito 7) -> Top 10 productos por ingreso total en todo el año.
Fórmula: ingreso = cantidad * precio_unitario
"""

import sys
import time
import csv
from collections import defaultdict

def main():
    if len(sys.argv) > 1:
        archivo = sys.argv[1]
    else:
        archivo = "ventas_125054487.csv"

    print(f"=== Iniciando procesamiento secuencial sobre {archivo} ===")
    t_inicio = time.time()

    ingresos_por_producto = defaultdict(float)
    filas_procesadas = 0
    filas_erroneas = 0

    try:
        with open(archivo, mode="r", encoding="utf-8") as f:
            lector = csv.reader(f)
            header = next(lector, None) # Omitir encabezado

            for fila in lector:
                try:
                    # id, fecha_hora, tienda, categoria, producto, cantidad, precio_unitario, metodo_pago
                    if len(fila) < 8:
                        filas_erroneas += 1
                        continue
                    
                    producto = fila[4].strip()
                    cantidad = float(fila[5])
                    precio = float(fila[6])
                    ingreso = cantidad * precio

                    ingresos_por_producto[producto] += ingreso
                    filas_procesadas += 1
                except (ValueError, IndexError):
                    filas_erroneas += 1
                    continue
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {archivo}", file=sys.stderr)
        sys.exit(1)

    # Ordenar productos de mayor a menor ingreso y tomar el Top 10
    top_10 = sorted(ingresos_por_producto.items(), key=lambda x: x[1], reverse=True)[:10]

    t_fin = time.time()
    t_total = t_fin - t_inicio

    print("\n=== TOP 10 PRODUCTOS POR INGRESO TOTAL (SECUENCIAL) ===")
    print(f"{'Ranking':<8} {'Producto':<15} {'Ingreso Total':>15}")
    print("-" * 40)
    for idx, (prod, total) in enumerate(top_10, start=1):
        print(f"{idx:<8} {prod:<15} ${total:>14,.2f}")

    print("-" * 40)
    print(f"Filas procesadas correctamente: {filas_procesadas:,}")
    print(f"Filas omitidas/erróneas:        {filas_erroneas:,}")
    print(f"Tiempo total de ejecución:      {t_total:.4f} segundos")
    print(f"Total productos analizados:     {len(ingresos_por_producto)}")

    return top_10, t_total

if __name__ == "__main__":
    main()
