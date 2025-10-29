import json
import pandas as pd
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle

class DataProcessor:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(model_name)
        self.chunks = []
        self.embeddings = None
        self.index = None
    
    def load_data(self, file_path):
        """Load data from JSON or CSV file"""
        if file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return self._extract_text_from_json(data)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            return df.to_string()
    
    def _extract_text_from_json(self, data):
        """Extract meaningful text from JSON"""
        text_parts = []
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (str, int, float)):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, (dict, list)):
                    text_parts.append(self._extract_text_from_json(value))
        elif isinstance(data, list):
            for item in data:
                text_parts.append(self._extract_text_from_json(item))
        else:
            text_parts.append(str(data))
        return " ".join(text_parts)
    
    def chunk_text(self, text, chunk_size=500, overlap=50):
        """Split text into chunks with overlap"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
            
        return chunks
    
    def create_embeddings(self, chunks):
        """Create embeddings for chunks"""
        self.chunks = chunks
        self.embeddings = self.embedding_model.encode(chunks)
        return self.embeddings
    
    def create_faiss_index(self):
        """Create FAISS index from embeddings"""
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings.astype('float32'))
        return self.index
    
    def save_index(self, index_path="faiss_index.bin", chunks_path="chunks.pkl"):
        """Save FAISS index and chunks"""
        faiss.write_index(self.index, index_path)
        with open(chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)
    
    def load_index(self, index_path="faiss_index.bin", chunks_path="chunks.pkl"):
        """Load FAISS index and chunks"""
        self.index = faiss.read_index(index_path)
        with open(chunks_path, 'rb') as f:
            self.chunks = pickle.load(f)
    
    def search(self, query, k=3):
        """Search for relevant chunks"""
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        return [self.chunks[i] for i in indices[0]]
