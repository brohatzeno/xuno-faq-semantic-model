# embeddings.py
from typing import List
import ollama

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    embeddings = []
    for text in texts:
        # Generate embedding using Ollama's qwen3-embedding model
        response = ollama.embeddings(model="qwen3-embedding:latest", prompt=text)
        embeddings.append(response['embedding'])
    return embeddings
