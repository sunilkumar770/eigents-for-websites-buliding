-- Sample seed data for development

-- Insert sample users
INSERT INTO users (email, password, name, role) VALUES
('owner@example.com', '$2a$10$hashedpassword', 'Store Owner', 'owner'),
('customer@example.com', '$2a$10$hashedpassword', 'John Customer', 'customer');

-- Insert sample stores
INSERT INTO stores (owner_id, name, description, category, address, lat, lng, verified) VALUES
((SELECT id FROM users WHERE email = 'owner@example.com'), 
 'Camera Rentals Pro', 
 'Professional camera equipment for rent', 
 'Photography', 
 '123 Main St, New York, NY',
 40.7128,
 -74.0060,
 true);

-- Insert sample products
INSERT INTO products (store_id, name, description, category, price_per_day) VALUES
((SELECT id FROM stores LIMIT 1),
 'Canon EOS R5',
 '45MP full-frame mirrorless camera',
 'Camera',
 150.00),
((SELECT id FROM stores LIMIT 1),
 'Sony A7 IV',
 '33MP full-frame mirrorless camera',
 'Camera',
 120.00);
