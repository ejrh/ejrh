<?php
    /*
     * review-deleted.php
     *
     * Copyright (C) 2004-2006 Edmund Horner.
     */
    
    require_once 'config.inc.php';
    require_once 'database.inc.php';
    
    $db = connect();
    
    if ($_SERVER['REQUEST_METHOD'] == 'POST' and @$_GET['delete'])
    {
        begin($db);
        $delete = $_GET['delete'];
        $duplicate = @$_GET['duplicate'];
        
        $query = "SELECT make_text_path(all_paths) AS path FROM all_paths($delete) WHERE all_paths[1] = (SELECT root_id FROM revision ORDER BY rev_id DESC LIMIT 1)";
        $result = pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        $arr = pg_fetch_all($result);
        
        foreach ($arr as $row)
        {
            $path = substr($row['path'], 1);
            
            @unlink ($path);
        }
        
        if (!$duplicate)
            $query = "UPDATE deleted SET confirmed = TRUE WHERE id = {$delete} AND duplicate_of IS NULL";
        else
            $query = "UPDATE deleted SET confirmed = TRUE WHERE id = {$delete} AND duplicate_of = {$duplicate}";
        pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        commit($db);
        
        header('Location: review-deleted');
        exit;
    }
    else if ($_SERVER['REQUEST_METHOD'] == 'POST' and @$_GET['undelete'])
    {
        begin($db);
        $undelete = $_GET['undelete'];
        $duplicate = @$_GET['duplicate'];
        if (!$duplicate)
            $query = "DELETE FROM deleted WHERE id = {$undelete} AND duplicate_of IS NULL";
        else
            $query = "DELETE FROM deleted WHERE id = {$undelete} AND duplicate_of = {$duplicate}";
        pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        commit($db);
        
        header('Location: review-deleted');
        exit;
    }
    else if ($_SERVER['REQUEST_METHOD'] == 'POST' and @$_GET['swap'])
    {
        begin($db);
        $swap = $_GET['swap'];
        $duplicate = @$_GET['duplicate'];
        $query = "UPDATE deleted SET id = $duplicate, duplicate_of = $swap WHERE id = $swap AND duplicate_of = $duplicate";
        pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        commit($db);
        
        header('Location: review-deleted');
        exit;
    }
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
</head>

<body>

<?php
    $query = "SELECT COUNT(*) FROM deleted WHERE NOT confirmed";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    $arr = pg_fetch_all($result);
    $count = $arr[0]['count'];
    
    $query = "SELECT
                  fii1.image_id AS image_id1,
                  fii2.image_id AS image_id2,
                  d.id AS deleted,
                  d.duplicate_of AS duplicate_of
              FROM
                  deleted AS d
                  JOIN file_is_image AS fii1 ON d.id = fii1.file_id
                  JOIN file_is_image AS fii2 ON d.duplicate_of = fii2.file_id
              WHERE
                  NOT d.confirmed
              LIMIT 1";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    $arr = pg_fetch_all($result);
    $id1 = $arr[0]['image_id1'];
    $id2 = $arr[0]['image_id2'];
    $deleted = $arr[0]['deleted'];
    $duplicate_of = $arr[0]['duplicate_of'];
?>
    <table>
        <tr>
            <td><?php echo $count ?> remaining</td>
        </tr>
        <tr>
            <td>
                <form method="post" action="review-deleted?delete=<?php echo $deleted ?>&duplicate=<?php echo $duplicate_of ?>">
                    <input type="submit" value="Confirm" />
                </form>
            </td>
            <td>
                <form method="post" action="review-deleted?undelete=<?php echo $deleted ?>&duplicate=<?php echo $duplicate_of ?>">
                    <input type="submit" value="Cancel" />
                </form>
            </td>
            <td>
                <form method="post" action="review-deleted?swap=<?php echo $deleted ?>&duplicate=<?php echo $duplicate_of ?>">
                    <input type="submit" value="Swap" />
                </form>
            </td>
        </tr>
        <tr>
            <td><img src="show?id=<?php echo $id1 ?>&full" /></td>
            <td><img src="show?id=<?php echo $id2 ?>&full" /></td>
        </tr>
    </table>
</body>
</html>
