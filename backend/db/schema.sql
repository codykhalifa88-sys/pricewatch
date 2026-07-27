CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    email               TEXT UNIQUE NOT NULL,
    password_hash       TEXT NOT NULL,
    subscription_tier   TEXT NOT NULL DEFAULT 'free',   -- 'free' or 'pro'
    stripe_customer_id  TEXT,
    telegram_chat_id    TEXT,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tracked_items (
    id              SERIAL PRIMARY KEY,
    user_id         INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_url     TEXT NOT NULL,
    product_name    TEXT,
    store           TEXT NOT NULL,
    target_price    NUMERIC NOT NULL,
    current_price   NUMERIC,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_tracked_items_user_id ON tracked_items (user_id);
CREATE INDEX IF NOT EXISTS ix_tracked_items_active ON tracked_items (is_active) WHERE is_active;

CREATE TABLE IF NOT EXISTS price_history (
    id              SERIAL PRIMARY KEY,
    tracked_item_id INT NOT NULL REFERENCES tracked_items(id) ON DELETE CASCADE,
    price           NUMERIC NOT NULL,
    checked_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_price_history_item_time ON price_history (tracked_item_id, checked_at);

CREATE TABLE IF NOT EXISTS discount_codes (
    id                  SERIAL PRIMARY KEY,
    store               TEXT NOT NULL,
    code                TEXT NOT NULL,
    description         TEXT,
    discount_percent    NUMERIC,
    expires_at          DATE,
    scraped_at          TIMESTAMP DEFAULT NOW(),
    is_verified         BOOLEAN DEFAULT FALSE,   -- true if seen working recently
    UNIQUE (store, code)
);

CREATE TABLE IF NOT EXISTS alerts_sent (
    id              SERIAL PRIMARY KEY,
    tracked_item_id INT NOT NULL REFERENCES tracked_items(id) ON DELETE CASCADE,
    channel         TEXT NOT NULL,   -- 'email', 'telegram', 'sms'
    sent_at         TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_alerts_sent_item_time ON alerts_sent (tracked_item_id, sent_at);

-- Scraper health: one row per (store, run) so an admin view / alerting job
-- can see "last successful scrape per store" per the brief's advanced
-- features section — a silently-broken scraper is this product's #1
-- real-world failure mode.
CREATE TABLE IF NOT EXISTS scraper_runs (
    id              SERIAL PRIMARY KEY,
    scraper_name    TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('success', 'failure')),
    items_checked   INT DEFAULT 0,
    items_failed    INT DEFAULT 0,
    error_message   TEXT,
    run_at          TIMESTAMP DEFAULT NOW()
);
