CREATE OR REPLACE FUNCTION lookup_path(parent_id INTEGER, path TEXT) RETURNS INTEGER
STABLE STRICT
LANGUAGE 'plpgsql'
AS $$
DECLARE
    prefix_id INTEGER;
    prefix TEXT;
    remainder TEXT;
BEGIN
    IF path = '' THEN
        RETURN parent_id;
    END IF;
    
    IF path LIKE '/%' THEN
        RETURN lookup_path(parent_id, SUBSTRING(path, 2));
    END IF;
    
    IF path NOT LIKE '%/%' THEN
        prefix := path;
        remainder := '';
    ELSE
        prefix := regexp_replace(path, '^([^/]+)/.+$', E'\\1');
        remainder = regexp_replace(path, '^([^/]+)/(.+)$', E'\\2');
    END IF;
    
    SELECT INTO prefix_id id FROM file_in_dir JOIN file ON file_id = id WHERE dir_id = parent_id AND name = prefix;
    
    RETURN lookup_path(prefix_id, remainder);
END;
$$;
