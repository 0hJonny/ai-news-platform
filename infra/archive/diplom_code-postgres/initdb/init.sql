-- Session parameter setup
SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

-- Drop the database and role if they already exist
DROP DATABASE IF EXISTS articles;
DROP ROLE IF EXISTS articles_maker;
DROP DATABASE IF EXISTS users;
DROP ROLE IF EXISTS user_profiler;

-- Create the role and database
CREATE ROLE articles_maker
    LOGIN PASSWORD 'articlespassword'
    CREATEDB CREATEROLE
    VALID UNTIL 'infinity';

CREATE ROLE user_profiler
    LOGIN PASSWORD 'userprofilepassword'
    CREATEDB CREATEROLE
    VALID UNTIL 'infinity';

GRANT articles_maker TO postgres;

GRANT user_profiler TO postgres;

CREATE DATABASE articles
    WITH OWNER = articles_maker
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

CREATE DATABASE users
    WITH OWNER = user_profiler
    ENCODING = 'UTF8'
    CONNECTION LIMIT = -1;

-- Create PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
-- CREATE EXTENSION IF NOT EXISTS tablefunc WITH SCHEMA indicators;
CREATE EXTENSION IF NOT EXISTS rum;

-- Grant access privileges
GRANT pg_monitor TO articles_maker;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO articles_maker;
GRANT ALL PRIVILEGES ON SCHEMA public TO articles_maker;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cron TO articles_maker;
-- GRANT ALL PRIVILEGES ON SCHEMA cron TO articles_maker;

-- Grant access privileges
GRANT pg_monitor TO user_profiler;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO user_profiler;
GRANT ALL PRIVILEGES ON SCHEMA public TO user_profiler;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cron TO user_profiler;
-- GRANT ALL PRIVILEGES ON SCHEMA cron TO user_profiler;

-- Connect to the "articles" database
\c articles;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS rum;

-- Initialize tables in articles


-- Create the themes table
CREATE TABLE IF NOT EXISTS themes (
    theme_id BIGSERIAL PRIMARY KEY,
    theme_name VARCHAR(255) UNIQUE NOT NULL
);

-- Populate the themes table

INSERT INTO themes (theme_name) VALUES
	('technology'),
	('crypto'),
	('privacy'),
	('security') ON CONFLICT DO NOTHING;;

-- Create the languages table
CREATE TABLE IF NOT EXISTS languages (
    language_id BIGSERIAL PRIMARY KEY,
    language_code VARCHAR(5) UNIQUE NOT NULL,
    language_name VARCHAR(255) UNIQUE NOT NULL
);

-- Populate the languages table
INSERT INTO languages (language_code, language_name) VALUES
    ('ru-RU', 'Russian'),
    ('en-US', 'English'),
    ('fr-FR', 'French'),
    ('de-DE', 'German') ON CONFLICT DO NOTHING;;

-- Create the articles table
CREATE TABLE IF NOT EXISTS articles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    author VARCHAR(255) NOT NULL,
    source_link VARCHAR(2048) UNIQUE NOT NULL,
    body TEXT NOT NULL,
    theme_id BIGINT,
    language_id BIGINT,
    post_date TIMESTAMP NOT NULL DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    FOREIGN KEY (theme_id) REFERENCES themes(theme_id) ON DELETE CASCADE,
    FOREIGN KEY (language_id) REFERENCES languages(language_id) ON DELETE CASCADE
);

-- Create an index
CREATE INDEX IF NOT EXISTS idx_source_link ON articles (source_link);
CREATE INDEX IF NOT EXISTS idx_id_articles ON articles (id);

-- Create the tags table
CREATE TABLE IF NOT EXISTS tags (
    tag_id BIGSERIAL PRIMARY KEY,
    tag_name VARCHAR(255) UNIQUE NOT NULL
);

-- Create the article_tags table
CREATE TABLE IF NOT EXISTS article_tags (
    article_id uuid,
    tag_id INTEGER,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

-- Create article_tags indexes
CREATE INDEX IF NOT EXISTS idx_article_id_tag_id_article_tags ON article_tags (article_id, tag_id);
CREATE INDEX IF NOT EXISTS idx_article_id_article_tags ON article_tags (article_id);
CREATE INDEX IF NOT EXISTS idx_tag_id_article_tags ON article_tags (tag_id);


-- Create the annotations table
CREATE TABLE IF NOT EXISTS annotations (
    annotation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id uuid,
    annotation TEXT NOT NULL,
    language_id BIGINT,
    neural_network VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (language_id) REFERENCES languages(language_id) ON DELETE CASCADE,
    CONSTRAINT unique_annotation_language UNIQUE (article_id, language_id)
);

-- Create annotations indexes
CREATE INDEX IF NOT EXISTS idx_language_id_annotations ON annotations (language_id);

-- Create the titles table
CREATE TABLE IF NOT EXISTS titles (
    title_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id uuid,
    title VARCHAR(255) NOT NULL,
    language_id BIGINT,
    neural_network VARCHAR(255) DEFAULT 'native' NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (language_id) REFERENCES languages(language_id) ON DELETE CASCADE,
    CONSTRAINT unique_article_language UNIQUE (article_id, language_id)
);


-- Create the titles index
CREATE INDEX IF NOT EXISTS idx_language_id_titles ON titles (language_id);


-- Create a trigger to delete related articles when a tag is deleted
CREATE OR REPLACE FUNCTION delete_articles_on_tag_delete()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM articles
    WHERE id IN (
        SELECT article_id
        FROM article_tags
        WHERE tag_id = OLD.tag_id
    );
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER delete_articles_trigger
AFTER DELETE ON tags
FOR EACH ROW
EXECUTE FUNCTION delete_articles_on_tag_delete();

-- Create RUM indexes

CREATE INDEX idx_title_rum ON titles USING rum (to_tsvector('simple', title));
CREATE INDEX idx_annotation_rum ON annotations USING rum (to_tsvector('simple', annotation));


-- Query logging
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id SERIAL PRIMARY KEY,
    table_name TEXT,
    operation CHAR(1), -- 'I' for insert, 'U' for update, 'D' for delete
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMP DEFAULT current_timestamp
);

-- Create the trigger for query logging
-- Trigger for the articles table
CREATE OR REPLACE FUNCTION log_articles_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, new_data)
        VALUES ('articles', 'I', row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, old_data, new_data)
        VALUES ('articles', 'U', row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, old_data)
        VALUES ('articles', 'D', row_to_json(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER articles_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON articles
FOR EACH ROW
EXECUTE FUNCTION log_articles_changes();

-- Trigger for the tags table

CREATE OR REPLACE FUNCTION log_tags_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, new_data)
        VALUES ('tags', 'I', row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, old_data, new_data)
        VALUES ('tags', 'U', row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, old_data)
        VALUES ('tags', 'D', row_to_json(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tags_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON tags
FOR EACH ROW
EXECUTE FUNCTION log_tags_changes();

-- Trigger for the article_tags table

CREATE OR REPLACE FUNCTION log_article_tags_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, new_data)
        VALUES ('article_tags', 'I', row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, old_data)
        VALUES ('article_tags', 'D', row_to_json(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER article_tags_audit_trigger
AFTER INSERT OR DELETE ON article_tags
FOR EACH ROW
EXECUTE FUNCTION log_article_tags_changes();

-- Trigger for the annotations table

CREATE OR REPLACE FUNCTION log_annotations_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, new_data)
        VALUES ('annotations', 'I', row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, old_data, new_data)
        VALUES ('annotations', 'U', row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, old_data)
        VALUES ('annotations', 'D', row_to_json(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER annotations_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON annotations
FOR EACH ROW
EXECUTE FUNCTION log_annotations_changes();

-- !!!!!!!!!!!!!!!  Notes on audit_log     !!!!!!!!!!!!!!!

-- SELECT * FROM audit_log;

-- -- View changes for the articles table only
-- SELECT * FROM audit_log WHERE table_name = 'articles';

-- -- View all inserts into the annotations table
-- SELECT * FROM audit_log WHERE table_name = 'annotations' AND operation = 'I';

-- -- View changes for a specific record by audit_id
-- SELECT * FROM audit_log WHERE audit_id = 123;


-- ### 1. Check for orphaned records in the `articles` table


-- -- Check for orphaned records in articles with no matching record in themes
-- SELECT a.*
-- FROM articles a
-- LEFT JOIN themes t ON a.theme_id = t.theme_id
-- WHERE t.theme_id IS NULL;

-- -- Check for orphaned records in articles with no matching record in languages
-- SELECT a.*
-- FROM articles a
-- LEFT JOIN languages l ON a.language_id = l.language_id
-- WHERE l.language_id IS NULL;
-- ```

-- ### 2. Check for orphaned records in the `article_tags` table

-- ```sql
-- -- Check for orphaned records in article_tags with no matching record in articles
-- SELECT at.*
-- FROM article_tags at
-- LEFT JOIN articles a ON at.article_id = a.id
-- WHERE a.id IS NULL;

-- -- Check for orphaned records in article_tags with no matching record in tags
-- SELECT at.*
-- FROM article_tags at
-- LEFT JOIN tags t ON at.tag_id = t.tag_id
-- WHERE t.tag_id IS NULL;
-- ```

-- ### 3. Check for orphaned records in the `annotations` table

-- ```sql
-- -- Check for orphaned records in annotations with no matching record in articles
-- SELECT an.*
-- FROM annotations an
-- LEFT JOIN articles a ON an.article_id = a.id
-- WHERE a.id IS NULL;

-- -- Check for orphaned records in annotations with no matching record in languages
-- SELECT an.*
-- FROM annotations an
-- LEFT JOIN languages l ON an.language_id = l.language_id
-- WHERE l.language_id IS NULL;

-- !!!!!!!!!!!!!!!  End of audit_log notes     !!!!!!!!!!!!!!!

-- Connect to the "users" database
\c users;
CREATE EXTENSION IF NOT EXISTS postgres_fdw;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Initialize tables in users


-- Create the roles table
CREATE TABLE IF NOT EXISTS roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

-- Add roles
INSERT INTO roles (role_name) VALUES
    ('admin'),
    ('user');

CREATE OR REPLACE FUNCTION get_role_id(role_name VARCHAR)
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT role_id FROM roles WHERE roles.role_name = get_role_id.role_name);
END;
$$ LANGUAGE plpgsql;

-- Create the users table with a role field
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password TEXT NOT NULL, -- TEXT type for storing the hashed password
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    birthdate DATE,
    avatar VARCHAR(255),
    confirmed BOOLEAN DEFAULT FALSE, -- Field for tracking account confirmation
    created_at TIMESTAMP DEFAULT now(),
    role_id INTEGER DEFAULT get_role_id('user'),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);


-- Function to hash the password when inserting a new record
CREATE OR REPLACE FUNCTION hash_password()
	RETURNS TRIGGER AS $$
	BEGIN
		NEW.password := crypt(NEW.password, gen_salt('bf')); -- Hash the password using bcrypt
		RETURN NEW;
	END;
	$$ LANGUAGE plpgsql;

-- Trigger to automatically hash the password when inserting a new record
CREATE TRIGGER hash_password_trigger
	BEFORE INSERT ON users
	FOR EACH ROW
	EXECUTE FUNCTION hash_password();

CREATE SERVER articles_server
	FOREIGN DATA WRAPPER postgres_fdw
	OPTIONS (dbname 'articles', host 'postgres', port '5432');

CREATE USER MAPPING FOR CURRENT_USER
	SERVER articles_server
	OPTIONS (user 'articles_maker', password 'articlespassword');

CREATE FOREIGN TABLE local_articles (
	id UUID,
	title TEXT
	)
	SERVER articles_server
	OPTIONS (table_name 'articles');

CREATE TABLE IF NOT EXISTS bookmarks (
    bookmark_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER,
    article_id UUID,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    -- FOREIGN KEY (article_id) REFERENCES local_articles(id) ON DELETE CASCADE
);


-- Create a function that checks whether a record with the given article_id exists
CREATE OR REPLACE FUNCTION check_and_delete_invalid_bookmarks()
RETURNS TRIGGER AS $$
BEGIN
    -- Check whether a record with the given article_id exists
    IF NOT EXISTS (
        SELECT 1 FROM local_articles WHERE id = NEW.article_id
    ) THEN
        -- If the record doesn't exist, delete the current record from bookmarks
        DELETE FROM bookmarks WHERE bookmark_id = NEW.bookmark_id;
        RETURN NULL; -- Cancel the insert/update operation
    END IF;
    RETURN NEW; -- Let the insert/update operation through if everything is fine
END;
$$ LANGUAGE plpgsql;

-- Create a trigger that calls check_and_delete_invalid_bookmarks before inserting or updating rows in bookmarks
CREATE TRIGGER check_and_delete_invalid_bookmarks_trigger
BEFORE INSERT OR UPDATE ON bookmarks
FOR EACH ROW
EXECUTE FUNCTION check_and_delete_invalid_bookmarks();

CREATE TABLE IF NOT EXISTS likes (
    like_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER,
    article_id UUID,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Trigger for the "likes" table
CREATE OR REPLACE FUNCTION check_and_delete_invalid_likes()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM local_articles WHERE id = NEW.article_id
    ) THEN
        DELETE FROM likes WHERE like_id = NEW.like_id;
        RETURN NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_and_delete_invalid_likes_trigger
BEFORE INSERT ON likes
FOR EACH ROW
EXECUTE FUNCTION check_and_delete_invalid_likes();

CREATE TABLE IF NOT EXISTS history (
    history_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER,
    article_id UUID,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Trigger for the "history" table
CREATE OR REPLACE FUNCTION check_and_delete_invalid_history()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM local_articles WHERE id = NEW.article_id
    ) THEN
        DELETE FROM history WHERE history_id = NEW.history_id;
        RETURN NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_and_delete_invalid_history_trigger
BEFORE INSERT ON history
FOR EACH ROW
EXECUTE FUNCTION check_and_delete_invalid_history();

-- Add super user
-- !!! WILL BE USE SED IN THE DOCKERFILE TO CHANGE THE VARS ${...}!!!
INSERT INTO users (username, password, role_id, confirmed)
VALUES ('${ADMIN_USERNAME}', '${ADMIN_PASSWORD}', get_role_id('admin'), TRUE);
