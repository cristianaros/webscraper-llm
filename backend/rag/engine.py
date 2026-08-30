import logging
import os
from datetime import datetime
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

from rag.openrouter import OpenRouterClient

load_dotenv()
logger = logging.getLogger(__name__)


class RAGEngine:
    """Retrieval local con ChromaDB y generacion mediante OpenRouter."""

    def __init__(self):
        self.llm = OpenRouterClient()

        # La coleccion v2 usa embeddings locales y no es compatible en dimensionesS
        local_embeddings = embedding_functions.DefaultEmbeddingFunction()
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma_client.get_or_create_collection(
            name="university_news_local_v2",
            metadata={"hnsw:space": "cosine"},
            embedding_function=local_embeddings,
        )
        self.max_distance = float(os.getenv("RAG_MAX_DISTANCE", "0.95"))
        logger.info(
            "RAGEngine inicializado con OpenRouter (%s) y embeddings locales.",
            self.llm.model,
        )

    def add_news(
        self,
        news_id: int,
        title: str,
        content: str,
        category: str,
        university: str,
        summary: Optional[str] = None,
        source_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ):
        """Agrega o actualiza una noticia en el indice vectorial."""
        doc_text = (
            f"Titulo: {title}\n"
            f"Universidad: {university}\n"
            f"Categoria: {category}\n"
        )
        if published_at:
            doc_text += f"Fecha de publicacion: {published_at.date().isoformat()}\n"
        if summary:
            doc_text += f"Resumen: {summary}\n"
        doc_text += f"Contenido: {content}"

        self.collection.upsert(
            ids=[str(news_id)],
            documents=[doc_text],
            metadatas=[
                {
                    "news_id": news_id,
                    "title": title,
                    "category": category,
                    "university": university,
                    "source_url": source_url or "",
                }
            ],
        )
        logger.info("Noticia %s indexada en ChromaDB.", news_id)

    def remove_news(self, news_id: int):
        """Elimina una noticia del indice vectorial."""
        try:
            self.collection.delete(ids=[str(news_id)])
            logger.info("Noticia %s eliminada de ChromaDB.", news_id)
        except Exception as exc:
            logger.warning("No se pudo eliminar noticia %s: %s", news_id, exc)

    def summarize_news(self, title: str, content: str) -> str:
        return self.llm.summarize_news(title, content)

    def query(
        self,
        question: str,
        n_results: int = 4,
        news_id: Optional[int] = None,
    ) -> dict:
        """Pregunta -> embedding local -> retrieval -> MiniMax M3 -> respuesta."""
        total_docs = self.collection.count()
        if total_docs == 0:
            return {
                "answer": (
                    "Aun no hay noticias indexadas. Importa noticias UPLA o agregalas "
                    "desde el panel de administracion."
                ),
                "sources": [],
            }

        if news_id is not None:
            selected = self.collection.get(
                ids=[str(news_id)],
                include=["documents", "metadatas"],
            )
            selected_documents = selected.get("documents") or []
            selected_metadatas = selected.get("metadatas") or []
            relevant = [
                (document, metadata, 0.0)
                for document, metadata in zip(selected_documents, selected_metadatas)
            ]
            if not relevant:
                return {
                    "answer": (
                        "La noticia seleccionada no esta disponible en el indice. "
                        "Actualizala desde el panel de administracion e intenta nuevamente."
                    ),
                    "sources": [],
                }
        else:
            results = self.collection.query(
                query_texts=[question],
                n_results=min(n_results, total_docs),
                include=["documents", "metadatas", "distances"],
            )

            documents = (results.get("documents") or [[]])[0]
            metadatas = (results.get("metadatas") or [[]])[0]
            distances = (results.get("distances") or [[]])[0]
            relevant = [
                (document, metadata, distance)
                for document, metadata, distance in zip(
                    documents, metadatas, distances
                )
                if distance <= self.max_distance
            ]

        if not relevant:
            return {
                "answer": (
                    "No encontre noticias suficientemente relacionadas con tu consulta. "
                    "Intenta reformular la pregunta."
                ),
                "sources": [],
            }

        context_parts = []
        sources = []
        for index, (document, metadata, _) in enumerate(relevant, 1):
            context_parts.append(f"[Noticia {index}]\n{document}")
            sources.append(
                {
                    "news_id": metadata.get("news_id"),
                    "title": metadata.get("title"),
                    "category": metadata.get("category"),
                    "university": metadata.get("university"),
                    "source_url": metadata.get("source_url") or None,
                }
            )

        answer = self.llm.answer_from_news(question, "\n\n".join(context_parts))
        return {"answer": answer, "sources": sources}

    def get_index_count(self) -> int:
        return self.collection.count()

    @property
    def model_name(self) -> str:
        return self.llm.model
