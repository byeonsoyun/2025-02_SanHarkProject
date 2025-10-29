# Integrated RAG Chatbot System

A complete chatbot system combining React frontend, Django backend, and Ollama-powered RAG (Retrieval-Augmented Generation) capabilities.

## 🏗️ System Architecture

```
Frontend (React) ←→ Backend (Django) ←→ RAG System (Ollama + FAISS)
     ↓                    ↓                      ↓
- Chat Interface    - REST APIs           - Document Processing
- File Upload       - File Handling       - Embedding Generation
- Bootstrap UI      - CORS Support        - Similarity Search
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Ollama installed

### 1. Setup System
```bash
cd /Users/sang/SanHark_25_02
python setup_integrated_system.py
```

### 2. Start Ollama
```bash
# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull llama3.2
# or
ollama pull deepseek-coder
```

### 3. Start Backend
```bash
cd backend
python manage.py runserver
```

### 4. Start Frontend
```bash
cd frontend
npm start
```

### 5. Access Application
Visit `http://localhost:3000`

## 📁 Project Structure

```
SanHark_25_02/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/          # Page components
│   │   └── App.js          # Main app component
│   └── package.json
├── backend/                 # Django application
│   ├── chat/               # Chat app
│   ├── api/                # API app
│   ├── backend/            # Django settings
│   ├── rag_integration.py  # RAG system integration
│   ├── data_processor.py   # Document processing
│   ├── ollama_client.py    # Ollama client
│   └── manage.py
└── setup_integrated_system.py
```

## 🔧 Features

### Frontend (React)
- **Modern UI**: Bootstrap-based responsive design
- **Chat Interface**: Real-time messaging with bot
- **File Upload**: Support for PDF, JSON, CSV files
- **Routing**: Multi-page navigation
- **Error Handling**: User-friendly error messages

### Backend (Django)
- **REST APIs**: Chat and file upload endpoints
- **CORS Support**: Cross-origin requests enabled
- **File Processing**: PDF text extraction, JSON/CSV parsing
- **Error Handling**: Comprehensive error responses
- **Media Management**: File storage and serving

### RAG System
- **Document Processing**: Text extraction and chunking
- **Embeddings**: Sentence-transformers for semantic search
- **Vector Storage**: FAISS for efficient similarity search
- **LLM Integration**: Ollama for response generation
- **Context Retrieval**: Relevant document chunks for answers

## 🔌 API Endpoints

### Chat API
```http
POST /chat/api/chat/
Content-Type: application/json

{
  "message": "What products are available?"
}
```

### PDF Upload
```http
POST /chat/upload_pdf/
Content-Type: multipart/form-data

pdf: [PDF file]
```

### Data Upload (JSON/CSV)
```http
POST /chat/upload_data/
Content-Type: multipart/form-data

file: [JSON or CSV file]
```

## 🧠 RAG System Usage

### 1. Upload Documents
- Upload PDF files through the chat interface
- Upload JSON/CSV data files for structured data
- Documents are automatically processed and indexed

### 2. Ask Questions
- Type questions in the chat interface
- System searches relevant document chunks
- Ollama generates contextual responses

### 3. Supported File Types
- **PDF**: Text extraction and processing
- **JSON**: Structured data parsing
- **CSV**: Tabular data processing

## ⚙️ Configuration

### Ollama Models
Edit `backend/rag_integration.py` to change the model:
```python
self.ollama_client = OllamaClient(model="llama3.2")  # or "deepseek-coder"
```

### RAG Parameters
Adjust in `backend/data_processor.py`:
```python
def chunk_text(self, text, chunk_size=500, overlap=50):
def search(self, query, k=3):  # Number of relevant chunks
```

### Django Settings
Configure in `backend/backend/settings.py`:
- CORS settings
- Media file handling
- Database configuration

## 🔍 Troubleshooting

### Common Issues

1. **RAG system not available**
   - Ensure Ollama is running: `ollama serve`
   - Check if model is pulled: `ollama list`
   - Verify file paths in `rag_integration.py`

2. **Frontend can't connect to backend**
   - Check Django server is running on port 8000
   - Verify CORS settings in Django
   - Check proxy setting in `frontend/package.json`

3. **File upload fails**
   - Check file permissions in media directory
   - Verify file size limits
   - Check supported file types

### Debug Mode
Enable Django debug mode in `backend/backend/settings.py`:
```python
DEBUG = True
```

## 🚀 Deployment

### Development
- Frontend: `npm start` (port 3000)
- Backend: `python manage.py runserver` (port 8000)
- Ollama: `ollama serve` (port 11434)

### Production
- Use production WSGI server (gunicorn)
- Configure proper CORS origins
- Set up reverse proxy (nginx)
- Use production database (PostgreSQL)

## 🤝 Team Integration

This system integrates:
- **Your RAG system**: Document processing and Ollama integration
- **Team's frontend**: React UI with chat interface
- **Team's backend**: Django REST API structure

The integration maintains the original team structure while adding RAG capabilities.

## 📝 License

This project combines multiple components and follows their respective licenses.
