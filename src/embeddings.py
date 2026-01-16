# embeddings.py
from typing import List
import ollama

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    embeddings = []
    for text in texts:
        # Generate embedding using Ollama's embeddinggemma model
        response = ollama.embeddings(model="embeddinggemma:latest", prompt=text)
        embeddings.append(response['embedding'])
    return embeddings
