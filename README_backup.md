# Xuno FAQ Embedding System (PostgreSQL Version)

This is a streamlined FAQ embedding and retrieval system that uses the Qwen3 embedding model from Ollama and stores data in PostgreSQL.

## Directory Structure

```
embedding/
├── src/
│   ├── embeddings.py              # Contains the embedding generation logic using Ollama
│   ├── query_faqs.py              # Script to query FAQs from PostgreSQL (with similarity threshold)
│   └── store_enhanced_embeddings_to_db.py  # Enhanced script that combines questions with keywords and stores directly to PostgreSQL
├── utils/
│   ├── db.py                    # Database connection functionality for PostgreSQL
│   └── db_utils.py              # Database utilities (table creation, schema management)
├── data/
│   ├── faq_intents.json         # FAQ data with questions, answers, categories, and match weights
│   └── faq_keywords.json        # FAQ keyword mappings linking keywords to FAQ IDs
├── sql/
│   └── create_faq_embeddings_table.sql  # SQL script to create PostgreSQL tables with vector storage for both FAQs and keywords
├── requirements.txt             # Python dependencies
└── README.md                  # This file
```

## Setup

1. **Prerequisites**:
   - Ollama with `qwen3-embedding:latest` model
   - PostgreSQL with pgvector extension

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**:
   ```bash
   createdb faq_db
   psql -d faq_db -f sql/create_faq_embeddings_table.sql
   ```

## Usage

### Generate and store enhanced embeddings to PostgreSQL:
```bash
DB_PASSWORD=your_password python src/store_enhanced_embeddings_to_db.py
```

### Query FAQs from PostgreSQL:
```bash
DB_PASSWORD=your_password python src/query_faqs.py
```

## Model Information

The project uses the `qwen3-embedding:latest` model from Ollama, which generates 4096-dimensional embeddings. The enhanced system combines each question with its associated keywords for improved retrieval quality. A similarity threshold of 0.6 is used to filter out low-quality matches.