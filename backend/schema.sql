-- MySQL Database Schema for AIgent Long-Term Memory
-- Run this script in MySQL to create the database and table

CREATE DATABASE IF NOT EXISTS aigent;
USE aigent;

CREATE TABLE IF NOT EXISTS memory_items (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(36),
    content TEXT NOT NULL,
    importance INT DEFAULT 5,
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_agent_id (agent_id),
    INDEX idx_importance (importance)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample query to check table
-- SELECT * FROM memory_items ORDER BY importance DESC;