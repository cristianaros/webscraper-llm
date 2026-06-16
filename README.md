# 🎓 UniNews — Sistema de Noticias Universitarias con IA

Plataforma web para gestionar y consultar **noticias universitarias** con un asistente de **Inteligencia Artificial** basado en **Google Gemini + RAG** (Retrieval-Augmented Generation).

## 🚀 Características

| Característica | Descripción |
|---|---|
| 📰 Gestión de Noticias | CRUD completo (crear, leer, editar, eliminar) |
| 🔍 Búsqueda & Filtros | Por categoría, universidad y texto libre |
| 🤖 Asistente IA | Chat en lenguaje natural con respuestas basadas en noticias reales |
| 🧠 RAG | Las respuestas se fundamentan en el contenido indexado (no alucinaciones) |
| ⭐ Noticias Destacadas | Sistema de noticias destacadas |
| 📊 Dashboard | Estadísticas en tiempo real |
| 🎨 Diseño Premium | Dark mode, Astro + shadcn/ui, animaciones |

---

## 📁 Estructura del Proyecto

```
webscraper-llm/
├── backend/               # FastAPI + SQLite + ChromaDB (RAG)
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── sample_data.py
│   ├── requirements.txt
│   ├── rag/
│   │   └── engine.py      # Motor RAG (Gemini + ChromaDB)
│   └── routers/
│       ├── news.py
│       └── chat.py
├── src/                   # Frontend Astro + shadcn/ui (raíz del proyecto)
│   ├── pages/             # index.astro, chat.astro, admin.astro
│   ├── components/        # NewsPage, ChatInterface, AdminPanel (React)
│   └── lib/
│       └── api.ts         # Cliente tipado para el backend
├── public/
├── astro.config.mjs
├── package.json
├── vercel.json
└── .env.example
```

---

## ⚙️ Instalación local

### 1. Requisitos previos

- Python 3.10+
- Node.js 22+
- [API Key gratuita de Google Gemini](https://aistudio.google.com/app/apikey)

### 2. Configurar el backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Edita .env y coloca tu GEMINI_API_KEY
```

### 3. Cargar datos de demo

```bash
python sample_data.py
```

### 4. Iniciar el servidor

```bash
python main.py
# El servidor quedará en http://localhost:8000
```

### 5. Instalar y correr el frontend

```bash
# Desde la raíz del proyecto
cp .env.example .env
# Edita .env si el backend no está en localhost:8000

npm install
npm run dev
# Abrir http://localhost:4321
```

---

## ☁️ Despliegue en Vercel

> **Importante:** el backend (FastAPI + SQLite + ChromaDB) **no puede desplegarse en Vercel** por sus requisitos de sistema de archivos persistente. Despliégalo en [Railway](https://railway.app), [Render](https://render.com) o [Fly.io](https://fly.io) y apunta `PUBLIC_API_URL` a esa URL.

### Frontend (Vercel)

1. Importa el repositorio en [vercel.com/new](https://vercel.com/new)
2. Vercel detecta Astro automáticamente — no toques nada
3. En **Environment Variables** agrega:

   | Variable | Valor |
   |---|---|
   | `PUBLIC_API_URL` | `https://tu-backend.railway.app` |

4. Haz clic en **Deploy**

### Backend (Railway / Render)

```bash
# En el servicio, configura:
GEMINI_API_KEY=tu_api_key

# Start command:
cd backend && python main.py
```

---

## 🔑 Variables de Entorno

| Variable | Dónde | Descripción |
|---|---|---|
| `GEMINI_API_KEY` | `backend/.env` | API Key de Google Gemini |
| `PUBLIC_API_URL` | `.env` / Vercel dashboard | URL del backend FastAPI |

---

## 🧠 Arquitectura RAG

```
Pregunta del usuario
      ↓
  Embedding (Gemini text-embedding-004)
      ↓
  Búsqueda vectorial en ChromaDB
      ↓
  Top-K noticias relevantes
      ↓
  Prompt contextualizado → Gemini 1.5 Flash
      ↓
  Respuesta fundamentada + fuentes citadas
```

---

## 📖 API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/news/` | Listar noticias (filtros, búsqueda) |
| GET | `/api/news/stats` | Estadísticas generales |
| GET | `/api/news/{id}` | Obtener noticia por ID |
| POST | `/api/news/` | Crear noticia (+ indexar en RAG) |
| PUT | `/api/news/{id}` | Actualizar noticia |
| DELETE | `/api/news/{id}` | Eliminar noticia |
| POST | `/api/chat/` | Consultar asistente IA con RAG |
| GET | `/api/chat/status` | Estado del motor RAG |

Documentación interactiva: **http://localhost:8000/docs**

---

## 🎓 Proyecto de Tesis

Este sistema fue desarrollado como proyecto de tesis para demostrar la integración de:
- **Web Scraping** y almacenamiento estructurado de noticias universitarias
- **LLM + RAG** para consulta inteligente de información
- **FastAPI** como backend moderno en Python
- **ChromaDB** como base de datos vectorial
- **Google Gemini** como modelo de lenguaje y embeddings
