from django.core.management.base import BaseCommand
from django.utils import timezone
import requests
import xml.etree.ElementTree as ET
from chat.models import LawDocument
import time

class Command(BaseCommand):
    help = 'Update legal database with new data from government API'

    def add_arguments(self, parser):
        parser.add_argument('--keyword', type=str, default='공무원', help='Search keyword')
        parser.add_argument('--pages', type=int, default=5, help='Max pages to crawl')

    def handle(self, *args, **options):
        keyword = options['keyword']
        max_pages = options['pages']
        
        self.stdout.write(f"🔄 Updating legal database for: {keyword}")
        
        # Your API configuration
        id = "qusthdbs1"  # Replace with actual API key
        base_url = (
            f"https://www.law.go.kr/DRF/lawSearch.do?OC={id}"
            "&target=prec&type=XML"
            f"&query={keyword}"
            "&display=100"
            "&prncYd=20000101~20231231"
            "&search=2"
        )
        
        new_count = 0
        existing_count = 0
        
        try:
            for page in range(1, max_pages + 1):
                url = f"{base_url}&page={page}"
                response = requests.get(url)
                
                if not response.text.strip().startswith('<?xml'):
                    break
                    
                xtree = ET.fromstring(response.text)
                items = xtree[5:]
                
                for node in items:
                    doc_id = self.safe_extract(node, "판례일련번호", f"AUTO_{page}_{new_count}")
                    
                    # Check if already exists
                    if LawDocument.objects.filter(document_id=doc_id).exists():
                        existing_count += 1
                        continue
                    
                    # Create new document
                    LawDocument.objects.create(
                        document_id=doc_id,
                        doc_type='PRECEDENT',
                        title=self.safe_extract(node, "사건명", "Unknown Case"),
                        content=f"사건번호: {self.safe_extract(node, '사건번호', 'N/A')}\n"
                               f"법원명: {self.safe_extract(node, '법원명', 'N/A')}",
                        enforcement_date=self.safe_extract(node, "선고일자", "00000000"),
                        case_number=self.safe_extract(node, "사건번호", ""),
                        court_name=self.safe_extract(node, "법원명", "")
                    )
                    new_count += 1
                
                time.sleep(0.5)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Update completed!\n'
                    f'📊 New documents: {new_count}\n'
                    f'⏭️  Existing: {existing_count}'
                )
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Update failed: {e}'))
    
    def safe_extract(self, node, tag, default=""):
        element = node.find(tag)
        return element.text if element is not None else default
