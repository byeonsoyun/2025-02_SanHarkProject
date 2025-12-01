import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB = "db.sqlite3"
PG_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "civil_law_db"),
    "user": os.getenv("DB_USER", "law_user"),
    "password": os.getenv("DB_PASSWORD", "1111"),
    "port": os.getenv("DB_PORT", "5432")
}

def migrate():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cur = pg_conn.cursor()
    
    # Clear existing data
    print("Clearing PostgreSQL data...")
    pg_cur.execute("TRUNCATE TABLE chat_lawdocument CASCADE")
    pg_conn.commit()
    
    # Get all records from SQLite
    print("Reading from SQLite...")
    sqlite_cur.execute("SELECT * FROM chat_lawdocument")
    rows = sqlite_cur.fetchall()
    total = len(rows)
    print(f"Found {total} records")
    
    # Insert into PostgreSQL
    print("Inserting into PostgreSQL...")
    for idx, row in enumerate(rows, 1):
        pg_cur.execute("""
            INSERT INTO chat_lawdocument 
            (doc_type, document_id, title, content, source_url, enforcement_date, 
             added_date, case_number, court_name, law_article_no)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_id) DO NOTHING
        """, row)
        
        if idx % 1000 == 0:
            pg_conn.commit()
            print(f"Progress: {idx}/{total} ({idx*100//total}%)")
    
    pg_conn.commit()
    print(f"✅ Migration complete: {total} records")
    
    sqlite_cur.close()
    sqlite_conn.close()
    pg_cur.close()
    pg_conn.close()

if __name__ == "__main__":
    migrate()
