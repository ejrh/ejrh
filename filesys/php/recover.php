<?php
    /*
     * This script recovers a directory of files, using the MD5 signatures to
     * find matching files.
     */

    require_once 'database.inc.php';
    
    set_time_limit(0);
    
    $rev_id = max(@$_GET['rev_id'], @$_GET['rev'], @$_GET['id']);
    
    $path = @$_GET['path'];
    
    $db = connect();
    
    /* Fix the directories. */
    begin($db);
    
    $path_ids = lookup_path($db, $rev_id, $path);
    $dir_id = $path_ids['id' . (count($path_ids) - 2)];

    recover_directory($dir_id, $path, $db);
    
    /* Done. */
    disconnect($db);

    function lookup_path($db, $rev_id, $path)
    {
        $query = make_lookup_query($rev_id, $path);
        $result = pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        
        $arr = pg_fetch_all($result);
        
        return @$arr[0];
    }

    function make_lookup_query($rev_id, $path)
    {
        $n = 0;
        $select_clauses = '';
        $from_clauses = '';
        $where_clauses = '';
        
        $tok = strtok($path, "/");
        while ($tok)
        {
            $tok = pg_escape_string($tok);
            $n0 = $n;
            $n++;
            
            $select_clauses .= ",
                                f$n.id AS id$n";
            $from_clauses .= "
                                  LEFT JOIN file_in_dir AS fd$n0 ON (f$n0.id = fd$n0.dir_id)
                                  LEFT JOIN file AS f$n ON (fd$n0.file_id) = f$n.id";
            $where_clauses .= "
                                   AND f$n.name = '$tok'";
            
            $tok = strtok("/");
        }
        
        $query = "SELECT
                      r.rev_id,
                      f0.id AS id0$select_clauses
                  FROM
                      revision AS r
                      LEFT JOIN file AS f0 ON (r.root_id = f0.id)$from_clauses
                  WHERE
                      r.rev_id = $rev_id
                      AND f0.name = '/'$where_clauses";
        
        return $query;
    }

    function recover_directory($dir_id, $path, $db)
    {
        echo "<br />\n";
        echo "<strong>Directory " . $path . "</strong><br />\n";
        
        $query = "SELECT
                      id,
                      name,
                      size,
                      modified,
                      md5
                  FROM
                      file
                      JOIN file_in_dir ON id = file_id
                  WHERE
                      dir_id = $dir_id
                      AND (size > 0 OR modified IS NULL)
                  ORDER BY
                      modified IS NULL,
                      name ASC";
        $result = pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        
        $arr = pg_fetch_all($result);
        
        if (!$arr)
            $arr = array();
        
        foreach ($arr as $item)
        {
            if ($item['modified'])
            {
                $query = "SELECT id FROM file WHERE name LIKE 'R--%' AND md5 = '{$item['md5']}'";
                $result = pg_query($db, $query)
                    or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
                
                $arr = pg_fetch_all($result);
                
                $d = @$arr[0]['id'];
                
                if ($d)
                {
                    $query = "SELECT make_text_path(p) AS path FROM all_paths($d) AS ap(p) WHERE make_text_path(p) LIKE '%:%'";
                    $result = pg_query($db, $query)
                        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
                    
                    $arr = pg_fetch_all($result);
                
                    $p = str_replace('/R--', '/', @$arr[0]['path']);
                }
                
                if (!$d or !@$p)
                {
                    $name2 = addslashes($item['name']);
                    $query = "SELECT make_text_path(all_paths) AS path FROM all_paths(ARRAY(SELECT id FROM file WHERE name = 'R--' || '$name2'))";
                    $result = pg_query($db, $query)
                        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
                    
                    $arr = pg_fetch_all($result);
                    
                    $p = str_replace('/R--', '/', @$arr[0]['path']);
                    
                    echo "<span style=\"color: red;\">{$item['name']}</span> not provided! md5 is {$item['md5']}, name match is $p<br />\n";
                }
                else
                {
                    echo "{$item['name']} provided by $d, path is $p<br />\n";
                }
            }
            else
            {
                recover_directory($item['id'], $path . '/' . $item['name'], $db);
            }
        }
    }
?>
