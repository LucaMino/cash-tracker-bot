SET time_zone = 'Europe/Rome';

-- --------------------------------------------------------

--
-- Table structure for table `openai_responses`
--

CREATE TABLE openai_responses (
    chat_id VARCHAR(255) PRIMARY KEY,
    prompt TEXT NOT NULL,
    response JSON NOT NULL,
    completion_tokens INT NOT NULL,
    prompt_tokens INT NOT NULL,
    total_tokens INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------------------------------------

--
-- Table structure for table `transactions`
--

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    payment_method VARCHAR(50) NOT NULL,
    note TEXT,
    paid_at DATE NULL,
    openai_response_chat_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_openai_response_chat_id (openai_response_chat_id),
    CONSTRAINT fk_openai_response_chat_id
    FOREIGN KEY (openai_response_chat_id) REFERENCES openai_responses(chat_id)
);

-- --------------------------------------------------------

--
-- Constraints for dumped tables
--
