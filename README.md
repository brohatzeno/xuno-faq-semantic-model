# Xuno FAQ Embedding System (Qdrant Version)

This is a streamlined FAQ embedding and retrieval system that uses the EmbeddingGemma model from Ollama and stores data in Qdrant vector database.

## Directory Structure

```
embedding/
├── src/
│   ├── embeddings.py                    # Contains the embedding generation logic using Ollama
│   ├── query_faqs_qdrant.py             # Script to query FAQs from Qdrant vector database
│   └── store_enhanced_embeddings_to_qdrant.py  # Enhanced script that combines questions with keywords and stores to Qdrant
├── utils/
│   └── qdrant_client.py                 # Qdrant client connection functionality
├── data/
│   ├── faq_intents.json                 # FAQ data with questions, answers, categories, and match weights
│   └── faq_keywords.json                # FAQ keyword mappings linking keywords to FAQ IDs
├── create_qdrant_collection.py          # Script to create Qdrant collection with proper vector settings
├── requirements.txt                     # Python dependencies
└── README.md                           # This file
```

## Setup

1. **Prerequisites**:
   - Ollama with `embeddinggemma:latest` model
   - Qdrant vector database (either local or cloud instance)

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Qdrant collection**:
   ```bash
   python create_qdrant_collection.py
   ```

## Environment Variables

Set these environment variables for Qdrant connection:
- `QDRANT_URL` - URL of your Qdrant instance (e.g., https://your-cluster.xxxx.us-east.aws.cloud.qdrant.io:6333)
- `QDRANT_API_KEY` - API key for your Qdrant instance (if using cloud)
- `QDRANT_HOST` - Host for local instance (default: localhost)
- `QDRANT_PORT` - Port for local instance (default: 6333)

## Usage

### Generate and store enhanced embeddings to Qdrant:
```bash
QDRANT_URL="your_qdrant_url" QDRANT_API_KEY="your_api_key" python src/store_enhanced_embeddings_to_qdrant.py
```

### Query FAQs from Qdrant:
```bash
QDRANT_URL="your_qdrant_url" QDRANT_API_KEY="your_api_key" python src/query_faqs_qdrant.py
```

## Model Information

The project uses the `embeddinggemma:latest` model from Ollama, which generates 768-dimensional embeddings. The enhanced system combines each question with its associated keywords for improved retrieval quality. A similarity threshold of 0.53 is used to filter out low-quality matches.