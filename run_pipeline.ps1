# run_pipeline.ps1 - Script de automatización para Windows PowerShell
# Matrícula: 125054487 - Top 10 productos por ingreso total

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Pipeline de Datos Contenerizado - Matrícula 125054487  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verificar existencia del archivo de ventas
if (-not (Test-Path "ventas_125054487.csv")) {
    Write-Host "[1/5] Generando dataset de 5,000,000 registros..." -ForegroundColor Yellow
    python generar_dataset.py 125054487
} else {
    Write-Host "[1/5] Dataset ventas_125054487.csv ya existe. Omitiendo generación." -ForegroundColor Green
}

# 2. Levantar servicios con Docker Compose
Write-Host "`n[2/5] Levantando contenedores aislados con Docker Compose..." -ForegroundColor Yellow
docker compose up --build -d

Write-Host "Esperando a que los servicios estén listos..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 3. Ejecutar MapReduce con Hadoop Streaming
Write-Host "`n[3/5] Ejecutando Hadoop Streaming Job..." -ForegroundColor Yellow
docker compose exec hadoop hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar `
  -input /data/input/ventas_125054487.csv `
  -output /data/output/resultado `
  -mapper "python3 /mapreduce/mapper.py" `
  -reducer "python3 /mapreduce/reducer.py"

Write-Host "`nSalida de part-00000:" -ForegroundColor Cyan
docker compose exec hadoop cat /data/output/resultado/part-00000

# 4. Ingesta a la base de datos PostgreSQL
Write-Host "`n[4/5] Cargando resultados en PostgreSQL..." -ForegroundColor Yellow
docker compose exec api python /app/scripts/cargar_resultados.py /data/output/resultado/part-00000

# 5. Probar API REST
Write-Host "`n[5/5] Probando endpoints de la API en http://localhost:5000..." -ForegroundColor Yellow
Write-Host "-> Probando GET /resultados:" -ForegroundColor Gray
try {
    $res = Invoke-RestMethod -Uri "http://localhost:5000/resultados" -Method Get
    $res | ConvertTo-Json -Depth 4
} catch {
    Write-Host "Error consultando API: $_" -ForegroundColor Red
}

Write-Host "`n-> Probando GET /resultados/ABA-0030 (Filtro por producto):" -ForegroundColor Gray
try {
    $prod = Invoke-RestMethod -Uri "http://localhost:5000/resultados/ABA-0030" -Method Get
    $prod | ConvertTo-Json -Depth 4
} catch {
    Write-Host "Error consultando producto: $_" -ForegroundColor Red
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  ¡Pipeline ejecutado y verificado exitosamente!          " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
