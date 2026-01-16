#!/usr/bin/env python3
"""
Enhanced embedding generator that stores directly to Qdrant vector database
"""
import json
import os
import sys
from typing import List, Dict, Tuple
from uuid import uuid4
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.embeddings import generate_embeddings

# Import Qdrant client
from qdrant_client import QdrantClient
from qdrant_client.http import models
from utils.qdrant_client import get_qdrant_client


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


def save_enhanced_embeddings_to_qdrant(qdrant_client, faqs: List[Dict], embeddings: List[List[float]]):
    """
    Save enhanced FAQ embeddings to Qdrant vector database
    """
    # Prepare points for batch upload
    points = []
    
    for i, (faq, embedding) in enumerate(zip(faqs, embeddings)):
        # Create a point for the main FAQ question
        question_point = models.PointStruct(
            id=str(uuid4()),  # Generate a unique UUID for the point
            vector=embedding,
            payload={
                "faq_id": faq.get("faq_id"),
                "type": "question",
                "category": faq.get("category"),
                "question": faq.get("question"),
                "answer": faq.get("answer"),
                "match_weight": faq.get("match_weight", 5),
                "combined_text": faq.get("combined_text_for_embedding", ""),
                "keywords": faq.get("keywords", [])
            }
        )
        points.append(question_point)

        # Create points for each keyword associated with this FAQ
        keywords = faq.get("keywords", [])
        for keyword in keywords:
            # Generate embedding for the keyword
            keyword_embedding = generate_embeddings([keyword])[0]
            
            keyword_point = models.PointStruct(
                id=str(uuid4()),  # Generate a unique UUID for the keyword point
                vector=keyword_embedding,
                payload={
                    "faq_id": faq.get("faq_id"),
                    "type": "keyword",
                    "keyword": keyword,
                    "category": faq.get("category"),
                    "question": faq.get("question"),
                    "answer": faq.get("answer"),
                    "match_weight": faq.get("match_weight", 5)
                }
            )
            points.append(keyword_point)

        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(faqs)} embeddings...")

    # Upload all points to Qdrant in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        qdrant_client.upsert(collection_name="faqs", points=batch)
        print(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")

    print(f"Successfully saved {len(faqs)} enhanced embeddings and {len(points) - len(faqs)} keyword embeddings to Qdrant.")


def generate_and_store_enhanced_embeddings(faq_files: List[str]):
    """
    Generate enhanced embeddings and store them directly to Qdrant
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

    # Initialize Qdrant client
    qdrant_client = get_qdrant_client()
    
    # Verify collection exists
    try:
        collection_info = qdrant_client.get_collection(collection_name="faqs")
        print(f"Collection 'faqs' exists with {collection_info.points_count} points")
    except:
        print("Collection 'faqs' does not exist. Please create it first with:")
        print('python create_qdrant_collection.py')
        return

    print("Saving enhanced embeddings to Qdrant...")
    save_enhanced_embeddings_to_qdrant(qdrant_client, faqs, embeddings)
    print("Enhanced embeddings successfully stored in Qdrant!")


def main():
    faq_files = ["./data/faq_intents.json", "./data/faq_keywords.json"]
    generate_and_store_enhanced_embeddings(faq_files)


if __name__ == "__main__":
    main()
