import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Manages the Pinecone vector store for RAG"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
        self.index_name = settings.pinecone_index_name
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
    async def initialize(self):
        """Initialize Pinecone connection and index"""
        try:
            # Initialize Pinecone
            pc = Pinecone(api_key=settings.pinecone_api_key)
            
            # Create index if it doesn't exist
            if self.index_name not in pc.list_indexes().names():
                pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # OpenAI embedding dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                logger.info(f"Created Pinecone index: {self.index_name}")
            
            # Get index
            index = pc.Index(self.index_name)
            
            # Create vector store
            self.vector_store = PineconeVectorStore(
                index=index,
                embedding=self.embeddings,
                text_key="text",
                namespace="company_docs"
            )
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to the vector store"""
        if not self.vector_store:
            await self.initialize()
        
        try:
            # Convert to LangChain documents
            langchain_docs = []
            for doc in documents:
                # Split large documents
                if len(doc['content']) > 1000:
                    splits = self.text_splitter.split_text(doc['content'])
                    for i, split in enumerate(splits):
                        langchain_doc = Document(
                            page_content=split,
                            metadata={
                                **doc.get('metadata', {}),
                                'title': doc['title'],
                                'doc_type': doc.get('type', 'general'),
                                'category': doc.get('category', 'general'),
                                'chunk_index': i,
                                'total_chunks': len(splits)
                            }
                        )
                        langchain_docs.append(langchain_doc)
                else:
                    langchain_doc = Document(
                        page_content=doc['content'],
                        metadata={
                            **doc.get('metadata', {}),
                            'title': doc['title'],
                            'doc_type': doc.get('type', 'general'),
                            'category': doc.get('category', 'general')
                        }
                    )
                    langchain_docs.append(langchain_doc)
            
            # Add to vector store
            ids = await self.vector_store.aadd_documents(langchain_docs)
            
            logger.info(f"Added {len(langchain_docs)} document chunks to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents"""
        if not self.vector_store:
            await self.initialize()
        
        try:
            # Perform search
            results = await self.vector_store.asimilarity_search(
                query=query,
                k=k,
                filter=filter
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    async def delete_documents(self, ids: List[str]):
        """Delete documents by ID"""
        if not self.vector_store:
            await self.initialize()
        
        try:
            await self.vector_store.adelete(ids)
            logger.info(f"Deleted {len(ids)} documents from vector store")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise