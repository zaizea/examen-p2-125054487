#!/usr/bin/env python3
"""
Mapper para Hadoop Streaming.
Pregunta de negocio (Matrícula 125054487, dígito 7):
Top 10 productos por ingreso total en todo el año.

Emite: producto \t ingreso
"""
import sys

def main():
    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue

        # Ignorar encabezado
        if linea.startswith("id,") or linea.startswith('"id"'):
            continue

        partes = linea.split(",")
        # Esquema esperado: id, fecha_hora, tienda, categoria, producto, cantidad, precio_unitario, metodo_pago
        if len(partes) < 8:
            continue

        try:
            producto = partes[4].strip()
            cantidad = float(partes[5].strip())
            precio = float(partes[6].strip())
            ingreso = cantidad * precio

            if producto:
                # Emitir producto \t ingreso
                print(f"{producto}\t{ingreso:.2f}")
        except (ValueError, IndexError):
            # Ignorar líneas corruptas o con formato inválido sin truncar el job
            continue

if __name__ == "__main__":
    main()
