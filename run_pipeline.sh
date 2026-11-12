#!/usr/bin/env bash
# run_pipeline.sh - Script de automatización para Linux / macOS / WSL
# Matrícula: 125054487 - Top 10 productos por ingreso total

set -e

echo "=========================================================="
echo "  Pipeline de Datos Contenerizado - Matrícula 125054487  "
echo "=========================================================="

# 1. Dataset
if [ ! -f "ventas_125054487.csv" ]; then
    echo "[1/5] Generando dataset de 5,000,000 registros..."
    python3 generar_dataset.py 125054487
else
    echo "[1/5] Dataset ventas_125054487.csv ya existe. Omitiendo."
fi

# 2. Levantar Docker Compose
echo "[2/5] Levantando contenedores aislados con Docker Compose..."
docker compose up --build -d

echo "Esperando que los contenedores estén listos..."
sleep 10

# 3. Hadoop Streaming
echo "[3/5] Ejecutando Hadoop Streaming Job..."
docker compose exec hadoop hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
  -input /data/input/ventas_125054487.csv \
  -output /data/output/resultado \
  -mapper "python3 /mapreduce/mapper.py" \
  -reducer "python3 /mapreduce/reducer.py"

echo "Salida de part-00000:"
docker compose exec hadoop cat /data/output/resultado/part-00000

# 4. Ingesta a PostgreSQL
echo "[4/5] Cargando resultados en PostgreSQL..."
docker compose exec api python3 /app/scripts/cargar_resultados.py /data/output/resultado/part-00000

# 5. Probar API
echo "[5/5] Probando API REST en http://localhost:5000..."
curl -s http://localhost:5000/resultados | python3 -m json.tool
curl -s http://localhost:5000/resultados/ABA-0030 | python3 -m json.tool

echo "=========================================================="
echo "  ¡Pipeline completado con éxito!                        "
echo "=========================================================="
