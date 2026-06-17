# 🎓 UniNews

> Plataforma de noticias universitarias potenciada por Inteligencia Artificial.  
> Consulta, busca y pregunta sobre noticias usando un asistente basado en **Google Gemini + RAG**.

![Astro](https://img.shields.io/badge/Astro-6-BC52EE?logo=astro&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-38BDF8?logo=tailwindcss&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Gemini-1.5_Flash-4285F4?logo=google&logoColor=white)

---

## ✨ Características

- 📰 **Gestión de noticias** — CRUD completo con panel de administración
- 🔍 **Búsqueda y filtros** — por categoría, universidad y texto libre
- 🤖 **Asistente IA** — chat en lenguaje natural respondiendo con base en las noticias reales
- 🧠 **RAG (Retrieval-Augmented Generation)** — respuestas fundamentadas, sin alucinaciones
- ⭐ **Noticias destacadas** — sistema de destacados con estadísticas en tiempo real
- 🎨 **Diseño dark mode** — Astro + shadcn/ui + Tailwind CSS v4

---

## 🖥️ Capturas

| Noticias | Asistente IA | Administrador |
|---|---|---|
| Grid con filtros por categoría | Chat con fuentes citadas | CRUD completo |

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (Vercel)                   │
│          Astro 6 + React 19 + shadcn/ui + Tailwind       │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP REST (PUBLIC_API_URL)
┌────────────────────▼────────────────────────────────────┐
│                   Backend (Railway / Render)              │
│                  FastAPI + SQLite + ChromaDB              │
│                                                          │
│   Pregunta → Embedding → ChromaDB → Top-K noticias →    │
│   Gemini 1.5 Flash → Respuesta + fuentes citadas         │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```
webscraper-llm/
├── backend/                  # API Python
│   ├── main.py               # FastAPI app + lifespan
│   ├── database.py           # Conexión SQLite + SQLAlchemy
│   ├── models.py             # Modelos de base de datos
│   ├── schemas.py            # Esquemas Pydantic
│   ├── app_state.py          # Estado global (RAG engine)
│   ├── sample_data.py        # Datos de demo
│   ├── requirements.txt
│   ├── rag/
│   │   └── engine.py         # Motor RAG (Gemini + ChromaDB)
│   └── routers/
│       ├── news.py           # CRUD de noticias
│       └── chat.py           # Endpoint del asistente IA
│
├── src/                      # Frontend Astro
│   ├── pages/
│   │   ├── index.astro       # Página principal (grid de noticias)
│   │   ├── chat.astro        # Asistente IA
│   │   └── admin.astro       # Panel de administración
│   ├── components/
│   │   ├── NewsPage.tsx      # Grid + filtros + modal de detalle
│   │   ├── ChatInterface.tsx # Chat con el asistente IA
│   │   ├── AdminPanel.tsx    # CRUD de noticias
│   │   └── ui/               # Componentes shadcn/ui
│   ├── layouts/
│   │   └── main.astro        # Layout principal con navbar
│   └── lib/
│       ├── api.ts            # Cliente tipado para el backend
│       └── utils.ts          # Utilidades (cn, etc.)
│
├── public/
├── astro.config.mjs
├── package.json
├── vercel.json               # Configuración Vercel
└── .env.example
```

---

## ⚙️ Instalación local

### Requisitos

- Python 3.10+
- Node.js 22+
- [API Key de Google Gemini](https://aistudio.google.com/app/apikey) (gratuita)

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/webscraper-llm.git
cd webscraper-llm
```

### 2. Configurar el backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / Mac

pip install -r requirements.txt
```

Crea el archivo `backend/.env`:

```env
GEMINI_API_KEY=tu_api_key_aqui
```

### 3. Cargar datos de demo

```bash
python sample_data.py
```

### 4. Iniciar el backend

```bash
python main.py
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

### 5. Configurar e iniciar el frontend

```bash
# Desde la raíz del proyecto
cp .env.example .env   # ya tiene PUBLIC_API_URL=http://localhost:8000

npm install
npm run dev
# → http://localhost:4321
```

---

## ☁️ Despliegue en producción

### Frontend → Vercel

1. Importa el repositorio en [vercel.com/new](https://vercel.com/new)
2. Vercel detecta Astro automáticamente
3. Agrega la variable de entorno:

   | Variable | Valor |
   |---|---|
   | `PUBLIC_API_URL` | `https://tu-backend.railway.app` |

4. Deploy ✅

### Backend → Railway / Render

> El backend usa SQLite y ChromaDB (filesystem local), por eso **no puede correr en Vercel**.

**Railway** es la opción más sencilla:

1. Crea un nuevo proyecto en [railway.app](https://railway.app)
2. Conecta el repositorio
3. Configura el directorio raíz como `backend`
4. Agrega la variable de entorno `GEMINI_API_KEY`
5. Comando de inicio: `python main.py`

---

## 📖 API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/news/` | Listar noticias con filtros |
| `GET` | `/api/news/stats` | Estadísticas generales |
| `GET` | `/api/news/{id}` | Obtener noticia por ID |
| `POST` | `/api/news/` | Crear noticia (se indexa en RAG) |
| `PUT` | `/api/news/{id}` | Actualizar noticia |
| `DELETE` | `/api/news/{id}` | Eliminar noticia |
| `POST` | `/api/chat/` | Consultar asistente IA |
| `GET` | `/api/chat/status` | Estado del motor RAG |

Documentación interactiva: **`http://localhost:8000/docs`**

---

## 🔑 Variables de entorno

| Variable | Archivo | Descripción |
|---|---|---|
| `GEMINI_API_KEY` | `backend/.env` | API Key de Google Gemini |
| `PUBLIC_API_URL` | `.env` / Vercel | URL del backend FastAPI |

---

## 🧠 Cómo funciona el RAG

```
Pregunta del usuario
        ↓
Embedding con text-embedding-004 (Gemini)
        ↓
Búsqueda vectorial en ChromaDB
        ↓
Top-K noticias más relevantes
        ↓
Prompt contextualizado → Gemini 1.5 Flash
        ↓
Respuesta fundamentada + fuentes citadas
```

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | Astro 6, React 19, shadcn/ui, Tailwind CSS v4 |
| Backend | FastAPI, SQLAlchemy, SQLite |
| IA / RAG | Google Gemini 1.5 Flash, ChromaDB |
| Embeddings | Google text-embedding-004 |
| Deploy frontend | Vercel |
| Deploy backend | Railway / Render |

---

## 📄 Licencia

MIT © 2025
