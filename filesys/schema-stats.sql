CREATE OR REPLACE VIEW stats AS
SELECT
    nspname AS namespace,
    CASE relkind
        WHEN 'i' THEN '  ' || relname
        ELSE relname
    END AS name,
    CASE relkind
        WHEN 'r' THEN 'table'
        WHEN 'v' THEN 'view'
        WHEN 'i' THEN 'index'
            || (CASE indisclustered
                WHEN TRUE THEN '/c'
                ELSE '' END)
        WHEN 'S' THEN 'sequence'
        WHEN 's' THEN 'special'
    END as kind,
    to_char(reltuples, '999,999,999') AS num_tuples,
    to_char(relpages*8192, '999,999,999') AS bytes
FROM
    pg_class
    JOIN pg_namespace ON relnamespace = pg_namespace.oid
    LEFT JOIN pg_index ON indexrelid = pg_class.oid
WHERE
    nspname NOT IN ('information_schema', 'contrib') AND nspname NOT LIKE 'pg_%'
ORDER BY
    nspname,
    (relkind IN ('r', 'i')) DESC,
    relname;



CREATE OR REPLACE FUNCTION function_args(INTEGER, oid[], TEXT[]) RETURNS TEXT
LANGUAGE 'plpgsql' IMMUTABLE CALLED ON NULL INPUT
AS $$
DECLARE
    args TEXT := ' ';
    r RECORD;
BEGIN
    FOR r IN SELECT typname AS t, ($3)[i] AS n FROM generate_series(1,$1) AS s(i) JOIN pg_type ON pg_type.oid = ($2)[i] LOOP
        SELECT INTO args args || ', ' || CASE WHEN r.n IS NULL THEN '' ELSE r.n || ' ' END || r.t;
    END LOOP;
    
    RETURN SUBSTRING(args, 4);
END;
$$;



CREATE OR REPLACE VIEW function_stats AS
SELECT
    nspname AS namespace,
    proname AS function,
    function_args(pronargs, CASE WHEN proallargtypes IS NULL THEN CAST(string_to_array(array_to_string(proargtypes, ','), ',') AS oid[]) ELSE proallargtypes END, proargnames) AS arguments,
    typname AS returns
FROM
    pg_proc
    JOIN pg_namespace ON pronamespace = pg_namespace.oid
    JOIN pg_type ON prorettype = pg_type.oid
WHERE
    nspname NOT IN ('information_schema', 'contrib') AND nspname NOT LIKE 'pg_%'
ORDER BY
    nspname,
    proname;



GRANT SELECT ON
    stats, function_stats
TO localuser;
