import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from pathlib import Path
from config.settings import (
    KNOWLEDGE_BASE_DIR,
    TOP_K_RETRIEVAL
)
from src.models import KnowledgeChunk
from .embeddings import EmbeddingGenerator

class VectorStore:
    """Vector database using Chroma for similarity search with continuous learning support"""

    def __init__(self, collection_name: str = "br18_knowledge"):
        # Ensure the knowledge base directory exists
        KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

        self.embedding_generator = EmbeddingGenerator()

        # Initialize Chroma client with persistent storage
        self.client = chromadb.PersistentClient(
            path=str(KNOWLEDGE_BASE_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "BR18 fire safety document knowledge base"}
        )

        print(f"Chroma collection '{collection_name}' initialized with {self.collection.count()} existing chunks")

    def add_chunk(self, chunk: KnowledgeChunk):
        """
        Add a knowledge chunk to the vector store

        Args:
            chunk: Knowledge chunk with content
        """
        # Generate embedding if not already present
        if chunk.embedding is None:
            chunk.embedding = self.embedding_generator.generate_embedding(
                chunk.content,
                task_type="retrieval_document"
            )

        # Prepare metadata (Chroma doesn't support nested dicts, so flatten)
        metadata = {
            "source_type": chunk.source_type,
            "source_reference": chunk.source_reference,
            "created_at": chunk.created_at.isoformat()
        }

        if chunk.municipality:
            metadata["municipality"] = chunk.municipality
        if chunk.document_type:
            metadata["document_type"] = chunk.document_type.value if hasattr(chunk.document_type, 'value') else str(chunk.document_type)

        # Add additional metadata fields (flatten the metadata dict)
        for key, value in chunk.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                metadata[f"meta_{key}"] = value

        # Add to Chroma
        self.collection.add(
            ids=[chunk.chunk_id],
            embeddings=[chunk.embedding],
            documents=[chunk.content],
            metadatas=[metadata]
        )

    def add_chunks_batch(self, chunks: List[KnowledgeChunk]):
        """
        Add multiple knowledge chunks efficiently

        Args:
            chunks: List of knowledge chunks
        """
        if not chunks:
            return

        # Generate embeddings for chunks without them
        texts_to_embed = []
        chunk_indices = []

        for i, chunk in enumerate(chunks):
            if chunk.embedding is None:
                texts_to_embed.append(chunk.content)
                chunk_indices.append(i)

        if texts_to_embed:
            embeddings = self.embedding_generator.generate_embeddings_batch(
                texts_to_embed,
                task_type="retrieval_document"
            )
            for chunk_idx, embedding in zip(chunk_indices, embeddings):
                chunks[chunk_idx].embedding = embedding

        # Prepare batch data
        ids = []
        embeddings = []
        documents = []
        metadatas = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            embeddings.append(chunk.embedding)
            documents.append(chunk.content)

            # Prepare metadata
            metadata = {
                "source_type": chunk.source_type,
                "source_reference": chunk.source_reference,
                "created_at": chunk.created_at.isoformat()
            }

            if chunk.municipality:
                metadata["municipality"] = chunk.municipality
            if chunk.document_type:
                metadata["document_type"] = chunk.document_type.value if hasattr(chunk.document_type, 'value') else str(chunk.document_type)

            # Add additional metadata fields
            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[f"meta_{key}"] = value

            metadatas.append(metadata)

        # Batch add to Chroma
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

        print(f"Added {len(chunks)} chunks to vector store (total: {self.collection.count()})")

    def search(
        self,
        query: str,
        top_k: int = TOP_K_RETRIEVAL,
        municipality: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> List[KnowledgeChunk]:
        """
        Search for similar chunks with optional filtering

        Args:
            query: Search query
            top_k: Number of results to return
            municipality: Filter by municipality (optional)
            document_type: Filter by document type (optional)

        Returns:
            List of similar knowledge chunks
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(
            query,
            task_type="retrieval_query"
        )

        # Build where filter for Chroma
        where_filter = None
        if municipality or document_type:
            where_filter = {}
            if municipality:
                where_filter["municipality"] = municipality
            if document_type:
                where_filter["document_type"] = document_type

        # Query Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        # Convert results to KnowledgeChunk objects
        chunks = []
        if results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]

                # Reconstruct metadata dict from flattened format
                chunk_metadata = {}
                for key, value in metadata.items():
                    if key.startswith('meta_'):
                        chunk_metadata[key[5:]] = value

                chunk = KnowledgeChunk(
                    chunk_id=chunk_id,
                    source_type=metadata['source_type'],
                    source_reference=metadata['source_reference'],
                    municipality=metadata.get('municipality'),
                    document_type=metadata.get('document_type'),
                    content=results['documents'][0][i],
                    metadata=chunk_metadata,
                    embedding=results['embeddings'][0][i] if results['embeddings'] else None
                )
                chunks.append(chunk)

        return chunks

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

    def clear(self):
        """Clear all data from the vector store (useful for clean runs)"""
        # Delete and recreate the collection
        try:
            self.client.delete_collection(name=self.collection.name)
            print(f"Deleted existing collection: {self.collection.name}")
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"description": "BR18 fire safety document knowledge base"}
        )
        print("Vector store cleared - ready for fresh data")

    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        total_count = self.collection.count()

        # Get all items to calculate stats
        if total_count == 0:
            return {
                "total_chunks": 0,
                "by_source_type": {},
                "by_municipality": {},
                "by_document_type": {}
            }

        # Retrieve all metadata
        all_data = self.collection.get()

        stats = {
            "total_chunks": total_count,
            "by_source_type": {},
            "by_municipality": {},
            "by_document_type": {}
        }

        for metadata in all_data['metadatas']:
            # Count by source type
            source_type = metadata.get('source_type', 'unknown')
            stats["by_source_type"][source_type] = \
                stats["by_source_type"].get(source_type, 0) + 1

            # Count by municipality
            municipality = metadata.get('municipality')
            if municipality:
                stats["by_municipality"][municipality] = \
                    stats["by_municipality"].get(municipality, 0) + 1

            # Count by document type
            doc_type = metadata.get('document_type')
            if doc_type:
                stats["by_document_type"][doc_type] = \
                    stats["by_document_type"].get(doc_type, 0) + 1

        return stats

    def save(self):
        """
        Save is automatic with Chroma's PersistentClient
        This method exists for API compatibility but does nothing
        """
        print(f"Chroma auto-saves. Current count: {self.collection.count()} chunks")

    def load(self):
        """
        Load is automatic with Chroma's PersistentClient
        This method exists for API compatibility but does nothing
        """
        print(f"Chroma auto-loads. Current count: {self.collection.count()} chunks")
