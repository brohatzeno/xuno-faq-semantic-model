from qdrant_client import QdrantClient
from qdrant_client.http import models
import os


def create_qdrant_collection():
    '''
    Create the faqs collection in Qdrant with appropriate vector settings
    '''
    # Initialize Qdrant client
    if os.getenv('QDRANT_URL') and os.getenv('QDRANT_API_KEY'):
        qdrant_client = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY'),
        )
    else:
        # Default to local instance
        qdrant_client = QdrantClient(host='localhost', port=6333)
    
    # Create the collection with 768-dimensional vectors and Cosine distance
    qdrant_client.recreate_collection(
        collection_name='faqs',
        vectors_config=models.VectorParams(
            size=768,  # Size of the vectors (matching EmbeddingGemma)
            distance=models.Distance.COSINE  # Distance metric
        )
    )
    
    print('Collection ''faqs'' created successfully in Qdrant!')
    print('Configuration: 768-dimensional vectors with Cosine distance')


if __name__ == '__main__':
    create_qdrant_collection()
