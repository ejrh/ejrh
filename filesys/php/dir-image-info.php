<?php
    /*
     * dir-image-info.php
     *
     * Copyright (C) 2004-2006 Edmund Horner.
     */
    
    require_once 'config.inc.php';
    require_once 'database.inc.php';
    
    $db = connect();
    
    if ($_SERVER['REQUEST_METHOD'] == 'POST' and $_GET['delete'])
    {
        $delete = $_GET['delete'];
        $duplicate = @$_GET['duplicate'];
        if (!$duplicate)
            $duplicate = 'NULL';
        $query = "INSERT INTO deleted (id, duplicate_of) VALUES ($delete, $duplicate)";
        pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        exit;
    }
    
    $id = @$_GET['id'];
    
    $max = 100;
?>
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html 
 PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "DTD/xhtml1-strict.dtd">
<html>
<head>
    <title>Images</title>
    
    <style type="text/css">
    <!--
        th { text-align: left; }
        td { text-align: left; }
    -->
    </style>
    
    <script type="text/javascript">
    <!--
    
        function delete_row(node, id, duplicate)
        {
            var req = new XMLHttpRequest();
            
            req.open('POST', 'dir-image-info?delete=' + id + '&duplicate=' + duplicate);
            req.send('');
            
            var nodes = node.parentNode.parentNode.parentNode.childNodes;
            
            for (var i = 0; i < nodes.length; i++)
            {
                if (nodes[i].nodeType == 1)
                {
                    if (nodes[i].id.indexOf('(' + id + '-') >= 0 || nodes[i].id.indexOf('-' + id + ')') >= 0)
                    {
                        nodes[i].style.display = 'none';
                    }
                }
            }
        }
    -->
    </script>
</head>

<body>

<?php
    set_time_limit(0);
    
    $dir_ids = "$id";
    
    $query = "SELECT id FROM all_subdirs($id) AS dir(id) NATURAL JOIN directory";
    
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    
    $arr = pg_fetch_all($result);
    foreach ($arr as $row)
    {
        $dir_ids = $dir_ids . "," . $row['id'];
    }

    $query = "SELECT
                 i1.id AS id1,
                 i1.width AS width1,
                 i1.height AS height1,
                 f1.id AS file_id1,
                 f1.name AS file_name1,
                 f1.size AS file_size1,
                 
                 i2.id AS id2,
                 i2.width AS width2,
                 i2.height AS height2,
                 f2.id AS file_id2,
                 f2.name AS file_name2,
                 f2.size AS file_size2,
                 
                 image_distance(w, i1, i2) AS distance
             FROM
                 image AS i1
                 JOIN file_is_image AS fii1 ON i1.id = fii1.image_id
                 JOIN file AS f1 ON fii1.file_id = f1.id
                 JOIN file_in_dir AS fid1 ON f1.id = fid1.file_id,
                 
                 image AS i2
                 JOIN file_is_image AS fii2 ON i2.id = fii2.image_id
                 JOIN file AS f2 ON fii2.file_id = f2.id
                 JOIN file_in_dir AS fid2 ON f2.id = fid2.file_id,
                 
                 image_weights AS w
             WHERE
                 f1.id < f2.id
                 AND fid1.dir_id IN ($dir_ids)
                 AND fid2.dir_id IN ($dir_ids)
                 AND f1.id NOT IN (SELECT id FROM deleted)
                 AND f2.id NOT IN (SELECT id FROM deleted)
                 AND (LENGTH(f1.name) <= 7 OR LENGTH(f2.name) <= 7 OR levenshtein(f1.name, f2.name) >= 3)
             ORDER BY
                 distance ASC
             LIMIT $max";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    
    $arr = pg_fetch_all($result);    
?>
    <table>
        <tr>
            <th>Id</th>
            <th>Width</th>
            <th>Height</th>
            <th>Name</th>
            <th>Size</th>
            <th>Thumbnail</th>
            <th>Delete?</th>
            
            <th>Id</th>
            <th>Width</th>
            <th>Height</th>
            <th>Name</th>
            <th>Size</th>
            <th>Thumbnail</th>
            <th>Delete?</th>
            
            <th>Distance</th>
        </tr>
<?php
    foreach ($arr as $row)
    {
        $style = '';
        $style1 = '';
        $style2 = '';
        
        if ($row['width1'] == $row['width2'] and $row['height1'] == $row['height2'])
        {
            $style = 'style="background: #EEEEEE"';
            
            if ($row['file_size1'] > $row['file_size2'])
            {
                $style1 = 'style="border: thin solid red"';
            }
            else if ($row['file_size2'] > $row['file_size1'])
            {
                $style2 = 'style="border: thin solid red"';
            }
        }
        
        if ($row['width1'] > $row['width2']*1.1 and $row['height1'] > $row['height2']*1.1)
        {
            $style2 = 'style="border: thin solid red"';
        }
        else if ($row['width2'] > $row['width1']*1.1 and $row['height2'] > $row['height1']*1.1)
        {
            $style1 = 'style="border: thin solid red"';
        }
?>
        <tr <?php echo $style ?> id="(<?php echo $row['file_id1'] ?>-<?php echo $row['file_id2'] ?>)">
            <td><a href="image-info?id=<?php echo $row['id1'] ?>"><?php echo $row['id1'] ?></a></td>
            <td><?php echo $row['width1'] ?></td>
            <td><?php echo $row['height1'] ?></td>
            <td><a href="file-info?id=<?php echo $row['file_id1'] ?>"><?php echo $row['file_name1'] ?></a></td>
            <td><?php echo $row['file_size1'] ?></td>
            <td><a href="show?id=<?php echo $row['id1'] ?>&full"><img src="show?id=<?php echo $row['id1'] ?>" /></a></td>
            <td <?php echo $style1 ?>>(<span onclick="delete_row(this, <?php echo $row['file_id1'] ?>, <?php echo $row['file_id2'] ?>)">delete</span>)</td>
            
            <td><a href="image-info?id=<?php echo $row['id2'] ?>"><?php echo $row['id2'] ?></a></td>
            <td><?php echo $row['width2'] ?></td>
            <td><?php echo $row['height2'] ?></td>
            <td><a href="file-info?id=<?php echo $row['file_id2'] ?>"><?php echo $row['file_name2'] ?></a></td>
            <td><?php echo $row['file_size2'] ?></td>
            <td><a href="show?id=<?php echo $row['id2'] ?>&full"><img src="show?id=<?php echo $row['id2'] ?>" /></a></td>
            <td <?php echo $style2 ?>>(<span onclick="delete_row(this, <?php echo $row['file_id2'] ?>, <?php echo $row['file_id1'] ?>)">delete</span>)</td>
            
            <td><?php echo number_format($row['distance'], 3) ?></td>
        </tr>
<?php
    }
?>
    </table>
</body>
</html>
