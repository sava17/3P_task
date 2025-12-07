from annoy import AnnoyIndex
from typing import List, Dict, Optional
import json
from pathlib import Path
from config.settings import (
    VECTOR_INDEX_PATH,
    CHUNKS_PATH,
    EMBEDDING_DIMENSION,
    TOP_K_RETRIEVAL
)
from src.models import KnowledgeChunk
from .embeddings import EmbeddingGenerator

class VectorStore:
    """Vector database using Annoy for similarity search"""

    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.index = AnnoyIndex(EMBEDDING_DIMENSION, 'angular')
        self.chunks: List[KnowledgeChunk] = []
        self.is_built = False

        # Load existing index if available
        if VECTOR_INDEX_PATH.exists() and CHUNKS_PATH.exists():
            self.load()

    def add_chunk(self, chunk: KnowledgeChunk):
        """
        Add a knowledge chunk to the vector store

        Args:
            chunk: Knowledge chunk with content
        """
        # Generate embedding if not already present
        if chunk.embedding is None:
            chunk.embedding = self.embedding_generator.generate_embedding(chunk.content)

        # Add to index
        idx = len(self.chunks)
        self.index.add_item(idx, chunk.embedding)
        self.chunks.append(chunk)
        self.is_built = False

    def add_chunks_batch(self, chunks: List[KnowledgeChunk]):
        """
        Add multiple knowledge chunks

        Args:
            chunks: List of knowledge chunks
        """
        # Generate embeddings for chunks without them
        texts_to_embed = []
        chunk_indices = []

        for i, chunk in enumerate(chunks):
            if chunk.embedding is None:
                texts_to_embed.append(chunk.content)
                chunk_indices.append(i)

        if texts_to_embed:
            embeddings = self.embedding_generator.generate_embeddings_batch(texts_to_embed)
            for chunk_idx, embedding in zip(chunk_indices, embeddings):
                chunks[chunk_idx].embedding = embedding

        # Add all chunks to index
        for chunk in chunks:
            idx = len(self.chunks)
            self.index.add_item(idx, chunk.embedding)
            self.chunks.append(chunk)

        self.is_built = False

    def build(self, n_trees: int = 10):
        """
        Build the index for similarity search

        Args:
            n_trees: Number of trees (more = higher precision, slower build)
        """
        if not self.is_built:
            self.index.build(n_trees)
            self.is_built = True
            print(f"Built vector index with {len(self.chunks)} chunks")

    def search(
        self,
        query: str,
        top_k: int = TOP_K_RETRIEVAL,
        municipality: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> List[KnowledgeChunk]:
        """
        Search for similar chunks

        Args:
            query: Search query
            top_k: Number of results to return
            municipality: Filter by municipality (optional)
            document_type: Filter by document type (optional)

        Returns:
            List of similar knowledge chunks
        """
        if not self.is_built:
            self.build()

        # Generate query embedding with retrieval_query task type
        query_embedding = self.embedding_generator.generate_embedding(
            query,
            task_type="retrieval_query"
        )

        # Get nearest neighbors
        indices, distances = self.index.get_nns_by_vector(
            query_embedding,
            top_k * 3,  # Get more than needed for filtering
            include_distances=True
        )

        # Retrieve chunks and apply filters
        results = []
        for idx, distance in zip(indices, distances):
            chunk = self.chunks[idx]

            # Apply filters
            if municipality and chunk.municipality and chunk.municipality != municipality:
                continue
            if document_type and chunk.document_type and str(chunk.document_type) != document_type:
                continue

            results.append(chunk)
            if len(results) >= top_k:
                break

        return results

    def retrieve_context(
        self,
        query: str,
        top_k: int = TOP_K_RETRIEVAL,
        municipality: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> List[str]:
        """
        Retrieve context strings for RAG

        Args:
            query: Search query
            top_k: Number of results
            municipality: Filter by municipality
            document_type: Filter by document type

        Returns:
            List of context strings
        """
        chunks = self.search(query, top_k, municipality, document_type)
        return [chunk.content for chunk in chunks]

    def save(self):
        """Save index and chunks to disk"""
        if not self.is_built:
            self.build()

        # Save Annoy index
        VECTOR_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.index.save(str(VECTOR_INDEX_PATH))

        # Save chunks
        chunks_data = [chunk.model_dump(mode='json') for chunk in self.chunks]
        with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2, default=str)

        print(f"Saved vector store: {len(self.chunks)} chunks")

    def load(self):
        """Load index and chunks from disk"""
        # Load Annoy index
        self.index.load(str(VECTOR_INDEX_PATH))
        self.is_built = True

        # Load chunks
        with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)

        self.chunks = [KnowledgeChunk(**chunk_dict) for chunk_dict in chunks_data]
        print(f"Loaded vector store: {len(self.chunks)} chunks")

    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        stats = {
            "total_chunks": len(self.chunks),
            "is_built": self.is_built,
            "by_source_type": {},
            "by_municipality": {},
            "by_document_type": {}
        }

        for chunk in self.chunks:
            # Count by source type
            stats["by_source_type"][chunk.source_type] = \
                stats["by_source_type"].get(chunk.source_type, 0) + 1

            # Count by municipality
            if chunk.municipality:
                stats["by_municipality"][chunk.municipality] = \
                    stats["by_municipality"].get(chunk.municipality, 0) + 1

            # Count by document type
            if chunk.document_type:
                doc_type = str(chunk.document_type)
                stats["by_document_type"][doc_type] = \
                    stats["by_document_type"].get(doc_type, 0) + 1

        return stats
