CREATE OR REPLACE FUNCTION fix_dir(id INTEGER, path TEXT) RETURNS RECORD
VOLATILE STRICT
LANGUAGE 'plpgsql'
AS $$
    RETURN 0;
$$;


CREATE OR REPLACE FUNCTION fix_dir(dir_id INTEGER, path TEXT) RETURNS RECORD
VOLATILE STRICT
LANGUAGE 'plpgsql'
AS $$
DECLARE
    item RECORD;
    
    child RECORD;
    child_path TEXT;
    
    regex1 TEXT;
    regex2 TEXT;
    
    new_size BIGINT;
    new_children INTEGER;
    new_descendants INTEGER;
    new_md5_str TEXT;
    new_md5 TEXT;
    
    new_id INTEGER;
BEGIN
    SELECT id,name,size,modified,md5,children,descendants INTO item FROM file NATURAL JOIN directory WHERE file.id = dir_id;
    
    --RAISE NOTICE 'fix_dir %', item;
    
    new_size := 0;
    new_children := 0;
    new_descendants := 0;
    new_md5_str := item.name || E'\n';
    
    FOR child IN
        SELECT
            id,
            name,
            size,
            modified,
            md5,
            children,
            descendants,
            free_space,
            total_space
        FROM
            file_in_dir
            JOIN file ON file_id = id
            NATURAL LEFT JOIN directory
            NATURAL LEFT JOIN drive
        WHERE
            file_in_dir.dir_id = item.id
        ORDER BY
            LOWER(name)
        LOOP
        
        child_path := path || '/' || child.name;
        
        /* Ignore this item if it matches one of the ignore regexes. */
        IF child_path ~ regex1 OR child_path ~ regex2 THEN
            --RAISE NOTICE 'ignoring %', child_path;
            DELETE FROM file_in_dir WHERE dir_id = this.id AND file_id = child.id;
        ELSIF child.descendants IS NOT NULL THEN
            child := fix_dir(child.id, child_path);
            
            new_size := new_size + child.size;
            new_children := new_children + 1;
            new_descendants := new_descendants + 1 + child.descendants;
            new_md5_str := new_md5_str || child.name || E'\t' || COALESCE(child.md5,'') || E'\n';
        ELSE
            new_size := new_size + child.size;
            new_children := new_children + 1;
            new_descendants := new_descendants + 1;
            new_md5_str := new_md5_str || child.name || E'\t' || child.size || E'\t' || child.modified || E'\n';
        END IF;
    END LOOP;
    
    new_md5 := pg_catalog.md5(new_md5_str);
    
    IF item.md5 != new_md5 THEN
        SELECT INTO new_id id FROM file WHERE md5 = new_md5;
        
        IF new_id IS NOT NULL THEN
            --RAISE NOTICE 'replacing % with %', item, new_id;
            PERFORM replace_file(item.id, new_id);
        END IF;
    ELSE
        new_id := item.id;
    END IF;
    
    IF item.size != new_size OR item.md5 != new_md5 THEN
        --RAISE NOTICE 'updating %, % -> %, %', item.size, item.md5, new_size, new_md5;
        UPDATE file SET size = new_size, md5 = new_md5 WHERE id = item.id;
    END IF;
    
    IF item.children != new_children OR item.descendants != new_descendants THEN
        --RAISE NOTICE 'updating %, % -> %, %', item.children, item.descendants, new_children, new_descendants;
        UPDATE directory SET children = new_children, descendants = new_descendants WHERE id = item.id;
    END IF;
    
    item.size = new_size;
    item.children = new_children;
    item.descendants = new_descendants;
    item.md5 = new_md5;
    
    RETURN item;
END;
$$;
