import os

import filesys


class Filesys(filesys.Filesys):

    def __init__(self):
        filesys.Filesys.__init__(self)


    def get_revision(self, rev_id):
        return filesys.Revision(self)


    def get_max_rev_id(self):
        return 1


    def lookup_item(self, parent, name, revision=None):
        if parent is None:
            path = name
        else:
            path = '/'.join([parent.path, name])
        
        return self.get_item(path)


    def get_item_uncached(self, path):
        real_path = path[1:]
        
        if path == '':
            item = filesys.Root(self)
        elif filesys.drive_re.match(path) and os.path.isdir(real_path):
            item = filesys.Drive(self)
            real_path = real_path + '/'
        elif os.path.isdir(real_path):
            item = filesys.Directory(self)
        else:
            item = filesys.File(self)
            stats = os.stat(real_path)
            item.size = stats.st_size
            item.modified = stats.st_mtime
        
        name = path.rsplit('/', 1)[-1]
        item.name = name
        item.id = path
        
        item.path = path
        item.real_path = real_path
        
        return item


    def get_all_children(self, parent):
        items = []
        
        if parent.path == '':
            for dl in range(ord('A'), ord('Z')+1):
                try:
                    items.append(self.lookup_item(parent, '%s:' % chr(dl)))
                except WindowsError:
                    pass
        else:
            for n in os.listdir(parent.real_path):
                items.append(self.lookup_item(parent, n))
        
        items.sort()
        
        return items
