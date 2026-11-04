-- Создаем базу данных
CREATE DATABASE IF NOT EXISTS tc_kpi_db;

-- Таблица для агрегированных метрик продаж
CREATE TABLE IF NOT EXISTS tc_kpi_db.sales_aggregated (
    timestamp DateTime,
    category String,
    total_revenue Float32,
    total_items UInt32,
    transaction_count UInt32,
    avg_check Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, category);

-- Таблица для топ-товаров
CREATE TABLE IF NOT EXISTS tc_kpi_db.top_products (
    timestamp DateTime,
    product_name String,
    category String,
    sold_count UInt32,
    revenue Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, sold_count DESC);

-- Создаем пользователя для Python-приложения
CREATE USER IF NOT EXISTS app_user IDENTIFIED WITH plaintext_password BY 'app_secret';

-- Даем права только на нашу базу
GRANT INSERT, SELECT ON tc_kpi_db.* TO app_user;