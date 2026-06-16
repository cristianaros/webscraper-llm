# Sistema de Noticias Universitarias con LLM + RAG

## Descripción General

Plataforma web completa para almacenar, gestionar y consultar noticias universitarias, con un asistente de inteligencia artificial basado en RAG (Retrieval-Augmented Generation) que permite hacer preguntas en lenguaje natural sobre las noticias almacenadas.

---

## User Review Required

> [!IMPORTANT]
> Antes de proceder, hay decisiones clave que debes confirmar:
> 1. **API de LLM**: ¿Tienes acceso a OpenAI, Google Gemini, o prefieres un modelo local (Ollama)?
> 2. **Base de Datos**: ¿Tienes PostgreSQL instalado, o prefieres SQLite para desarrollo?
> 3. **Lenguaje del backend**: ¿Python (FastAPI) o Node.js (Express)?

> [!WARNING]
> Para el RAG se requiere una **API key** (OpenAI, Google Gemini, etc.) o tener Ollama instalado localmente con un modelo descargado.

---

## Open Questions

1. **¿Cuál API de LLM prefieres?**
   - `OpenAI (GPT-4o)` → Mejor calidad, requiere cuenta de pago
   - `Google Gemini` → Tiene tier gratuito generoso
   - `Ollama (local)` → Completamente gratuito, requiere GPU/CPU potente

2. **¿El sistema de scraping debe automatizarse?** (el README menciona extracción de datos)
   - ¿Quieres que el sistema haga web scraping automático de portales universitarios?
   - ¿O el usuario sube/crea las noticias manualmente?

3. **¿Necesitas autenticación?**
   - Roles: Admin (puede crear/editar), Usuario (solo consulta)

---

## Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (HTML/CSS/JS)              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │  Panel Admin  │ │  Noticias    │ │  Chat IA     │ │
│  │  (CRUD)       │ │  (Listado)   │ │  (RAG)       │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ │
└────────────────────────┬────────────────────────────┘
                         │ REST API / WebSocket
┌────────────────────────▼────────────────────────────┐
│                BACKEND (FastAPI / Python)            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │  API Noticias │ │  Web Scraper │ │  RAG Engine  │ │
│  │  (CRUD)       │ │  (opcional)  │ │              │ │
│  └──────────────┘ └──────────────┘ └──────┬───────┘ │
└───────────────────────────────────────────┼─────────┘
                                            │
              ┌─────────────────────────────┼────────┐
              │                             │        │
   ┌──────────▼──────┐         ┌───────────▼──────┐ │
   │  Base de Datos  │         │  Vector Store     │ │
   │  (SQLite/PostgreSQL)│     │  (ChromaDB)       │ │
   │  Noticias, Meta │         │  Embeddings       │ │
   └─────────────────┘         └──────────────────┘  │
                                                      │
                              ┌───────────────────┐   │
                              │  LLM API          │   │
                              │  (OpenAI/Gemini/  │   │
                              │   Ollama)         │   │
                              └───────────────────┘
```

---

## Stack Tecnológico

| Capa | Tecnología | Propósito |
|------|-----------|-----------|
| Frontend | HTML + CSS + Vanilla JS | UI/UX de la aplicación |
| Backend | Python + FastAPI | API REST |
| Base de datos | SQLite (dev) / PostgreSQL (prod) | Almacenamiento de noticias |
| Vector Store | ChromaDB | Almacenamiento de embeddings para RAG |
| LLM | OpenAI / Google Gemini / Ollama | Generación de respuestas |
| Embeddings | `sentence-transformers` o API de embeddings | Vectorización del texto |
| Web Scraping | BeautifulSoup + requests | Extracción automática de noticias |
| Auth | JWT Tokens | Autenticación básica |

---

## Proposed Changes

### Backend (Python/FastAPI)

#### [NEW] `backend/main.py`
Punto de entrada de la API FastAPI con CORS, rutas y configuración.

#### [NEW] `backend/models.py`
Modelos SQLAlchemy para `Noticia`, `Categoria`, `Universidad`.

#### [NEW] `backend/database.py`
Conexión a SQLite/PostgreSQL con SQLAlchemy.

#### [NEW] `backend/routers/news.py`
CRUD completo de noticias: crear, listar, filtrar, editar, eliminar.

#### [NEW] `backend/routers/chat.py`
Endpoint del asistente RAG: recibe una pregunta, busca en ChromaDB y genera respuesta con el LLM.

#### [NEW] `backend/rag/engine.py`
Motor RAG: carga documentos → genera embeddings → almacena en ChromaDB → recupera contexto → llama al LLM.

#### [NEW] `backend/rag/scraper.py`
Web scraper opcional para extraer noticias automáticamente de portales universitarios.

#### [NEW] `backend/requirements.txt`
Dependencias del proyecto Python.

---

### Frontend (HTML/CSS/JS)

#### [NEW] `frontend/index.html`
Landing page con listado de noticias universitarias, buscador y acceso al chat IA.

#### [NEW] `frontend/admin.html`
Panel de administración para gestionar noticias (CRUD).

#### [NEW] `frontend/chat.html`
Interfaz del asistente de IA con historial de conversación tipo chat.

#### [NEW] `frontend/css/styles.css`
Sistema de diseño completo: dark mode, glassmorphism, animaciones.

#### [NEW] `frontend/js/app.js`
Lógica del frontend: llamadas a la API, renderizado dinámico de noticias.

#### [NEW] `frontend/js/chat.js`
Lógica del chat con el asistente IA: streaming de respuestas, historial.

---

### Configuración

#### [NEW] `.env.example`
Variables de entorno necesarias (API keys, configuración de DB).

#### [NEW] `docker-compose.yml`
Configuración para levantar todo el sistema con un solo comando.

#### [NEW] `README.md` (actualizado)
Instrucciones de instalación y uso.

---

## Módulos Funcionales

### 1. Gestión de Noticias
- ✅ Crear/editar/eliminar noticias con título, contenido, fecha, categoría, universidad
- ✅ Listado con paginación, filtros por categoría/fecha/universidad
- ✅ Búsqueda de texto completo
- ✅ Imágenes/miniaturas por noticia

### 2. Web Scraper (Opcional)
- ✅ Extracción automática desde URLs de portales universitarios
- ✅ Programación de scraping periódico
- ✅ Deduplicación de noticias

### 3. Asistente IA con RAG
- ✅ Vectorización automática de noticias al crearlas
- ✅ Chat en lenguaje natural
- ✅ Respuestas fundamentadas en las noticias almacenadas (con citas)
- ✅ Historial de conversación

### 4. Panel Admin
- ✅ Dashboard con estadísticas
- ✅ Gestión de categorías y universidades
- ✅ Trigger manual del scraper

---

## Verification Plan

### Automated Tests
```bash
# Backend
pytest backend/tests/

# Verificar API
curl http://localhost:8000/api/news
curl -X POST http://localhost:8000/api/chat -d '{"question": "¿Qué noticias hay sobre becas?"}'
```

### Manual Verification
- [ ] Crear una noticia desde el panel admin
- [ ] Verificar que aparece en el listado principal
- [ ] Hacer una pregunta al chat IA relacionada con esa noticia
- [ ] Verificar que el LLM responde con información de la noticia creada
