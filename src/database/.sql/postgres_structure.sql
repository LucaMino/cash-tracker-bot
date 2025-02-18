SET TIME ZONE 'Europe/Rome';

CREATE TABLE openai_responses (
    chat_id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    response JSONB NOT NULL,
    completion_tokens INT NOT NULL,
    prompt_tokens INT NOT NULL,
    total_tokens INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    payment_method VARCHAR(50) NOT NULL,
    note TEXT,
    paid_at DATE NULL,
    openai_response_chat_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_openai_response_chat_id FOREIGN KEY (openai_response_chat_id) REFERENCES openai_responses(chat_id) ON DELETE SET NULL
);

CREATE INDEX idx_openai_response_chat_id ON transactions (openai_response_chat_id);
