<?php
    set_time_limit(600);
    
    require_once 'config.inc.php';
    require_once 'database.inc.php';
    
    $db = connect();
    
    $id = @$_GET['id'];
    $max = 10;
?>
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html 
 PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "DTD/xhtml1-strict.dtd">
<html>
<head>
    <title>Orphan Images</title>
    
    <style type="text/css">
    <!--
        th { text-align: left; }
        td { text-align: left; }
    -->
    </style>
</head>

<body>

<?php
    $query = "SELECT image.id FROM file_is_image
    RIGHT JOIN image ON image.id = image_id
    WHERE image_id IS NULL
    ORDER BY image.id;";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    
    $arr = pg_fetch_all($result);    
    foreach ($arr as $row)
    {
        $id = $row['id'];
?>
    <a href="image-info?id=<?php echo $id ?>&search=anywhere"><img src="show?id=<?php echo $id ?>" /></a>
<?php
    }
?>
</body>
</html>
