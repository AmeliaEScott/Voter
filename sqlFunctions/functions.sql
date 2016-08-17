CREATE OR REPLACE FUNCTION add_candidate(candidateName TEXT, OUT id INTEGER, OUT resultName TEXT, OUT isNew BOOLEAN) AS $$
    
    DECLARE
        result RECORD;
    BEGIN
        WITH dist AS (
            SELECT c.id, c.name, levenshtein(name, candidateName) AS dist FROM candidates c
        )
        SELECT dist.id, dist.name FROM dist WHERE dist.dist < 4 ORDER BY dist.dist ASC LIMIT 1 INTO result;
        
        IF FOUND THEN
            id := result.id;
            resultName := result.name;
            isNew := false;
        ELSE
            INSERT INTO candidates (name) VALUES (candidateName) RETURNING candidates.id,name INTO result;
            id := result.id;
            resultName := result.name;
            isNew := true;
        END IF;
    END;

$$ LANGUAGE plpgsql;