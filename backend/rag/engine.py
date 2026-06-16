import os
import logging
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
import chromadb

load_dotenv()
logger = logging.getLogger(__name__)


class RAGEngine:
    """Motor RAG: ChromaDB para retrieval + Google Gemini para generacion."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no esta configurada en el archivo .env")

        # Cliente Gemini nuevo SDK
        self.client = genai.Client(api_key=api_key)

        # Cliente ChromaDB persistente
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name="university_news",
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("RAGEngine inicializado correctamente.")

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    def _get_embedding(self, text: str) -> list:
        """Genera embedding de documento con Gemini text-embedding-004."""
        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        return response.embeddings[0].values

    def _get_query_embedding(self, text: str) -> list:
        """Genera embedding de consulta con Gemini text-embedding-004."""
        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        return response.embeddings[0].values

    # ------------------------------------------------------------------
    # Gestion del indice vectorial
    # ------------------------------------------------------------------
    def add_news(
        self,
        news_id: int,
        title: str,
        content: str,
        category: str,
        university: str,
        summary: Optional[str] = None,
    ):
        """Agrega o actualiza una noticia en el indice vectorial."""
        doc_text = (
            f"Titulo: {title}\n"
            f"Universidad: {university}\n"
            f"Categoria: {category}\n"
        )
        if summary:
            doc_text += f"Resumen: {summary}\n"
        doc_text += f"Contenido: {content}"

        embedding = self._get_embedding(doc_text)

        self.collection.upsert(
            ids=[str(news_id)],
            embeddings=[embedding],
            documents=[doc_text],
            metadatas=[{
                "news_id": news_id,
                "title": title,
                "category": category,
                "university": university,
            }],
        )
        logger.info(f"Noticia {news_id} indexada en ChromaDB.")

    def remove_news(self, news_id: int):
        """Elimina una noticia del indice vectorial."""
        try:
            self.collection.delete(ids=[str(news_id)])
            logger.info(f"Noticia {news_id} eliminada de ChromaDB.")
        except Exception as e:
            logger.warning(f"No se pudo eliminar noticia {news_id}: {e}")

    # ------------------------------------------------------------------
    # Consulta RAG
    # ------------------------------------------------------------------
    def query(self, question: str, n_results: int = 4) -> dict:
        """Pipeline RAG: pregunta -> embedding -> busqueda -> Gemini -> respuesta."""
        total_docs = self.collection.count()
        if total_docs == 0:
            return {
                "answer": (
                    "Aun no hay noticias indexadas. "
                    "Por favor, agrega noticias desde el panel de administracion."
                ),
                "sources": [],
            }

        n = min(n_results, total_docs)
        query_embedding = self._get_query_embedding(question)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        # Filtrar por relevancia coseno (menor distancia = mas similar)
        relevant = [
            (doc, meta, dist)
            for doc, meta, dist in zip(documents, metadatas, distances)
            if dist < 0.8
        ]

        if not relevant:
            return {
                "answer": (
                    "No encontre noticias relevantes para tu consulta. "
                    "Intenta reformular la pregunta o agrega mas noticias sobre ese tema."
                ),
                "sources": [],
            }

        # Construir contexto para el LLM
        context_parts = []
        sources = []
        for i, (doc, meta, _) in enumerate(relevant, 1):
            context_parts.append(f"[Noticia {i}]\n{doc}")
            sources.append({
                "news_id": meta.get("news_id"),
                "title": meta.get("title"),
                "category": meta.get("category"),
                "university": meta.get("university"),
            })

        context = "\n\n".join(context_parts)

        prompt = (
            "Eres un asistente experto en noticias universitarias. "
            "Responde siempre en espanol de forma clara, precisa y amable.\n\n"
            "Basandote UNICAMENTE en las siguientes noticias universitarias, "
            "responde la pregunta del usuario de forma detallada y util.\n\n"
            "=== NOTICIAS DISPONIBLES ===\n"
            f"{context}\n"
            "=== FIN DE NOTICIAS ===\n\n"
            f"Pregunta: {question}\n\n"
            "Responde en espanol de forma clara y estructurada. "
            "Si mencionas informacion especifica, indica de que noticia proviene."
        )

        response = self.client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )

        return {
            "answer": response.text,
            "sources": sources,
        }

    def get_index_count(self) -> int:
        """Retorna el numero de documentos indexados."""
        return self.collection.count()
