<?php
    require_once 'database.inc.php';
    
    $db = connect();
    
    $path = $_GET['path'];
    $dir_id = $_GET['dir_id'];
    $rev_id = $_GET['rev_id'];
    
    $file_list = lookup_directory_contents($db, $dir_id);
    
    $old_rev_id = @$_GET['old_rev_id'];
    if ($old_rev_id == $rev_id)
        $old_rev_id = null;
    
    $old_dir_id = @$_GET['old_dir_id'];
    if ($old_dir_id == $dir_id)
        $old_dir_id = null;
    if ($old_dir_id)
    {
        $old_file_list = lookup_directory_contents($db, $old_dir_id);
        $file_list = combine_file_lists($file_list, $old_file_list);
    }
    else
    {
        $file_list = combine_file_lists($file_list, array());
    }
    
    lookup_dir_images($db, $file_list);
    
    disconnect($db);
    
    $expiry_date = 2000000000;
    header('Expires: ' . strftime('%a, %d %b %Y %T GMT', $expiry_date));

    function lookup_directory_contents($db, $dir_id)
    {
        $epoch = "'epoch'::timestamp";
        
        $query = "SELECT
                      f.id AS id,
                      name,
                      NULLIF(size, -1) AS size,
                      NULLIF(modified, $epoch) AS modified,
                      NULLIF(modified IS NOT NULL,TRUE) as descendants,
                      fii.image_id AS image_id
                  FROM
                      file AS f
                      JOIN file_in_dir AS fid ON f.id = fid.file_id
                      LEFT JOIN file_is_image AS fii ON f.id = fii.file_id
                  WHERE
                      dir_id = $dir_id
                  ORDER BY
                      UPPER(name)";
        $result = pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        
        $arr = pg_fetch_all($result);
        
        if (!$arr)
            $arr = array();
        return $arr;
    }

    function combine_file_lists($new_list, $old_list)
    {
        $ret = array();
        foreach ($old_list as $item)
        {
            $ret[$item['name']] = array_merge($item, array('status' => 'deleted'));
        }

        foreach ($new_list as $item)
        {
            if (!@$ret[$item['name']]['id'])
            {
                $ret[$item['name']] = array_merge($item, array('status' => 'added'));
            }
            else if (@$ret[$item['name']]['id'] != $item['id'])
            {
                $ret[$item['name']]['status'] = 'original';
                $ret[$item['name'] . '/2'] = array_merge($item, array('status' => 'changed'));
            }
            else
            {
                $ret[$item['name']]['status'] = 'unchanged';
            }
        }
        
        ksort($ret);
        return $ret;
    }

    function lookup_dir_images($db, &$list)
    {
        $dir_list = '';
        foreach ($list as $item)
        {
            if ($item['descendants'] !== null)
            {
                $dir_list .= ',' . $item['id'];
                $name2 = pg_escape_string($item['name']);
                $query = "SELECT image_id AS id FROM file_in_dir NATURAL JOIN file_is_image
                          WHERE dir_id = '{$item['id']}' ORDER BY random() LIMIT 1";
            }
        }
        $dir_list = substr($dir_list, 1);
        if ($dir_list == '')
            return;
        
        $query = "SELECT dir_id,MAX(image_id) AS id FROM file_in_dir NATURAL JOIN file_is_image
                  WHERE dir_id IN ($dir_list) GROUP BY dir_id";
        $result = pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        
        $arr = pg_fetch_all($result);
        $result = array();
        if (!@$arr)
            $arr = array();
        foreach ($arr as $row)
        {
            $result[$row['dir_id']] = $row['id'];
        }
        
        foreach($list as $item)
        {
            if ($item['descendants'] !== null)
            {
                $list[$item['name']]['image_id'] = @$result[$item['id']];
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

    Directory information: <a href="file-info?id=<?php echo $dir_id ?>"><?php echo $dir_id ?></a><br />
    
    Similar images in this directory: <a href="dir-image-info?id=<?php echo $dir_id ?>"><?php echo $dir_id ?></a><br />
    
    <table width="100%">
        <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Size</th>
            <th>Last modified</th>
<?php
    if ($old_dir_id)
    {
        echo "<th>Status</th>\n";
    }
?>
        </tr>
<?php
    foreach ($file_list as $item)
    {
        if ($item['descendants'] !== null)
        {
?>
        <tr>
            <td><a href="browse?rev_id=<?php echo $rev_id ?><?php if ($old_rev_id) echo '&old_rev_id=' . $old_rev_id ?>&path=<?php echo $path, $item['name'] ?>/"><?php echo $item['name'] ?></a></td>
            <td></td>
            <td></td>
            <td></td>
<?php
    if ($old_dir_id)
    {
        echo "<td>{$item['status']}</td>\n";
    }
    if (@$item['image_id'])
    {
        echo "<td><img src=\"show?id={$item['image_id']}\" /></td>\n";
    }
?>
        </tr>
<?php
        }
        else
        {
?>
        <tr>
            <td><a href="file-info?id=<?php echo $item['id'] ?>"><?php echo $item['name'] ?></a></td>
            <td>?</td>
            <td><?php echo $item['size'] ?></td>
            <td><?php echo $item['modified'] ?></td>
<?php
    if ($old_dir_id)
    {
        echo "<td>{$item['status']}</td>\n";
    }
    if (@$item['image_id'])
    {
        echo "<td><a href=\"image-info?id={$item['image_id']}\"><img src=\"show?id={$item['image_id']}\" /></a></td>\n";
    }
?>
        </tr>
<?php
        }
    }
?>
    </table>
</body>
</html>
