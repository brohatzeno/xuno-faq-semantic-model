#!/usr/bin/env python3
"""
Enhanced embedding generator that stores directly to PostgreSQL database
"""
import json
import os
import sys
from typing import List, Dict, Tuple
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.embeddings import generate_embeddings
from utils.db import DatabaseConnection
from utils.db_utils import ensure_vector_extension, ensure_table_schema

def load_faqs_with_keywords(intents_file: str, keywords_file: str) -> List[Dict]:
    """
    Load FAQs and combine each FAQ with its associated keywords
    """
    # Load intents (main FAQ data)
    if os.path.exists(intents_file):
        with open(intents_file, "r") as f:
            intents_data = json.load(f)
    else:
        # Try relative path from script location
        script_dir = os.path.dirname(__file__)
        intents_path = os.path.join(script_dir, "..", intents_file)
        if os.path.exists(intents_path):
            with open(intents_path, "r") as f:
                intents_data = json.load(f)
        else:
            print(f"Warning: {intents_file} not found")
            intents_data = []

    # Load keywords
    if os.path.exists(keywords_file):
        with open(keywords_file, "r") as f:
            keywords_data = json.load(f)
    else:
        # Try relative path from script location
        script_dir = os.path.dirname(__file__)
        keywords_path = os.path.join(script_dir, "..", keywords_file)
        if os.path.exists(keywords_path):
            with open(keywords_path, "r") as f:
                keywords_data = json.load(f)
        else:
            print(f"Warning: {keywords_file} not found")
            keywords_data = []
    
    # Create a mapping from faq_id to keywords
    keywords_by_faq = {}
    for keyword_entry in keywords_data:
        faq_id = keyword_entry.get("faq_id")
        keyword = keyword_entry.get("keyword")
        if faq_id and keyword:
            if faq_id not in keywords_by_faq:
                keywords_by_faq[faq_id] = []
            keywords_by_faq[faq_id].append(keyword)
    
    # Combine intents with their keywords
    combined_faqs = []
    for intent in intents_data:
        faq_id = intent.get("faq_id")
        if faq_id:
            # Get keywords for this FAQ
            keywords = keywords_by_faq.get(faq_id, [])
            # Add keywords to the intent data
            intent["keywords"] = keywords
            # Create combined text for embedding
            question = intent.get("question", "")
            keywords_str = " ".join(keywords)
            combined_text = f"{question} {keywords_str}"
            intent["combined_text_for_embedding"] = combined_text
        combined_faqs.append(intent)
    
    return combined_faqs

def save_enhanced_embeddings_to_db(db_connection, faqs: List[Dict], embeddings: List[List[float]]):
    """
    Save enhanced FAQ embeddings to PostgreSQL database
    """
    ensure_vector_extension(db_connection)
    ensure_table_schema(db_connection)

    for i, (faq, embedding) in enumerate(zip(faqs, embeddings)):
        query = """INSERT INTO faq_embeddings (faq_id, category, question, answer, match_weight, embedding)
VALUES (%s, %s, %s, %s, %s, %s::vector)
ON CONFLICT (faq_id) DO UPDATE SET
    category = EXCLUDED.category,
    question = EXCLUDED.question,
    answer = EXCLUDED.answer,
    match_weight = EXCLUDED.match_weight,
    embedding = EXCLUDED.embedding;"""
        db_connection.execute_update(query, (
            faq.get("faq_id"),
            faq.get("category"),
            faq.get("question"),
            faq.get("answer"),
            faq.get("match_weight", 5),
            embedding
        ))

        # Generate and store keyword embeddings
        keywords = faq.get("keywords", [])
        for keyword in keywords:
            keyword_embedding = generate_embeddings([keyword])[0]  # Generate embedding for the keyword
            keyword_insert_query = """INSERT INTO faq_keywords (faq_id, keyword, embedding)
VALUES (%s, %s, %s::vector)
ON CONFLICT (faq_id, keyword) DO UPDATE SET
    embedding = EXCLUDED.embedding;"""
            db_connection.execute_update(keyword_insert_query, (
                faq.get("faq_id"),
                keyword,
                keyword_embedding
            ))

        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(faqs)} embeddings...")
    print(f"Successfully saved {len(faqs)} enhanced embeddings to the database.")

def generate_and_store_enhanced_embeddings(faq_files: List[str]):
    """
    Generate enhanced embeddings and store them directly to PostgreSQL
    """
    intents_file, keywords_file = faq_files
    
    print("Loading FAQs with keywords...")
    faqs = load_faqs_with_keywords(intents_file, keywords_file)
    
    if not faqs:
        print("No FAQs loaded. Exiting.")
        return
    
    # Extract the combined text for embedding
    texts_to_embed = [faq.get("combined_text_for_embedding", faq.get("question", "")) for faq in faqs]
    
    print(f"Generating enhanced embeddings for {len(texts_to_embed)} combined FAQ+keyword entries...")
    embeddings = generate_embeddings(texts_to_embed)
    
    # Connect to database
    import os
    from getpass import getpass
    db_password = os.getenv("DB_PASSWORD") or getpass("Enter database password (or set DB_PASSWORD env var): ")
    os.environ["DB_PASSWORD"] = db_password
    
    db = DatabaseConnection()
    if not db.connect():
        print("Failed to connect to database.")
        return
    
    try:
        print("Saving enhanced embeddings to database...")
        save_enhanced_embeddings_to_db(db, faqs, embeddings)
        print("Enhanced embeddings successfully stored in PostgreSQL database!")
    finally:
        db.disconnect()

def main():
    faq_files = ["./data/faq_intents.json", "./data/faq_keywords.json"]
    generate_and_store_enhanced_embeddings(faq_files)

if __name__ == "__main__":
    main()
