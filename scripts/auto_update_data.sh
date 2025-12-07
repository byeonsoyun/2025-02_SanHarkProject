#!/bin/bash

echo "🔄 Starting automatic data update..."
cd ~/SanHark_CBNU/backend

# Activate virtual environment
source venv/bin/activate

# 1. Crawl new notices
echo "📡 Crawling new data..."
cd cbnu_crawler
scrapy crawl cbnu_notice >> ~/SanHark_CBNU/logs/auto_crawl.log 2>&1
scrapy crawl calendar >> ~/SanHark_CBNU/logs/auto_crawl.log 2>&1
scrapy crawl dorm >> ~/SanHark_CBNU/logs/auto_crawl.log 2>&1

# 2. Update RAG index
echo "🔍 Updating RAG index..."
cd ~/SanHark_CBNU/backend
python manage.py run_rag_index >> ~/SanHark_CBNU/logs/auto_index.log 2>&1

echo "✅ Data update completed at $(date)"
