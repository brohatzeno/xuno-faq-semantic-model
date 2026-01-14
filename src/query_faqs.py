#!/usr/bin/env python3
"""
Query script to find similar FAQs using vector similarity (fixed for PostgreSQL)
"""
import os
import sys
from getpass import getpass
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.db import DatabaseConnection
from src.embeddings import generate_embeddings
import numpy as np

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

def query_faqs(user_query, db_connection, top_k=5, min_similarity_threshold=0.6):
    """Query the database for FAQs similar to the user query"""
    # Generate embedding for the user query
    print("Generating embedding for your query...")
    query_embeddings = generate_embeddings([user_query])
    query_embedding = query_embeddings[0]

    # Retrieve all embeddings from the database
    print("Retrieving stored embeddings from database...")
    query = """
    SELECT faq_id, category, question, answer, embedding
    FROM faq_embeddings;
    """

    try:
        results = db_connection.execute_query(query)
        if not results:
            print("No FAQs found in the database.")
            return []

        # Calculate similarity scores
        similarities = []
        for row in results:
            # PostgreSQL vector format can be like "{val1,val2,val3,...}" or "[val1, val2, val3, ...]"
            # Clean the string to remove brackets and braces
            embedding_str = row['embedding']
            # Remove leading/trailing brackets or braces
            embedding_str = embedding_str.strip('[]{}')
            if embedding_str:
                # Split by comma and convert to float
                stored_embedding = [float(x.strip()) for x in embedding_str.split(',') if x.strip()]
            else:
                stored_embedding = []

            if len(stored_embedding) != len(query_embedding):
                print(f"Warning: Embedding dimension mismatch for FAQ {row['faq_id']}")
                continue

            similarity = cosine_similarity(query_embedding, stored_embedding)
            similarities.append((similarity, row))

        # Sort by similarity score in descending order
        similarities.sort(key=lambda x: x[0], reverse=True)

        # Filter results based on minimum similarity threshold
        filtered_results = [(sim, row) for sim, row in similarities if sim >= min_similarity_threshold]

        # Return top_k results that meet the threshold
        return filtered_results[:top_k]

    except Exception as e:
        print(f"Error querying database: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    print("Xuno FAQ Query System")
    print("Type \"quit\" or \"exit\" to exit the program")
    print("-" * 50)

    # Connect to database
    db_password = os.getenv('DB_PASSWORD') or getpass("Enter database password (or set DB_PASSWORD env var): ")
    os.environ['DB_PASSWORD'] = db_password  # Set for DatabaseConnection

    db = DatabaseConnection()
    if not db.connect():
        print("Failed to connect to database. Exiting.")
        return

    try:
        while True:
            user_input = input("\nEnter your question: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            # Find similar FAQs with minimum similarity threshold
            results = query_faqs(user_input, db, top_k=3, min_similarity_threshold=0.6)

            if not results:
                print("Sorry the query is out of my knowledge base!")
                continue

            print(f"\nTop {len(results)} similar FAQs:")
            print("=" * 50)

            for i, (similarity, faq) in enumerate(results, 1):
                print(f"{i}. [Similarity: {similarity:.4f}]")
                print(f"   Category: {faq['category']}")
                print(f"   Question: {faq['question']}")
                print(f"   Answer: {faq['answer']}")
                print()

    except KeyboardInterrupt:
        print("\n\nGoodbye!")

    finally:
        db.disconnect()

if __name__ == "__main__":
    main()
