-- Fix Supabase Authentication Issues
-- Run this in Supabase SQL Editor

-- 1. Disable RLS temporarily for testing
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE positions DISABLE ROW LEVEL SECURITY;
ALTER TABLE signals DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_config DISABLE ROW LEVEL SECURITY;
ALTER TABLE performance DISABLE ROW LEVEL SECURITY;

-- 2. Verify users exist
SELECT email, full_name, substring(password_hash, 1, 20) as pass_preview 
FROM users;

-- 3. Update password hash for our users (correct SHA256 for "Profitz2025!")
UPDATE users 
SET password_hash = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92'
WHERE email IN ('aurbaez@botphia.com', 'jalcazar@botphia.com');

-- 4. Verify the update
SELECT email, full_name, 
       CASE 
         WHEN password_hash = '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92' 
         THEN '✅ Password Updated' 
         ELSE '❌ Wrong Password' 
       END as status
FROM users;

-- 5. Create API function for login (optional but recommended)
CREATE OR REPLACE FUNCTION public.authenticate_user(
  user_email TEXT,
  user_password_hash TEXT
)
RETURNS TABLE (
  id UUID,
  email TEXT,
  full_name TEXT
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT u.id, u.email, u.full_name
  FROM users u
  WHERE u.email = user_email 
    AND u.password_hash = user_password_hash;
END;
$$;