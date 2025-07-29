from typing import List, Dict, Any, Optional
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI
from .vector_store import VectorStoreManager
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

class RAGRetriever:
    """Retrieval Augmented Generation system for company knowledge"""
    
    def __init__(self):
        self.vector_store_manager = VectorStoreManager()
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",  # Use cheaper model for compression
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        self.compressor = None
        self.compression_retriever = None
        
    async def initialize(self):
        """Initialize the RAG system"""
        try:
            # Initialize vector store
            await self.vector_store_manager.initialize()
            
            # Create compressor
            self.compressor = LLMChainExtractor.from_llm(self.llm)
            
            # Create compression retriever
            base_retriever = self.vector_store_manager.vector_store.as_retriever(
                search_kwargs={"k": 10}  # Retrieve more docs for compression
            )
            
            self.compression_retriever = ContextualCompressionRetriever(
                base_compressor=self.compressor,
                base_retriever=base_retriever
            )
            
            logger.info("RAG Retriever initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG Retriever: {e}")
            raise
    
    async def get_relevant_documents(
        self,
        query: str,
        filter: Optional[Dict[str, Any]] = None,
        use_compression: bool = True
    ) -> List[str]:
        """Get relevant documents for a query"""
        try:
            if use_compression and self.compression_retriever:
                # Use compression retriever
                if filter:
                    self.compression_retriever.base_retriever.search_kwargs['filter'] = filter
                
                docs = await self.compression_retriever.aget_relevant_documents(query)
                return [doc.page_content for doc in docs]
            else:
                # Use simple similarity search
                docs = await self.vector_store_manager.similarity_search(
                    query=query,
                    k=5,
                    filter=filter
                )
                return [doc.page_content for doc in docs]
                
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    async def add_company_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add company documents to the knowledge base"""
        return await self.vector_store_manager.add_documents(documents)
    
    async def update_document(self, doc_id: str, new_content: Dict[str, Any]):
        """Update a document in the knowledge base"""
        # Delete old version
        await self.vector_store_manager.delete_documents([doc_id])
        
        # Add new version
        ids = await self.vector_store_manager.add_documents([new_content])
        return ids[0] if ids else None
    
    async def cleanup(self):
        """Cleanup resources"""
        # Any cleanup needed
        pass