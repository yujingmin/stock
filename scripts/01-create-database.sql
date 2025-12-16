-- Step 1: Create database and user
-- Execute this with: psql -U postgres -f scripts/01-create-database.sql

-- Create user if not exists
DO
$$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles WHERE rolname = 'quant_user'
   ) THEN
      CREATE USER quant_user WITH PASSWORD 'quant_password_dev';
      RAISE NOTICE 'User quant_user created';
   ELSE
      RAISE NOTICE 'User quant_user already exists';
   END IF;
END
$$;

-- Drop database if exists (optional, comment out if you want to keep existing data)
-- DROP DATABASE IF EXISTS quant_platform;

-- Create database
CREATE DATABASE quant_platform
    WITH
    OWNER = quant_user
    ENCODING = 'UTF8'
    TEMPLATE = template0;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE quant_platform TO quant_user;

\echo 'Database quant_platform created successfully!'
\echo 'User: quant_user'
\echo 'Password: quant_password_dev'
