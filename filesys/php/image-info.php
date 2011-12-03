<?php
    /*
     * image-info.php
     *
     * Copyright (C) 2004,2005 Edmund Horner.
     */
    
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
    $query = "SELECT
                 width,
                 height,
                 ravg,
                 gavg,
                 bavg,
                 savg,
                 lavg,
                 rsd,
                 gsd,
                 bsd,
                 ssd,
                 lsd,
                 rlavg,
                 glavg,
                 blavg
             FROM
                 image AS i
             WHERE
                 i.id = $id";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    
    $arr = pg_fetch_all($result);    
    $row = $arr[0];
    
    $width = $row['width'];
    $height = $row['height'];
    
    $ravg = $row['ravg'];
    $gavg = $row['gavg'];
    $bavg = $row['bavg'];
    $savg = $row['savg'];
    $lavg = $row['lavg'];
    $rsd = $row['rsd'];
    $gsd = $row['gsd'];
    $bsd = $row['bsd'];
    $ssd = $row['ssd'];
    $lsd = $row['lsd'];
    $rlavg = $row['rlavg'];
    $glavg = $row['glavg'];
    $blavg = $row['blavg'];
?>
    <a href="show?id=<?php echo $id ?>&full"><img src="show?id=<?php echo $id ?>" /></a>
    
    <table>
    <tr>
        <th>Width</th><td><?php echo $width ?></td>
    </tr>
    <tr>
        <th>Height</th><td><?php echo $height ?></td>
    </tr>
    <tr>
        <td></td>
        <th>Red</th>
        <th>Green</th>
        <th>Blue</th>
        <th>Saturation</th>
        <th>Luminosity</th>
    </tr>
    <tr>
        <th>Average</th>
        <td><?php echo number_format($ravg, 3) ?></td>
        <td><?php echo number_format($gavg, 3) ?></td>
        <td><?php echo number_format($bavg, 3) ?></td>
        <td><?php echo number_format($savg, 3) ?></td>
        <td><?php echo number_format($lavg, 3) ?></td>
    </tr>
    <tr>
        <th>S.d.</th>
        <td><?php echo number_format($rsd, 3) ?></td>
        <td><?php echo number_format($gsd, 3) ?></td>
        <td><?php echo number_format($bsd, 3) ?></td>
        <td><?php echo number_format($ssd, 3) ?></td>
        <td><?php echo number_format($lsd, 3) ?></td>
    </tr>                              
    <tr>
        <th>- Luminosity</th>
        <td><?php echo number_format($rlavg, 3) ?></td>
        <td><?php echo number_format($glavg, 3) ?></td>
        <td><?php echo number_format($blavg, 3) ?></td>
    </tr>                              
    </table>
    
<?php
    set_time_limit(600);
    
    $query = "SELECT
                 ravg,
                 gavg,
                 bavg,
                 savg,
                 lavg,
                 rsd,
                 gsd,
                 bsd,
                 ssd,
                 lsd,
                 rlavg,
                 glavg,
                 blavg
             FROM
                 image_weights";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    
    $arr = pg_fetch_all($result);    
    $w = $arr[0];
    
    $extra_filter = "AND i.id IN (SELECT
            fii.image_id
        FROM
            file_is_image AS fii
            JOIN file_in_dir AS fid ON fii.file_id = fid.file_id
        WHERE
            dir_id = (SELECT
                            MAX(dir_id)
                        FROM
                            file_in_dir AS fid
                            JOIN file_is_image AS fii ON fid.file_id = fii.file_id
                        WHERE
                            image_id = $id))";
    if (@$_GET['search'] == 'anywhere')
        $extra_filter = '';
    
    $query = "SELECT
                  i.id AS id,
                  i.width,
                  i.height,
                  i.ravg,
                  i.gavg,
                  i.bavg,
                  i.savg,
                  i.lavg,
                  i.rsd,
                  i.gsd,
                  i.bsd,
                  i.ssd,
                  i.lsd,
                  i.rlavg,
                  i.glavg,
                  i.blavg,
                  image_distance(w, i, i2) AS distance,
                  ARRAY(SELECT file_id FROM file_is_image WHERE image_id = i.id) AS file_ids
              FROM
                  image AS i,
                  image AS i2,
                  image_weights AS w
              WHERE
                  i.id != $id
                  AND i2.id = $id
                  $extra_filter
              ORDER BY
                  distance ASC
              LIMIT
                  $max";
    $result = pg_query($db, $query)
        or error(__FILE__, __LINE__, pg_last_error(), $query, $db);
    
    $arr = pg_fetch_all($result);    
    
    if ($arr)
    {
?>
    <h2>Top <?php echo $max ?> similar images</h2>
    
    <table>
        <tr>
            <th>Id</th>
            <th>Width</th>
            <th>Height</th>
            <th>Measures</th>
            <th>Distance</th>
            <th>Thumbnail</th>
            <th>Files</th>
        </tr>
<?php
        foreach ($arr as $row)
        {
?>
        <tr>
            <td><a href="image-info?id=<?php echo $row['id'] ?>"><?php echo $row['id'] ?></a></td>
            <td><?php echo $row['width'] ?></td>
            <td><?php echo $row['height'] ?></td>
            <td>[<?php echo number_format($row['ravg'], 3) ?>
                <?php echo number_format($row['gavg'], 3) ?>
                <?php echo number_format($row['bavg'], 3) ?>
                <?php echo number_format($row['savg'], 3) ?>
                <?php echo number_format($row['lavg'], 3) ?><br />
                <?php echo number_format($row['rsd'], 3) ?>
                <?php echo number_format($row['gsd'], 3) ?>
                <?php echo number_format($row['bsd'], 3) ?>
                <?php echo number_format($row['ssd'], 3) ?>
                <?php echo number_format($row['lsd'], 3) ?><br />
                <?php echo number_format($row['rlavg'], 3) ?>
                <?php echo number_format($row['glavg'], 3) ?>
                <?php echo number_format($row['blavg'], 3) ?>]</td>
            <td><?php echo number_format($row['distance'], 3) ?></td>
            <td><a href="show?id=<?php echo $row['id'] ?>&full"><img src="show?id=<?php echo $row['id'] ?>" /></a></td>
            <td>
<?php
    $l = split("{|,|}", '0' . $row['file_ids']);
    for ($i = 1; $i < count($l)-1; $i++)
    {
        if ($i > 1)
            echo ', ';
        echo "<a href=\"file-info?id={$l[$i]}\">{$l[$i]}</a>";
    }
?>
            </td>
        </tr>
<?php
        }
?>
    </table>
<?php
    }
    else
    {
?>
    <p>No similar images found.</p>
<?php
    }
?>
</body>
</html>
