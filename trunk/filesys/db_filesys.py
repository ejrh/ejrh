import database
import filesys


class Filesys(filesys.Filesys):

    def __init__(self, conn=None):
        filesys.Filesys.__init__(self)
        
        if conn is None:
            import database
            conn = database.Connection()
        self.conn = conn
        self.prepare_queries()


    def prepare_queries(self):
        self.conn.prepare("""PREPARE get_max_rev_id AS SELECT MAX(rev_id) AS rev_id FROM revision""", min=1, max=1)
        
        self.conn.prepare("""PREPARE get_revision(INTEGER) AS SELECT rev_id,time,root_id FROM revision WHERE rev_id = $1""", min=0, max=1)
        
        self.conn.prepare("""PREPARE get_item(INTEGER) AS SELECT id, directory.id AS dir_id, drive.id AS drive_id, name, size, modified, md5, children, descendants, free_space, total_space FROM file NATURAL LEFT JOIN directory NATURAL LEFT JOIN drive WHERE id = $1""", min=0, max=1)
        
        self.conn.prepare("""PREPARE get_child_item(INTEGER, TEXT) AS SELECT id, directory.id AS dir_id, drive.id AS drive_id, name, size, modified, md5, children, descendants, free_space, total_space FROM file_in_dir JOIN file ON (file_id = id) NATURAL LEFT JOIN directory NATURAL LEFT JOIN drive WHERE dir_id = $1 AND name = $2""", min=0, max=1)
        
        self.conn.prepare("""PREPARE get_revision_root(INTEGER) AS SELECT id, directory.id AS dir_id, drive.id AS drive_id, name, size, modified, md5, children, descendants, free_space, total_space FROM revision JOIN file ON (root_id = id) NATURAL LEFT JOIN directory NATURAL LEFT JOIN drive WHERE rev_id = $1""", min=0, max=1)
        
        self.conn.prepare("""PREPARE get_all_children(INTEGER) AS SELECT id, directory.id AS dir_id, drive.id AS drive_id, name, size, modified, md5, children, descendants, free_space, total_space FROM file_in_dir JOIN file ON (file_id = id) NATURAL LEFT JOIN directory NATURAL LEFT JOIN drive WHERE dir_id = $1 ORDER BY name""", min=0)

        self.conn.prepare("""PREPARE get_all_child_ids(INTEGER) AS SELECT file_id AS id FROM file_in_dir WHERE dir_id = $1""", min=0)


    def create_revision(self):
        rev = filesys.Revision(self)
        
        rev.rev_id = self.conn.query('get_max_rev_id') + 1
        
        return rev


    def copy_revision(self, revision):
        rev = self.create_revision()
        
        root = revision.get_root()
        rev.root = self.copy_item(root)
        
        return rev


    def copy_item(self, item):
        try:
            if item.database == self:
                return item
        except:
            pass
        
        
        return new_item


    def fix(self, rev_id = 1):
        """Fix computed item fields such as total size, number of children and number of descendants."""
        
        max_rev_id = self.get_max_rev_id()
        
        while rev_id <= max_rev_id:
            rev = self.get_revision(rev_id)
            
            root = rev.get_root()
            id = fix_item(root)
            rev.set_root(id)
            
            rev_id = rev_id + 1


    def fix_item(self, item):
        """Fix an item, recursively.  Return a tuple of the id, number of descendants + 1, and a suitable md5 substr"""
        
        if item.__class__ == File:
            return item.id, 1, "%s\t%d\t%s\t%s\n" % (item.name, item.size, item.modified, item.md5)
        
        children = item.get_child_list()
        size = 0
        num_children = 0
        num_descendants = 0
        md5_str = ''
        child_ids = []
        for c in children:
            id, count, substr = self.fix_item(c)
            size = size + c.size
            num_children = num_children + 1
            num_descendants = num_descendants + count
            md5_str = md5_str + substr
            child_ids.append(id)
        
        md5 = md5(ms5_str)
        
        id = self.update_item_if_necessary(item, size, md5, num_children, num_descendants, child_ids)
        
        return id, item.descendants + 1, "%s\t%s\n" % (item.name, item.md5)


    def update_item_if_necessary(item, size, md5, num_children, num_descendants, child_ids):
        if item.size != size or item.md5 != md5:
            self.conn.execute('update_file_size_modified', **kwargs)
        
        if item.num_children != num_children or item.num_descendants != num_descendants:
            self.conn.execute('update_directory', **kwargs)
        
        if item.child_ids != child_ids:
           self.conn.execute('update_file_children', **kwargs)
        
        return item.id


    def get_revision(self, rev_id):
        """Look up the revision with the given rev_id."""
        
        result = self.conn.execute('EXECUTE get_revision(%(rev_id)s)', locals())
        row = self.conn.fetchone()
        
        rev = filesys.Revision(self)
        rev.rev_id = rev_id
        rev.root_id = row['root_id']
        return rev


    def get_item_uncached(self, id):
        """Look up the item in the database and return an object of class
        File, Directory, Drive, or Revision for it."""
        
        result = self.conn.execute('EXECUTE get_item(%(id)s)', locals())
        row = self.conn.fetchone()
        
        return self.create_item_from_row(row)


    def create_item_from_row(self, row):
        if row['name'] in ['']:
            item = filesys.Root(self)
        elif row['drive_id'] is not None:
            item = filesys.Drive(self)
        elif row['dir_id'] is not None:
            item = filesys.Directory(self)
        else:
            item = filesys.File(self)
        
        item.__dict__.update(row)
        
        return item


    def get_child_item(self, parent_id, name):
        """Look up the named child of an item."""
        
        result = self.conn.execute('EXECUTE get_child_item(%(parent_id)s, %(name)s)', locals())
        row = self.conn.fetchone()
        
        item = self.create_item_from_row(row)
        self.cache_item(item)
        return item


    def get_revision_root(self, rev):
        """Look up the root item for a revision."""
        
        if type(rev) == int:
            raise NotImplementedError
        
        """result = self.conn.execute('EXECUTE get_revision_root(%(rev_id)s)', locals())
        row = self.conn.fetchone()
        
        item = self.create_item_from_row(row)
        self.cache_item(item)"""
        
        
        return self.get_item(rev.root_id)


    def get_all_children(self, parent):
        """Look up all the children of an item."""
        
        if type(parent) == int:
            parent_id = parent
        else:
            parent_id = parent.id
        
        result = self.conn.execute('EXECUTE get_all_child_ids(%(parent_id)s)', locals())
        rows = self.conn.fetchall()
        
        items = []
        
        for row in rows:
            id = row['id']
            items.append(self.get_item(id))
        
        items.sort()
        
        return items


    def get_max_rev_id(self):
        """Return the maximum rev_id."""
        
        self.conn.execute('EXECUTE get_max_rev_id')
        row = self.conn.fetchone()
        return row['rev_id']


    def lookup_item(self, parent, name, revision=None):
        if parent is None:
            return self.get_revision_root(revision)
        return self.get_child_item(parent.id, name)
