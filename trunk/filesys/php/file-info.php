<?php
    /*
     * file-info.php
     *
     * Copyright (C) 2004,2005 Edmund Horner.
     */
    
    require_once 'config.inc.php';
    require_once 'database.inc.php';
    
    $db = connect();
    
    $id = @$_GET['id'];
?>
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html 
 PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "DTD/xhtml1-strict.dtd">
<html>
<head>
    <title>File information</title>
    
    <style type="text/css">
    <!--
        th { text-align: left; }
        td { text-align: left; }
    -->
    </style>
</head>

<body>
    <h2>File paths</h2>
<?php
    $query = "SELECT
                  rev_id, make_text_path(all_paths) AS path
              FROM
                  all_paths($id),
                  revision
              WHERE
                  all_paths[1] = root_id
              ORDER BY
                  rev_id";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    $arr = pg_fetch_all($result);
    
    $arr2 = array('0' => array(0, 0, ''));
    $i = 0;
    foreach ($arr as $r)
    {
        if ($r['path'] == $arr2[$i][2])
        {
            $arr2[$i][1] = $r['rev_id'];
        }
        else
        {
            $i++;
            $arr2[$i] = array($r['rev_id'], $r['rev_id'], $r['path']);
        }
    }
    
    unset($arr2[0]);
    
    echo "<table>\n";
    echo "<tr><th>Revisions</th><th>Path</th></tr>\n";
    foreach ($arr2 as $r)
    {
        echo "<tr><td>{$r[0]} to {$r[1]}</td><td>{$r[2]}</td></tr>\n";
    }
    echo "</table>\n";
    
    /* Check if it's an image. */
    $query = "SELECT image_id FROM file_is_image WHERE file_id = $id";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    $arr = pg_fetch_all($result);
    
    if (@$arr[0]['image_id'])
    {
        $image_id = $arr[0]['image_id'];
        echo "<a href=\"image-info?id=$image_id\"><img src=\"show?id=$image_id\" /></a></td>\n";
    }
?>
</body>
</html>
