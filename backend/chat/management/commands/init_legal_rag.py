from django.core.management.base import BaseCommand
from chat.models import LawDocument
from chat.rag_integration import rag_chatbot

class Command(BaseCommand):
    help = 'Initialize RAG system with legal documents from database'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=1000, help='Limit number of documents to process')

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write(f"🔄 Initializing RAG with legal documents (limit: {limit})")
        
        try:
            # Get legal documents
            legal_docs = LawDocument.objects.all()[:limit]
            
            if not legal_docs:
                self.stdout.write(self.style.ERROR("❌ No legal documents found in database"))
                return
            
            self.stdout.write(f"📊 Processing {len(legal_docs)} legal documents...")
            
            # Prepare text data
            all_text = []
            for doc in legal_docs:
                doc_text = f"제목: {doc.title}\n내용: {doc.content}\n법원: {doc.court_name}\n사건번호: {doc.case_number}"
                all_text.append(doc_text)
            
            # Process with RAG
            combined_text = "\n\n".join(all_text)
            chunks = rag_chatbot.processor.chunk_text(combined_text)
            
            rag_chatbot.processor.create_embeddings(chunks)
            rag_chatbot.processor.create_faiss_index()
            rag_chatbot.processor.save_index()
            rag_chatbot.is_initialized = True
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Legal RAG initialized!\n'
                    f'📊 Documents: {len(legal_docs)}\n'
                    f'📝 Chunks: {len(chunks)}\n'
                    f'🧠 Ready for legal Q&A!'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ RAG initialization failed: {e}'))
