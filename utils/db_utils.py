# db_utils.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.db import DatabaseConnection
from typing import List, Dict

def ensure_vector_extension(db: DatabaseConnection):
    result = db.execute_query("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
    if not result:
        print("Installing vector extension...")
        db.execute_update("CREATE EXTENSION IF NOT EXISTS vector;")
        print("Vector extension installed successfully.")
    else:
        print("Vector extension is already installed.")

def ensure_table_schema(db: DatabaseConnection):
    result = db.execute_query("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'faq_embeddings' AND column_name = 'embedding';
    """)
    if not result:
        print("Creating faq_embeddings table...")
        create_table_query = """
            CREATE TABLE IF NOT EXISTS faq_embeddings (
                faq_id TEXT PRIMARY KEY,
                category TEXT,
                question TEXT NOT NULL,
                answer TEXT,
                match_weight INTEGER DEFAULT 5,
                embedding vector(768),  -- 768-dimensional for embeddinggemma model
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        db.execute_update(create_table_query)
        print("faq_embeddings table created successfully.")
    else:
        print("faq_embeddings table schema is correct.")

def save_embeddings_to_db(db: DatabaseConnection, faqs: List[Dict], embeddings: List[List[float]]):
    ensure_vector_extension(db)
    ensure_table_schema(db)
    for i, (faq, embedding) in enumerate(zip(faqs, embeddings)):
        query = """
        INSERT INTO faq_embeddings (faq_id, category, question, answer, embedding)
        VALUES (%s, %s, %s, %s, %s::vector)
        ON CONFLICT (faq_id) DO UPDATE SET
            category = EXCLUDED.category,
            question = EXCLUDED.question,
            answer = EXCLUDED.answer,
            embedding = EXCLUDED.embedding;
        """
        db.execute_update(query, (
            faq.get("faq_id"),
            faq.get("category"),
            faq.get("question"),
            faq.get("answer"),
            embedding
        ))
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(faqs)} embeddings...")
    print(f"Successfully saved {len(faqs)} embeddings to the database.")
