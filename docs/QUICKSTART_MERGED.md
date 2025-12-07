# Quick Start Guide - Merged System

## Prerequisites

Ensure you have:
- PostgreSQL with pgvector extension installed
- Python 3.8+
- All dependencies from requirements.txt

## 1. Database Setup

```bash
# Create PostgreSQL database and user (if not exists)
psql -U postgres
CREATE DATABASE civil_law_db;
CREATE USER law_user WITH PASSWORD '1111';
GRANT ALL PRIVILEGES ON DATABASE civil_law_db TO law_user;
\q

# Enable pgvector extension
psql -U law_user -d civil_law_db
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

## 2. Environment Configuration

Check `.env` file has all required variables:
```bash
cat ~/SanHark_25_02/backend/.env
```

Should contain:
```
OLLAMA_BASE_URL=http://10.198.138.249:22434
OLLAMA_MODEL=civil-law-expert
DB_NAME=civil_law_db
DB_USER=law_user
DB_PASSWORD=1111
DB_HOST=localhost
DB_PORT=5432
LAW_API_KEY=qusthdbs1
```

## 3. Install Dependencies

```bash
cd ~/SanHark_25_02/backend
pip install -r requirements.txt

# Additional dependencies for merged features
pip install psycopg2-binary pgvector sentence-transformers
```

## 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## 5. Test Crawler Modules

```bash
# Test precedent crawler
python manage.py shell
>>> from chat.crawler_modules.crawler_precedent import fetch_precedent_list
>>> results = fetch_precedent_list(page_no=1, display_count=5)
>>> print(f"Fetched {len(results)} precedents")
>>> exit()
```

## 6. Index Legal Data (Optional)

```bash
# If you have legal data to index
python scripts/index_data.py
```

## 7. Start Server

```bash
python manage.py runserver
```

Watch for initialization messages:
```
=========================================================
🌟 [DB 초기화] 서버 재시작 감지: 로그 백업 및 삭제 명령 호출...
🌟 [DB 초기화] 백업/삭제 프로세스가 완료되었습니다.
=========================================================
```

## 8. Test Frontend

```bash
# In another terminal
cd ~/SanHark_25_02/frontend
npm start
```

## Testing the Merged Features

### Test 1: Basic Chat
1. Open http://localhost:3000
2. Ask: "민사법이란?"
3. Should get response from database + LLM

### Test 2: Complex Question
1. Ask: "상속세 납부 기한과 관련된 판례를 비교 분석해주세요"
2. Should trigger LLM analysis with context

### Test 3: Crawler Module
```bash
python manage.py shell
from chat.crawler_modules.crawler_term import fetch_term_list
terms = fetch_term_list(page_no=1, display_count=10)
print(f"Fetched {len(terms)} legal terms")
```

### Test 4: pgvector Search
```bash
python db_search.py
# Should run test query and show results
```

## Troubleshooting

### Issue: pgvector not found
```bash
# Install pgvector extension in PostgreSQL
psql -U postgres -d civil_law_db
CREATE EXTENSION vector;
```

### Issue: Crawler fails
```bash
# Check LAW_API_KEY in .env
echo $LAW_API_KEY
# Should output: qusthdbs1
```

### Issue: Database connection error
```bash
# Verify PostgreSQL is running
pg_isready
# Check credentials in .env match your PostgreSQL setup
```

### Issue: Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Management Commands

### Export and Clean Logs
```bash
python manage.py export_and_clean_logs
```

### Import Legal Data
```bash
python manage.py import_legal_data
```

### Update Legal Data
```bash
python manage.py update_legal_data
```

## Architecture Overview

```
User Request
    ↓
Frontend (React)
    ↓
Backend Views (Django)
    ↓
    ├─→ Complexity Detection
    ├─→ Database Search (pgvector)
    ├─→ Context Retrieval (ChatHistory)
    └─→ LLM Generation (Ollama)
    ↓
Response to User
```

## Data Flow

```
Crawler Modules
    ↓
Raw Legal Data
    ↓
DataProcessor (embedding)
    ↓
PostgreSQL + pgvector
    ↓
Semantic Search
    ↓
LLM Context
    ↓
Final Answer
```

## Performance Tips

1. **Use External GPU**: Ensure OLLAMA_BASE_URL points to GPU server
2. **Index Optimization**: Run VACUUM ANALYZE on PostgreSQL regularly
3. **Cache Results**: Consider Redis for frequently asked questions
4. **Batch Processing**: Use crawler modules during off-peak hours

## Next Steps

1. Populate database with legal documents using crawlers
2. Fine-tune complexity detection thresholds
3. Add more crawler modules for additional data sources
4. Implement caching layer
5. Set up monitoring and logging
6. Configure production settings

## Support

For issues or questions:
1. Check MERGE_SUMMARY.md for detailed merge information
2. Review backend_v4 documentation
3. Check Django logs: `tail -f backend/chat/logs/*.csv`
