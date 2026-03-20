import os
import uuid
import logging
import ollama
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

logger = logging.getLogger("RAGMemory")

# Load DB Host (Often host.docker.internal when run via Docker on Windows, or direct IP)
QDRANT_HOST = os.environ.get("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

COLLECTION_NAME = "aka_memory"
EMBEDDING_MODEL = "nomic-embed-text" # Model trained specifically for compact RAG vectors

class RAGMemoryService:
    def __init__(self):
        self.qdrant = None
        self.enabled = False
        try:
            self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
            self._init_collection()
            self.enabled = True
            logger.info(f"Qdrant connecté à {QDRANT_HOST}:{QDRANT_PORT}. Mémoire active.")
        except Exception as e:
            logger.error(f"Impossible de connecter Qdrant: {e}. Mémoire RAG désactivée.")

    def _init_collection(self):
        """Creates the collection if it doesn't exist."""
        collections = self.qdrant.get_collections().collections
        exists = any(c.name == COLLECTION_NAME for c in collections)
        if not exists:
            # nomic-embed-text generates 768-dimensional vectors natively
            self.qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
            logger.info(f"Collection {COLLECTION_NAME} créée.")

    def _get_embedding(self, text: str) -> list:
        try:
            ollama_client = ollama.Client(host=OLLAMA_HOST)
            # Instructs Ollama to vectorize the text
            res = ollama_client.embeddings(model=EMBEDDING_MODEL, prompt=text)
            return res["embedding"]
        except Exception as e:
            logger.error(f"Erreur Embeddings Ollama: {e}")
            raise e

    def memorize(self, subject: str, content: str) -> bool:
        """Saves a string as a permanent thought in Qdrant."""
        if not self.enabled:
            return False
            
        try:
            vector = self._get_embedding(f"{subject}. {content}")
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"subject": subject, "content": content}
            )
            self.qdrant.upsert(
                collection_name=COLLECTION_NAME,
                points=[point]
            )
            return True
        except Exception as e:
            logger.error(f"RAG Memorize Error: {e}")
            return False

    def recall(self, query: str, limit: int = 2) -> str:
        """Searches memory for semantically closest matches."""
        if not self.enabled:
            return "Mémoire désactivée (Base de données Qdrant injoignable)."
            
        try:
            vector = self._get_embedding(query)
            hits = self.qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=vector,
                limit=limit
            )
            if not hits:
                return "Aucun souvenir pertinent trouvé à ce sujet."
                
            memories = []
            for hit in hits:
                if hit.score > 0.5: # Only return highly relevant thoughts
                    memories.append(f"[{hit.payload.get('subject')}] : {hit.payload.get('content')} (Similarité: {hit.score:.2f})")
            
            if not memories:
                return "J'ai cherché dans ma mémoire mais rien n'était vraiment pertinent par rapport à la question."
                
            return "\n".join(memories)
        except Exception as e:
            logger.error(f"RAG Recall Error: {e}")
            return f"Erreur lors de la consultation de ma mémoire: {str(e)}"

# Singleton
memory = RAGMemoryService()
