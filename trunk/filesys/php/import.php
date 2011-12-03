<?php
    /*
     * UPDATE ALGORITHM
     *
     *   1. Starting at the virtual root '/':
     *
     *   2. If this item is a directory, then get a list of its children:
     *       a. For each child item, get its size and modification date; or, if it's
     *          a directory, recur from 2.
     *       b. Combine each child item's stats into the stats for this item.
     *   3. If this item is a directory, look for an identical existing directory
     *      with a matching md5.
     *       a. If there is one, just return that existing directory.
     *   4. If this item is a file, look for an identical existing file
     *      with matching name/size/modification time.
     *       a. If there is one, just return the existing file.
     *   5. Create a new 'files' tuple.
     *   6. If it's a directory, create a new 'directories' tuple too.
     *   7. Return the item.
     */
    
    require_once 'database.inc.php';
    require_once 'image.inc.php';
    
    $root_path = @$_GET['root_path'] ? $_GET['root_path'] : '';
    $root_name = $root_path ? $root_path : '/';
    if ($root_name != '/' && eregi('/$', $root_name))
        $root_name = substr($root_name, 0, strlen($root_name) - 1);
    import($root_path, $root_name);
    exit;
    
    function import($root_path, $root_name)
    {
        global $prefix;
        $prefix = '';
        
        //For recovery:
        //$prefix = 'R--';
        
        set_time_limit(0);
        
        $db = connect();
        
        /* Prepare some common queries. */
        prepare(__FILE__, __LINE__, 'reset_sequences',
            "SELECT setval('file_id_seq', (SELECT MAX(id) FROM file)),
                         setval('image_id_seq', (SELECT MAX(id) FROM image))", $db);
        
        prepare(__FILE__, __LINE__, 'insert_revision',
            "INSERT INTO revision (rev_id, time, root_id)
                  VALUES ((SELECT COALESCE(MAX(rev_id),0)+1 FROM revision), NOW(), $1)", $db);
        
        prepare(__FILE__, __LINE__, 'find_duplicates',
            "SELECT
                id
            FROM
                file
            WHERE
                name = $1 and size = $2
                AND EXTRACT(MINUTE FROM modified) = EXTRACT(MINUTE FROM $3::timestamp)
                AND EXTRACT(SECOND FROM modified) = EXTRACT(SECOND FROM $3::timestamp)
                AND modified != 'epoch'::timestamp AND modified IS NOT NULL AND modified != $3
            ORDER BY
                id ASC", $db);
        
        prepare(__FILE__, __LINE__, 'update_duplicates',
            "UPDATE file SET modified = $2 WHERE modified != $2::timestamp AND id = $1", $db);
        
        prepare(__FILE__, __LINE__, 'find_image_file',
            "SELECT file_id FROM file_is_image WHERE file_id = $1", $db);
        
        prepare(__FILE__, __LINE__, 'add_image_file',
            "INSERT INTO file_is_image (file_id, image_id) VALUES ($1, $2)", $db);
        
        prepare(__FILE__, __LINE__, 'find_matching_dir',
            "SELECT id,md5 FROM file WHERE md5 = $1 AND modified IS NULL", $db);
        
        prepare(__FILE__, __LINE__, 'find_matching_file',
            "SELECT
                id,
                md5
            FROM
                file
            WHERE
                name = $1
                AND size = $2
                AND modified = $3", $db);
        
        prepare(__FILE__, __LINE__, 'update_md5',
            "UPDATE file SET md5 = $2 WHERE id = $1", $db);
        
        prepare(__FILE__, __LINE__, 'insert_file',
            "INSERT INTO file (name, size, modified, md5)
                VALUES ($1, $2, $3, $4)
            RETURNING id", $db);
            
        prepare(__FILE__, __LINE__, 'insert_dir',
            "INSERT INTO directory (id, children, descendants)
                VALUES ($1, $2, $3)", $db);
        
        prepare(__FILE__, __LINE__, 'insert_drive',
            "INSERT INTO drive (id, free_space, total_space)
                VALUES ($1, $2, $3)", $db);
        
        prepare(__FILE__, __LINE__, 'insert_file_in_dir',
            "INSERT INTO file_in_dir (file_id, dir_id)
                VALUES ($1, $2)", $db);
        
        init_import_image($db);
        
        /* Connect to remote drives. */
        ob_start();
        system("NET USE V: \\\\chrysophylax\\f /USER:remote remote");
        system("NET USE W: \\\\chrysophylax\\cdrive /USER:remote remote");
        system("NET USE X: \\\\chrysophylax\\data /USER:remote remote");
        system("NET USE Y: \\\\chrysophylax\\films /USER:remote remote");
        system("NET USE Z: \\\\chrysophylax\\zdrive /USER:remote remote");
        ob_end_clean();
        
        echo "Creating new file system revision...<br />\n";
        flush();
        
        /* Import the data. */
        begin($db);
        
        /* Reset the sequences for files and images. */
        if ($root_path == '')
            query(__FILE__, __LINE__, 'reset_sequences', array(), $db);
        
        $root_item = array('name' => $root_name, 'size' => null, 'modified' => null, 'children' => 0, 'descendants' => 0);
        if ($root_name == '/' || eregi('^/[A-Z]:(/|())$', $root_name))
            $root_item['is_drive'] = true;
        
        if ($root_item)
        {
            $root_item = import_item($root_item, $root_path, $db);
            $root_id = $root_item['id'];
            if ($root_name == '/')
                make_revision($db, $root_id);
        }
        commit($db);
        
        echo "<br /><br />\n";
        
        /* Done. */
        disconnect($db);
    }

    function make_revision($db, $root_id)
    {
        /* Create a new revision. */
        query(__FILE__, __LINE__, 'insert_revision', array($root_id), $db);
    }

    function get_dir_contents($dirname)
    {
        global $prefix;
        
        /* Should be 0 during winter; 3600 during summer. */
        $dls_offset = 0;
        
        $rv = array();
        
        if ($dirname == '')
        {
            for ($i = 'A'; $i <= 'Z'; $i = chr(ord($i)+1))
            {
                if (is_dir("$i:"))
                {
                    $rv["$i:"] = array
                    (
                        'fs_name' => "$i:",
                        'orig_name' => "$i:",
                        'name' => "$i:",
                        'size' => null,
                        'modified' => null,
                        'children' => 0,
                        'descendants' => 0,
                        'is_drive' => true,
                    );
                }
            }
        }
        else
        {
            $dirname = substr($dirname, 1);
            
            $dir = @opendir($dirname);
            if ($dir)
            {
                while (($file = readdir($dir)) !== false)
                {
                    if ($file != '.' and $file != '..')
                    {
                        $modified = strftime('%Y-%m-%d %H:%M:%S', filemtime($dirname . '/' . $file)-$dls_offset);
                        $size = sprintf("%u", filesize($dirname . '/' . $file));
                        
                        if ($modified === false)
                            $modified = null;
                        if ($size === false)
                            $size = null;
                        
                        $rv[$file] = array
                        (
                            'fs_name' => $file,
                            'orig_name' => mb_convert_encoding($file, "UTF-8"),
                            'name' => (is_dir($dirname . '/' . $file) ? '' : $prefix) . mb_convert_encoding($file, "UTF-8"),
                            'size' => $size,
                            'modified' => $modified,
                            'children' => is_dir($dirname . '/' . $file) ? 0 : null,
                            'descendants' => is_dir($dirname . '/' . $file) ? 0 : null,
                            'is_drive' => false,
                        );
                    }
                }
            }
            else
            {
                echo "Failed reading directory $dirname<br />";
                return false;
            }
        }
        
        sort($rv);
        return $rv;
    }

    /*
     * Find files that have the same name and size and similar modification
     * time (as if they had been imported in a different time zone), and
     * replace them with this item.  This will involve recycling the lower
     * ID of an existing file; the recycled ID is returned for use by the
     * newly imported item.
     */
    function process_duplicates($db, $item)
    {
        $name2 = $item['name'];
        $size2 = $item['size'] !== null ? $item['size'] : '-1';
        $modified2 = $item['modified'];
        
        $result = query(__FILE__, __LINE__, 'find_duplicates', array($name2, $size2, $modified2), $db);
        
        $arr = pg_fetch_all($result);
        if (!@$arr[0])
        {
            return null;
        }
        
        if (count($arr) > 1)
        {
            echo "More than one duplicate found!\n";
            print_r(array($name2, $size2, $modified2));
            exit;
        }
        
        $result = query(__FILE__, __LINE__, 'update_duplicates', array($arr[0]['id'], $modified2), $db);
        
        return $arr[0]['id'];
    }

    /*
     * Do special processing on an item.  For example, import an image if it's
     * not already know to the filesys database.
     */
    function process_special($db, $full_name, $item)
    {
        if (eregi('.+\.(gif|png|jpg|jpeg|jpe)$', $item['name']))
        {
            $filename = substr($full_name, 1);
            $image_id = import_image($db, $filename, $item['md5']);
            
            if ($image_id)
            {
                $result = query(__FILE__, __LINE__, 'find_image_file', array($item['id']), $db);
                
                $arr = pg_fetch_all($result);
                if (!@$arr[0])
                {
                    query(__FILE__, __LINE__, 'add_image_file', array($item['id'], $image_id), $db);
                }
            }
        }
    }

    /* Commit the changes so far, just in case this update gets
       interrupted after it has done a lot of expensive work. */
    function commit_if_necessary($db)
    {
        global $config;
        
        static $last_time;
        
        if (time() > @$last_time + $config['commit_interval'])
        {
            commit($db);
            begin($db);
            
            $last_time = time();
        }
    }
    
    /*
     * Import a directory.
     *
     * $dir_id is the id of the old directory in 'import'.
     * $full_name is the full name of this directory.
     * $db is the PostgreSQL database connection.
     *
     * Returns the id of the new (or pre-existing) entry for this directory.
     */
    function import_item($this_item, $full_name, $db)
    {
        global $config;
        
        commit_if_necessary($db);
        
        /* Test to see if this item should be ignored. */
        if (ereg($config['ignore_regex'], $full_name)
            or eregi($config['ignore_regex_i'], $full_name))
        {
            echo 'Ignoring: ', $full_name, "<br />\n";
            flush();
            return null;
        }
        
        $epoch = 'epoch';
        
        $name2 = $this_item['name'];
        $size2 = $this_item['size'] !== null ? $this_item['size'] : -1;
        $modified2 = $this_item['descendants'] !== null ? null : ($this_item['modified'] ? $this_item['modified'] : $epoch);
        
        if ($this_item['descendants'] !== null)
        {
            /* Process child items first. */
            $child_list = get_dir_contents($full_name);
            if ($child_list === false)
            {
                $this_item['children'] = null;
                $this_item['descendants'] = null;
                $this_item['size'] = null;
                $size2 = '-1';
                $modified2 = $epoch;
            }
            else
            {
                $child_ids = array();
                $md5str = "{$this_item['name']}\n";
                $children = 0;
                $descendants = 0;
                $size = 0;
                
                foreach ($child_list as $item)
                {
                    $item = import_item($item, $full_name . '/' . $item['fs_name'], $db);
                    if ($item === null)
                        continue;
                    
                    $child_ids[] = $item['id'];
                    if ($item['descendants'] === null)
                    {
                        $md5str .= "{$item['name']}\t{$item['size']}\t{$item['modified']}\n";
                        $descendants += 1;
                        $size += $item['size'];
                    }
                    else
                    {
                        $md5str .= "{$item['name']}\t{$item['md5']}\n";
                        $children += 1;
                        $descendants += $item['descendants'] + 1;
                        $size += $item['size'];
                    }
                }
                
                $this_item['md5'] = md5($md5str);
                $this_item['children'] = $children;
                $this_item['descendants'] = $descendants;
                $this_item['size'] = $size;
            }
        }
        
        /* If it's a directory, then look for a matching existing directory. */
        if ($this_item['descendants'] !== null)
        {
            $result = query(__FILE__, __LINE__, 'find_matching_dir', array($this_item['md5']), $db);
            
            $arr = pg_fetch_all($result);
            $copy_id = @$arr[0]['id'];
            $copy_md5 = @$arr[0]['md5'];
            
            if ($copy_id)
            {
                $this_item['id'] = $copy_id;
                $this_item['md5'] = $copy_md5;
                return $this_item;
            }
        }
        /* Or if it's a file, look for a matching file. */
        else
        {
            if ($this_item['modified'])
            {
                $dup_id = process_duplicates($db, $this_item);
            }
            
            $result = query(__FILE__, __LINE__, 'find_matching_file', array($name2, $size2, $modified2), $db);
            
            $arr = pg_fetch_all($result);
            $copy_id = @$arr[0]['id'];
            $old_md5 = @$arr[0]['md5'];
            
            if (!$old_md5)
            {
                $this_item['md5'] = @md5_file(substr($full_name, 1));
                
                if ($this_item['md5'] === false)
                    $this_item['md5'] = null;
            }
            else
            {
                $this_item['md5'] = $old_md5;
            }
            
            if ($copy_id)
            {
                if ($this_item['md5'] != $old_md5)
                {
                    $result = query(__FILE__, __LINE__, 'update_md5', array($copy_id, $this_item['md5']), $db);
                }
                
                $this_item['id'] = $copy_id;
                return $this_item;
            }
        }
        
        /* It's a new file or directory then. */
        echo "$full_name<br />\n";
        flush();
        
        /* Insert the item. */
        $result = query(__FILE__, __LINE__, 'insert_file', array($name2, $size2, $modified2, $this_item['md5']), $db);
        
        $arr = pg_fetch_all($result);
        $new_id = $arr[0]['id'];
        $this_item['id'] = $new_id;
        
        /* If it was a file, we're done. */
        if ($this_item['descendants'] === null)
        {
            process_special($db, $full_name, $this_item);
            
            return $this_item;
        }
        
        /* Add a tuple to 'directories'. */
        query(__FILE__, __LINE__, 'insert_dir', array($new_id, $this_item['children'], $this_item['descendants']), $db);
        
        /* If it's a drive, add a tuple to 'drive'. */
        if (@$this_item['is_drive'])
        {
            $true_name = substr($full_name, 1);
            
            $free_space = @disk_free_space($true_name);
            if (!@$free_space && $free_space !== 0)
                $free_space = null;
            
            $total_space = @disk_total_space($true_name);
            if (!@$total_space && $total_space !== 0)
                $total_space = null;
            
            query(__FILE__, __LINE__, 'insert_drive', array($new_id, $free_space, $total_space), $db);
        }
        
        /* Finally add each child item to this directory. */
        foreach ($child_ids as $id)
        {
            /* Insert an entry into 'file_in_dir' for this item. */
            query(__FILE__, __LINE__, 'insert_file_in_dir', array($id, $new_id), $db);
        }
        
        return $this_item;
    }
?>
