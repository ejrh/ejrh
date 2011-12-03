<?php
    /*
     * This script fixes the md5, size, children and descendants information
     * for all directories in the filesys database.
     */

    require_once 'database.inc.php';
    
    set_time_limit(0);
    
    $rev_id = max(@$_GET['rev_id'], @$_GET['rev'], @$_GET['id']);
    
    $db = connect();
    
    /* Plan some common queries. */
    prepare(__FILE__, __LINE__, 'get_revision',
        "SELECT
            id,
            name,
            rev_id
        FROM
            revision
            JOIN (directory NATURAL JOIN file) ON (root_id = id)
        WHERE
            name ='/'
            AND rev_id >= $1
        ORDER BY
            rev_id", $db);
    
    prepare(__FILE__, __LINE__, 'get_children',
        "SELECT
            id,
            name,
            NULLIF(size, -1) AS size,
            NULLIF(modified, 'epoch'::timestamp) AS modified,
            md5,
            children,
            descendants
        FROM
            file_in_dir
            JOIN file ON (file_id = id)
            NATURAL LEFT JOIN directory
        WHERE
            dir_id = $1
        ORDER BY name", $db);
    
    prepare(__FILE__, __LINE__, 'get_dir_info',
        "SELECT size, children, descendants, md5 FROM file NATURAL JOIN directory WHERE id = $1", $db);
    
    prepare(__FILE__, __LINE__, 'find_matching_dir',
        "SELECT id FROM directory NATURAL JOIN file WHERE md5 = $1", $db);
    
    prepare(__FILE__, __LINE__, 'update_file_in_dir',
        "UPDATE file_in_dir SET file_id = $2 WHERE file_id = $1", $db);
    
    prepare(__FILE__, __LINE__, 'delete_file',
        "DELETE FROM file WHERE id = $1", $db);
    
    prepare(__FILE__, __LINE__, 'delete_file_in_dir',
        "DELETE FROM file_in_dir WHERE file_id = $1 AND dir_id = $2", $db);
    
    prepare(__FILE__, __LINE__, 'update_file',
        "UPDATE file SET md5 = $2, size = $3 WHERE id = $1", $db);
    
    prepare(__FILE__, __LINE__, 'update_dir',
        "UPDATE directory SET children = $2, descendants = $3 WHERE id = $1", $db);
    
    /* Fix the directories. */
    begin($db);
    
    $dir_list = array();
    
    $result = query(__FILE__, __LINE__, 'get_revision', array($rev_id ? $rev_id : 0), $db);
    
    $arr = pg_fetch_all($result);
    commit($db);
    foreach ($arr as $item)
    {
        echo "<strong>Fixing revision {$item['rev_id']} directories:</strong><br />\n";
        flush();
        begin($db);
        $num_dirs = 0;
        $num_files = 0;
        fix_directory($item['id'], $item['name'], '/', $db);
        commit($db);
        echo "<strong>Fixed ($num_dirs new directories, $num_files new files).</strong><br />\n";
        echo "<br />\n";
        flush();
    }
    
    /* Done. */
    disconnect($db);

    function fix_directory($id, $name, $full_name, $db)
    {
        global $config;
        
        //TODO: shouldn't be global, should be passed by ref or something
        global $dir_list;
        
        global $num_files, $num_dirs;
        
        $stats = array();
        $stats['id'] = $id;
        $stats['name'] = $name;
        $stats['children'] = 0;
        $stats['descendants'] = 0;
        $stats['size'] = 0;
        
        $str = "$name\n";
        
        /* Get a list of children. */
        $result = query(__FILE__, __LINE__, 'get_children', array($id), $db);
        
        $arr = pg_fetch_all($result);
        if ($arr)
        {
            foreach ($arr as $item)
            {
                if ($full_name == '/')
                    $new_full_name = $full_name . $item['name'];
                else
                    $new_full_name = $full_name . '/' . $item['name'];
                
                /* Test to see if this item should be ignored. */
                /*if (ereg($config['ignore_regex'], $new_full_name)
                    or eregi($config['ignore_regex_i'], $new_full_name))
                {
                    echo 'Ignoring: ', $new_full_name, "<br />\n";
                    flush();
                    
                    query(__FILE__, __LINE__, 'delete_file_in_dir', array($item['id'], $id), $db);
                    continue;
                }*/
                
                if ($item['descendants'] != null)
                {
                    if (!@$dir_list[$item['id']])
                    {
                        $item = fix_directory($item['id'], $item['name'], $new_full_name, $db);
                        $num_dirs++;
                    }
                    
                    $stats['descendants'] += $item['descendants'];
                    $str .= "{$item['name']}\t{$item['md5']}\n";
                }
                else
                {
                    $str .= "{$item['name']}\t{$item['size']}\t{$item['modified']}\n";
                }
                
                $stats['size'] += $item['size'];
                $stats['children']++;
                $stats['descendants']++;
                
                $num_files++;
            }
        }
        
        $stats['md5'] = md5($str);
        
        $result = query(__FILE__, __LINE__, 'get_dir_info', array($id), $db);
        
        $arr = pg_fetch_all($result);
        $old_stats = $arr[0];
        
        if ($old_stats['md5'] != $stats['md5'])
        {
            $result = query(__FILE__, __LINE__, 'find_matching_dir', array($stats['md5']), $db);
            
            $arr = pg_fetch_all($result);
            $item = @$arr[0];
            
            if ($item)
            {
                echo "[{$stats['id']}] {$stats['name']} (<font color=\"red\">duplicate of [{$item['id']}]</font>.)<br />";
                flush();
                
                $low_id = min($item['id'], $stats['id']);
                $high_id = max($item['id'], $stats['id']);
                
                query(__FILE__, __LINE__, 'update_file_in_dir', array($high_id, $low_id), $db);
            
                query(__FILE__, __LINE__, 'delete_file', array($high_id), $db);
                
                unset($dir_list[$low_id]);
                unset($dir_list[$high_id]);
                $id = $low_id;
            }
        }
        
        if ($old_stats['md5'] != $stats['md5']
            or $old_stats['size'] != $stats['size']
            or $old_stats['children'] != $stats['children']
            or $old_stats['descendants'] != $stats['descendants'])
        {
            echo "[{$stats['id']}] {$stats['name']} (";
            
            if ($old_stats['md5'] != $stats['md5'])
                echo " md5e {$old_stats['md5']} --> {$stats['md5']}";
            
            if ($old_stats['size'] != $stats['size'])
                echo " size {$old_stats['size']} --> {$stats['size']}";
                
            if ($old_stats['children'] != $stats['children'])
                echo " children {$old_stats['children']} --> {$stats['children']}";
            
            if ($old_stats['descendants'] != $stats['descendants'])
                echo " descendants {$old_stats['descendants']} --> {$stats['descendants']}";
            
            echo ")<br />";
            flush();
            
            query(__FILE__, __LINE__, 'update_file', array($id, $stats['md5'], $stats['size']), $db);
            
            query(__FILE__, __LINE__, 'update_dir', array($id, $stats['children'], $stats['descendants']), $db);
        }
        
        $dir_list[$id] = 1;
        return $stats;
    }
?>
