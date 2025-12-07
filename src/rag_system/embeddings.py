from google import genai
from google.genai import types
from typing import List, Optional
from config.settings import GEMINI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSION

class EmbeddingGenerator:
    """Generate embeddings for text chunks using Gemini"""

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def generate_embedding(
        self,
        text: str,
        task_type: str = "retrieval_document",
        title: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for a single text using Gemini

        Args:
            text: Input text
            task_type: Type of task - "retrieval_document" for documents to store,
                      "retrieval_query" for search queries
            title: Optional title for the document (helps with context)

        Returns:
            Embedding vector
        """
        config_params = {
            "output_dimensionality": EMBEDDING_DIMENSION,
            "task_type": task_type
        }
        if title:
            config_params["title"] = title

        result = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(**config_params)
        )
        return result.embeddings[0].values

    def generate_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "retrieval_document",
        titles: Optional[List[str]] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using Gemini batch processing

        Args:
            texts: List of input texts
            task_type: Type of task - "retrieval_document" for documents,
                      "retrieval_query" for queries
            titles: Optional list of titles (must match length of texts)

        Returns:
            List of embedding vectors
        """
        # Gemini supports true batch processing by passing list of texts
        config_params = {
            "output_dimensionality": EMBEDDING_DIMENSION,
            "task_type": task_type
        }

        # If no titles provided, process as a single batch
        if not titles:
            result = self.client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(**config_params)
            )
            return [emb.values for emb in result.embeddings]

        # If titles provided, process individually (API limitation)
        embeddings = []
        for text, title in zip(texts, titles):
            config_params["title"] = title
            result = self.client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(**config_params)
            )
            embeddings.append(result.embeddings[0].values)

        return embeddings
