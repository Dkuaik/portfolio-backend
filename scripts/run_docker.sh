#!/bin/bash

# Script para ejecutar el contenedor Docker con variables de entorno del archivo .env

# Verificar si el archivo .env existe
if [ ! -f ".env" ]; then
    echo "Error: El archivo .env no existe. Por favor, crea uno basado en .env.example"
    exit 1
fi

# Cargar variables de entorno desde .env y ejecutar el contenedor
echo "Ejecutando contenedor con variables de entorno desde .env..."

docker run --name portfolios-backend \
    --env-file .env \
    -p 8000:8000 \
    -d \
    portfolios-backend:latest

echo "Contenedor iniciado. Puedes verificar su estado con: docker ps"
echo "Para ver los logs: docker logs portfolios-backend"
echo "Para acceder a la API: http://localhost:8000"
echo "Para acceder a los docs: http://localhost:8000/docs"
