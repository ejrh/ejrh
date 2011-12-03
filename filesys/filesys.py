import re
import os
import gc
import weakref


drive_re = re.compile('^/[A-Z]:$')


ITEM_CACHE_MIN = 10000
ITEM_CACHE_MAX = 100000


class Filesys(object):

    def __init__(self):
        self.item_cache = {}
        self.weak_item_cache = weakref.WeakValueDictionary()
        self.discards = set()
        self.cache_time_increment = 0
        self.hit_count = 0
        self.weak_hit_count = 0
        self.miss_count = 0
        self.reload_count = 0


    def get_item(self, id):
        self.cache_time_increment += 1
        
        try:
            item = self.item_cache[id]
            item.filesys_cache_time = self.cache_time_increment
            self.hit_count += 1
            return item
        except KeyError:
            pass
        
        try:
            item = self.weak_item_cache[id]
            del self.weak_item_cache[id]
            self.cache_item(item)
            self.weak_hit_count += 1
            return item
        except KeyError:
            pass
        
        item = self.get_item_uncached(id)
        if id in self.discards:
            self.reload_count += 1
        self.cache_item(item)
        self.miss_count += 1
        return item


    def cache_item(self, item):
            self.item_cache[item.id] = item
            item.filesys_cache_time = self.cache_time_increment
            
            if len(self.item_cache) > ITEM_CACHE_MAX:
                items = list(self.item_cache.itervalues())
                items.sort(cmp=lambda a,b: b.filesys_cache_time - a.filesys_cache_time)
                for i in items[ITEM_CACHE_MIN:]:
                    del self.item_cache[i.id]
                    self.weak_item_cache[i.id] = i
                    self.discards.add(i.id)
                
                print '(cache)', self.hit_count, self.weak_hit_count, self.miss_count, self.reload_count


class Revision(object):

    def __init__(self, filesys):
        self.filesys = filesys


    def lookup_path(self, path):
        """Look up a path in this revision."""
        
        names = path.split('/')
        
        p = Path(self, path)
        
        parent = None
        for n in names:
            item = self.filesys.lookup_item(parent, n, revision=self)
            p.append_item(item)
            parent = item
        
        return p


    def get_root(self):
        return self.filesys.lookup_item(None, '', revision=self)


class File(object):

    def __init__(self, source):
        self.source = source
        self.size = None
        self.modified = None
        self.md5 = None


    def get_size(self):
        return self.size


    def get_modified(self):
        return self.modified


    def get_md5(self):
        return self.md5


    def get_descendants(self):
        return []


class Directory(File):

    def __init__(self, source):
        File.__init__(self, source)
        self.child_ids = None
        self.num_children = None
        self.num_descendants = None


    def get_child_items(self):
        if self.child_ids is None:
            self.child_ids = [i.id for i in self.source.get_all_children(self)]
        return [self.source.get_item(id) for id in self.child_ids]


    def get_descendants(self):
        for child in self.get_child_items():
            yield child
            for grandchild in child.get_descendants():
                yield grandchild


    def get_num_children(self):
        return self.num_children


    def get_num_descendants(self):
        return self.num_descendants


class Drive(Directory):

    def __init__(self, source):
        Directory.__init__(self, source)
        self.free_space = None
        self.total_space = None


    def get_free_space(self):
        return self.free_space


    def get_total_space(self):
        return self.total_space


class Root(Drive):

    def __init__(self, source):
        Drive.__init__(self, source)


class Path(object):

    def __init__(self, revision, path):
        self.revision = revision
        self.path = path
        self.items = []


    def append_item(self, item):
        self.items.append(item)
