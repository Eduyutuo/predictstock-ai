# PredictStock AI

Sistema Inteligente de Gestión de Inventarios y Análisis Predictivo.
Este repositorio está estructurado como un monorepo (Full-stack) preparado para producción.

## Estructura del Proyecto

- `backend/`: API construida con FastAPI, Pandas y Scikit-learn (RandomForest).
- `frontend/`: Aplicación de React + Vite con Tailwind CSS v4 y Recharts.

---

---

## 💻 Entorno de Desarrollo Local

Si deseas correr el proyecto en tu PC:

**1. Terminal 1 (Backend):**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

**2. Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173` en tu navegador.

## 🚀 Despliegue en Render (Producción)

Este proyecto está configurado para ser desplegado fácilmente en [Render](https://render.com/) utilizando el archivo `render.yaml` (Blueprint) incluido en este repositorio.

### Opción 1: Despliegue Automático con Blueprint (Recomendado)

Render leerá el archivo `render.yaml` de la raíz del proyecto para crear automáticamente el servicio web con la configuración correcta (rama, comandos de build, variables de entorno como Python 3.11.9, etc.).

1. Sube o haz un fork de este repositorio a tu propia cuenta de GitHub.
2. Inicia sesión en el [Dashboard de Render](https://dashboard.render.com).
3. Haz clic en el botón de **"New +"** y selecciona **"Blueprint"**.
4. Conecta tu cuenta de GitHub y selecciona este repositorio.
5. Render analizará el repositorio. Haz clic en **"Apply"**.
6. Render se encargará de instalar las dependencias (`build.sh`) y desplegar la aplicación automáticamente.

### Opción 2: Despliegue Manual como Web Service

Si prefieres configurar el servicio manualmente sin usar la opción Blueprint:

1. Ve al Dashboard de Render, haz clic en **"New +"** -> **"Web Service"**.
2. Conecta tu repositorio de GitHub y selecciónalo.
3. Rellena los campos principales de la siguiente manera:
   - **Name**: predictstock-ai (o nombre similar)
   - **Language**: Python
   - **Branch**: main
   - **Root Directory**: *(Déjalo completamente en blanco)*
   - **Build Command**: `./build.sh`-
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
4. En la sección de **Environment Variables** (Variables de Entorno Avanzadas), añade:
   - `PYTHON_VERSION` = `3.11.9`
5. Haz clic en **"Create Web Service"**.

Una vez que termine la construcción (Build), Render te proporcionará una URL pública (ej. `https://predictstock-ai.onrender.com`) desde donde podrás acceder a toda la aplicación (Frontend y Backend integrados).
