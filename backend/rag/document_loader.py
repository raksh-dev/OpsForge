from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..database.models import CompanyDocument
from ..database.connection import SessionLocal
from .retriever import RAGRetriever
import logging

logger = logging.getLogger(__name__)

class DocumentLoader:
    """Loads company documents into the RAG system"""
    
    def __init__(self, rag_retriever: RAGRetriever):
        self.rag_retriever = rag_retriever
    
    async def load_all_documents(self):
        """Load all active company documents into the vector store"""
        db = SessionLocal()
        try:
            # Get all active documents
            documents = db.query(CompanyDocument).filter(
                CompanyDocument.is_active == True
            ).all()
            
            if not documents:
                logger.warning("No documents found to load")
                return
            
            # Prepare documents for vector store
            doc_list = []
            for doc in documents:
                doc_dict = {
                    'title': doc.title,
                    'content': doc.content,
                    'type': doc.document_type,
                    'category': doc.category,
                    'metadata': {
                        'version': doc.version,
                        'created_at': doc.created_at.isoformat(),
                        'db_id': doc.id
                    }
                }
                doc_list.append(doc_dict)
            
            # Add to vector store
            ids = await self.rag_retriever.add_company_documents(doc_list)
            
            # Update documents with embedding IDs
            for i, doc in enumerate(documents):
                if i < len(ids):
                    doc.embedding_id = ids[i]
            
            db.commit()
            
            logger.info(f"Loaded {len(documents)} documents into RAG system")
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    async def load_document(self, document_id: int):
        """Load a specific document into the vector store"""
        db = SessionLocal()
        try:
            document = db.query(CompanyDocument).filter(
                CompanyDocument.id == document_id
            ).first()
            
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Prepare document
            doc_dict = {
                'title': document.title,
                'content': document.content,
                'type': document.document_type,
                'category': document.category,
                'metadata': {
                    'version': document.version,
                    'created_at': document.created_at.isoformat(),
                    'db_id': document.id
                }
            }
            
            # Add to vector store
            ids = await self.rag_retriever.add_company_documents([doc_dict])
            
            # Update document with embedding ID
            if ids:
                document.embedding_id = ids[0]
                db.commit()
            
            logger.info(f"Loaded document {document_id} into RAG system")
            
        except Exception as e:
            logger.error(f"Error loading document {document_id}: {e}")
            db.rollback()
            raise
        finally:
            db.close()