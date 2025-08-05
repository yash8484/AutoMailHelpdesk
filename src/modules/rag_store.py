import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from tenacity import retry, stop_after_attempt, wait_exponential
from ..settings import settings as app_settings

logger = logging.getLogger(__name__)


class RAGStore:
    """
    ChromaDB-based vector store for RAG (Retrieval-Augmented Generation).
    """
    
    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.HttpClient(
            host=app_settings.CHROMADB_HOST,
            port=app_settings.CHROMADB_PORT,
            settings=Settings(
                chroma_client_auth_provider="chromadb.auth.basic.BasicAuthClientProvider",
                chroma_client_auth_credentials_provider="chromadb.auth.basic.BasicAuthCredentialsProvider"
            )
        )
        
        # Get or create collection
        self.collection_name = app_settings.CHROMADB_COLLECTION_NAME
        self.collection = self._get_or_create_collection()
        
        logger.info(f"Initialized RAG store with collection: {self.collection_name}")
    
    def _get_or_create_collection(self):
        """
        Get existing collection or create new one.
        """
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "AutoMailHelpdesk knowledge base"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        return collection
    
    @retry(
        stop=stop_after_attempt(app_settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None
    ):
        """
        Add documents to the vector store.
        """
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(documents)} documents to RAG store")
        
        except Exception as e:
            logger.error(f"Error adding documents to RAG store: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(app_settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def search_similar(
        self,
        query: str,
        n_results: int = 5,
        query_embedding: Optional[List[float]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents.
        """
        try:
            # If no embedding provided, use query text directly
            if query_embedding is None:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where
                )
            else:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where
                )
            
            logger.debug(f"Found {len(results['documents'][0])} similar documents for query")
            return results
        
        except Exception as e:
            logger.error(f"Error searching RAG store: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def get_context_for_query(
        self,
        query: str,
        max_context_length: int = 2000,
        n_results: int = 5
    ) -> str:
        """
        Get relevant context for a query.
        """
        try:
            # Search for similar documents
            results = self.search_similar(query, n_results=n_results)
            
            # Combine documents into context
            context_parts = []
            current_length = 0
            
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                # Skip if document is too dissimilar (adjust threshold as needed)
                if distance > 0.8:
                    continue
                
                # Add document with source information
                source = metadata.get('source', f'Document {i+1}')
                doc_text = f"[Source: {source}]\n{doc}\n"
                
                # Check if adding this document would exceed max length
                if current_length + len(doc_text) > max_context_length:
                    break
                
                context_parts.append(doc_text)
                current_length += len(doc_text)
            
            context = "\n---\n".join(context_parts)
            
            logger.debug(f"Generated context of {len(context)} characters from {len(context_parts)} documents")
            return context
        
        except Exception as e:
            logger.error(f"Error getting context for query: {e}")
            return ""
    
    def update_document(self, doc_id: str, document: str, metadata: Dict[str, Any]):
        """
        Update an existing document.
        """
        try:
            self.collection.update(
                ids=[doc_id],
                documents=[document],
                metadatas=[metadata]
            )
            
            logger.debug(f"Updated document {doc_id}")
        
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            raise
    
    def delete_document(self, doc_id: str):
        """
        Delete a document from the store.
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted document {doc_id}")
        
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        """
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.collection_name
            }
        
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"document_count": 0, "collection_name": self.collection_name}
    
    def load_knowledge_base(self, knowledge_files: List[str]):
        """
        Load knowledge base from files.
        """
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, file_path in enumerate(knowledge_files):
                # TODO: Implement file reading and processing
                # This is a placeholder - implement based on file types (PDF, TXT, etc.)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split content into chunks if needed
                    chunks = self._split_text(content)
                    
                    for j, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadatas.append({
                            "source": file_path,
                            "chunk_id": j,
                            "file_type": file_path.split('.')[-1].lower()
                        })
                        ids.append(f"{file_path}_{j}")
                
                except Exception as e:
                    logger.error(f"Error loading file {file_path}: {e}")
                    continue
            
            if documents:
                self.add_documents(documents, metadatas, ids)
                logger.info(f"Loaded {len(documents)} chunks from {len(knowledge_files)} files")
        
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            raise
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks.
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > start + chunk_size // 2:
                    chunk = text[start:break_point + 1]
                    end = break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    # TODO: Add methods for backup, restore, and collection management

