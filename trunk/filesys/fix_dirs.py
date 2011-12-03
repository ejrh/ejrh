import hashlib
import string, re
from database import Connection


class Item(object):
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name
        self.size = 0
        self.children = 0
        self.descendants = 0


class DirectoryFixer(object):
    def __init__(self):
        self.db = None


    def prepare_queries(self):
        self.db.prepare("""PREPARE get_revisions(INTEGER) AS SELECT
            id,
            name,
            rev_id
        FROM
            revision
            JOIN (directory NATURAL JOIN file) ON (root_id = id)
        WHERE
            name = ''
            AND rev_id >= $1
        ORDER BY
            rev_id""")

        self.db.prepare("""PREPARE get_children(INTEGER) AS SELECT
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
        ORDER BY name""")
        
        self.db.prepare("""PREPARE get_dir_info(INTEGER) AS SELECT size, children, descendants, md5 FROM file NATURAL JOIN directory WHERE id = $1""")

        self.db.prepare("""PREPARE find_matching_dir(VARCHAR) AS SELECT id FROM directory NATURAL JOIN file WHERE md5 = $1""")

        self.db.prepare("""PREPARE update_file_in_dir(INTEGER, INTEGER) AS UPDATE file_in_dir SET file_id = $2 WHERE file_id = $1""")
        
        self.db.prepare("""PREPARE delete_file(INTEGER) AS DELETE FROM file WHERE id = $1""")

        self.db.prepare("""PREPARE delete_file_in_dir(INTEGER, INTEGER) AS DELETE FROM file_in_dir WHERE file_id = $1 AND dir_id = $2""")

        self.db.prepare("""PREPARE update_file(INTEGER, VARCHAR, BIGINT) AS UPDATE file SET md5 = $2, size = $3 WHERE id = $1""")

        self.db.prepare("""PREPARE update_dir(INTEGER, INTEGER, INTEGER) AS UPDATE directory SET children = $2, descendants = $3 WHERE id = $1""")


    def make_item(self, row):
        item = Item()
        for f,v in row.iteritems():
            setattr(item, f, v)
        return item


    def should_ignore(self, path):
            return self.ignore_re.search(path) or self.ignore_re2.search(path)


    def fix_directory(self, id, name, full_name):
        stats = Item(id, name)
        md5 = hashlib.md5("%s\n" % name)

        params = {'id': id}
        self.db.execute("""EXECUTE get_children(%(id)s)""", params)
        rows = self.db.fetchall()
        for r in rows:
            item = self.make_item(r)
            
            if full_name == '/':
                item.path = full_name + item.name
            else:
                item.path = full_name + '/' + item.name
            
            if self.should_ignore(item.path):
                print 'Ignoring %s' % item.path
                params = {'id': item.id, 'dir_id': id}
                self.db.execute("""EXECUTE delete_file_in_dir(%(id)s, %(dir_id)s)""", params)
                continue
            
            if item.descendants is not None:
                if item.id not in self.processed_dirs:
                    item = self.fix_directory(item.id, item.name, item.path)
                    self.num_dirs += 1
                stats.descendants += item.descendants
                md5.update("%s\t%s\n" % (item.name, item.md5))
            else:
                size_str = item.size
                if item.size is None:
                    size_str = ''
                
                modified_str = item.modified
                if item.modified is None:
                    modified_str = ''
                
                md5.update("%s\t%s\t%s\n" % (item.name, size_str, modified_str))
            
            if item.size is not None:
                stats.size += item.size
            stats.children += 1
            stats.descendants += 1
        
        stats.md5 = md5.hexdigest()
        
        params = {'id': id}
        self.db.execute("""EXECUTE get_dir_info(%(id)s)""", params)
        row = self.db.fetchone()
        old_stats = self.make_item(row)
        
        if old_stats.md5 != stats.md5:
            params = {'md5': stats.md5}
            self.db.execute("""EXECUTE find_matching_dir(%(md5)s)""", params)
            row = self.db.fetchone()
            if row is not None:
                item = self.make_item(row)
                
                low_id = min(item.id, stats.id)
                high_id = max(item.id, stats.id)
                
                print "Removing duplicate directory %d '%s'" % (high_id, name)
                
                self.db.execute("""EXECUTE update_file_in_dir(%(high_id)s, %(low_id)s)""", locals())
                self.db.execute("""EXECUTE delete_file(%(high_id)s)""", locals())
                
                
                if low_id in self.processed_dirs:
                    self.processed_dirs.remove(low_id)
                if high_id in self.processed_dirs:
                    self.processed_dirs.remove(high_id)
                id = low_id
        
        first_diff = True
        updates = [False, False]
        for f,s in {'md5': 0, 'size': 0, 'children': 1, 'descendants': 1}.iteritems():
            old = getattr(old_stats, f) 
            new = getattr(stats, f)
            if old != new:
                if first_diff:
                    print "Item %d '%s' will be updated:" % (id, name)
                    first_diff = False
                print 'Difference in %s: %s to %s' % (f, old, new)
                updates[s] = True

        if updates[0]:
            params = {'id': id, 'md5': stats.md5, 'size': stats.size}
            self.db.execute("""EXECUTE update_file(%(id)s, %(md5)s, %(size)s)""", params)
        if updates[1]:
            params = {'id': id, 'children': stats.children, 'descendants': stats.descendants}
            self.db.execute("""EXECUTE update_dir(%(id)s, %(children)s, %(descendants)s)""", params)
        
        self.processed_dirs.add(id)
        return stats


    def read_config(self):
        try:
            self.db.execute("""SELECT * FROM config""")
            row = self.db.fetchone()
            for f,v in row.iteritems():
                setattr(self, f, v)
        except Exception, e:
            raise Exception('Error reading config!', e)


    def run(self, rev):
        self.db = Connection()
        self.db.connect()
        self.read_config()
        self.prepare_queries()
        
        self.processed_dirs = set()

        self.ignore_re = re.compile(self.ignore_regex)
        self.ignore_re2 = re.compile(self.ignore_regex_i, re.IGNORECASE)

        params = {'rev': rev}
        self.db.execute("""EXECUTE get_revisions(%(rev)s)""", params)
        rows = self.db.fetchall()
        
        for r in rows:
            id = r['id']
            name = r['name']
            rev_id = r['rev_id']
            print 'Fixing revision %d directories:' % rev_id
            self.db.begin()
            self.num_dirs = 0
            self.num_files = 0
            self.fix_directory(id, name, name)
            self.db.commit()


if __name__ == "__main__":
    import sys
    try:
        rev = int(sys.argv[1])
    except IndexError:
        rev = 0
    f = DirectoryFixer()
    f.run(rev)
