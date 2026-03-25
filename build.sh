#!/usr/bin/env bash
# build.sh - Script de construcción para producción (Render.com)
set -o errexit

echo "📦 Instalando dependencias de Python (Backend)..."
cd backend
pip install -r requirements.txt

# Opcional: Si quieres que el modelo siempre tenga datos de prueba en producción,
# puedes generar los datos aquí. Si no, borra esta línea.
# python generate_sample_data.py

cd ..

echo "📦 Instalando dependencias de Node.js (Frontend)..."
cd frontend
npm install

echo "🛠️ Compilando Frontend (React/Vite)..."
# Inyectar variables de entorno para producción si es necesario
# En local/Render al servir el frontend desde FastAPI, el API está en el mismo dominio
export VITE_API_URL="/api"
npm run build

echo "✅ Build completo."
