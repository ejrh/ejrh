<?php
    /*
     * image.inc.php
     *
     * Image handling routines for the filesys application (originally from
     * the imagedb).
     */
    
    require_once 'config.inc.php';
    require_once 'database.inc.php';

    function init_import_image($db)
    {
        prepare(__FILE__, __LINE__, 'find_image_dups',
            "SELECT
               i.id,
               t.id AS tid
            FROM
                file AS f
                JOIN file_is_image ON file_id = f.id
                JOIN image AS i ON image_id = i.id
                LEFT JOIN thumbnail AS t ON i.id = t.id
            WHERE
                f.md5 = $1
            ORDER BY
                f.id DESC
            LIMIT 1", $db);
        
        prepare(__FILE__, __LINE__, 'insert_image',
            "INSERT INTO image (width, height,
                    ravg, gavg, bavg, savg, lavg,
                    rsd, gsd, bsd, ssd, lsd,
                    rlavg, glavg, blavg)
                VALUES ($1, $2,
                    $3, $4, $5, $6, $7,
                    $8, $9, $10, $11, $12,
                    $13, $14, $15)
            RETURNING id", $db);
        
        /* Something in PHP / PostgreSQL is horribly wrong, and this is
           the only way to get a bytea into the database through a
           prepared statement. */
        prepare(__FILE__, __LINE__, 'insert_thumbnail',
            "INSERT INTO thumbnail (id, thumbnail) VALUES ($1, decode(replace(replace($2::text, E'\\'\\'', E'\\''), E'\\\\\\\\', E'\\\\'), 'escape'))", $db);
    }

    /*
     * Imports the image in $filename, creating a new 'images' tuple if
     * necessary, otherwise using an existing matching tuple.  Returns
     * the id of the tuple.
     */
    function import_image($db, $filename, $md5, $callback = false)
    {
        global $ravg, $gavg, $bavg, $savg, $lavg;
        global $rsd, $gsd, $bsd, $ssd, $lsd;
        global $rlavg, $glavg, $blavg;
        
        $short_filename = substr(strrchr($filename, '/'), 1);
        $dirname = substr($filename, 0, strrpos($filename, '/')+1);
        
        if ($callback)
        {
            call_user_func($callback, $short_filename, $dirname);
        }
        
        /* Look for existing images in the DB with matching md5, etc.
           If a match is found, just re that one. */
        if (!$md5)
            $md5 = @md5_file($filename);
        if (!$md5)
            return false;
        
        $result = query(__FILE__, __LINE__, 'find_image_dups', array($md5), $db);
        
        $arr = pg_fetch_all($result);
        if (@$arr[0])
        {
            $image_id = $arr[0]['id'];
            
            /* If the existing image already has a thumbnail, then just return it. */
            if ($arr[0]['tid'])
                return $image_id;
        }
        
        /* Load the image. */
        if (eregi('\.(png)$', $filename))
        {
            $img = @imagecreatefrompng($filename); 
        }
        else if (eregi('\.(jpg|jpeg|jpe)$', $filename))
        {
            $img = @imagecreatefromjpeg($filename); 
        }
        else if (eregi('\.(gif)$', $filename))
        {
            $img = @imagecreatefromgif($filename); 
        }
        else
        {
            return false;
        }
        
        if (!$img)
        {
            return false;
        }
        
        $width = imagesx($img);
        $height = imagesy($img);
        
        $dw = $width;
        $dh = $height;
        if ($dw > 64)
        {
            $dh *= (64/$dw);
            $dw = 64;
        }
        if ($dh > 64)
        {
            $dw *= (64/$dh);
            $dh = 64;
        }
        if ($dw < 1)
        {
            $dw = 1;
        }
        if ($dh < 1)
        {
            $dh = 1;
        }
        
        /* If there is no existing image, analyze this one. */
        if (!@$image_id)
        {
            $xstep = 1;
            $ystep = 1;
            
            while ($width/$xstep >= 1024)
                $xstep++;
            while ($height/$ystep >= 1024)
                $ystep++;
            
            /* Initialise stats. */
            $r = 0;
            $g = 0;
            $b = 0;
            $s = 0;
            $l = 0;
            
            $r2 = 0;
            $g2 = 0;
            $b2 = 0;
            $s2 = 0;
            $l2 = 0;
            
            if ($callback)
            {
                call_user_func($callback, $short_filename, $dirname, 0);
            }
            
            if (imageistruecolor($img))
            {
                for ($yl = 0; $yl < imagesy($img); $yl += $ystep)
                {
                    for ($xl = 0; $xl < imagesx($img); $xl += $xstep)
                    {
                        $rgb = imagecolorat($img, $xl, $yl);
                        
                        $r1 = (($rgb >> 16) & 0xFF) / 255;
                        $g1 = (($rgb >> 8) & 0xFF) / 255;
                        $b1 = ($rgb & 0xFF) / 255;
                        $s1 = @(1 - (min($r1,$g1,$b1) / max($r1,$g1,$b1)));
                        $l1 = ($r1 + $g1 + $b1) / 3;
                        
                        $r += $r1;
                        $g += $g1;
                        $b += $b1;
                        $s += $s1;
                        $l += $l1;
                        
                        $r2 += $r1 * $r1;
                        $g2 += $g1 * $g1;
                        $b2 += $b1 * $b1;
                        $s2 += $s1 * $s1;
                        $l2 += $l1 * $l1;
                    }
                    
                    if ($callback)
                    {
                        call_user_func($callback, $short_filename, $dirname, $yl/imagesy($img));
                    }
                }
            }
            else
            {
                $colours = array();
                
                for ($yl = 0; $yl < imagesy($img); $yl += $ystep)
                {
                    for ($xl = 0; $xl < imagesx($img); $xl += $xstep)
                    {
                        $c = imagecolorat($img, $xl, $yl);
                        $colours[$c] = @$colours[$c] + 1;
                    }
                    
                    if ($callback)
                    {
                        call_user_func($callback, $short_filename, $dirname, $yl/imagesy($img));
                    }
                }
                
                foreach ($colours as $c => $n)
                {
                    $cols = imagecolorsforindex($img, $c);
                    
                    $r1 = ($cols['red'] / 255);
                    $g1 = ($cols['green'] / 255);
                    $b1 = ($cols['blue'] / 255);
                    
                    $r += $r1 * $n;
                    $g += $g1 * $n;
                    $b += $b1 * $n;
                    $s += @(1 - (min($r1,$g1,$b1) / max($r1,$g1,$b1))) * $n;
                    $l += (($r1 + $g1 + $b1) / 3) * $n;
                    
                    $r2 += $r1 * $r1 * $n;
                    $g2 += $g1 * $g1 * $n;
                    $b2 += $b1 * $b1 * $n;
                    $s2 += @((1 - (min($r1,$g1,$b1) / max($r1,$g1,$b1))) * (1 - (min($r1,$g1,$b1) / max($r1,$g1,$b1))) * $n);
                    $l2 += @((($r1 + $g1 + $b1) / 3) * (($r1 + $g1 + $b1) / 3) * $n);
                }
            }
            
            $n = floor(imagesx($img)/$xstep) * floor(imagesy($img)/$ystep);
            
            $rvar = ($n * $r2 - $r * $r) / ($n * $n);
            $gvar = ($n * $g2 - $g * $g) / ($n * $n);
            $bvar = ($n * $b2 - $b * $b) / ($n * $n);
            $svar = ($n * $s2 - $s * $s) / ($n * $n);
            $lvar = ($n * $l2 - $l * $l) / ($n * $n);
            
            $ravg = $r / $n;
            $gavg = $g / $n;
            $bavg = $b / $n;
            $savg = $s / $n;
            $lavg = $l / $n;
            
            $rsd = sqrt($rvar) * 2;
            $gsd = sqrt($gvar) * 2;
            $bsd = sqrt($bvar) * 2;
            $ssd = sqrt($svar) * 2;
            $lsd = sqrt($lvar) * 2;
            
            $rlavg = ($lavg - $ravg) * 0.75 + 0.5;
            $glavg = ($lavg - $gavg) * 0.75 + 0.5;
            $blavg = ($lavg - $bavg) * 0.75 + 0.5;
            
            /* Store the new image in the 'images' table. */

            $ravg2  = is_nan($ravg)  ? null : $ravg;
            $gavg2  = is_nan($gavg)  ? null : $gavg;
            $bavg2  = is_nan($bavg)  ? null : $bavg;
            $savg2  = is_nan($savg)  ? null : $savg;
            $lavg2  = is_nan($lavg)  ? null : $lavg;
            $rsd2   = is_nan($rsd)   ? null : $rsd;
            $gsd2   = is_nan($gsd)   ? null : $gsd;
            $bsd2   = is_nan($bsd)   ? null : $bsd;
            $ssd2   = is_nan($ssd)   ? null : $ssd;
            $lsd2   = is_nan($lsd)   ? null : $lsd;
            $rlavg2 = is_nan($rlavg) ? null : $rlavg;
            $glavg2 = is_nan($glavg) ? null : $glavg;
            $blavg2 = is_nan($blavg) ? null : $blavg;
            
            $result = query(__FILE__, __LINE__, 'insert_image', array($width, $height,
                            $ravg2, $gavg2, $bavg2, $savg2, $lavg2,
                            $rsd2, $gsd2, $bsd2, $ssd2, $lsd2,
                            $rlavg2, $glavg2, $blavg2), $db);
            
            $arr = pg_fetch_all($result);
            $image_id = $arr[0]['id'];
        }
        
        /* Create a thumbnail. */
        $thumbnail = imagecreatetruecolor($dw, $dh);
        imagecopyresampled($thumbnail, $img, 0, 0, 0, 0, $dw, $dh, imagesx($img), imagesy($img));
        imagetruecolortopalette($thumbnail, false, 256);
        ob_start();
        imagepng($thumbnail);
        $tn2 = pg_escape_bytea(ob_get_contents());
        ob_end_clean();
        imagedestroy($thumbnail);

        query(__FILE__, __LINE__, 'insert_thumbnail', array($image_id, $tn2), $db);
        
        imagedestroy($img);
        
        if ($callback)
        {
            call_user_func($callback, $short_filename, $dirname, 1.0);
        }
        
        return $image_id;
    }
?>
