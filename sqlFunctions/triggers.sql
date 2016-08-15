CREATE OR REPLACE FUNCTION vote_error_check() RETURNS trigger AS $$
    DECLARE
        newArray INTEGER[];
        i INTEGER;
        foundZero BOOLEAN;
    BEGIN
        newArray := ('{' || coalesce(NEW.c1, 0) || ',' || coalesce(NEW.c2, 0) || ',' || coalesce(NEW.c3, 0) || ',' ||
                     coalesce(NEW.c4, 0) || ',' || coalesce(NEW.c5, 0) || ',' || coalesce(NEW.c6, 0) || ',' ||
                     coalesce(NEW.c7, 0) || ',' || coalesce(NEW.c8, 0) || ',' || coalesce(NEW.c9, 0) || ',' ||
                     coalesce(NEW.c10, 0) || ',' || coalesce(NEW.c11, 0) || ',' || coalesce(NEW.c12, 0) || ',' ||
                     coalesce(NEW.c13, 0) || ',' || coalesce(NEW.c14, 0) || ',' || coalesce(NEW.c15, 0) || ',' ||
                     coalesce(NEW.c16, 0) || ',' || coalesce(NEW.c17, 0) || ',' || coalesce(NEW.c18, 0) || ',' ||
                     coalesce(NEW.c19, 0) || ',' || coalesce(NEW.c20, 0) || '}')::INTEGER[];
        foundZero := FALSE;
        FOR i IN 1..20 LOOP
            --RAISE NOTICE 'i: %, val: %', i, newArray[i];
            IF foundZero AND newArray[i] > 0 THEN
                RAISE EXCEPTION 'Column c% was not null, but column c% was.', i, i-1;
            ELSIF newArray[i] = 0 THEN
                foundZero := TRUE;
            ELSIF newArray[i] = ANY(newArray[1:i-1]) THEN
                RAISE EXCEPTION 'Repeated candidate %', newArray[i];
            END IF;
        END LOOP;
        --RAISE NOTICE 'Array: %', newArray::TEXT;
        RETURN NEW;
    END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER vote_error_check BEFORE INSERT OR UPDATE ON votes
    FOR EACH ROW EXECUTE PROCEDURE vote_error_check();