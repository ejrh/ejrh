-- This aggregate returns the concatenatation of text strings.
-- Since the order in which each string is encountered can make a
-- difference to the final result, it's kind of an incorrect use of
-- aggregates.

DROP AGGREGATE IF EXISTS strsum(text);

CREATE AGGREGATE strsum
(
    BASETYPE=text,
    SFUNC=textcat,
    STYPE=text
);

-- Because they're mutually recursive, we need to make a dummy function
-- for "bootstrapping" the function definitions.
CREATE OR REPLACE FUNCTION dirmd5(INTEGER)
RETURNS CHAR(32) LANGUAGE 'sql' IMMUTABLE STRICT
AS $$SELECT '42'::TEXT$$;

-- Define the functions from the bottom up (though it's a bit
-- contentious which one is at the bottom, since they're mutually
-- recursive...).

-- Return a string for a file or directory with id = $1, of the form
-- "name\tsize\tmodified\n" or "name\tmd5\n" (for directories).
CREATE OR REPLACE FUNCTION childstr(INTEGER)
RETURNS TEXT LANGUAGE 'sql' IMMUTABLE STRICT
AS $$SELECT name || E'\t' ||
     (CASE WHEN d.id IS NOT NULL
      THEN dirmd5($1)
      ELSE COALESCE(CAST(NULLIF(size,-1) AS TEXT),'')
           || E'\t'
           || COALESCE(CAST(NULLIF(modified,'epoch'::timestamp) AS TEXT),'')
      END)
     || E'\n'
     FROM file AS f NATURAL LEFT JOIN directory AS d
     WHERE f.id = $1$$;

CREATE OR REPLACE FUNCTION allchildstrs(INTEGER)
RETURNS TEXT LANGUAGE 'sql' IMMUTABLE STRICT
AS $$SELECT strsum(cs)
     FROM (SELECT childstr(file_id) AS cs
           FROM file JOIN file_in_dir ON file_id = id
           WHERE dir_id = $1 ORDER BY LOWER(name)) AS c$$;

-- Return an even longer string consisting of the name of the
-- directory identified by id = $1, followed by '\n', together with
-- the allchildstrs() string for that directory.
CREATE OR REPLACE FUNCTION dirstr(INTEGER)
RETURNS TEXT LANGUAGE 'sql' IMMUTABLE STRICT
AS $$SELECT name || E'\n' || COALESCE(allchildstrs($1),'')
     FROM file WHERE id = $1$$;

-- Return the MD5 for the directory id = $1.
CREATE OR REPLACE FUNCTION dirmd5(INTEGER)
RETURNS CHAR(32) LANGUAGE 'sql' IMMUTABLE STRICT
AS $$SELECT md5(dirstr($1))$$;


-- Return a set of all descendants of this directory.
CREATE OR REPLACE FUNCTION all_children(INTEGER) RETURNS SETOF INTEGER
LANGUAGE 'plpgsql' STABLE STRICT AS
$$
DECLARE
    r RECORD;
    r2 RECORD;
BEGIN
    FOR r IN SELECT file_id FROM file_in_dir WHERE dir_id = $1 LOOP
        RETURN NEXT r.file_id;
    END LOOP;
    
    FOR r IN SELECT file_id FROM file_in_dir JOIN directory ON file_id = id WHERE dir_id = $1 LOOP
        FOR r2 IN SELECT id FROM all_children(r.file_id) AS ac(id) LOOP
            RETURN NEXT r2.id;
        END LOOP;
    END LOOP;
    
    RETURN;
END;
$$;


-- all_paths(id)
-- Return the set of all paths to this file id, where each path is an
-- array of parent ids, the first of which is the id of a root, and the
-- last of which is id.
CREATE OR REPLACE FUNCTION all_paths(INTEGER) RETURNS SETOF INTEGER[]
LANGUAGE 'plpgsql' STABLE STRICT AS
$$
DECLARE
    r RECORD;
    r2 RECORD;
    b BOOLEAN := FALSE;
BEGIN
    FOR r IN SELECT dir_id FROM file_in_dir WHERE file_id = $1 LOOP
        FOR r2 IN SELECT * FROM all_paths(r.dir_id) LOOP
            RETURN NEXT array_append(r2.all_paths, $1);
        END LOOP;
        SELECT INTO b TRUE;
    END LOOP;
    
    IF NOT b THEN
        RETURN NEXT ARRAY[$1];
    END IF;
    
    RETURN;
END;
$$;

-- all_paths(id_array)
-- Same as all_paths(id), but for an array of ids.
CREATE OR REPLACE FUNCTION all_paths(INTEGER[]) RETURNS SETOF INTEGER[]
LANGUAGE 'plpgsql' STABLE STRICT AS
$$
DECLARE
    r RECORD;
    r2 RECORD;
BEGIN
    FOR r IN SELECT ($1)[i] AS i2 FROM generate_series(array_lower($1, 1), array_upper($1, 1)) AS s(i) LOOP
        FOR r2 IN SELECT all_paths FROM all_paths(r.i2) LOOP
            RETURN NEXT r2.all_paths;
        END LOOP;
    END LOOP;
    
    RETURN;
END;
$$;

-- make_text_path(id_array)
-- Translate an array of path components into an actual text path.
CREATE OR REPLACE FUNCTION make_text_path(INTEGER[]) RETURNS TEXT
LANGUAGE 'plpgsql' STABLE STRICT AS
$$
DECLARE
    r RECORD;
    rv TEXT := '';
BEGIN
    FOR r IN SELECT ($1)[i] AS i2 FROM generate_series(array_lower($1, 1), array_upper($1, 1)) AS s(i) LOOP
        SELECT INTO rv (rv || '/' || name) FROM file WHERE id = r.i2;
    END LOOP;
    
    IF rv LIKE '///%' THEN
        RETURN SUBSTRING(rv, 3);
    END IF;
    
    IF rv LIKE '/%' THEN
        RETURN SUBSTRING(rv, 2);
    END IF;
    
    RETURN rv;
END;
$$;

-- get_free_id(min)
-- Returns a free file id > than min.
CREATE OR REPLACE FUNCTION get_free_id(INTEGER) RETURNS INTEGER
VOLATILE
STRICT
LANGUAGE 'sql' AS
$$
    SELECT f.id+1 FROM file AS f WHERE f.id > $1 AND NOT EXISTS (SELECT id FROM file WHERE id = f.id+1) LIMIT 1;
$$;

-- copy_dir(id)
CREATE OR REPLACE FUNCTION copy_dir(INTEGER) RETURNS INTEGER
VOLATILE
STRICT
LANGUAGE 'plpgsql' AS
$$
DECLARE
    new_id INTEGER;
BEGIN
    SELECT INTO new_id get_free_id($1);
    INSERT INTO file (id, name, md5, size) SELECT new_id, name, 'new-' || new_id, size FROM file WHERE id = $1;
    INSERT INTO directory (id, descendants, children) SELECT new_id, 0, 0;
    INSERT INTO file_in_dir (file_id, dir_id) SELECT file_id,new_id FROM file_in_dir WHERE dir_id = $1;
    RETURN new_id;
END;
$$;

-- This trigger function ensures that (dir_id, name) is unique on
-- file_in_dir JOIN file ON file_id = id.  Triggers are defined on
-- INSERT and UPDATE to file_in_dir, and UPDATE to file (for when
-- file.name is changed).

CREATE OR REPLACE FUNCTION file_in_dir_uq_name_trig() RETURNS trigger
LANGUAGE 'plpgsql'
AS $$
DECLARE
    conflict_id INTEGER;
BEGIN
    IF (TG_OP = 'INSERT' OR TG_OP = 'UPDATE') AND TG_RELNAME = 'file_in_dir' THEN
        -- Look and see if there's already a row with this (dir_id, name).
        SELECT INTO conflict_id
            file_id
        FROM
            file_in_dir
            JOIN file ON file_id = id
        WHERE
            dir_id = NEW.dir_id
            AND file_id != NEW.file_id
            AND name = (SELECT name FROM file WHERE id = NEW.file_id);
        
        -- If so, raise an exception.
        IF conflict_id IS NOT NULL THEN
            RAISE NOTICE 'file_id = % conflicts with file_id = %', NEW.file_id, conflict_id;
            RAISE NOTICE '(TG_OP = %, TG_RELNAME = %, OLD = %, NEW = %)', TG_OP, TG_RELNAME, OLD, NEW;
            RAISE EXCEPTION 'special unique constraint "file_in_dir_uq_name" violated on (dir_id, name)';
        END IF;
    
    ELSEIF TG_OP = 'UPDATE' AND TG_RELNAME = 'file' THEN
        IF OLD.name != NEW.name THEN
            -- Look and see if there's already a row with this (dir_id, name).
            SELECT INTO conflict_id
                file_id
            FROM
                file_in_dir
                JOIN file ON file_id = id
            WHERE
                name = NEW.name
                AND file_id != NEW.id
                AND dir_id IN (SELECT dir_id FROM file_in_dir WHERE file_id = NEW.id);
            
            -- If so, raise an exception.
            IF conflict_id IS NOT NULL THEN
                RAISE NOTICE 'file_id = % conflicts with file_id = %', NEW.id, conflict_id;
                RAISE NOTICE '(TG_OP = %, TG_RELNAME = %, OLD = %, NEW = %)', TG_OP, TG_RELNAME, OLD, NEW;
                RAISE EXCEPTION 'special unique constraint "file_in_dir_uq_name" violated on (dir_id, name)';
            END IF;
        END IF;
    
    ELSE
        RAISE NOTICE 'file_in_dir_uq_name_trig called with % operation and % relation!', TG_OP, TG_RELNAME;
    END IF;
    
    -- Otherwise just let the new row go in.
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS file_in_dir_uq_name_insert ON file_in_dir;
DROP TRIGGER IF EXISTS file_in_dir_uq_name_update ON file_in_dir;
DROP TRIGGER IF EXISTS file_in_dir_uq_name_update_on_file ON file;

CREATE TRIGGER file_in_dir_uq_name_insert
AFTER INSERT ON file_in_dir
FOR EACH ROW EXECUTE PROCEDURE file_in_dir_uq_name_trig();

CREATE TRIGGER file_in_dir_uq_name_update
AFTER UPDATE ON file_in_dir
FOR EACH ROW EXECUTE PROCEDURE file_in_dir_uq_name_trig();

CREATE TRIGGER file_in_dir_uq_name_update_on_file
AFTER UPDATE ON file
FOR EACH ROW EXECUTE PROCEDURE file_in_dir_uq_name_trig();



CREATE OR REPLACE FUNCTION delete_orphans() RETURNS INTEGER
VOLATILE STRICT LANGUAGE 'plpgsql' AS
$$
DECLARE
    new_orphans INTEGER;
    total_orphans INTEGER;
    deleted_orphans INTEGER;
    total_file_count INTEGER;
BEGIN
    TRUNCATE orphan;
    
    /*DELETE FROM file
        WHERE
            name = '/'
            AND id NOT IN (SELECT root_id FROM revision);*/
    
    SELECT INTO total_file_count COUNT(*) FROM file;
    RAISE NOTICE 'files % initial files', total_file_count;
    
    INSERT INTO orphan
        SELECT
            id
        FROM
            file
        WHERE
            name NOT LIKE '/%'
            AND name != ''
            AND NOT EXISTS (SELECT file_id FROM file_in_dir WHERE file_id = id);
    
    GET DIAGNOSTICS total_orphans = ROW_COUNT;
    
    RAISE NOTICE 'found % initial orphans', total_orphans;
    
    LOOP
        INSERT INTO orphan
            SELECT
                DISTINCT file_id
            FROM
                file_in_dir AS f
            WHERE
                dir_id IN (SELECT id FROM orphan)
                AND file_id NOT IN (SELECT id FROM orphan)
                AND NOT EXISTS (SELECT * FROM file_in_dir AS f2
                                WHERE f2.file_id = f.file_id AND dir_id NOT IN (SELECT id FROM orphan));
        
        GET DIAGNOSTICS new_orphans = ROW_COUNT;
        
        IF (new_orphans <= 0) THEN
            EXIT;
        END IF;
        
        total_orphans := total_orphans + new_orphans;
        RAISE NOTICE 'found % new orphans', new_orphans;
    END LOOP;
    
    RAISE NOTICE 'deleting % orphans', total_orphans;

    LOOP
        DELETE FROM file
            WHERE
                id IN (SELECT id FROM orphan)
                AND NOT EXISTS (SELECT file_id FROM file_in_dir WHERE file_id = id);
        
        GET DIAGNOSTICS deleted_orphans = ROW_COUNT;
        
        IF (deleted_orphans <= 0) THEN
            EXIT;
        END IF;
    END LOOP;
    
    SELECT INTO total_file_count COUNT(*) FROM file;
    RAISE NOTICE 'found % files after', total_file_count;
    
    RETURN total_orphans;
END;
$$;



-- Replace all references to $1 with $2, and delete $1.  If necessary, this
-- may mean reusing $1's id (if it's the lesser of them).
CREATE OR REPLACE FUNCTION replace_file(INTEGER, INTEGER) RETURNS INTEGER
LANGUAGE 'plpgsql' VOLATILE STRICT AS
$$
DECLARE
    min_id INTEGER;
    vals RECORD;
BEGIN
    IF $1 = $2 THEN
        RETURN $1;
    END IF;
    
    min_id = LEAST($1, $2);
    
    IF min_id = $1 THEN
        SELECT INTO vals f.name, f.size, f.modified, f.md5 FROM file AS f WHERE id = $2;
        UPDATE file_in_dir SET file_id = $1 WHERE file_id = $2;
        UPDATE file_is_image SET file_id = $1 WHERE file_id = $2 AND NOT EXISTS (SELECT 1 FROM file_is_image WHERE file_id = $1);
        UPDATE deleted SET id = $1 WHERE id = $2;
        UPDATE deleted SET duplicate_of = $1 WHERE duplicate_of = $2;
        DELETE FROM file WHERE id = $2;
        UPDATE file SET name = vals.name, size = vals.size, modified = vals.modified, md5 = vals.md5 WHERE id = $1;
    ELSE
        UPDATE file_in_dir SET file_id = $2 WHERE file_id = $1;
        UPDATE file_is_image SET file_id = $2 WHERE file_id = $1 AND NOT EXISTS (SELECT 1 FROM file_is_image WHERE file_id = $2);
        UPDATE deleted SET id = $2 WHERE id = $1;
        UPDATE deleted SET duplicate_of = $2 WHERE duplicate_of = $1;
        DELETE FROM file WHERE id = $1;
    END IF;
    
    RETURN min_id;
EXCEPTION
    WHEN not_null_violation THEN
        RAISE NOTICE 'not replaced';
        RETURN NULL;
END;
$$;


CREATE OR REPLACE FUNCTION merge_revisions(INTEGER, INTEGER) RETURNS INTEGER
LANGUAGE 'plpgsql' VOLATILE STRICT AS
$$
DECLARE
    min_id INTEGER;
    max_id INTEGER;
    min_root INTEGER;
    max_root INTEGER;
BEGIN
    IF $1 = $2 THEN
        RETURN $1;
    END IF;
    
    min_id = LEAST($1, $2);
    max_id = GREATEST($1, $2);
    
    min_root := (SELECT root_id FROM revision WHERE rev_id = min_id);
    max_root := (SELECT root_id FROM revision WHERE rev_id = max_id);
    
    UPDATE file_in_dir SET dir_id = max_root WHERE dir_id = min_root;
    
    DELETE FROM revision WHERE rev_id = min_id;
    
    UPDATE revision SET rev_id = rev_id - 1 WHERE rev_id > min_id;
    
    RETURN max_id - 1;
END;
$$;


-- Quickly show the revisions and paths for a given file.
CREATE OR REPLACE FUNCTION show_paths(TEXT) RETURNS SETOF rev_path
LANGUAGE 'sql' STABLE AS
$$
    SELECT rev_id,make_text_path(all_paths) AS path FROM all_paths(ARRAY(SELECT id FROM file WHERE lower(name) = lower($1))) LEFT JOIN revision ON root_id = all_paths[1];
$$;

CREATE OR REPLACE FUNCTION show_paths(INTEGER) RETURNS SETOF rev_path
LANGUAGE 'sql' STABLE AS
$$
    SELECT rev_id,make_text_path(all_paths) AS path FROM all_paths($1) LEFT JOIN revision ON root_id = all_paths[1];
$$;

CREATE OR REPLACE FUNCTION show_paths(INTEGER[]) RETURNS SETOF rev_path
LANGUAGE 'sql' STABLE AS
$$
    SELECT rev_id,make_text_path(all_paths) AS path FROM all_paths($1) LEFT JOIN revision ON root_id = all_paths[1];
$$;



-- What's the extension part of a filename?
-- TODO: this is rather dodgy, and has only been tested for
-- files with at least one ".", no leading or trailing ".", and no
-- occurences of "..".
CREATE OR REPLACE FUNCTION get_extension(TEXT) RETURNS TEXT
IMMUTABLE STRICT LANGUAGE 'plpgsql' AS
$$
DECLARE
    i INTEGER;
    s TEXT;
BEGIN
    i := 2;
    s := NULL;
    
    LOOP
        IF COALESCE(split_part($1, '.', i),'') = '' THEN
            EXIT;
        END IF;
        
        s := split_part($1, '.', i);
        i := i + 1;
    END LOOP;
    
    RETURN s;
END;
$$;


CREATE OR REPLACE FUNCTION remove_gaps(max_gaps INTEGER) RETURNS VOID
VOLATILE CALLED ON NULL INPUT
LANGUAGE 'plpgsql' AS
$$
DECLARE
    num INTEGER;
    first_id INTEGER;
    closing_id INTEGER;
    done INTEGER;
    total_count INTEGER;
    gap_id INTEGER;
    gap_size INTEGER;
    next_gap_id INTEGER;
    filer RECORD;
    percent INTEGER;
BEGIN
    RAISE NOTICE 'Finding gaps';
    TRUNCATE gap;
    INSERT INTO gap SELECT id+1 AS id,0  AS size FROM file AS f WHERE NOT EXISTS (SELECT 1 FROM file WHERE id = f.id+1);
    UPDATE gap SET size = (SELECT id FROM file WHERE id > gap.id ORDER BY id LIMIT 1) - id;
    
    SELECT INTO num COUNT(*) FROM gap;
    IF max_gaps IS NOT NULL AND num > max_gaps THEN
        num := max_gaps;
    END IF;
    
    SELECT INTO first_id id FROM gap ORDER BY id ASC LIMIT 1;
    SELECT INTO closing_id id FROM gap ORDER BY id ASC LIMIT 1 OFFSET num;
    IF closing_id IS NULL THEN
        SELECT INTO closing_id MAX(id) FROM gap;
    END IF;
    SELECT INTO total_count closing_id - first_id - SUM(size) FROM (SELECT size FROM gap ORDER BY id LIMIT num) AS sizes;
    
    done := 0;
    
    RAISE NOTICE 'Removing % gaps...', num;
    
    FOR i IN 1..num LOOP
        SELECT INTO gap_id id FROM gap ORDER BY id ASC LIMIT 1;
        SELECT INTO gap_size size FROM gap ORDER BY id ASC LIMIT 1;
        SELECT INTO next_gap_id id FROM gap WHERE id > gap_id ORDER BY id ASC LIMIT 1;
        
        FOR filer IN SELECT id FROM file WHERE id > gap_id AND id < next_gap_id ORDER BY id LOOP
            UPDATE file SET id = id - gap_size WHERE id = filer.id;
        END LOOP;
        
        UPDATE gap SET id = id - gap_size, size = size + gap_size WHERE id = next_gap_id;
        DELETE FROM gap WHERE id = gap_id;
        
        done := done + next_gap_id - gap_id - gap_size;
        percent := (100 * done) / total_count;
        RAISE NOTICE 'Removed gap %/% (% %%), at %, size %, count %', i, num, percent, gap_id, gap_size, next_gap_id - gap_id - gap_size;
    END LOOP;
END;
$$;


CREATE OR REPLACE FUNCTION inherit_drive(drive_name TEXT, rev INTEGER) RETURNS INTEGER
VOLATILE STRICT
LANGUAGE 'plpgsql' AS
$$
DECLARE
    drive_id INTEGER;
BEGIN
    SELECT INTO drive_id f.id
        FROM file AS f
            JOIN file_in_dir AS fid ON f.id = fid.file_id
            JOIN file AS f2 ON f2.id = fid.dir_id
            JOIN revision AS r ON r.root_id = f2.id
        WHERE f.name = drive_name
            AND r.rev_id <= rev
        ORDER BY rev_id DESC
        LIMIT 1;
    IF drive_id IS NULL THEN
        RETURN NULL;
    END IF;
    
    INSERT INTO file_in_dir (file_id, dir_id)
        SELECT drive_id, root_id FROM revision AS r WHERE r.rev_id = rev;
    
    RETURN drive_id;
END;
$$;


CREATE OR REPLACE FUNCTION find_duplicates(name_size_modified[]) RETURNS SETOF RECORD
STABLE STRICT
LANGUAGE 'plpgsql'
AS $$
DECLARE
    i INTEGER;
    r RECORD;
BEGIN
    IF array_lower($1, 1) IS NULL THEN
        RETURN;
    END IF;
    FOR i IN array_lower($1, 1) .. array_upper($1, 1) LOOP
        RETURN QUERY SELECT $1[i].name::VARCHAR AS orig_name, f.id, f.name::VARCHAR, f.size, f.modified, f.md5::VARCHAR FROM file AS f WHERE f.name = $1[i].name AND f.size = $1[i].size AND f.modified = $1[i].modified;
    END LOOP;
END;
$$;


CREATE OR REPLACE FUNCTION all_file_in_dirs(INTEGER) RETURNS SETOF file_in_dir
STABLE LANGUAGE 'sql'
AS $$
    WITH RECURSIVE w(file_id, dir_id) AS
    (SELECT file_id, dir_id
        FROM file_in_dir AS fid WHERE dir_id = $1
        UNION ALL
        SELECT fid.file_id, fid.dir_id
        FROM file_in_dir AS fid JOIN w ON w.file_id = fid.dir_id)
    SELECT file_id, dir_id FROM w;
$$;
