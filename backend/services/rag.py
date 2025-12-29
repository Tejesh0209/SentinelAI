# backend/services/rag.py
from openai import AsyncOpenAI
import faiss
import numpy as np
import pickle
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class RAGService:
    """Retrieval Augmented Generation using FAISS"""
    
    def __init__(
        self,
        api_key: str,
        db_path: str,
        dimension: int = 1536  # OpenAI embedding size
    ):
        self.client = AsyncOpenAI(api_key=api_key)
        self.db_path = Path(db_path)
        self.dimension = dimension
        
        # Initialize or load index
        self.index_path = self.db_path / "faiss.index"
        self.docs_path = self.db_path / "documents.pkl"
        
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.docs_path, 'rb') as f:
                self.documents = pickle.load(f)
            logger.info(f"Loaded existing index with {len(self.documents)} docs")
        else:
            self.index = faiss.IndexFlatL2(dimension)
            self.documents: List[Dict[str, Any]] = []
            logger.info("Created new FAISS index")
    
    async def embed_text(self, text: str) -> np.ndarray:
        """Get embedding for text"""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    async def add_document(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> int:
        """
        Add a document to the index
        
        Args:
            text: Document text
            metadata: Optional metadata (title, source, etc.)
            
        Returns:
            Document ID
        """
        try:
            # Get embedding
            embedding = await self.embed_text(text)
            
            # Add to index
            self.index.add(embedding.reshape(1, -1))
            
            # Store document
            doc_id = len(self.documents)
            self.documents.append({
                "id": doc_id,
                "text": text,
                "metadata": metadata or {}
            })
            
            logger.info(f"Added document {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Add document error: {e}")
            raise
    
    async def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None
    ) -> List[int]:
        """Add multiple documents"""
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        doc_ids = []
        for text, metadata in zip(texts, metadatas):
            doc_id = await self.add_document(text, metadata)
            doc_ids.append(doc_id)
        
        return doc_ids
    
    async def search(
        self,
        query: str,
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of documents with scores
        """
        try:
            if len(self.documents) == 0:
                return []
            
            # Get query embedding
            query_embedding = await self.embed_text(query)
            
            # Search
            distances, indices = self.index.search(
                query_embedding.reshape(1, -1),
                min(k, len(self.documents))
            )
            
            # Format results
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc['score'] = float(1 / (1 + distance))  # Convert distance to similarity
                    results.append(doc)
            
            logger.info(f"Search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def save(self) -> None:
        """Save index and documents to disk"""
        try:
            self.db_path.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path))
            
            with open(self.docs_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            logger.info(f"Saved index with {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Save error: {e}")
            raise
    
    def clear(self) -> None:
        """Clear all documents"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        logger.info("Cleared index")
    
    def __len__(self) -> int:
        return len(self.documents)