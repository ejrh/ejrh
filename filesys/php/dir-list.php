<?php
    require_once 'database.inc.php';
    
    $db = connect();
    
    $path = $_GET['path'];
    $rev_id = $_GET['rev_id'];
    $root_id = $_GET['root_id'];
    $dir_id = $_GET['dir_id'];

    $old_rev_id = @$_GET['old_rev_id'];
    if ($old_rev_id == $rev_id)
        $old_rev_id = null;
    
    $old_dir_id = @$_GET['old_dir_id'];
    if ($old_dir_id == $dir_id)
        $old_dir_id = null;
    
    $expiry_date = 2000000000;
    header('Expires: ' . strftime('%a, %d %b %Y %T GMT', $expiry_date));

    function lookup_subdirs($db, $dir_id)
    {
        static $prepared;
        
        if (!@$prepared)
        {
            $query = 'SELECT 
                          id,
                          name,
                          children,
                          descendants,
                          size
                      FROM
                          file_in_dir 
                          JOIN (file NATURAL JOIN directory) AS f ON file_id = f.id
                      WHERE
                          dir_id = $1
                      ORDER BY
                          UPPER(name)';
            prepare(__FILE__, __LINE__, 'lookup_subdirs', $query, $db);
            
            $prepared = true;
        }
        $result = query(__FILE__, __LINE__, 'lookup_subdirs', array($dir_id), $db);
        
        $arr = pg_fetch_all($result);
        
        if (!$arr)
            $arr = array();
        return @$arr;
    }

    function output_dir($db, $rev_id, $dir_id, $old_rev_id, $item, $full_path, $path, $indent = '')
    {
        $name = $item['name'];
        $children = @$item['children'];
        $descendants = @$item['descendants'];
        $size = @$item['size'];
        
        if ($name != '/')
            $full_path .= $name;
        $full_path .= '/';
        
        $stats = "<td>" . number_format($children) . "</td><td>" . number_format($descendants) . "</td><td>" . number_format($size) . "</td>";
        
        $name = str_replace(' ', '&nbsp;', $name);
        if ($path == $full_path)
        {
            echo "<tr><td><strong><a name=\"current\">$indent$name</a></strong></td>$stats</tr>\n";
        }
        else
        {
            echo "<tr><td>$indent<a href=\"browse?rev_id=$rev_id";
            if ($old_rev_id) echo '&old_rev_id=' . $old_rev_id;
            echo "&path=$full_path\">$name</a></td>$stats</tr>\n";
        }

        if (substr($path, 0, strlen($full_path)) == $full_path)
        {
            $subdirs = lookup_subdirs($db, $dir_id);
            
            foreach ($subdirs as $item)
            {
                output_dir($db, $rev_id, $item['id'], $old_rev_id, $item, $full_path, $path, $indent . '&nbsp;&nbsp;&nbsp;&nbsp;');
            }
        }
    }
?>
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html 
 PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "DTD/xhtml1-strict.dtd">
<html>
<head>
    <style type="text/css">
    <!--
        body { background: #3A6EA5; color: #FFFFFF; margin: 0cm; }
        a:link { color: #CCCCFF; }
        a:visited { color: #FFCCFF; }

        h1 { font-size: 150%; }
        h2 { font-size: 100%; }

        table { padding: 0.1cm; }
        th { text-align: left; }
        
        td + td { text-align: right; }
        th + th { text-align: right; }
    -->
    </style>

    <base target="_top">
</head>

<body>
    <table width="100%">
        <tr>
            <th>Name</th>
            <th>Ch.</th>
            <th>Desc.</th>
            <th>Size</th>
        </tr>
<?php
    $query = "SELECT 
                  id,
                  name,
                  children,
                  descendants,
                  size
              FROM
                  revision
                  JOIN (file NATURAL JOIN directory) AS f ON root_id = f.id
              WHERE
                  rev_id = $rev_id";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    
    $arr = pg_fetch_all($result);
    output_dir($db, $rev_id, $root_id, $old_rev_id, $arr[0], '', $path);
        
    disconnect($db);
?>
    </table>
</body>
</html>

