<?php
    require_once 'config.inc.php';

    function connect()
    {
        global $config;
        static $seed = '';
        
        $db = pg_pconnect("host={$config['dbhost']} $seed dbname={$config['dbname']} user={$config['dbuser']} password={$config['dbpassword']}")
            or die (pg_last_error());
        
        $query = "SET TRANSACTION ISOLATION LEVEL READ COMMITTED";
        pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error($db), $query, $db);
        
        /* Load extra config information. */
        load_config($db);
        
        $seed .= ' ';
        return $db;
    }
    
    function load_config($db)
    {
        global $config;
        
        $query = "SELECT * FROM config";
        $result = @pg_query($db, $query);
        
        $row = @pg_fetch_array($result);
        
        if (!$row)
            return;
        
        for ($i = 0; $i < pg_num_fields($result); $i++)
        {
            $fn = pg_field_name($result, $i);
            $config[$fn] = $row[$fn];
        }
    }

    function disconnect($db)
    {
        pg_close($db);
    }

    function begin($db)
    {
        $query = "BEGIN";
        pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error($db), $query, $db);
    }

    function commit($db)
    {
        $query = "COMMIT";
        pg_query($db, $query)
            or error(__FILE__, __LINE__, pg_last_error($db), $query, $db);
    }

    function rollback($db, $query = "ROLLBACK")
    {
        pg_query($db, "ROLLBACK")
            or error(__FILE__, __LINE__, pg_last_error($db), $query);
    }

    function error($file, $line, $msg, $query = '', $db = null)
    {
        if ($db)
            rollback($db, $query);
        echo $file . ':' . $line . ': ' . $msg . '<br />';
        
        if (is_string($query))
        {
            echo "<pre>$query</pre>\n";
        }
        else
        {
            list($plan, $args) = $query;
            
            echo "<pre>$plan</pre>\n";
            
            for ($i = 0; $i < count($args); $i++)
            {
                echo '<pre>$', $i+1, ' => ', $args[$i], "</pre>\n";
            }
        }
        
        die('Operation aborted');
    }
    
    function prepare($file, $line, $query_name, $query, $db)
    {
        global $plans;
        global $plan_stats;
        
        if (@!$plans)
        {
            $plans = array();
            $plan_stats = array();
        }
        
        $plans[$query_name] = $query;
        $plan_stats[$query_name] = 0;
        
        @pg_query($db, "DEALLOCATE " . $query_name);
        
        pg_prepare($db, $query_name, "/* $query_name */ $query")
            or error($file, $line, pg_last_error($db), "Prepare $query_name: " . $plans[$query_name], $db);
    }
    
    function query($file, $line, $query_name, $args, $db)
    {
        global $plans;
        global $plan_stats;
        
        $result = pg_execute($db, $query_name, $args);
        
        if ($result === false)
            error($file, $line, pg_last_error($db), array("Execute $query_name: " . $plans[$query_name], $args), $db);
        
        $plan_stats[$query_name]++;
        
        /*if ($plan_stats[$query_name] % 1000 == 0)
        {
            echo "Query $query_name executed {$plan_stats[$query_name]} times thus far...<br />\n";
            flush();
        }*/
        
        return $result;
    }
?>
