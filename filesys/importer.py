import sys
import os, stat, time, tempfile
import math
import hashlib, codecs
import string, re
import Image, ImageStat, ImageMath
from database import Connection, TransactionRollbackError
import platform
import socket
from optparse import OptionParser


WINDOWS = (platform.system() == 'Windows')


def exception_info(msg, exc):
    print >>sys.stderr, 'Exception info: %s; %s: %s' % (msg, type(exc), exc)


class Item(object):
    def __init__(self):
        self.id = None
        self.name = None
        self.path = None
        self.size = None
        self.modified = None
        self.md5 = None
        self.is_dir = None
        self.is_drive = None
        self.md5str = None
    
    def __str__(self):
        s = 'item()'
        try:
            s = 'item(id=%s, name=%s, path=%s, size=%s, modified=%s, md5=%s, is_dir=%s, md5str=%s)' % (self.id, self.name, self.path, self.size, self.modified, self.md5, self.is_dir, self.md5str)
        except UnicodeDecodeError:
            s = 'item(undecodable)'
        return s


class Importer(object):
    def __init__(self):
        self.db = None


    def prepare_queries(self):
        self.db.prepare("""PREPARE bulk_find_duplicates(name_size_modified[]) AS SELECT
                orig_name, id, name, size, modified, md5
            FROM
                find_duplicates($1) AS fd(orig_name VARCHAR, id INTEGER, name VARCHAR, size BIGINT, modified TIMESTAMP, md5 VARCHAR)""")

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
        
        self.db.prepare("""PREPARE set_modified(INTEGER, TEXT, TIMESTAMP) AS UPDATE file SET name = $2, modified = $3 WHERE id = $1""")

        self.db.prepare("""PREPARE insert_image(INTEGER, INTEGER,
                DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION,
                DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION,
                DOUBLE PRECISION, DOUBLE PRECISION, DOUBLE PRECISION) AS INSERT INTO image (width, height,
                    ravg, gavg, bavg, savg, lavg,
                    rsd, gsd, bsd, ssd, lsd,
                    rlavg, glavg, blavg)
                VALUES ($1, $2,
                    $3, $4, $5, $6, $7,
                    $8, $9, $10, $11, $12,
                    $13, $14, $15)
            RETURNING id""")

        self.db.prepare("""PREPARE insert_thumbnail(INTEGER, BYTEA) AS INSERT INTO thumbnail (id, thumbnail) VALUES ($1, $2)""")
        
        self.db.prepare("""PREPARE find_image_file(INTEGER) AS SELECT file_id FROM file_is_image WHERE file_id = $1""")

        self.db.prepare("""PREPARE find_matching_file(VARCHAR, BIGINT, TIMESTAMP) AS SELECT id,md5 FROM file WHERE name = $1 AND size = $2 AND modified = $3""")

        self.db.prepare("""PREPARE insert_file(VARCHAR, BIGINT, TIMESTAMP, VARCHAR) AS INSERT INTO file (name, size, modified, md5) VALUES ($1, $2, $3, $4) RETURNING id""")

        self.db.prepare("""PREPARE find_matching_dir(VARCHAR) AS SELECT id FROM file NATURAL JOIN directory WHERE md5 = $1""")
        
        self.db.prepare("""PREPARE insert_dir(INTEGER, INTEGER, INTEGER) AS INSERT INTO directory (id, children, descendants) VALUES ($1,$2,$3)""")

        self.db.prepare("""PREPARE insert_drive(INTEGER, BIGINT, BIGINT) AS INSERT INTO drive (id, free_space, total_space) VALUES ($1,$2,$3)""")

        self.db.prepare("""PREPARE insert_file_in_dir(INTEGER, INTEGER) AS INSERT INTO file_in_dir (file_id, dir_id) VALUES ($1,$2)""")

        self.db.prepare("""PREPARE insert_revision(INTEGER) AS INSERT INTO revision (rev_id, time, root_id)
                  VALUES ((SELECT COALESCE(MAX(rev_id),0)+1 FROM revision), NOW(), $1)""")


    def begin(self):
        self.db.begin()
        self.db.altered = False
        self.db.transaction_age = time.time()
        self.db.transaction_number += 1


    def commit_if_necessary(self):
        if self.db.altered and time.time() > self.db.transaction_age + self.commit_interval:
            self.db.commit()
            self.begin()
            return True
        return False


    def get_list(self, path):
        list = []
        
        if path in ['']:
            item = Item()
            item.name = self.hostname
            item.path = '/' + self.hostname
            item.actual_path = '/'
            item.is_dir = True
            item.is_drive = True
            list.append(item)
            return list
        
        if  WINDOWS and path == '/' + self.hostname:
            for i in range(ord('A'), ord('Z')+1):
                item = Item()
                item.name = chr(i) + ':'
                item.path = '/' + self.hostname + '/' + chr(i) + ':'
                item.actual_path = chr(i) + ':' + '/'
                item.is_dir = True
                item.is_drive = True
                list.append(item)
            list.sort(key=(lambda i: i.name))
            return list
        
        actual_path = path[len('/' + self.hostname):]
        if WINDOWS:
            if self.drive_re.search(actual_path):
                actual_path = actual_path + '/'
            if self.leading_slash_re.search(actual_path):
                actual_path = actual_path[1:]
        
        if actual_path == '':
            actual_path = '/'
        
        try:
            l = os.listdir(actual_path)
        except OSError, inst:
            exception_info("Couldn't list directory '%s'" % actual_path, inst)
            return []
        
        for name in l:
            item  = Item()
            try:
                item.name = self.fs_decode(name)[0]
            except UnicodeDecodeError, inst:
                exception_info("Couldn't decode '%s'!" % name, inst)
                raise
            item.path = path + '/' + name
            item.actual_path = os.path.join(actual_path, name)
            if self.ignore_re.search(item.path) or self.ignore_re2.search(item.path):
                print 'Ignoring %s' % item.path
                continue
            try:
                statinfo = os.lstat(item.actual_path)
            except OSError, inst:
                exception_info("Couldn't stat '%s'" % item.actual_path, inst)
                continue
            if not stat.S_ISREG(statinfo[stat.ST_MODE]) and not stat.S_ISDIR(statinfo[stat.ST_MODE]):
                continue
            item.size = statinfo.st_size
            try:
                item.modified = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(statinfo.st_mtime))
            except ValueError:
                item.modified = 'epoch'
            item.is_dir = stat.S_ISDIR(statinfo[stat.ST_MODE])
            item.is_drive = False
            list.append(item)
        list.sort(key=(lambda i: i.name))
        return list


    def process_duplicates(self, item, dupes):
        dupe_items = dupes[item.name]
        
        if len(dupe_items) == 0:
            return None
        
        if len(dupe_items) > 1:
            raise Exception("More than one duplicate found!  item = %s, dupe_items = %s" % (item, dupe_items))
        
        dupe_item = dupe_items[0]
        
        if dupe_item.name != item.name or dupe_item.modified != item.modified:
            params = {"id": dupe_item.id, "name": item.name, "modified": item.modified}
            try:
                self.db.execute("""EXECUTE set_modified(%(id)s, %(name)s, %(modified)s)""", params)
                self.db.altered = True
            except Exception, inst:
                exception_info("Couldn't set modified with dict %s" % params, inst)
                raise
        return dupe_item


    def insert_file(self, item):
        params = {"name": item.name, "size": item.size, "modified": item.modified, "md5": item.md5}
        try:
            self.db.execute("""EXECUTE insert_file(%(name)s, %(size)s, %(modified)s, %(md5)s)""", params)
            self.db.altered = True
        except Exception, inst:
            exception_info("Couldn't insert file with dict %s" % params, inst)
            raise
        rows = self.db.fetchall()
        
        item.id = rows[0]['id']
        return item


    def insert_directory(self, item, child_ids):
        item.modified = None
        item = self.insert_file(item)

        params = {"id": item.id, "children": item.children, "descendants": item.descendants}
        try:
            self.db.execute("""EXECUTE insert_dir(%(id)s, %(children)s, %(descendants)s)""", params)
            self.db.altered = True
        except Exception, inst:
            exception_info("Couldn't insert dir with dict %s" % params, inst)
            raise

        if item.is_drive:
            params = {"id": item.id, "free_space": item.free_space, "total_space": item.total_space}
            try:
                self.db.execute("""EXECUTE insert_drive(%(id)s, %(free_space)s, %(total_space)s)""", params)
                self.db.altered = True
            except Exception, inst:
                exception_info("Couldn't insert drive with dict %s" % params, inst)
                raise

        params = [{'file_id': cid, 'dir_id': item.id} for cid in set(child_ids)]
        try:
            self.db.executemany("""EXECUTE insert_file_in_dir(%(file_id)s, %(dir_id)s)""", params)
            self.db.altered = True
        except Exception, inst:
            exception_info("Couldn't insert file_in_dir with dict %s" % params, inst)
            raise

        return item


    def get_file_md5(self, path):
        try:
            fd = open(path, 'rb')
            m = hashlib.md5()
            BUFSIZE = 65536
            while True:
                buf = fd.read(BUFSIZE)
                m.update(buf)
                if len(buf) == 0:
                    break
            fd.close()
            return m.hexdigest()
        except Exception, inst:
            exception_info("Failed getting MD5 of %s" % path, inst)
            return None


    def import_image(self, filename, md5):
        
        # Look for existing images in the DB with matching md5, etc.
        # If a match is found, just re that one.
        if md5 == None:
            md5 = self.get_file_md5(filename)
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
            exception_info("Failed opening image '%s'" % filename, inst)
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
                exception_info("Failed in processing image '%s'" % filename, inst)
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
            
            params = {'width': width, 'height': height,
                'ravg': ravg, 'gavg': gavg, 'bavg': bavg, 'savg': savg, 'lavg': lavg,
                'rsd': rsd, 'gsd': gsd, 'bsd': bsd, 'ssd': ssd, 'lsd': lsd,
                'rlavg': rlavg, 'glavg': glavg, 'blavg': blavg}
            self.db.execute("""EXECUTE insert_image(%(width)s, %(height)s,
                        %(ravg)s, %(gavg)s, %(bavg)s, %(savg)s, %(lavg)s,
                        %(rsd)s, %(gsd)s, %(bsd)s, %(ssd)s, %(lsd)s,
                        %(rlavg)s, %(glavg)s, %(blavg)s)""", params)
            self.db.altered = True
            rows = self.db.fetchall()
            image_id = rows[0]['id']

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
            exception_info("Unable to create thumbnail for '%s'" % filename, inst)
            raise
        except Exception, inst:
            exception_info("Unable to create thumbnail for '%s'" % filename, inst)
            
        return image_id


    def import_file(self, item, dupes):
        dupe = self.process_duplicates(item, dupes)
        
        if dupe is not None:
            item.id, item.md5 = dupe.id, dupe.md5
        else:
            if not self.no_md5_re.search(item.path):
                if item.size > 100000000:
                    print "(Reading item %s of size %d)" % (item.actual_path, item.size)
                item.md5 = self.get_file_md5(item.actual_path)
            else:
                print "Skipping md5 for %s" % item.path
                item.md5 = None
            
            item = self.insert_file(item)
        
        item.md5line = "%s\t%s\t%s\n" % (item.name, item.size, item.modified)
        item.descendants = 0
        
        # If it's an image, process it.
        if self.image_re.search(item.name):
            try:
                image_id = self.import_image(item.actual_path, item.md5)
            except TransactionRollbackError, inst:
                exception_info('Image %s not processed' % item.actual_path, inst)
                raise
            except Exception, inst:
                exception_info('Image %s not processed' % item.actual_path, inst)
                image_id = None
            if image_id != None:
                params = {"id": item.id}
                try:
                    self.db.execute("""EXECUTE find_image_file(%(id)s)""", params)
                except Exception, inst:
                    exception_info("Couldn't find duplicate image with dict %s, item.id = %s" % (params, item.id), inst)
                    raise

                rows = self.db.fetchall()
                if len(rows) == 0:
                    params = {"file_id": item.id, "image_id": image_id}
                    self.db.execute("INSERT INTO file_is_image (file_id, image_id) VALUES (%(file_id)s, %(image_id)s)", params)
        
        if self.commit_if_necessary():
            print "Commit after: %s" % item.path

        return item


    def import_dir(self, item):
        print 'Importing:', item.path
        child_ids = []
        item.md5str = "%s\n" % item.name
        item.size = 0
        item.children = 0
        item.descendants = 0
        
        md5_parts = []
        
        child_list = self.get_list(item.path)
        
        dupes = {}
        params = []
        for child_item in child_list:
            dupes[child_item.name] = []
            size_str = child_item.size
            if size_str is None:
                size_str = -1
            modified_str = child_item.modified
            if modified_str is None:
                modified_str = 'epoch'
            params.append((child_item.name, size_str, modified_str))
        try:
            self.db.execute("""EXECUTE bulk_find_duplicates(%s::name_size_modified[])""", [params])
        except Exception, inst:
            exception_info("Couldn't find duplicates with list %s" % params, inst)
            raise
        rows = self.db.fetchall()
        for r in rows:
            dupe_item = Item()
            dupe_item.id = r['id']
            dupe_item.name = self.db_decode(r['name'])[0]
            dupe_item.size = r['size']
            dupe_item.modified = str(r['modified'])
            dupe_item.md5 = r['md5']
            orig_name = self.db_decode(r['orig_name'])[0]
            dupes[orig_name].append(dupe_item)
        
        for child_item in child_list:
            if not child_item.is_dir:
                child_item = self.import_file(child_item, dupes)
        
        for child_item in child_list:
            if child_item.is_dir:
                child_item = self.try_import_dir(child_item)
            
            child_ids.append(child_item.id)
            md5_parts.append(child_item.md5line)
            item.size += child_item.size
            item.children += 1
            item.descendants += 1 + child_item.descendants
        
        item.md5str = self.db_encode(item.md5str + ''.join(md5_parts))[0]
        ppp = hashlib.md5(item.md5str)
        item.md5 = ppp.hexdigest()
        
        # Does this directory already exist in the database?
        params = {"md5": item.md5}
        self.db.execute("""EXECUTE find_matching_dir(%(md5)s)""", params)
        rows = self.db.fetchall()
        
        if len(rows) > 1:
            raise Exception("More than one matching directory!")
        
        if len(rows) == 1:
            item.id = rows[0]['id']
        else:
            # If it's a drive, try to get drive info.
            if item.is_drive:
                try:
                    import win32file
                    dummy,item.total_space,item.free_space = win32file.GetDiskFreeSpaceEx(item.actual_path)
                except:
                    item.total_space,item.free_space = None,None
            item = self.insert_directory(item, child_ids)
        
        item.md5line = "%s\t%s\n" % (item.name, item.md5)
        return item

    def try_import_dir(self, item, top_level=False):
        while True:
            start_transaction_number = self.db.transaction_number
            try:
                return self.import_dir(item)
            except TransactionRollbackError, inst:
                if top_level or self.db.transaction_number != start_transaction_number:
                    exception_info("Serialisation error in '%s'; retrying" % item.path, inst)
                    self.db.rollback()
                    self.begin()
                    continue
                else:
                    exception_info("Serialisation error in '%s'; bubbling up" % item.path, inst)
                    raise


    def make_revision(self, root_item):
        params = {"root_id": root_item.id}
        self.db.execute("""EXECUTE insert_revision(%(root_id)s)""", params)


    def read_config(self):
        try:
            self.db.execute("""SELECT * FROM config""")
            desc = self.db.cursor.description
            row = self.db.fetchone()
            for f,v in row.iteritems():
                setattr(self, f, v)
        except Exception, e:
            exception_info('Error reading config!', e)
            raise


    def run(self, path, db_host=None):
        root_item = Item()
        root_item.path = path
        root_item.name = path
        
        os.stat_float_times(False)
        
        if WINDOWS:
            fs_codec = 'latin_1'
            db_codec = 'utf_8'
        else:
            fs_codec = 'utf_8'
            db_codec = 'utf_8'
        self.fs_decode = codecs.getdecoder(fs_codec)
        self.fs_encode = codecs.getencoder(fs_codec)
        self.db_decode = codecs.getdecoder(db_codec)
        self.db_encode = codecs.getencoder(db_codec)
        
        if db_host is not None:
            connstr = "dbname='filesys' user='localuser' host='%s' password='localuser'" % db_host
        else:
            connstr = None
        self.db = Connection(connstr)
        self.db.connect()
        self.db.execute("SET client_encoding = UTF8");
        self.db.transaction_number = 0
        self.read_config()
        self.prepare_queries()

        self.drive_re = re.compile('[A-Za-z]:$')
        self.leading_slash_re = re.compile('^/')
        self.ignore_re = re.compile(self.ignore_regex)
        self.ignore_re2 = re.compile(self.ignore_regex_i, re.IGNORECASE)
        self.no_md5_re = re.compile(self.no_md5_regex)
        self.image_re = re.compile('\\.(png|jpg|jpe|jpeg|bmp|gif)$', re.IGNORECASE)
        
        self.hostname = socket.gethostname()

        self.begin()
        root_item = self.try_import_dir(root_item, top_level=True)
        
        if path == '':
            self.make_revision(root_item)
        self.db.commit()
        
        return root_item


if __name__ == "__main__":
    usage = """usage: %prog PATH [--host DB_HOST]"""
    desc = """Import a directory into the filesystem database."""
    parser = OptionParser(usage=usage, description=desc)
    parser.add_option("--host", metavar="DB_HOST",
                      action="store", dest="db_host",
                      help="specify the host of the filesys database")

    options, args = parser.parse_args()
    if len(args) == 0:
        path = ''
    else:
        path = args[0]
    
    i = Importer()
    i.run(path, options.db_host)
