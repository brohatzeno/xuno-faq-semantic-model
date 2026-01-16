# qdrant_client.py
import os
from qdrant_client import QdrantClient


def get_qdrant_client():
    '''
    Initialize and return Qdrant client
    '''
    # Check if we're using cloud or local instance
    if os.getenv('QDRANT_URL') and os.getenv('QDRANT_API_KEY'):
        qdrant_client = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY'),
        )
    elif os.getenv('QDRANT_HOST'):
        # Local instance
        qdrant_client = QdrantClient(
            host=os.getenv('QDRANT_HOST', 'localhost'),
            port=int(os.getenv('QDRANT_PORT', 6333)),
        )
    else:
        # Default to local instance
        qdrant_client = QdrantClient(host='localhost', port=6333)
    
    return qdrant_client
