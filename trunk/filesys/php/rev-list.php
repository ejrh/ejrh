<?php
    require_once 'database.inc.php';
    
    $db = connect();
    
    $path = $_GET['path'];
    $rev_id = $_GET['rev_id'];
    
    $old_rev_id = @$_GET['old_rev_id'];
    if ($old_rev_id == $rev_id)
        $old_rev_id = null;
    
    $rev_list = lookup_revisions($db);
    
    disconnect($db);
    
    function lookup_revisions($db)
    {
        $query = "SELECT * FROM revision ORDER BY rev_id";
        $result = pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        
        $arr = pg_fetch_all($result);
        
        if (!$arr)
            $arr = array();
        return $arr;
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
    -->
    </style>

    <base target="_top">
</head>

<body>
    <table width="100%">
        <tr>
<?php
    foreach ($rev_list as $item)
    {
        if ($item['rev_id'] == $rev_id)
        {
?>
            <th><a name="current"><?php echo substr($item['time'], 0, 10) ?></a></th>
<?php
        }
        else
        {
?>
            <td><a href="browse?rev_id=<?php echo $item['rev_id'] ?><?php if ($old_rev_id) echo '&old_rev_id=' . $old_rev_id; ?>&path=<?php echo $path ?>"><?php echo substr($item['time'], 0, 10) ?></a></td>
<?php
        }
    }
?>
        </tr>
        <tr>
<?php
    foreach ($rev_list as $item)
    {
        if ($item['rev_id'] == $rev_id and !$old_rev_id)
        {
?>
            <td>(no diffs)</td>
<?php
        }
        else if ($item['rev_id'] == $rev_id)
        {
?>
            <td><a href="browse?rev_id=<?php echo $rev_id ?>&path=<?php echo $path ?>">(no diffs)</a></td>
<?php
        }
        else if ($item['rev_id'] == $old_rev_id)
        {
?>
            <th><?php echo substr($item['time'], 0, 10) ?></th>
<?php
        }
        else
        {
?>
            <td><a href="browse?rev_id=<?php echo $rev_id ?>&old_rev_id=<?php echo $item['rev_id'] ?>&path=<?php echo $path ?>"><?php echo substr($item['time'], 0, 10) ?></a></td>
<?php
        }
    }
?>
        </tr>
    </table>
</body>
</html>
