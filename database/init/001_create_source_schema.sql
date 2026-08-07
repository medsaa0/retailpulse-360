CREATE SCHEMA IF NOT EXISTS source;

CREATE TABLE IF NOT EXISTS source.customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(30),
    city VARCHAR(100),
    country VARCHAR(100) NOT NULL DEFAULT 'Morocco',
    customer_segment VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT customers_segment_check
        CHECK (customer_segment IN ('STANDARD', 'PREMIUM', 'VIP')),

    CONSTRAINT customers_timestamps_check
        CHECK (updated_at >= created_at)
);

CREATE TABLE IF NOT EXISTS source.products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    unit_price NUMERIC(12, 2) NOT NULL,
    unit_cost NUMERIC(12, 2) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT products_price_check
        CHECK (unit_price >= 0),

    CONSTRAINT products_cost_check
        CHECK (unit_cost >= 0),

    CONSTRAINT products_timestamps_check
        CHECK (updated_at >= created_at)
);

CREATE TABLE IF NOT EXISTS source.stores (
    store_id VARCHAR(20) PRIMARY KEY,
    store_name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    region VARCHAR(150) NOT NULL,
    opening_date DATE NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT stores_timestamps_check
        CHECK (updated_at >= created_at)
);

CREATE TABLE IF NOT EXISTS source.orders (
    order_id VARCHAR(25) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    store_id VARCHAR(20),
    channel VARCHAR(20) NOT NULL,
    order_status VARCHAR(20) NOT NULL,
    order_date TIMESTAMPTZ NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'MAD',
    payment_method VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,

    CONSTRAINT orders_customer_fk
        FOREIGN KEY (customer_id)
        REFERENCES source.customers (customer_id),

    CONSTRAINT orders_store_fk
        FOREIGN KEY (store_id)
        REFERENCES source.stores (store_id),

    CONSTRAINT orders_channel_check
        CHECK (
            channel IN (
                'WEB',
                'MOBILE',
                'STORE',
                'CALL_CENTER'
            )
        ),

    CONSTRAINT orders_status_check
        CHECK (
            order_status IN (
                'CREATED',
                'PAID',
                'PROCESSING',
                'SHIPPED',
                'DELIVERED',
                'CANCELLED',
                'REFUNDED'
            )
        ),

    CONSTRAINT orders_currency_check
        CHECK (currency = 'MAD'),

    CONSTRAINT orders_payment_method_check
        CHECK (
            payment_method IN (
                'CARD',
                'CASH',
                'MOBILE_WALLET',
                'CASH_ON_DELIVERY'
            )
        ),

    CONSTRAINT orders_store_channel_check
        CHECK (
            (channel = 'STORE' AND store_id IS NOT NULL)
            OR channel <> 'STORE'
        ),

    CONSTRAINT orders_timestamps_check
        CHECK (updated_at >= created_at)
);

CREATE TABLE IF NOT EXISTS source.order_items (
    order_item_id VARCHAR(40) NOT NULL,
    order_id VARCHAR(25) NOT NULL,
    product_id VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    unit_cost NUMERIC(12, 2) NOT NULL,
    discount_percentage NUMERIC(5, 4) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,

    PRIMARY KEY (
        order_id,
        order_item_id
    ),

    CONSTRAINT order_items_order_fk
        FOREIGN KEY (order_id)
        REFERENCES source.orders (order_id)
        ON DELETE CASCADE,

    CONSTRAINT order_items_product_fk
        FOREIGN KEY (product_id)
        REFERENCES source.products (product_id),

    CONSTRAINT order_items_quantity_check
        CHECK (quantity > 0),

    CONSTRAINT order_items_price_check
        CHECK (unit_price >= 0),

    CONSTRAINT order_items_cost_check
        CHECK (unit_cost >= 0),

    CONSTRAINT order_items_discount_check
        CHECK (discount_percentage BETWEEN 0 AND 1),

    CONSTRAINT order_items_timestamps_check
        CHECK (updated_at >= created_at)
);

CREATE INDEX IF NOT EXISTS idx_customers_updated_at
    ON source.customers (updated_at);

CREATE INDEX IF NOT EXISTS idx_products_updated_at
    ON source.products (updated_at);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id
    ON source.orders (customer_id);

CREATE INDEX IF NOT EXISTS idx_orders_store_id
    ON source.orders (store_id);

CREATE INDEX IF NOT EXISTS idx_orders_order_date
    ON source.orders (order_date);

CREATE INDEX IF NOT EXISTS idx_orders_updated_at
    ON source.orders (updated_at);

CREATE INDEX IF NOT EXISTS idx_order_items_product_id
    ON source.order_items (product_id);

CREATE INDEX IF NOT EXISTS idx_order_items_updated_at
    ON source.order_items (updated_at);
