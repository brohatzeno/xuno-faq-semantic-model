-- Schema for storing FAQ embeddings and keywords in PostgreSQL

-- Enable the vector extension (requires pgvector to be installed)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the faq_embeddings table (stores main FAQ data with embeddings)
CREATE TABLE IF NOT EXISTS faq_embeddings (
    faq_id TEXT PRIMARY KEY,
    category TEXT,
    question TEXT NOT NULL,
    answer TEXT,
    match_weight INTEGER DEFAULT 5,
    embedding vector(4096),  -- Qwen3 embedding dimension is 4096
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the faq_keywords table (stores keyword mappings to FAQs)
CREATE TABLE IF NOT EXISTS faq_keywords (
    keyword_id SERIAL PRIMARY KEY,
    faq_id TEXT REFERENCES faq_embeddings(faq_id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
-- Indexes for faq_embeddings
CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_embeddings(category);
CREATE INDEX IF NOT EXISTS idx_faq_question ON faq_embeddings USING gin(question gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_faq_embedding ON faq_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Indexes for faq_keywords
CREATE INDEX IF NOT EXISTS idx_faq_keywords_keyword ON faq_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_faq_keywords_faq_id ON faq_keywords(faq_id);

-- Optional: Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language "plpgsql";

-- Triggers to automatically update the updated_at column
CREATE TRIGGER update_faq_embeddings_updated_at
    BEFORE UPDATE ON faq_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faq_keywords_updated_at
    BEFORE UPDATE ON faq_keywords
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sample data insertion examples
/*
INSERT INTO faq_embeddings (faq_id, category, question, answer, match_weight, embedding)
VALUES (
    'Re_001',
    'Getting Started/Onboarding',
    'How do I sign up for Xuno?',
    'You can download the Xuno app or visit xuno.co, verify your email and set a password to create your account.',
    5,
    '[0.016314290463924408, -0.003922430798411369, -0.014764786697924137, ...]'::vector
);

INSERT INTO faq_keywords (faq_id, keyword) VALUES
('Re_001', 'sign up'),
('Re_001', 'register'),
('Re_001', 'email'),
('Re_001', 'account');
*/

-- Query examples for finding similar FAQs
/*
SELECT fe.faq_id, fe.category, fe.question, fe.answer,
       1 - (fe.embedding <=> '[QUERY_EMBEDDING_HERE]'::vector) AS cosine_similarity
FROM faq_embeddings fe
ORDER BY fe.embedding <=> '[QUERY_EMBEDDING_HERE]'::vector
LIMIT 5;
*/

-- Query to find FAQs by keyword
/*
SELECT DISTINCT fe.faq_id, fe.category, fe.question, fe.answer
FROM faq_embeddings fe
JOIN faq_keywords fk ON fe.faq_id = fk.faq_id
WHERE fk.keyword ILIKE '%sign up%';
*/
