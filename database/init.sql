-- SIH26165 AI-Powered Safety Intelligence & Early Warning System
-- Database initialization script

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Notice of successful init
DO $$
BEGIN
    RAISE NOTICE 'Safety Intelligence database initialized successfully.';
END
$$;
