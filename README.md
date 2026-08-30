# UniNews UPLA

Plataforma para importar noticias de la [Universidad de Playa Ancha](https://upla.cl/noticias/), almacenarlas y consultarlas mediante un chat con RAG.

El flujo principal es:

```text
UPLA → ScrapeGraphAI → MiniMax M3 (resumen) → SQLite + ChromaDB
                                                    ↓
Pregunta → retrieval local → MiniMax M3/OpenRouter → respuesta con fuentes
```

## Características

- Importación manual de las noticias UPLA más recientes desde el panel administrador.
- Extracción estructurada del listado y de cada artículo con ScrapeGraphAI v2.
- Deduplicación por URL antes de consumir la extracción de cada noticia.
- Resúmenes en español generados por MiniMax M3 a través de OpenRouter.
- Fecha de publicación, autor, categoría, imagen y enlace a la fuente original.
- Chat basado únicamente en las noticias recuperadas desde ChromaDB.
- CRUD de noticias, filtros, buscador, destacados y estadísticas.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Astro 6, React 19, shadcn/ui, Tailwind CSS 4 |
| Backend | FastAPI, SQLAlchemy, SQLite |
| Scraping | ScrapeGraphAI API v2 |
| LLM | OpenRouter + `minimax/minimax-m3:free` |
| Retrieval | ChromaDB + embeddings locales |

Los embeddings se ejecutan localmente. OpenRouter se utiliza para resumir las noticias importadas y responder las consultas; Gemini ya no es necesario.

## Configuración local

### Requisitos

- Node.js 22.12 o superior.
- Python 3.10 o superior.
- API key de ScrapeGraphAI.
- API key de OpenRouter con acceso al modelo configurado.

### Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `backend/.env`:

```env
OPENROUTER_API_KEY=tu_api_key_de_openrouter
OPENROUTER_MODEL=minimax/minimax-m3:free
SGAI_API_KEY=tu_api_key_de_scrapegraphai
```

También se admite `API_SCRAPEGRAPHAI`, que es el nombre utilizado por la configuración inicial de este proyecto. No es necesario duplicar la key: basta con definir uno de los dos nombres.

Inicia el backend:

```powershell
python main.py
```

La API queda disponible en `http://localhost:8000` y su documentación en `http://localhost:8000/docs`.

### Frontend

Desde la raíz:

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

El frontend queda disponible en `http://localhost:4321`.

Para iniciar ambas capas a la vez, una vez creado `backend/venv`:

```powershell
npm run dev:all
```

## Importar noticias UPLA

1. Abre `http://localhost:4321/admin`.
2. Selecciona **Importar UPLA**.
3. Elige 3, 5 o 10 noticias.
4. Inicia la importación.

Primero se extrae el listado principal. Las URLs existentes se omiten antes de extraer el artículo, por lo que las ejecuciones repetidas no vuelven a consumir créditos por esas páginas. Cada noticia nueva requiere una extracción adicional y una llamada a MiniMax M3 para su resumen.

## API

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/news/` | Lista y filtra noticias |
| `GET` | `/api/news/stats` | Estadísticas generales |
| `POST` | `/api/news/` | Crea e indexa una noticia |
| `PUT` | `/api/news/{id}` | Actualiza y reindexa una noticia |
| `DELETE` | `/api/news/{id}` | Elimina una noticia y su índice |
| `POST` | `/api/scrape/upla` | Importa de 1 a 10 noticias UPLA |
| `POST` | `/api/chat/` | Consulta el asistente RAG |
| `GET` | `/api/chat/status` | Estado, documentos y modelo activo |

Ejemplo de importación:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/scrape/upla `
  -ContentType application/json `
  -Body '{"limit":5}'
```

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---:|---|
| `OPENROUTER_API_KEY` | Sí | Key utilizada exclusivamente en el backend |
| `OPENROUTER_MODEL` | Sí | Modelo de resumen y chat; por defecto `minimax/minimax-m3:free` |
| `SGAI_API_KEY` | Sí* | Nombre oficial de la key de ScrapeGraphAI |
| `API_SCRAPEGRAPHAI` | Sí* | Alias compatible con la configuración inicial |
| `PUBLIC_API_URL` | Sí | URL pública del backend para Astro |
| `OPENROUTER_SITE_URL` | No | Referente enviado a OpenRouter |
| `OPENROUTER_APP_NAME` | No | Nombre de la aplicación enviado a OpenRouter |
| `SGAI_TIMEOUT` | No | Timeout de ScrapeGraphAI en segundos, por defecto 120 |
| `RAG_MAX_DISTANCE` | No | Umbral de distancia coseno, por defecto 0.95 |

\* Define `SGAI_API_KEY` o `API_SCRAPEGRAPHAI`, no ambas.

Las API keys nunca se envían al navegador. Los archivos `.env` están ignorados por Git; solo los ejemplos sin secretos se versionan.

## Despliegue

El frontend puede desplegarse en Vercel configurando `PUBLIC_API_URL`. El backend necesita un servicio persistente (por ejemplo, Railway o Render) porque SQLite y ChromaDB escriben en disco. Configura allí las variables de OpenRouter y ScrapeGraphAI.
