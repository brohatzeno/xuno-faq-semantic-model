#!/usr/bin/env python3
"""
Query script to find similar FAQs using vector similarity in Qdrant
"""
import os
import sys
import numpy as np
from getpass import getpass
import difflib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.embeddings import generate_embeddings
from qdrant_client import QdrantClient
from utils.qdrant_client import get_qdrant_client


def query_faqs(user_query, qdrant_client, top_k=5, min_similarity_threshold=0.4):
    """Query the Qdrant database for FAQs similar to the user query"""
    # Generate embedding for the user query
    print("Generating embedding for your query...")
    query_embeddings = generate_embeddings([user_query])
    query_embedding = query_embeddings[0]

    # Search for similar vectors in Qdrant
    print("Searching for similar FAQs in Qdrant...")
    
    # Search for both question and keyword types
    search_result = qdrant_client.query_points(
        collection_name="faqs",
        query=query_embedding,
        limit=top_k * 2,  # Get more results to account for filtering
        score_threshold=min_similarity_threshold,
    )

    if not search_result:
        print("No FAQs found in the database.")
        return []

    # Process results and apply additional scoring logic
    processed_results = []
    seen_faq_ids = set()  # Track unique FAQs to avoid duplicates
    
    user_query_lower = user_query.lower()

    for hit in search_result.points:
        # Extract payload data
        payload = hit.payload
        similarity_score = hit.score  # This is the cosine similarity from Qdrant
        
        # Skip if we've already processed this FAQ
        faq_id = payload.get("faq_id")
        if faq_id in seen_faq_ids:
            continue
            
        # Apply additional scoring logic similar to the original PostgreSQL version
        faq_question_lower = payload.get("question", "").lower()
        
        # Calculate orthographic similarity (for typos, abbreviations, etc.)
        orthographic_similarity = difflib.SequenceMatcher(None, user_query_lower, faq_question_lower).ratio()
        
        # Define stop words to exclude from matching
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'hi', 'hello', 'hey', 'how', 'what', 'who', 'where', 'when', 'why'}
        
        # Boost calculation
        boost = 0.0
        
        # Boost based on orthographic similarity
        if orthographic_similarity > 0.3:
            boost += orthographic_similarity * 0.2

        # Boost for meaningful word matches
        query_words = [word for word in user_query_lower.split() if word not in stop_words and len(word) > 2]
        faq_words = [word for word in faq_question_lower.split() if word not in stop_words and len(word) > 2]

        # Count meaningful word matches
        query_set = set(query_words)
        faq_set = set(faq_words)
        common_words = query_set.intersection(faq_set)

        if common_words:
            match_ratio = len(common_words) / len(query_set) if query_set else 0
            boost += match_ratio * 0.15

        # Extra boost if the full query appears in the FAQ
        if user_query_lower in faq_question_lower:
            boost += 0.3

        # Extra boost for word-level matches
        for query_word in query_set:
            if query_word in faq_set:
                boost += 0.05

        # Special case: boost "create" queries for "sign up" FAQs specifically
        if "create" in query_set and ("sign" in faq_set and "up" in faq_set):
            boost += 0.2

        # Define variables for related term matching
        query_words_lower = set(user_query_lower.split())
        faq_words_lower = set(faq_question_lower.split())

        # Specific semantic boosts for related terms
        related_term_pairs = [
            ({"create", "make", "setup", "start", "new"}, {"sign", "up", "register", "account"}),
            ({"delete", "remove", "cancel"}, {"delete", "remove", "cancel", "close"}),
            ({"password", "login", "signin", "access"}, {"password", "login", "sign", "access"}),
            ({"bank", "account", "money", "transfer"}, {"bank", "account", "money", "transfer"})
        ]

        for positive_terms, target_terms in related_term_pairs:
            if positive_terms.intersection(query_words_lower) and target_terms.intersection(faq_words_lower):
                boost += 0.15

        # Identify potentially out-of-domain terms in the query
        out_of_domain_terms = {'dresscode', 'dress', 'code', 'hotdog', 'pasta', 'cooking', 'sunday', 'leaves', 'leave', 'vacation', 'holiday'}
        out_of_domain_matches = query_words_lower.intersection(out_of_domain_terms)

        # Reduce similarity if query contains out-of-domain terms
        final_similarity = similarity_score
        if out_of_domain_matches:
            final_similarity *= 0.7

        # Apply boost to final similarity
        final_similarity += boost
        
        # Only add if final similarity meets threshold
        if final_similarity >= min_similarity_threshold:
            processed_results.append((final_similarity, {
                'base_similarity': similarity_score,
                'orthographic_similarity': orthographic_similarity,
                'boost': boost,
                'faq_data': payload
            }))
            seen_faq_ids.add(faq_id)

    # Sort by final similarity score in descending order
    processed_results.sort(key=lambda x: x[0], reverse=True)

    # Return top_k results
    return processed_results[:top_k]


def main():
    print("Xuno FAQ Query System (Qdrant Version)")
    print("Type "quit" or "exit" to exit the program")
    print("-" * 50)

    # Initialize Qdrant client
    qdrant_client = get_qdrant_client()
    
    # Verify collection exists
    try:
        collection_info = qdrant_client.get_collection(collection_name="faqs")
        print(f"Connected to Qdrant collection 'faqs' with {collection_info.points_count} points")
    except Exception as e:
        print(f"Error connecting to Qdrant collection: {e}")
        return

    try:
        while True:
            user_input = input("
Enter your question: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            # Find similar FAQs with minimum similarity threshold
            results = query_faqs(user_input, qdrant_client, top_k=3, min_similarity_threshold=0.53)

            if not results:
                print("Sorry the query is out of my knowledge base!")
                continue

            print(f"
Top {len(results)} similar FAQs:")
            print("=" * 50)

            for i, (similarity, item) in enumerate(results, 1):
                faq = item['faq_data']
                print(f"{i}. [Final Score: {similarity:.4f}]")
                print(f"   Category: {faq.get('category', 'N/A')}")
                print(f"   Question: {faq.get('question', 'N/A')}")
                print(f"   Answer: {faq.get('answer', 'N/A')}")
                print()

    except KeyboardInterrupt:
        print("

Goodbye!")


if __name__ == "__main__":
    main()
