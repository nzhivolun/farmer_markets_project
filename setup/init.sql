-- === Создание схемы для приложения фермерских рынков ===
-- Этот SQL-скрипт используется для создания структуры базы данных.
-- Мы создаём 5 таблиц:
-- 1. locations  (локации рынков)
-- 2. markets    (сами рынки)
-- 3. reviews (отзывы)
-- 4. categories (справочник категорий товаров)
-- 5. market_categories (связь рынков и категорий)
-- Также добавляем индексы для ускорения поиска.

-- ======================================================
-- 1. Таблица locations (адреса рынков)
-- Хранит информацию о месте (улица, город, штат и т.д.)
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,           -- id - уникальный идентификатор локации (автоинкремент)
    street VARCHAR(255),             -- улица (может быть NULL, потому что не всегда указано)
    city VARCHAR(100) NOT NULL,      -- город (обязательно)
    county VARCHAR(100),             -- округ (необязательное поле)
    state VARCHAR(50) NOT NULL,      -- штат (обязательно)
    zip VARCHAR(20)                  -- почтовый индекс (необязательное поле)
);

-- ======================================================
-- 2. Таблица markets (фермерские рынки)
-- Хранит основную информацию о каждом рынке.
CREATE TABLE markets (
    id SERIAL PRIMARY KEY,           -- id рынка (уникальный)
    name VARCHAR(255) NOT NULL,      -- название рынка (обязательно)
    location_id INT REFERENCES locations(id) ON DELETE CASCADE,
                                      -- внешний ключ на таблицу locations
                                      -- ON DELETE CASCADE: если удалим локацию, удалятся все рынки из этой локации
    website VARCHAR(255),            -- сайт рынка (если есть)
    facebook VARCHAR(255),           -- ссылка на Facebook
    twitter VARCHAR(255),            -- ссылка на Twitter
    youtube VARCHAR(255),            -- ссылка на YouTube
    other_media TEXT,                -- другие медиа (например, Instagram)
    latitude DECIMAL(10, 6),         -- широта (для поиска по радиусу)
    longitude DECIMAL(10, 6),        -- долгота

    -- Ограничение уникальности по совокупности полей
    CONSTRAINT unique_market_entry UNIQUE (name, location_id, website, facebook, twitter, youtube, other_media, latitude, longitude)
);

-- ======================================================
-- 3. Таблица reviews (отзывы)
-- Теперь с полем user_id для привязки к пользователю Django (auth_user)
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,                             -- id отзыва
    market_id INT REFERENCES markets(id) ON DELETE CASCADE,  -- рынок
    user_id INT REFERENCES auth_user(id) ON DELETE SET NULL, -- автор (если есть)
    user_name VARCHAR(100) NOT NULL,                   -- имя (для старых отзывов или анонимов)
    rating INT CHECK (rating BETWEEN 1 AND 5),         -- оценка (1–5)
    review_text TEXT,                                  -- текст отзыва
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP     -- дата создания
);


-- ======================================================
-- 4. Таблица categories (справочник категорий товаров)
-- Здесь храним все возможные категории из CSV-файла:
-- Bakedgoods, Cheese, Meat, Fruits, Vegetables и т.д.
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,              -- Уникальный идентификатор категории
    name VARCHAR(100) UNIQUE NOT NULL   -- Название категории (например, "Meat" или "Fruits")
);

-- ======================================================
-- 5. Таблица market_categories (связь рынков и категорий)
-- Зачем нужна?
-- Один рынок может предлагать несколько категорий товаров.
-- Одна категория может встречаться на многих рынках.
-- Это связь "многие ко многим" между markets и categories.
CREATE TABLE market_categories (
    market_id INT REFERENCES markets(id) ON DELETE CASCADE,
                                        -- ID рынка, внешний ключ на markets.id
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
                                        -- ID категории, внешний ключ на categories.id
    PRIMARY KEY (market_id, category_id)
                                        -- Первичный ключ по двум колонкам (уникальная пара)
);

-- ======================================================
-- === Индексы для ускорения поиска ===
-- Индексы ускоряют выполнение запросов, где мы фильтруем по этим колонкам.
CREATE INDEX idx_city ON locations(city);      -- поиск по городу
CREATE INDEX idx_state ON locations(state);    -- поиск по штату
CREATE INDEX idx_zip ON locations(zip);        -- поиск по индексу
CREATE INDEX idx_market_name ON markets(name); -- поиск по названию рынка
