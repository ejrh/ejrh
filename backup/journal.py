"""This program outputs every changed file in the file system.  The first time it is run, it will print every
currently existing file.  It will then print every file that has been changed since the prior run.  The output
is lossy in the sense that it may print additional paths (for instance, if the journal id is different it has to
assume that every existing path has been changed).

Reference material:

http://msdn.microsoft.com/en-us/library/aa363798%28v=VS.85%29.aspx
http://www.microsoft.com/msj/0999/journal/journal.aspx
http://www.microsoft.com/msj/1099/journal2/journal2.aspx
"""

import sys
import os
import cPickle

from journalcmd import *


def default_notifier(msg):
    pass


def print_notifier(msg):
    print msg


def normalise(path):
    """Return a normalised path: lowercase, with forward slashes, starting at / (i.e. no drive)."""
    path = os.path.normcase(path)
    path = path.replace('\\', '/')
    path = path.replace('//', '/')    
    if len(path) >= 2 and path[1] == ':':
        path = path[2:]
    return path


def get_ancestors(path):
    """Return a list of the ancestor directories of this file."""
    ancestors = []
    components = normalise(path).split('/')
    subpath = '/'
    for c in components:
        if subpath == '':
            subpath = c
        else:
            subpath = subpath + '/' + c
        subpath = normalise(subpath)
        ancestors.append(subpath)
    return ancestors


class FrnMap(object):
    """A map from FRNs to parent FRNs and names.  This is enough information to
    translate a FRN to a path (as done in build_path)."""
    
    def __init__(self):
        self.map = {}

    def load(self, filename):
        f = open(filename, 'rb')
        self.map.update(cPickle.load(f))
        f.close()

    def save(self, filename):
        f = open(filename, 'wb')
        cPickle.dump(self.map, f)
        f.close()

    def set(self, frn, parent_frn, name):
        self.map[frn] = parent_frn, name

    def build_path(self, frn):
        if frn not in self.map:
            return ''
        parent_frn, name = self.map[frn]
        return self.build_path(parent_frn) + '/' + name


class Journal(object):
    
    def __init__(self, drive):
        self.drive = drive
        self.set_state((None, None, {}))

    def process_usn(self, tup, fn):
        if tup[10] & win32file.FILE_ATTRIBUTE_DIRECTORY:
            self.frn_to_dir_map.set(tup[3], tup[4], fn)
        
        parent_frn = tup[4]
        parent_path = self.frn_to_dir_map.build_path(parent_frn)
        try:
            path = parent_path + '/' + fn
        except UnicodeEncodeError, ex:
            print >>sys.stderr, "Error outputting file name:", ex
            return
        for p in get_ancestors(normalise(path))[:-1]:
            if p not in self.affected_dirs:
                self.affected_dirs.add(p)
        self.changed_paths.add(normalise(path))

    def get_state(self):
        return self.journal_id, self.last_usn, self.frn_to_dir_map.map

    def set_state(self, state):
        self.journal_id = state[0]
        self.last_usn = state[1]
        self.frn_to_dir_map = FrnMap()
        self.frn_to_dir_map.map.update(state[2])
    
    def load_state(self, filename):
        f = open(filename, 'rb')
        obj = cPickle.load(f)
        f.close()
        self.set_state(obj)
        
    def save_state(self, filename):
        obj = self.get_state()
        f = open(filename, 'wb')
        cPickle.dump(obj, f)
        f.close()

    def get_changed_paths(self):
        return self.changed_paths

    def process(self, notifier=default_notifier):
        notifier('Opening volume %s' % self.drive)
        volh = open_volume(self.drive)
        
        notifier('Querying journal')
        try:
            tup = query_journal(volh)
        except pywintypes.error, ex:
            if ex.winerror == 1179:   # ERROR_JOURNAL_NOT_ACTIVE
                notifier('Creating new journal')
                create_journal(volh)
                notifier('Re-querying')
                tup = query_journal(volh)
            else:
                raise
        queried_journal_id = tup[0]
        first_usn = tup[1]
        next_usn = tup[2]
        self.replay_all = False
        
        if self.journal_id != queried_journal_id or first_usn > self.last_usn:
            if self.journal_id is None:
                notifier('Journal is new (available id 0x%016x, first available USN 0x%016x)' % (queried_journal_id, first_usn))
            else:
                notifier('Journal is too new (recorded id 0x%016x, available id 0x%016x, last recorded USN 0x%016x, first available USN 0x%016x)' % (self.journal_id, queried_journal_id, self.last_usn, first_usn))
            self.journal_id = queried_journal_id
            self.last_usn = first_usn
            self.replay_all = True
        
        self.changed_paths = set()
        self.affected_dirs = set()

        if self.replay_all:
            tup = get_ntfs_volume_data(volh)
            mft_entry_size = tup[7]
            mft_max = tup[9] / mft_entry_size
            
            notifier('Reading all USNs from MFT')
            last_pct = 0
            for next_frn,tup,fn in generate_usns(volh, 0, next_usn):
                self.process_usn(tup, fn)
                if tup[5] > self.last_usn:
                    self.last_usn = tup[5]
                    
                mft_pos = next_frn & 0xFFFFFFFFFFFF
                pct = 100 * mft_pos / mft_max
                if pct > last_pct and 0 <= pct <= 100:
                    notifier('Read MFT pos %d; %d percent done' % (mft_pos, pct))
                    last_pct = pct
            
            notifier('Re-querying journal')
            tup = query_journal(volh)
            next_usn = tup[2]
        
        start_usn = self.last_usn
        notifier('Replaying journal from USN 0x%016x to 0x%016x' % (start_usn, next_usn))
        last_pct = 0
        for tup,fn in generate_journal(volh, self.journal_id, start_usn):
            if self.replay_all or self.last_usn < tup[5]:
                self.process_usn(tup, fn)
                self.last_usn = tup[5]
            pct = 100 * (tup[5] - start_usn) / (next_usn - start_usn)
            if pct > last_pct:
                notifier('Replayed USN 0x%016x; %d percent done' % (tup[5], pct))
                last_pct = pct
        
        notifier('Closing volume')
        close_volume(volh)
    
    def affected(self, path):
        """Could this path possibly have changed according to the journal?"""
        
        path = normalise(path)
        
        if path in self.affected_dirs:
            return True
        
        for p in get_ancestors(path):
            if p in self.changed_paths:
                return True
        
        return False


def main(argv=None):
    if argv is None:
        argv = sys.argv
    drive = argv[1]
    journal_filename = argv[2]
    try:
        target_dir = argv[3]
    except IndexError:
        target_dir = os.getcwd()
    
    print 'Opening journal'
    j = Journal(drive)
    try:
        j.load_state(journal_filename)
    except IOError:
        pass
        
    print 'Processing'
    j.process(notifier=print_notifier)
    
    print 'Changed paths:'
    for p in sorted(j.get_changed_paths()):
        try:
            print p
        except UnicodeEncodeError:
            print repr(p)
    
    print 'Affected paths:'
    for dirpath, dirnames, filenames in os.walk(target_dir):
        for fn in filenames + dirnames:
            path = normalise(os.path.join(dirpath, fn))
            if j.affected(path):
                print path
    
    j.save_state(journal_filename)


if __name__ == '__main__':
    main()
