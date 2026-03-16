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
