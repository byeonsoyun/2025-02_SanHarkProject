"""
RAG Integration Module for Django Backend
Connects the Ollama RAG system with Django views
"""
import os
import sys
import json
import PyPDF2
from pathlib import Path

# Add the current directory to path
RAG_SYSTEM_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(RAG_SYSTEM_PATH)

try:
    from data_processor import DataProcessor
    from ollama_client import OllamaClient
except ImportError as e:
    print(f"RAG system modules not found: {e}")
    DataProcessor = None
    OllamaClient = None

class RAGChatbot:
    def __init__(self):
        self.processor = DataProcessor() if DataProcessor else None
        self.ollama_client = OllamaClient(model="llama3.2") if OllamaClient else None
        self.is_initialized = False
        
        # Try to load existing index
        if self.processor:
            try:
                self.processor.load_index(
                    os.path.join(RAG_SYSTEM_PATH, "faiss_index.bin"),
                    os.path.join(RAG_SYSTEM_PATH, "chunks.pkl")
                )
                self.is_initialized = True
            except Exception as e:
                print(f"No existing RAG index found: {e}")
                print("Upload documents to initialize.")
    
    def process_pdf(self, pdf_path):
        """Process PDF file and update RAG index"""
        if not self.processor:
            return "RAG system not available"
        
        try:
            # Extract text from PDF
            text_content = self._extract_pdf_text(pdf_path)
            
            # Create JSON-like structure for processing
            pdf_data = {
                "document": os.path.basename(pdf_path),
                "content": text_content,
                "type": "pdf"
            }
            
            # Process with RAG system
            text_data = self.processor._extract_text_from_json(pdf_data)
            chunks = self.processor.chunk_text(text_data)
            
            # If first document, create new index
            if not self.is_initialized:
                self.processor.create_embeddings(chunks)
                self.processor.create_faiss_index()
            else:
                # Add to existing index
                new_embeddings = self.processor.embedding_model.encode(chunks)
                self.processor.chunks.extend(chunks)
                self.processor.index.add(new_embeddings.astype('float32'))
            
            # Save updated index
            self.processor.save_index(
                f"{RAG_SYSTEM_PATH}/faiss_index.bin",
                f"{RAG_SYSTEM_PATH}/chunks.pkl"
            )
            self.is_initialized = True
            
            return f"PDF processed successfully. Added {len(chunks)} chunks to knowledge base."
            
        except Exception as e:
            return f"Error processing PDF: {str(e)}"
    
    def initialize_with_legal_data(self):
        """Initialize RAG system with legal documents from database"""
        if not self.processor:
            return "RAG system not available"
        
        try:
            import django
            django.setup()
            from .models import LawDocument
            
            # Get all legal documents
            legal_docs = LawDocument.objects.all()[:1000]  # Limit for testing
            
            if not legal_docs:
                return "No legal documents found in database"
            
            # Prepare text data
            all_text = []
            for doc in legal_docs:
                doc_text = f"제목: {doc.title}\n내용: {doc.content}\n법원: {doc.court_name}\n사건번호: {doc.case_number}"
                all_text.append(doc_text)
            
            # Process with RAG
            combined_text = "\n\n".join(all_text)
            chunks = self.processor.chunk_text(combined_text)
            
            self.processor.create_embeddings(chunks)
            self.processor.create_faiss_index()
            self.processor.save_index()
            self.is_initialized = True
            
            return f"Legal RAG system initialized with {len(chunks)} chunks from {len(legal_docs)} documents"
            
        except Exception as e:
            return f"Error initializing legal RAG: {str(e)}"
        """Extract text from PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
        return text
    
    def chat(self, message):
        """Process chat message with RAG"""
        if not self.processor or not self.ollama_client:
            return "RAG system not available"
        
        if not self.is_initialized:
            return "Please upload a document first to initialize the knowledge base."
        
        try:
            # Search for relevant context
            relevant_chunks = self.processor.search(message, k=3)
            context = " ".join(relevant_chunks)
            
            # Generate response using Ollama
            response = self.ollama_client.generate_response(message, context)
            return response
            
        except Exception as e:
            return f"Error generating response: {str(e)}"

# Global RAG instance
rag_chatbot = RAGChatbot()
