-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create enum types
CREATE TYPE product_category AS ENUM (
    'Electronics',
    'Clothing',
    'Food',
    'Home',
    'Beauty',
    'Sports'
);

CREATE TYPE location_size AS ENUM (
    'Small',
    'Medium',
    'Large'
);

CREATE TYPE vehicle_type AS ENUM (
    'Delivery',
    'Express'
);

CREATE TYPE alert_severity AS ENUM (
    'low',
    'medium',
    'high'
);

-- Create tables
CREATE TABLE products (
    product_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category product_category NOT NULL,
    subcategory VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    weight DECIMAL(10, 2) NOT NULL,
    shelf_life INTEGER NOT NULL,
    min_stock INTEGER NOT NULL,
    max_stock INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE locations (
    location_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    size location_size NOT NULL,
    capacity INTEGER NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles (
    vehicle_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type vehicle_type NOT NULL,
    capacity INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weather_data (
    id SERIAL PRIMARY KEY,
    location_id VARCHAR(10) REFERENCES locations(location_id),
    date DATE NOT NULL,
    temperature DECIMAL(5, 2) NOT NULL,
    precipitation DECIMAL(5, 2) NOT NULL,
    humidity DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(location_id, date)
);

CREATE TABLE events (
    event_id VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    type VARCHAR(50) NOT NULL,
    impact_factor DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(10) REFERENCES products(product_id),
    location_id VARCHAR(10) REFERENCES locations(location_id),
    date DATE NOT NULL,
    demand INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    revenue DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, location_id, date)
);

CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(10) REFERENCES products(product_id),
    location_id VARCHAR(10) REFERENCES locations(location_id),
    date DATE NOT NULL,
    stock_level INTEGER NOT NULL,
    incoming INTEGER NOT NULL DEFAULT 0,
    outgoing INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, location_id, date)
);

CREATE TABLE routes (
    route_id VARCHAR(10) PRIMARY KEY,
    vehicle_id VARCHAR(10) REFERENCES vehicles(vehicle_id),
    date DATE NOT NULL,
    total_distance DECIMAL(10, 2) NOT NULL,
    total_duration DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'planned',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE route_stops (
    id SERIAL PRIMARY KEY,
    route_id VARCHAR(10) REFERENCES routes(route_id),
    location_id VARCHAR(10) REFERENCES locations(location_id),
    sequence INTEGER NOT NULL,
    arrival_time TIME NOT NULL,
    estimated_duration INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(route_id, sequence)
);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    product_id VARCHAR(10) REFERENCES products(product_id),
    location_id VARCHAR(10) REFERENCES locations(location_id),
    route_id VARCHAR(10) REFERENCES routes(route_id),
    severity alert_severity NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_locations_city ON locations(city);
CREATE INDEX idx_weather_data_location_date ON weather_data(location_id, date);
CREATE INDEX idx_events_date ON events(date);
CREATE INDEX idx_sales_product_location_date ON sales(product_id, location_id, date);
CREATE INDEX idx_inventory_product_location_date ON inventory(product_id, location_id, date);
CREATE INDEX idx_routes_vehicle_date ON routes(vehicle_id, date);
CREATE INDEX idx_route_stops_route_sequence ON route_stops(route_id, sequence);
CREATE INDEX idx_alerts_type_severity ON alerts(type, severity);

-- Create functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_locations_updated_at
    BEFORE UPDATE ON locations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicles_updated_at
    BEFORE UPDATE ON vehicles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routes_updated_at
    BEFORE UPDATE ON routes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_route_stops_updated_at
    BEFORE UPDATE ON route_stops
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alerts_updated_at
    BEFORE UPDATE ON alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 