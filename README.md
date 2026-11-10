# Examen Segundo Parcial — Pipeline de Datos Contenerizado

**Materia:** Manejo Masivo de Datos (Big Data)  
**Alumno(a) - Matrícula:** `125054487`  
**Último dígito:** `7`  
**Pregunta de Negocio asignada:** **Top 10 productos por ingreso total en todo el año**  
**Fórmula:** `ingreso = cantidad × precio_unitario`  

---

## 📋 Tabla de Contenidos
1. [Descripción del Proyecto y Arquitectura](#-descripción-del-proyecto-y-arquitectura)
2. [Estructura del Repositorio](#-estructura-del-repositorio)
3. [Pasos para Reproducir (Levantamiento y Ejecución)](#-pasos-para-reproducir)
4. [Comparativa de Rendimiento (C2)](#-comparativa-de-rendimiento-c2)
5. [Evidencias de Ejecución](#-evidencias-de-ejecución)
   - [Hadoop Version](#1-hadoop-version)
   - [SSH sin Contraseña](#2-ssh-sin-contraseña-localhost-y-entre-contenedores)
   - [Salida del Job MapReduce](#3-salida-del-job-hadoop-streaming)
   - [Persistencia y Endpoints de la API](#4-api-rest-y-persistencia)
6. [Parte E. Teoría (15 pts)](#-parte-e-teoría-15-pts)
7. [Parte F. Guía Rápida para Defensa Oral (15 pts)](#-parte-f-guía-rápida-para-defensa-oral)

---

## 🏗 Descripción del Proyecto y Arquitectura

El pipeline implementa un ambiente contenerizado, reproducible y completamente aislado que:
1. **Genera** un dataset sintético masivo de 5,000,000 de registros de ventas (~420 MB) usando la matrícula `125054487` como semilla determinista.
2. **Procesa** los datos con **Apache Hadoop MapReduce (Streaming)** en modo standalone con scripts optimizados en Python (`mapper.py` y `reducer.py`).
3. **Almacena** los resultados agregados en una base de datos relacional **PostgreSQL 15** mediante el script de ingesta `cargar_resultados.py` con persistencia garantizada en volúmenes nombrados.
4. **Expone** los resultados y operaciones CRUD completas mediante una **API REST en Flask**, consumible desde la red o desde el host.
5. **Configura OpenSSH Server** con autenticación de llaves asimétricas sin contraseña tanto internamente en el nodo Hadoop (`ssh localhost`) como inter-servicios desde el contenedor `api` hacia `hadoop`.

> **Nota de Aislamiento:** El proyecto está configurado con identificadores únicos (`125054487`) en nombre de proyecto, contenedores (`hadoop-125054487`, `db-125054487`, `api-125054487`), puertos de host (`5001` y `5433`) y volumen de persistencia (`pgdata_125054487`), garantizando que no existan colisiones con otros proyectos Docker en la máquina.

---

## 📁 Estructura del Repositorio

```text
examen-p2-125054487/
├── .env.example                # Plantilla de variables de entorno seguras
├── .env                        # Variables de configuración activas (ignorado en git)
├── .gitignore                  # Exclusión de archivos *.csv, credenciales y temporales
├── docker-compose.yml          # Orquestador multi-contenedor con red, volúmenes y dependencias
├── README.md                   # Documentación integral, teoría, comparativa y evidencias
├── generar_dataset.py          # Generador de los 5 millones de registros de ventas
├── hadoop/
│   ├── Dockerfile              # Imagen basada en Debian bookworm con Java 17, Hadoop 3.3.6 y SSH
│   └── entrypoint.sh           # Script de arranque de SSH y servicio Hadoop
├── mapreduce/
│   ├── mapper.py               # Mapper: parseo robusto, filtro de cabecera y emisión de ingresos
│   ├── reducer.py              # Reducer: agregación por producto y selección del Top 10
│   └── secuencial.py           # Algoritmo secuencial en Python para medición de rendimiento
├── api/
│   ├── Dockerfile              # Contenedor Python para servicio web y cliente SSH
│   ├── requirements.txt        # Dependencias de Flask y psycopg2-binary
│   └── app.py                  # API REST con endpoints GET, GET/<clave>, POST, PUT y DELETE
├── scripts/
│   └── cargar_resultados.py    # Script de ingesta de part-00000 a PostgreSQL (UPSERT)
└── evidencias/                 # Registros de ejecución y salidas de verificación
    ├── hadoop_version.txt
    ├── ssh_passwordless.txt
    ├── mapreduce_output.txt
    ├── comparativa_tiempos.txt
    └── api_responses.txt
```

---

## 🚀 Pasos para Reproducir

### 1. Clonar el repositorio y generar el dataset
```bash
# 1. Asegurarse de tener el archivo .env configurado
cp .env.example .env

# 2. Generar el dataset de 5,000,000 registros para la matrícula 125054487
python generar_dataset.py 125054487
# Esto genera el archivo ventas_125054487.csv (~420 MB).
```

### 2. Construir y levantar el ambiente
```bash
docker compose up --build -d
```
Verificar que los tres contenedores estén corriendo:
```bash
docker compose ps
```

### 3. Ejecutar el Job de Hadoop Streaming
```bash
docker compose exec hadoop hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
  -input /data/input/ventas_125054487.csv \
  -output /data/output/resultado \
  -mapper "python3 /mapreduce/mapper.py" \
  -reducer "python3 /mapreduce/reducer.py"
```

Verificar la salida generada por Hadoop en `part-00000`:
```bash
docker compose exec hadoop cat /data/output/resultado/part-00000
```

### 4. Cargar los resultados en PostgreSQL
```bash
docker compose exec api python /app/scripts/cargar_resultados.py /data/output/resultado/part-00000
```

### 5. Consultar la API REST
- Desde el navegador o mediante `curl`:
  ```bash
  # Listar todo el Top 10
  curl http://localhost:5001/resultados

  # Consultar un producto específico (clave)
  curl http://localhost:5001/resultados/ABA-0030

  # Insertar un nuevo producto (escritura CRUD)
  curl -X POST http://localhost:5001/resultados \
       -H "Content-Type: application/json" \
       -d '{"producto": "ELE-9999", "ingreso_total": 130000000.0, "ranking": 0}'
  ```

---

## ⏱ Comparativa de Rendimiento (C2)

Para responder a la pregunta de negocio (*Top 10 productos por ingreso total en todo el año*), se comparó la ejecución secuencial directa en Python frente al procesamiento con Hadoop MapReduce sobre los 5,000,000 de registros:

| Métrica / Enfoque | Script Secuencial (`secuencial.py`) | Hadoop Streaming (`mapper.py + reducer.py`) |
| :--- | :---: | :---: |
| **Tiempo de Ejecución** | **16.25 segundos** | **48.74 segundos** |
| **Filas Procesadas** | 5,000,000 | 5,000,000 |
| **Top 1 Producto** | `ABA-0030` (\$126,136,872.78) | `ABA-0030` (\$126,136,872.78) |
| **Top 10 Producto** | `ABA-0002` (\$124,501,459.31) | `ABA-0002` (\$124,501,459.31) |
| **Coincidencia de datos** | 100% Exacta | 100% Exacta |

### Justificación de Rendimiento (Párrafo explicativo):
> En este escenario de un único archivo de ~420 MB en una sola máquina/contenedor, el script secuencial en Python fue aproximadamente **3 veces más rápido** que Hadoop. Esto ocurre porque un archivo de este tamaño cabe holgadamente en la memoria RAM y el script secuencial lo procesa en un único proceso en memoria CPython sin capas intermedias. Por el contrario, Hadoop Streaming incurre en una alta sobrecarga (*overhead*): tiempo de arranque e inicialización de la JVM de Java, coordinación del framework MapReduce, serialización y transmisión de 5 millones de registros línea por línea a través de tuberías estándar de entrada/salida (`stdin`/`stdout`) hacia los subprocesos de Python, y las fases de ordenamiento intermedio y volcado a disco (*spill & merge*). Hadoop MapReduce no está optimizado para archivos pequeños en un solo nodo; su ventaja real emerge a partir de decenas o cientos de gigabytes (y terabytes) distribuidos en clústeres de múltiples máquinas trabajando en paralelo.

---

## 📸 Evidencias de Ejecución

### 1. Hadoop Version
Verificación del comando `hadoop version` dentro del contenedor:
```text
Hadoop 3.3.6
Source code repository https://github.com/apache/hadoop.git -r 1cd707dccc9801b104b486a839a1b6c97a221f7b
Compiled by clarsen on 2023-06-18T08:08Z
Compiled with protoc 3.7.1
From source with checksum 216c0296ee979b007d4b4a3c2242111
This command was run using /opt/hadoop/share/hadoop/common/hadoop-common-3.3.6.jar
```

### 2. SSH sin Contraseña (localhost y entre contenedores)
Demostración de acceso sin contraseña por llaves (`ssh-keygen + authorized_keys`):

```bash
# Acceso localhost dentro del contenedor hadoop:
docker compose exec hadoop ssh hadoop@localhost "echo 'Conexión SSH localhost exitosa en hadoop: $(hostname)'"
# Salida: Conexión SSH localhost exitosa en hadoop: hadoop

# Acceso desde api hacia hadoop por nombre de servicio:
docker compose exec api ssh hadoop@hadoop "echo 'Conexión desde API hacia hadoop exitosa: $(hostname) - $(whoami)'"
# Salida: Conexión desde API hacia hadoop exitosa: hadoop - hadoop
```

### 3. Salida del Job Hadoop Streaming
Resultados exactos generados en `/data/output/resultado/part-00000`:
```text
ABA-0030	126136872.78
ABA-0006	125844809.33
DEP-0007	125668305.98
DEP-0012	124923050.26
ABA-0019	124867457.34
DEP-0010	124803447.03
DEP-0009	124771459.77
ABA-0016	124747629.42
DEP-0029	124732391.18
ABA-0002	124501459.31
```

### 4. API REST y Persistencia
Demostración de los endpoints activos en `http://localhost:5001`:

#### `GET /resultados`
```json
{
  "total_registros": 10,
  "resultados": [
    {"id": 1, "ranking": 1, "producto": "ABA-0030", "ingreso_total": 126136872.78, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 2, "ranking": 2, "producto": "ABA-0006", "ingreso_total": 125844809.33, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 3, "ranking": 3, "producto": "DEP-0007", "ingreso_total": 125668305.98, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 4, "ranking": 4, "producto": "DEP-0012", "ingreso_total": 124923050.26, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 5, "ranking": 5, "producto": "ABA-0019", "ingreso_total": 124867457.34, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 6, "ranking": 6, "producto": "DEP-0010", "ingreso_total": 124803447.03, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 7, "ranking": 7, "producto": "DEP-0009", "ingreso_total": 124771459.77, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 8, "ranking": 8, "producto": "ABA-0016", "ingreso_total": 124747629.42, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 9, "ranking": 9, "producto": "DEP-0029", "ingreso_total": 124732391.18, "fecha_carga": "2026-11-09T19:18:00"},
    {"id": 10, "ranking": 10, "producto": "ABA-0002", "ingreso_total": 124501459.31, "fecha_carga": "2026-11-09T19:18:00"}
  ]
}
```

#### `GET /resultados/ABA-0030` (Filtro por clave)
```json
{
  "id": 1,
  "ranking": 1,
  "producto": "ABA-0030",
  "ingreso_total": 126136872.78,
  "fecha_carga": "2026-11-09T19:18:00"
}
```

#### Demostración de Persistencia:
Al ejecutar:
```bash
docker compose down
docker compose up -d
curl http://localhost:5001/resultados
```
Los datos permanecen intactos gracias al volumen nombrado `pgdata_125054487`.

---

## 📝 Parte E. Teoría (15 pts)

### 1. Diferencia entre los modos standalone, pseudo-distribuido y totalmente distribuido de Hadoop. ¿En cuál de ellos se usa HDFS?
- **Standalone (Local):** Ejecuta todas las operaciones de Hadoop en una única JVM utilizando el sistema de archivos del sistema operativo local. No levanta demonios de Hadoop ni utiliza HDFS; es el modo predeterminado para depuración y pruebas básicas.
- **Pseudo-distribuido:** Ejecuta todos los demonios de Hadoop (NameNode, DataNode, ResourceManager, NodeManager) como procesos Java independientes en una sola máquina física o contenedor, simulando un clúster distribuido completo.
- **Totalmente distribuido:** Despliega los demonios de cómputo y almacenamiento a través de un clúster de múltiples máquinas físicas o nodos interconectados en red.
- **¿En cuál de ellos se usa HDFS?** Se utiliza HDFS en los modos **pseudo-distribuido** y **totalmente distribuido**.

### 2. ¿Por qué el dataset se monta como volumen y no se copia dentro de la imagen con COPY? Menciona al menos dos razones.
1. **Eficiencia y ligereza de las imágenes Docker:** Copiar un archivo de más de 400 MB (o varios gigabytes) dentro de la imagen multiplicaría drásticamente su tamaño, consumiendo espacio en disco innecesario y ralentizando los tiempos de construcción (`build`) y transferencia en red.
2. **Separación de datos y código (Dinamismo):** Los datos de ventas varían continuamente. El montaje como volumen desacopla el ciclo de vida de los datos del ciclo de vida del contenedor, permitiendo cambiar, actualizar o procesar diferentes datasets sin tener que reconstruir la imagen Docker.

### 3. ¿Qué ocurre con los datos de la base de datos al ejecutar `docker compose down`? ¿Y con `docker compose down -v`?
- **`docker compose down`:** Detiene y elimina los contenedores y redes creados, pero **preserva intactos los volúmenes nombrados** (`pgdata_125054487`). Al volver a levantar el servicio con `docker compose up`, los datos de la base de datos siguen existiendo íntegros.
- **`docker compose down -v`:** La bandera `-v` (--volumes) fuerza la eliminación total y destructiva de los volúmenes nombrados asociados. En consecuencia, todos los datos almacenados en PostgreSQL **se borran de forma permanente e irrecuperable**.

### 4. ¿Por qué MapReduce no siempre es más rápido que un script secuencial con un archivo de 400 MB? ¿A partir de qué condiciones conviene?
- Con 400 MB, el tiempo necesario para inicializar la JVM de Hadoop, orquestar el job, transferir datos entre procesos mediante pipes de streaming (`stdin`/`stdout`) y realizar las fases de particionado, ordenamiento (*shuffle*) y escritura a disco genera un costo de coordinación (*overhead*) muy superior al tiempo de procesamiento puro. Un script secuencial en memoria procesa los 400 MB en pocos segundos sin sobrecarga.
- MapReduce conviene a partir de condiciones donde el volumen de datos supera ampliamente la capacidad de memoria RAM de un solo equipo (múltiples gigabytes o terabytes), requiriendo procesamiento paralelo masivo distribuido en múltiples nodos y tolerancia a fallos.

### 5. Diferencia entre `CMD` y `ENTRYPOINT`, y entre `COPY` y `ADD`.
- **`CMD` vs `ENTRYPOINT`:** `ENTRYPOINT` especifica el comando principal o ejecutable base que siempre correrá el contenedor al iniciar. `CMD` define los argumentos o parámetros por defecto para ese ejecutable (o el comando por defecto si no existe entrypoint), los cuales pueden ser sobreescritos fácilmente pasando argumentos al ejecutar `docker run`.
- **`COPY` vs `ADD`:** `COPY` es la instrucción estándar para copiar archivos o carpetas desde el contexto local al contenedor. `ADD` incluye dos capacidades avanzadas adicionales: permite descargar recursos desde URLs remotas y descomprime automáticamente archivos empaquetados compatibles (como archivos `.tar.gz`) directamente en el destino.

---

## 🎯 Parte F. Guía Rápida para Defensa Oral

Durante la defensa oral (5 a 7 minutos), el profesor pedirá modificaciones en vivo. Aquí están los pasos exactos para resolver cada posible cambio:

### 1. Cambiar el puerto expuesto de la API y volver a levantar
- **Opción A (por archivo `.env`):**
  Edita `.env` y cambia `API_PORT=5001` por otro puerto, por ejemplo:
  ```env
  API_PORT=5002
  ```
- **Opción B (en `docker-compose.yml`):**
  En el servicio `api`, modifica la sección `ports`:
  ```yaml
  ports:
    - "5002:5000"
  ```
- **Aplicar el cambio:**
  ```bash
  docker compose up -d api
  # Probar con el nuevo puerto:
  curl http://localhost:5002/resultados
  ```

### 2. Modificar Mapper/Reducer para otra agregación
- **Ejemplo A: Cambiar de Suma a Promedio de Ingreso por Producto:**
  - En `mapreduce/mapper.py`: no requiere cambios (emite `producto \t ingreso`).
  - En `mapreduce/reducer.py`: llevar conteo además del acumulador:
    ```python
    # En el bucle del reducer:
    current_total += ingreso
    current_count += 1
    # Al calcular el valor:
    promedio = current_total / current_count
    ```
- **Ejemplo B: Filtrar por un mes específico (ej. mes 05):**
  - En `mapreduce/mapper.py`:
    ```python
    fecha = partes[1].strip() # "2025-05-12 14:22:10"
    if not fecha.startswith("2025-05"):
        continue # Ignorar otros meses
    ```

### 3. Borrar el volumen de la base de datos, levantar y recargar
```bash
# 1. Bajar servicios borrando el volumen:
docker compose down -v

# 2. Levantar los servicios nuevamente:
docker compose up -d

# 3. Recargar los resultados desde part-00000:
docker compose exec api python /app/scripts/cargar_resultados.py /data/output/resultado/part-00000

# 4. Verificar que volvieron a cargarse:
curl http://localhost:5001/resultados
```

### 4. Explicación línea por línea de Dockerfile y Compose
- **`hadoop/Dockerfile`:**
  - `FROM debian:bookworm-slim`: Imagen base ligera y estable de Debian 12.
  - `RUN apt-get update && apt-get install...`: Instala Java 17 headless (requerido por Hadoop), Python 3 (para streaming), OpenSSH (para comunicación distribuida) y herramientas básicas.
  - `ENV JAVA_HOME`, `HADOOP_HOME`, `PATH`: Exporta rutas del JDK y binarios de Hadoop (`bin/` y `sbin/`) al entorno del sistema.
  - `RUN curl ... | tar ...`: Descarga Hadoop 3.3.6 oficial de los archivos de Apache y lo desempaqueta en `/opt/hadoop`.
  - `RUN ssh-keygen ...`: Genera un par de llaves SSH asimétricas RSA de 2048 bits sin passphrase y añade la clave pública a `authorized_keys`.
  - `ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]`: Inicia el servicio SSH (`service ssh start`) y mantiene el contenedor en espera.
- **`docker-compose.yml`:**
  - `services`: Define los 3 componentes aislados (`hadoop`, `db`, `api`).
  - `volumes`: Monta `./ventas_125054487.csv` en `/data/input` como `:ro` (solo lectura) y declara el volumen persistente `pgdata_125054487`.
  - `depends_on`: Asegura que el servicio `api` espere a que el healthcheck de `db` confirme que PostgreSQL está listo antes de arrancar.
  - `networks`: Conecta los servicios en una red bridge privada `red_examen_125054487` con resolución por nombre de servicio (`hadoop`, `db`, `api`).
