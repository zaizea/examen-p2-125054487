#!/bin/bash
set -e

# Iniciar servicio SSH en segundo plano
service ssh start

# Si existe un volumen compartido para llaves SSH, asegurar que la llave privada esté copiada
if [ -d "/shared_ssh" ]; then
    mkdir -p /shared_ssh
    cp -u /home/hadoop/.ssh/id_rsa /shared_ssh/id_rsa 2>/dev/null || true
    cp -u /home/hadoop/.ssh/id_rsa.pub /shared_ssh/id_rsa.pub 2>/dev/null || true
    chmod 600 /shared_ssh/id_rsa 2>/dev/null || true
    chmod 644 /shared_ssh/id_rsa.pub 2>/dev/null || true
fi

# Mantener el contenedor en ejecución o ejecutar comando especificado
if [ $# -eq 0 ]; then
    echo "Contenedor Hadoop iniciado con SSH activo en puerto 22."
    exec tail -f /dev/null
else
    exec "$@"
fi
