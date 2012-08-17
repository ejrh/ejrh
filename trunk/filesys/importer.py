import sys
import time
import hashlib, codecs
import re

from database import Connection, TransactionRollbackError

from image_importer import ImageImporter


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
    def __init__(self, model):
        self.db = None
        self.model = model


    def prepare_queries(self):
        self.db.prepare("""PREPARE bulk_find_duplicates(name_size_modified[]) AS SELECT
                orig_name, id, name, size, modified, md5
            FROM
                find_duplicates($1) AS fd(orig_name VARCHAR, id FileId, name VARCHAR, size BIGINT, modified TIMESTAMP, md5 VARCHAR)""")

        self.db.prepare("""PREPARE set_modified(INTEGER, TEXT, TIMESTAMP) AS UPDATE file SET name = $2, modified = $3 WHERE id = $1""")

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
        if ((self.db.altered and time.time() > self.db.transaction_age + self.commit_interval)
                or (time.time() > self.db.transaction_age + self.commit_interval_max)):
            self.db.commit()
            self.begin()
            return True
        return False


    def get_list(self, path):
        items = []
        for item in self.model.get_list(path):
            if self.ignore_re.search(item.path) or self.ignore_re2.search(item.path):
                print 'Ignoring %s' % item.path
                continue
            items.append(item)
        items.sort(key=(lambda i: i.name))
        return items


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


    def import_file(self, item, dupes):
        dupe = self.process_duplicates(item, dupes)
        
        if dupe is not None:
            item.id, item.md5 = dupe.id, dupe.md5
        else:
            if not self.no_md5_re.search(item.path):
                if item.size > 100000000:
                    print "(Reading item %s of size %d)" % (item.actual_path, item.size)
                item.md5 = self.model.get_file_md5(item.actual_path)
            else:
                print "Skipping md5 for %s" % item.path
                item.md5 = None
            
            item = self.insert_file(item)
        
        item.md5line = "%s\t%s\t%s\n" % (item.name, item.size, item.modified)
        item.descendants = 0
        
        self.image_importer.process(item)
        
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
        
        db_codec = 'utf_8'
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

        self.ignore_re = re.compile(self.ignore_regex)
        self.ignore_re2 = re.compile(self.ignore_regex_i, re.IGNORECASE)
        self.no_md5_re = re.compile(self.no_md5_regex)
        
        self.image_importer = ImageImporter(self.model, self.db, exception_info)
        
        self.begin()
        root_item = self.try_import_dir(root_item, top_level=True)
        
        if path == '':
            self.make_revision(root_item)
        self.db.commit()
        
        return root_item
