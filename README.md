# PredictStock AI

Sistema Inteligente de Gestión de Inventarios y Análisis Predictivo.
Este repositorio está estructurado como un monorepo (Full-stack) preparado para producción.

## Estructura del Proyecto

- `backend/`: API construida con FastAPI, Pandas y Scikit-learn (RandomForest).
- `frontend/`: Aplicación de React + Vite con Tailwind CSS v4 y Recharts.

---

## 🚀 Despliegue en Producción (Render.com)

El proyecto está configurado para desplegarse fácilmente de forma **100% gratuita** como un **Web Service único** en [Render.com](https://render.com). FastAPI se encargará de servir tanto la API de Python como los archivos estáticos generados por React.

### Pasos para desplegar:

1. **Sube este proyecto a tu repositorio de GitHub** (debe contener ambas carpetas `frontend` y `backend`, además de `render.yaml` y `build.sh` en la raíz).
2. Entra a [Render.com](https://render.com) y crea un nuevo **Web Service**.
3. Conecta tu cuenta de GitHub y selecciona este repositorio.
4. Render detectará automáticamente el archivo `render.yaml` (Blueprint) en la raíz del proyecto y configurará todo por ti:
   - **Build Command:** `./build.sh` (instalará Python, Node y compilará el frontend).
   - **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Haz clic en **Deploy**. Render hará el build y te entregará una URL pública (ej. `https://predictstock-ai.onrender.com`).

¡Eso es todo! El frontend funcionará automáticamente conectado al backend en la misma URL.

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
