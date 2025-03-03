# Usar una imagen base de Python
FROM python:3.10-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar los archivos de requisitos
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY src/ ./src/
COPY data/ ./data/

# Crear el directorio data si no existe
RUN mkdir -p data

# Establecer variables de entorno
ENV PYTHONUNBUFFERED=1
ENV LM_STUDIO_URL=http://host.docker.internal:1234
ENV PYTHONPATH=/app

# Comando por defecto
CMD ["python", "src/app.py"] 