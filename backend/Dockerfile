# Imagen del backend para el perfil local (no es la de AWS: allá lo empaqueta SAM).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# uvicorn solo se necesita para correr la API en local; en Lambda lo reemplaza Mangum.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn==0.34.0

COPY app ./app
COPY scripts ./scripts

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
