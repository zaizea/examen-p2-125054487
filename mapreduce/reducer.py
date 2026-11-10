#!/usr/bin/env python3
"""
Reducer para Hadoop Streaming.
Pregunta de negocio (Matrícula 125054487, dígito 7):
Top 10 productos por ingreso total en todo el año.

Recibe pares ordenados por clave: producto \t ingreso
Acumula el ingreso total por producto y al finalizar emite el Top 10 ordenado descendente.
Formato de salida:
producto \t total_ingreso
"""
import sys

def main():
    totales_por_producto = {}
    current_producto = None
    current_total = 0.0

    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue

        partes = linea.split("\t")
        if len(partes) != 2:
            continue

        producto, ingreso_str = partes[0].strip(), partes[1].strip()
        try:
            ingreso = float(ingreso_str)
        except ValueError:
            continue

        if current_producto == producto:
            current_total += ingreso
        else:
            if current_producto is not None:
                totales_por_producto[current_producto] = current_total
            current_producto = producto
            current_total = ingreso

    # Guardar el último producto procesado
    if current_producto is not None:
        totales_por_producto[current_producto] = current_total

    # Obtener el Top 10 ordenado por ingreso descendente
    top_10 = sorted(totales_por_producto.items(), key=lambda x: x[1], reverse=True)[:10]

    # Emitir resultados en formato: producto \t ingreso_total
    for producto, total in top_10:
        print(f"{producto}\t{total:.2f}")

if __name__ == "__main__":
    main()
