<?php
    require_once 'database.inc.php';
    
    $db = connect();
    
    //$path = @$_SERVER['PATH_INFO'];
    $path = $_GET['path'];
    
    $rev_id = @$_GET['rev_id'];
    if (!$rev_id)
        $rev_id = lookup_latest_rev($db);
    
    $path_ids = lookup_path($db, $rev_id, $path);
    
    $root_id = $path_ids['id0'];
    $dir_id = $path_ids['id' . (count($path_ids) - 2)];
    
    $old_rev_id = @$_GET['old_rev_id'];
    if ($old_rev_id == $rev_id)
        $old_rev_id = null;
    
    if ($old_rev_id)
    {
        $old_path_ids = lookup_path($db, $old_rev_id, $path);
    
        $old_root_id = $old_path_ids['id0'];
        $old_dir_id = $old_path_ids['id' . (count($old_path_ids) - 2)];
    }
    
    pg_close($db);
    
    /* If rev_id was specified then this is a unique request and can be
       permanently cached. */
    if (@$_GET['rev_id'])
    {
        $expiry_date = 2000000000;
        header('Expires: ' . strftime('%a, %d %b %Y %T GMT', $expiry_date));
    }

    function lookup_latest_rev($db)
    {
        $query = "SELECT MAX(rev_id) AS rev_id FROM revision";
        $result = pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
        
        $arr = pg_fetch_all($result);
        
        return $arr[0]['rev_id'];
    }

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
?>
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html 
 PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
 "DTD/xhtml1-frameset.dtd">
<html>
<head>
    <title><?php echo $path ?></title>
</head>

<frameset rows="72, *">
    <frame src="rev-list?rev_id=<?php echo $rev_id ?><?php if ($old_rev_id) echo '&old_rev_id=' . $old_rev_id . '&old_dir_id=' . $old_dir_id ?>&path=<?php echo $path ?>#current">
    <frameset cols="30%, 80%">
        <frame src="dir-list?rev_id=<?php echo $rev_id ?><?php if ($old_rev_id) echo '&old_rev_id=' . $old_rev_id . '&old_dir_id=' . $old_dir_id ?>&root_id=<?php echo $root_id ?>&dir_id=<?php echo $dir_id ?>&path=<?php echo $path ?>#current">
        <frame src="file-list?rev_id=<?php echo $rev_id ?><?php if ($old_rev_id) echo '&old_rev_id=' . $old_rev_id . '&old_dir_id=' . $old_dir_id ?>&dir_id=<?php echo $dir_id ?>&path=<?php echo $path ?>">
    </frameset>
</frameset>
</html>
