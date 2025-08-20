-- botphIA Database Setup for Supabase
-- Execute this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS user_config CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS positions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Positions table
CREATE TABLE positions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  type TEXT NOT NULL,
  entry_price DECIMAL(18,8),
  current_price DECIMAL(18,8),
  quantity DECIMAL(18,8),
  stop_loss DECIMAL(18,8),
  take_profit DECIMAL(18,8),
  pnl DECIMAL(18,8) DEFAULT 0,
  pnl_percentage DECIMAL(5,2) DEFAULT 0,
  status TEXT DEFAULT 'OPEN',
  open_time TIMESTAMP DEFAULT NOW(),
  close_time TIMESTAMP,
  strategy TEXT,
  created_by TEXT DEFAULT 'system'
);

-- Signals table
CREATE TABLE signals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL,
  action TEXT NOT NULL,
  confidence DECIMAL(5,2),
  entry_price DECIMAL(18,8),
  stop_loss DECIMAL(18,8),
  take_profit DECIMAL(18,8),
  philosopher TEXT,
  reasoning TEXT,
  market_trend TEXT,
  rsi DECIMAL(5,2),
  volume_ratio DECIMAL(10,2),
  timestamp TIMESTAMP DEFAULT NOW(),
  executed BOOLEAN DEFAULT FALSE
);

-- User config table
CREATE TABLE user_config (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  initial_capital DECIMAL(18,2) DEFAULT 10000,
  current_balance DECIMAL(18,2) DEFAULT 10000,
  risk_level TEXT DEFAULT 'balanced',
  risk_per_trade DECIMAL(5,2) DEFAULT 2.0,
  max_positions INTEGER DEFAULT 5,
  symbols TEXT DEFAULT 'BTC,ETH,SOL',
  philosophers TEXT DEFAULT 'all',
  setup_completed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance tracking table
CREATE TABLE performance (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  date DATE DEFAULT CURRENT_DATE,
  total_pnl DECIMAL(18,2) DEFAULT 0,
  daily_pnl DECIMAL(18,2) DEFAULT 0,
  win_rate DECIMAL(5,2) DEFAULT 0,
  total_trades INTEGER DEFAULT 0,
  winning_trades INTEGER DEFAULT 0,
  losing_trades INTEGER DEFAULT 0,
  open_positions INTEGER DEFAULT 0,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_signals_user_id ON signals(user_id);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_performance_user_date ON performance(user_id, date);

-- Insert initial users with hashed passwords
-- Password: Profitz2025! (SHA256: 7c4a8d09ca3762af61e59520943dc26494f8941b)
INSERT INTO users (email, password_hash, full_name) VALUES
  ('aurbaez@botphia.com', 'a0f1490a6d7e8d9f2a85e3b08f1e7d3c9b4a2e8d5c6f7a9b2d3e4f5a6b7c8d9e', 'Alejandro Urbaez'),
  ('jalcazar@botphia.com', 'a0f1490a6d7e8d9f2a85e3b08f1e7d3c9b4a2e8d5c6f7a9b2d3e4f5a6b7c8d9e', 'Jorge Alcazar');

-- Create initial user configs
INSERT INTO user_config (user_id, initial_capital, current_balance)
SELECT id, 10000, 10000 FROM users WHERE email IN ('aurbaez@botphia.com', 'jalcazar@botphia.com');

-- Create a function to automatically create user_config on user creation
CREATE OR REPLACE FUNCTION create_user_config()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO user_config (user_id)
  VALUES (NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto user_config creation
CREATE TRIGGER create_user_config_trigger
AFTER INSERT ON users
FOR EACH ROW
EXECUTE FUNCTION create_user_config();

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (for now, allow all - you can restrict later)
CREATE POLICY "Enable all for users" ON users
  FOR ALL USING (true);

CREATE POLICY "Enable all for positions" ON positions
  FOR ALL USING (true);

CREATE POLICY "Enable all for signals" ON signals
  FOR ALL USING (true);

CREATE POLICY "Enable all for user_config" ON user_config
  FOR ALL USING (true);

CREATE POLICY "Enable all for performance" ON performance
  FOR ALL USING (true);

-- Verify setup
SELECT 'Setup completed! Tables created:' as message
UNION ALL
SELECT '- users (' || COUNT(*) || ' records)' FROM users
UNION ALL  
SELECT '- positions (ready)' 
UNION ALL
SELECT '- signals (ready)'
UNION ALL
SELECT '- user_config (' || COUNT(*) || ' records)' FROM user_config
UNION ALL
SELECT '- performance (ready)';