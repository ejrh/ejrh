<?php
    /*
     * show.php
     *
     * Copyright (C) 2004,2005, Edmund Horner.
     *
     * View the image for ?id.
     */
    
    require_once 'config.inc.php';
    require_once 'database.inc.php';
    
    global $config;
    
    $db = connect();
    
    $id = @$_GET['id'];
    
    if (isset($_GET['full']))
    {
        $query = "SELECT
                      rev_id,
                      make_text_path(all_paths) AS path
                  FROM
                      all_paths(ARRAY(SELECT file_id FROM file_is_image WHERE image_id = $id))
                      JOIN revision ON all_paths[1] = root_id
                  ORDER BY
                      rev_id DESC";
        $result = pg_query($db, $query);
        $arr = pg_fetch_all($result);
        
        for ($i = 0; $i < count($arr); $i++)
        {
            $path = $arr[$i]['path'];
            
            if (file_exists(substr($path, 1)))
            {
                $type = mime_type($path);
                header("Content-type: $type");
                virtual(files_internal_path($path));
                exit;
            }
        }
    }

    $query = "SELECT thumbnail FROM image NATURAL LEFT JOIN extra.thumbnail WHERE id = '$id'";
    $result = pg_query($db, $query);
    if (!$result)
    {
        error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    }
    
    $arr = pg_fetch_all($result);
    $image = pg_unescape_bytea($arr[0]['thumbnail']);
    
    $type = $config['thumbnail_type'];
    
    header("Content-type: $type");
    $expiry_date = 2000000000;
    header('Expires: ' . strftime('%a, %d %b %Y %T GMT', $expiry_date));
    
    echo $image;
    
    exit;
    
    function mime_type($filename)
    {
        if (eregi('\.(jpg|jpe|jpeg)$', $filename))
        {
            return 'image/jpg';
        }
        else if (eregi('\.(png)$', $filename))
        {
            return 'image/png';
        }
        else if (eregi('\.(gif)$', $filename))
        {
            return 'image/gif';
        }
    }

    function files_internal_path($path)
    {
        return '/files.internal/' . substr($path, 1, 1) . substr($path, 3);
    }
?>
