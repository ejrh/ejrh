import re
import math
import os, tempfile
import Image, ImageStat, ImageMath

from database import TransactionRollbackError

class ImageImporter(object):

    def __init__(self, model, db, exception_info):
        self.image_re = re.compile('\\.(png|jpg|jpe|jpeg|bmp|gif)$', re.IGNORECASE)
        
        self.model = model
        self.db = db
        self.exception_info = exception_info
        self.prepare_queries()
        
        self.create_feature_map()
    
    def prepare_queries(self):
        self.db.prepare("""PREPARE find_image_dups(VARCHAR) AS SELECT
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
            LIMIT 1""")
        
        self.db.prepare("""PREPARE insert_image(INTEGER, INTEGER) AS INSERT INTO image (width, height)
                VALUES ($1, $2)
            RETURNING id""")

        self.db.prepare("""PREPARE insert_image_point(INTEGER, cube) AS INSERT INTO image_point (id, point)
                VALUES ($1, $2)
            RETURNING id""")

        self.db.prepare("""PREPARE insert_thumbnail(INTEGER, BYTEA) AS INSERT INTO thumbnail (id, thumbnail) VALUES ($1, $2)""")
        
        self.db.prepare("""PREPARE find_image_file(INTEGER) AS SELECT file_id FROM file_is_image WHERE file_id = $1""")
        
        self.db.prepare("""PREPARE get_features AS SELECT id, name FROM image_feature""")

    def create_feature_map(self):
        self.feature_map = {}
        
        self.db.execute("""EXECUTE get_features""");
        rows = self.db.fetchall()
        for r in rows:
            id, name = r['id'], r['name']
            self.feature_map[name] = id
        
        self.max_feature_id = max(self.feature_map.values())
    
    def get_point_str(self, values):
        vals = [0.0]*self.max_feature_id
        for name, pos in self.feature_map.iteritems():
            val = values[name]
            vals[pos-1] = val
        return '(' + ','.join([repr(x) for x in vals]) + ')'

    def import_image(self, filename, md5):
        
        # Look for existing images in the DB with matching md5, etc.
        # If a match is found, just re that one.
        if md5 == None:
            md5 = self.model.get_file_md5(filename)
        if md5 == None:
            return None
        
        params = {"md5": md5}
        self.db.execute("""EXECUTE find_image_dups(%(md5)s)""", params)
        rows = self.db.fetchall()
        
        if len(rows) == 1:
            image_id,tid = rows[0]['id'],rows[0]['tid']
            
            if tid != None:
                return image_id
        else:
            image_id = None
        
        # Load the image.
        try:
            im = Image.open(filename)
        except IOError, inst:
            self.exception_info("Failed opening image '%s'" % filename, inst)
            return None
        
        im.load()
        
        width,height = im.size
        MAX_IMAGE_SIZE = 10000000.0
        if width*height > MAX_IMAGE_SIZE:
            shrink_ratio = math.sqrt((width*height)/MAX_IMAGE_SIZE)
            shrink_width = int(width/shrink_ratio)
            shrink_height = int(height/shrink_ratio)
            print "(Shrinking image '%s' to %dx%d for processing)" % (filename, shrink_width, shrink_height)
            im = im.resize((shrink_width, shrink_height))
        
        dw,dh = width,height
        
        if dw > 64:
            dh = dh * 64.0/dw
            dw = 64
        
        if dh > 64:
            dw = dw * 64.0/dh
            dh = 64
        
        if dw < 1:
            dw = 1
        
        if dh < 1:
            dh = 1
        
        dw,dh = int(dw),int(dh)
        
        if image_id == None:
            try:
                if im.mode != 'RGB':
                    im = im.convert('RGB')
                r,g,b = im.split()
                sat = ImageMath.eval("1 - float(min(a, min(b, c))) / float(max(a, max(b, c)))", a=r, b=g, c=b)
                lum = ImageMath.eval("convert(float(a + b + c)/3, 'L')", a=r, b=g, c=b)
            except IOError, inst:
                self.exception_info("Failed in processing image '%s'" % filename, inst)
                return None

            ravg = ImageStat.Stat(r).mean[0]/255.0
            gavg = ImageStat.Stat(g).mean[0]/255.0
            bavg = ImageStat.Stat(b).mean[0]/255.0
            try:
                savg = ImageStat.Stat(sat).mean[0]/255.0
            except:
                savg = 1.0
            lavg = ImageStat.Stat(lum).mean[0]/255.0
            
            rsd = ImageStat.Stat(r).stddev[0]/255.0 * 2
            gsd = ImageStat.Stat(g).stddev[0]/255.0 * 2
            bsd = ImageStat.Stat(b).stddev[0]/255.0 * 2
            try:
                ssd = ImageStat.Stat(sat).stddev[0]/255.0 * 2
            except:
                ssd = 0.0
            lsd = ImageStat.Stat(lum).stddev[0]/255.0 * 2
            
            rlavg = (lavg - ravg) * 0.75 + 0.5
            glavg = (lavg - gavg) * 0.75 + 0.5
            blavg = (lavg - bavg) * 0.75 + 0.5
            
            params = {'width': width, 'height': height}
            self.db.execute("""EXECUTE insert_image(%(width)s, %(height)s)""", params)
            self.db.altered = True
            rows = self.db.fetchall()
            image_id = rows[0]['id']
            
            point_str = self.get_point_str(locals())
            params = {'image_id': image_id, 'point': point_str}
            self.db.execute("""EXECUTE insert_image_point(%(image_id)s, %(point)s)""", params)
            

        # Create a thumbnail.
        try:
            thumbnail = im.resize((dw, dh))
            fp,tempname = tempfile.mkstemp('.png')
            thumbnail.save(tempname)
            os.lseek(fp, 0, 0)
            tn = os.read(fp, 1048576)
            params = {'id': image_id, 'tn': self.db.make_binary(tn)}
            self.db.execute("""EXECUTE insert_thumbnail(%(id)s, %(tn)s)""", params)
            self.db.altered = True
            os.close(fp)
            os.unlink(tempname)
        except TransactionRollbackError, inst:
            self.exception_info("Unable to create thumbnail for '%s'" % filename, inst)
            raise
        except Exception, inst:
            self.exception_info("Unable to create thumbnail for '%s'" % filename, inst)
            
        return image_id

    def process(self, item):
        # If it's an image, process it.
        if self.image_re.search(item.name):
            try:
                image_id = self.import_image(item.actual_path, item.md5)
            except TransactionRollbackError, inst:
                self.exception_info('Image %s not processed' % item.actual_path, inst)
                raise
            except Exception, inst:
                self.exception_info('Image %s not processed' % item.actual_path, inst)
                image_id = None
            if image_id != None:
                params = {"id": item.id}
                try:
                    self.db.execute("""EXECUTE find_image_file(%(id)s)""", params)
                except Exception, inst:
                    self.exception_info("Couldn't find duplicate image with dict %s, item.id = %s" % (params, item.id), inst)
                    raise

                rows = self.db.fetchall()
                if len(rows) == 0:
                    params = {"file_id": item.id, "image_id": image_id}
                    self.db.execute("INSERT INTO file_is_image (file_id, image_id) VALUES (%(file_id)s, %(image_id)s)", params)
        

