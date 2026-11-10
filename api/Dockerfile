FROM python:3.11-slim

# Instalar dependencias del sistema, cliente SSH y herramientas de diagnóstico
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requerimientos e instalarlos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la API
COPY app.py .

# Preparar directorio SSH para conexión sin contraseña hacia hadoop
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

EXPOSE 5000

CMD ["python", "app.py"]
