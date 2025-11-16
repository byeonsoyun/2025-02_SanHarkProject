#!/usr/bin/env python3
"""
Automated legal data crawler that saves directly to database
"""
import os
import sys
import django
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chat.models import LawDocument

def crawl_and_save_legal_data(keyword="공무원", max_pages=10):
    """Crawl legal data and save directly to database"""
    
    # API configuration
    id = "qusthdbs1"  # Replace with your actual API key
    base_url = (
        f"https://www.law.go.kr/DRF/lawSearch.do?OC={id}"
        "&target=prec&type=XML"
        f"&query={keyword}"
        "&display=100"
        "&prncYd=20000101~20231231"
        "&search=2"
    )
    
    print(f"🔍 Crawling legal data for keyword: {keyword}")
    
    # Get total count
    res = requests.get(base_url)
    if not res.text.strip().startswith('<?xml'):
        print("❌ Invalid API response. Check your API key.")
        return
    
    xtree = ET.fromstring(res.text)
    totalCnt = int(xtree.find('totalCnt').text)
    print(f"📊 Total available: {totalCnt} documents")
    
    imported_count = 0
    skipped_count = 0
    
    # Crawl and save data
    for page in tqdm(range(1, min(max_pages + 1, totalCnt // 100 + 2))):
        url = f"{base_url}&page={page}"
        response = requests.get(url)
        
        if not response.text.strip().startswith('<?xml'):
            print(f"❌ Page {page} failed")
            break
            
        xtree = ET.fromstring(response.text)
        items = xtree[5:]  # Skip metadata nodes
        
        for node in items:
            try:
                # Extract data safely
                doc_id = node.find("판례일련번호")
                doc_id = doc_id.text if doc_id is not None else f"AUTO_{page}_{imported_count}"
                
                title = node.find("사건명")
                title = title.text if title is not None else "Unknown Case"
                
                case_num = node.find("사건번호")
                case_num = case_num.text if case_num is not None else "N/A"
                
                court = node.find("법원명")
                court = court.text if court is not None else "N/A"
                
                date = node.find("선고일자")
                date = date.text if date is not None else "00000000"
                
                # Create or skip if exists
                law_doc, created = LawDocument.objects.get_or_create(
                    document_id=doc_id,
                    defaults={
                        'doc_type': 'PRECEDENT',
                        'title': title,
                        'content': f"사건번호: {case_num}\n법원명: {court}",
                        'enforcement_date': date,
                        'case_number': case_num,
                        'court_name': court
                    }
                )
                
                if created:
                    imported_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                print(f"Error processing document: {e}")
                continue
        
        time.sleep(0.5)  # Rate limiting
    
    print(f"✅ Crawling completed!")
    print(f"📊 New documents: {imported_count}")
    print(f"⏭️  Existing documents: {skipped_count}")

if __name__ == "__main__":
    crawl_and_save_legal_data()
