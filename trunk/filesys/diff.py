from filesys import *


class DiffResult(object):

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    def __str__(self):
        return self.name


class Diff(object):

    INCOMPLETE = DiffResult('INCOMPLETE')
    INCOMPATIBLE = DiffResult('INCOMPATIBLE')
    IDENTICAL = DiffResult('IDENTICAL')
    DIFFERENT = DiffResult('DIFFERENT')
    NEW = DiffResult('NEW')
    DELETED = DiffResult('DELETED')
    VACUOUS = DiffResult('VACUOUS')

    def __init__(self, old, new):
        self.old = old
        self.new = new
        self.result = Diff.INCOMPLETE
        self.subdiffs = []
        self.case_insensitive = False
        self.strip_bracenums = False


    def adjust_filename(self, name):
        new_name = name
        
        if self.case_insensitive:
            new_name = new_name.lower()
        
        if self.strip_bracenums:
            for i in range(1,10):
                new_name = new_name.replace('[%d].' % i, '.')
        
        return new_name


    def get_result(self):
        if self.result == Diff.INCOMPLETE:
            self.compare()
        
        return self.result


    def get_name(self):
        if self.old is not None:
            return self.old.name
        elif self.new is not None:
            return self.new.name
        else:
            return None


    def compare(self):
        if self.old is None and self.new is None:
            self.result = Diff.VACUOUS
            return
        if self.old is None:
            self.result = Diff.NEW
            return
        if self.new is None:
            self.result = Diff.DELETED
            return
        
        if self.old.__class__ != self.old.__class__:
            result = Diff.INCOMPATIBLE
        
        if self.old.__class__ == File:
            self.compare_files()
        else:
            self.compare_directories()


    def compare_files(self):
        if self.adjust_filename(self.old.name) != self.adjust_filename(self.new.name):
            self.result = Diff.DIFFERENT
        elif self.old.size is not None and self.new.size is not None and self.old.size != self.new.size:
            self.result = Diff.DIFFERENT
        else:
            self.result = Diff.IDENTICAL


    def compare_directories(self):
        if self.old.id == self.new.id:
            self.result = Diff.IDENTICAL
            return
        
        self.compare_files()
        
        old_children = self.make_item_map(self.old.get_child_items())
        new_children = self.make_item_map(self.new.get_child_items())
        
        for name in old_children:
            if name in new_children:
                d = Diff(old_children[name], new_children[name])
                d.case_insensitive = self.case_insensitive
                d.strip_bracenums = self.strip_bracenums
                self.subdiffs.append(d)
                del new_children[name]
            else:
                d = Diff(old_children[name], None)
                d.case_insensitive = self.case_insensitive
                d.strip_bracenums = self.strip_bracenums
                self.subdiffs.append(d)
        
        for name in new_children:
            d = Diff(None, new_children[name])
            d.case_insensitive = self.case_insensitive
            d.strip_bracenums = self.strip_bracenums
            self.subdiffs.append(d)
        
        """def cmp(a, b):
            if a.get_name() < b.get_name():
                return -1
            elif a.get_name() > b.get_name():
                return 1
            else:
                return 0"""
        
        self.subdiffs.sort(cmp, Diff.get_name)
        
        for sd in self.subdiffs:
            sd.compare()
        if any([sd.result not in [Diff.IDENTICAL, Diff.INCOMPLETE] for sd in self.subdiffs]):
            self.result = Diff.DIFFERENT


    def make_item_map(self, items):
        map = {}
        
        for item in items:
            map[self.adjust_filename(item.name)] = item
        
        return map


    def print_tree(self, indent = 0):
        if self.result == Diff.INCOMPLETE:
            self.compare()
        
        if self.result == Diff.IDENTICAL:
            return
        
        print '\t' * indent,
        
        if self.result == Diff.VACUOUS:
            print '[VACUOUS]'
        elif self.result == Diff.NEW:
            print '[NEW %s] %s' % (self.new.id, self.new.name)
        elif self.result == Diff.DELETED:
            print '[DELETED %s] %s' % (self.old.id, self.old.name)
        elif self.result == Diff.IDENTICAL:
            print '[IDENTICAL %s] %s' % (self.old.id, self.old.name)
        else:
            print '[%s %s] %s (%s)\t[%s] %s (%s)' % (self.result, self.old.id, self.old.name, self.old.size, self.new.id, self.new.name, self.new.size)
            
            for d in self.subdiffs:
                d.print_tree(indent+1)


if __name__ == "__main__":
    import sys
    import db_filesys, live_filesys
    revid1 = sys.argv[1]
    path1 = sys.argv[2]
    revid2 = sys.argv[3]
    path2 = sys.argv[4]
    
    def get_rev(revid):
        if revid == 'LIVE':
            fs = live_filesys.Filesys()
            rev = fs.get_revision(0)
        elif revid == 'HEAD':
            fs = db_filesys.Filesys()
            rev = fs.get_revision(fs.get_max_rev_id())
        else:
            fs = db_filesys.Filesys()
            rev = fs.get_revision(revid)
        return rev
    
    rev1 = get_rev(revid1)
    rev2 = get_rev(revid2)
    
    item1 = rev1.lookup_path(path1).items[-1]
    item2 = rev2.lookup_path(path2).items[-1]
    d = Diff(item1, item2)
    d.case_insensitive = True
    d.strip_bracenums = True
    d.print_tree()
