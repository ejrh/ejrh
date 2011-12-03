from database import Connection

class Item(object):

    def __init__(self, row):
        for n,v in row.iteritems():
            setattr(self, n, v)


class Filesys(object):

    def __init__(self):
        self.db = None


    def connect(self, connstr = None):
        self.db = Connection(connstr)
        self.db.connect()
        self.prepare_queries()


    def prepare_queries(self):
        self.db.prepare("""PREPARE get_latest_rev AS SELECT MAX(rev_id) AS rev_id FROM revision""")
        
        self.db.prepare("""PREPARE get_root(INTEGER) AS SELECT rev_id, time, id, name, size, modified FROM revision JOIN file ON root_id = id WHERE rev_id = $1""")
        
        self.db.prepare("""PREPARE get_all_roots AS SELECT rev_id,time, id, name, size, modified FROM revision JOIN file ON root_id = id""")
        
        self.db.prepare("""PREPARE get_subdirs(INTEGER) AS SELECT id, name, size, modified, md5, children, descendants, free_space, total_space FROM file_in_dir JOIN file ON file_id = id NATURAL JOIN directory NATURAL LEFT JOIN drive WHERE dir_id = $1 ORDER BY LOWER(name)""")
        
        self.db.prepare("""PREPARE get_children(INTEGER) AS SELECT id, name, size, modified, md5, children, descendants, free_space, total_space FROM file_in_dir JOIN file ON file_id = id NATURAL LEFT JOIN directory NATURAL LEFT JOIN drive WHERE dir_id = $1 ORDER BY LOWER(name)""")


    def get_latest_rev(self):
        self.db.execute("""EXECUTE get_latest_rev""")
        return self.db.fetchone()['rev_id']


    def get_root(self, rev_id):
        params = {'rev_id': rev_id}
        self.db.execute("""EXECUTE get_root(%(rev_id)s)""", params)
        row = self.db.fetchone()
        
        return Item(row)


    def get_all_roots(self):
        params = {}
        self.db.execute("""EXECUTE get_all_roots""", params)
        
        rv = []
        for row in self.db.fetchall():
            rv.append(Item(row))
        
        return rv


    def get_subdirs(self, id):
        params = {'id': id}
        self.db.execute("""EXECUTE get_subdirs(%(id)s)""", params)
        
        rv = []
        for row in self.db.fetchall():
            rv.append(Item(row))
        
        return rv


    def get_children(self, id):
        params = {'id': id}
        self.db.execute("""EXECUTE get_children(%(id)s)""", params)
        
        rv = []
        for row in self.db.fetchall():
            rv.append(Item(row))
        
        return rv
