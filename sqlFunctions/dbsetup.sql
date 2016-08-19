--Make sure all of the following are installed:
--  postgresql94 (obviously)
--  postgresql94-contrib (for extensions like fuzzystrmatch)
--On client:
--  postgresql94-devel (needed for psycopg2)

CREATE DATABASE votes;

--Then connect to votes

CREATE TABLE candidates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    bio_url TEXT
);

CREATE TABLE tentative_votes (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    c1 INTEGER REFERENCES candidates (id),
    c2 INTEGER REFERENCES candidates (id),
    c3 INTEGER REFERENCES candidates (id),
    c4 INTEGER REFERENCES candidates (id),
    c5 INTEGER REFERENCES candidates (id),
    c6 INTEGER REFERENCES candidates (id),
    c7 INTEGER REFERENCES candidates (id),
    c8 INTEGER REFERENCES candidates (id),
    c9 INTEGER REFERENCES candidates (id),
    c10 INTEGER REFERENCES candidates (id),
    c11 INTEGER REFERENCES candidates (id),
    c12 INTEGER REFERENCES candidates (id),
    c13 INTEGER REFERENCES candidates (id),
    c14 INTEGER REFERENCES candidates (id),
    c15 INTEGER REFERENCES candidates (id),
    c16 INTEGER REFERENCES candidates (id),
    c17 INTEGER REFERENCES candidates (id),
    c18 INTEGER REFERENCES candidates (id),
    c19 INTEGER REFERENCES candidates (id),
    c20 INTEGER REFERENCES candidates (id),
    normalvote INTEGER REFERENCES candidates (id)
);

CREATE TABLE votes (
    email TEXT PRIMARY KEY,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
    c1 INTEGER REFERENCES candidates (id),
    c2 INTEGER REFERENCES candidates (id),
    c3 INTEGER REFERENCES candidates (id),
    c4 INTEGER REFERENCES candidates (id),
    c5 INTEGER REFERENCES candidates (id),
    c6 INTEGER REFERENCES candidates (id),
    c7 INTEGER REFERENCES candidates (id),
    c8 INTEGER REFERENCES candidates (id),
    c9 INTEGER REFERENCES candidates (id),
    c10 INTEGER REFERENCES candidates (id),
    c11 INTEGER REFERENCES candidates (id),
    c12 INTEGER REFERENCES candidates (id),
    c13 INTEGER REFERENCES candidates (id),
    c14 INTEGER REFERENCES candidates (id),
    c15 INTEGER REFERENCES candidates (id),
    c16 INTEGER REFERENCES candidates (id),
    c17 INTEGER REFERENCES candidates (id),
    c18 INTEGER REFERENCES candidates (id),
    c19 INTEGER REFERENCES candidates (id),
    c20 INTEGER REFERENCES candidates (id),
    normalvote INTEGER REFERENCES candidates (id)
);

--Now insert the trigger function found in triggers.sql

CREATE TRIGGER tentative_vote_error_check BEFORE INSERT OR UPDATE ON tentative_votes
    FOR EACH ROW EXECUTE PROCEDURE vote_error_check();

CREATE TRIGGER vote_error_check BEFORE INSERT OR UPDATE ON votes
    FOR EACH ROW EXECUTE PROCEDURE vote_error_check();

CREATE USER website
    NOCREATEDB
    NOCREATEROLE
    NOCREATEUSER
    LOGIN
    PASSWORD '<password>';

GRANT INSERT ON candidates TO website;
GRANT SELECT ON candidates TO website;
GRANT INSERT ON tentative_votes TO website;
GRANT DELETE ON tentative_votes TO website;
GRANT SELECT ON tentative_votes TO website;
GRANT INSERT ON votes TO website;
GRANT SELECT ON votes TO website;

CREATE EXTENSION fuzzystrmatch;

--Insert function(s) in functions.sql