"""This module implements a backup procedure, with optimisations
for NTFS drives.

Source can be any directory, for example C:/
Target is a directory, with each backup getting a subdirectory within it.
For example, C:/snapshots/20101103.

The target is essentially a copy of the source, except that:
  - some files and/or directories may have been excluded, and
  - files and/or directories that have not changed since the previous
    backup will be links (hard for file, sym for dirs to the copies
    in the previous backup dir).

Some state files are maintained in the base target dir:
  - journal for the state of the NTFS journal from the last
  backup, including a dir map.
  - previous for the previous successful backup name
  - exclusions is a list of files and dirs to exclude from backups.

Basic algorithm:
  - Input is source directory, target directory, and name.
  - Read exclusions file and journal file.
  - Open journal and build list of changed paths.
  - Iterate over source, using changed paths to optimise if possible.
     - For each file/dir, either copy in or make link to copy in previous
       backup.
  - Save journal file.
  
Example:

backup.py C:/ C:/snapshots 20101103
"""

import sys
import os
import os.path
import cPickle
import hashlib
import time
from optparse import OptionParser

import links


BUFFER_SIZE = 1024*1024
MAX_BUFFERS = 512

JOURNAL_FILENAME = "journal"
PREVIOUS_FILENAME = "previous"
EXCLUSIONS_FILENAME = "exclusions"
MANIFEST_FILENAME = "manifest"

ALLOW_JOURNAL = True

if ALLOW_JOURNAL:
    try:
        import journal
        from journal import Journal
    except ImportError:
        ALLOW_JOURNAL = False


def unpickle_file(filename):
    f = open(filename, 'rb')
    obj = cPickle.load(f)
    f.close()
    return obj

def pickle_to_file(obj, filename):
    f = open(filename, 'wb')
    cPickle.dump(obj, f)
    f.close()


class ConsoleNotifier(object):
    def __init__(self, parent):
        self.parent = parent

    def notice(self, msg):
        print >>sys.stderr, msg
    
    def warning(self, msg):
        print >>sys.stderr, 'Warning: %s' % msg
    
    def error(self, msg, ex=None):
        print >>sys.stderr, 'Error: %s' % msg
        if ex is not None:
            print >>sys.stderr, 'Exception was:', ex


class Backup(object):
    """A backup is the process of copying all current files in a drive
    into a backup location."""

    def __init__(self):
        self.name = None
        self.source = None
        self.target = None
        self.enable_journal = False
        self.enable_dir_reuse = False
    
    def get_md5(self, source_path):
        f = open(source_path, 'rb')
        big_buf = []
        m = hashlib.md5()
        total = 0
        while len(big_buf) < MAX_BUFFERS:
            buf = f.read(BUFFER_SIZE)
            if len(buf) == 0:
                f.close()
                return m.hexdigest(), total, big_buf
            total += len(buf)
            m.update(buf)
            big_buf.append(buf)
        big_buf = None
        while True:
            buf = f.read(BUFFER_SIZE)
            if len(buf) == 0:
                break
            total += len(buf)
            m.update(buf)           
        f.close()
        return m.hexdigest(), total, big_buf
    
    def reuse_from_manifest(self, md5, size, item_path):
        if size == 0:
            return False
        
        new_path = os.path.join(self.name, item_path)
        if md5 not in self.manifest:
            self.manifest[md5] = [new_path]
            return False
        
        l = self.manifest[md5]
        size_list = []
        s = None
        while len(l) > 0:
            n = l.pop()
            try:
                link_path = os.path.join(self.target, n)
                s = os.path.getsize(link_path)
            except (IOError, WindowsError):
                self.notifier.warning('Unable to find in manifest: %s' % n)
                n = None
                continue
                
            if s != size:
                self.notifier.warning('Unable to reuse from manifest due to size (expected %d, was %d): %s' % (s, size, link_path))
                size_list.append(n)
                n = None
            else:
                break
        l.extend(size_list)
        
        l.append(new_path)
        
        if n is None:
            return False
            
        l.append(n)
    
        link_path = os.path.join(self.target, n)
        dest_path = os.path.join(self.target, new_path)
        links.link(link_path, dest_path)
        return True
        
    def copy_item(self, item_path):
        source_path = os.path.join(self.source, item_path)
        md5, size, big_buf = self.get_md5(source_path)
        if self.reuse_from_manifest(md5, size, item_path):
            self.notifier.notice('Reused (from manifest): %s' % item_path)
            return
        dest_path = os.path.join(self.target, self.name, item_path)
        
        f2 = open(dest_path, 'wb')
        if big_buf is not None:
            for buf in big_buf:
                f2.write(buf)
        else:
            f = open(source_path, 'rb')
            while True:
                buf = f.read(BUFFER_SIZE)
                if len(buf) == 0:
                    break
                f2.write(buf)
            f.close()
        f2.close()
        self.notifier.notice('Copied: %s' % item_path)

    def reuse_item(self, item_path):
        source_path = os.path.join(self.source, item_path)
        dest_path = os.path.join(self.target, self.name, item_path)
        link_path = os.path.join(self.target, self.previous_name, item_path)
        if os.path.isfile(source_path):
            try:
                links.link(link_path, dest_path)
            except Exception, ex:
                self.notifier.error('Unable to make hard link from %s to %s' % (dest_path, link_path), ex)
                raise ex
        else:
            links.symlink(link_path, dest_path)

    def make_dir(self, item_path):
        dest_path = os.path.join(self.target, self.name, item_path)
        os.mkdir(dest_path)

    def get_children(self, item_path):
        source_path = os.path.join(self.source, item_path)
        try:
            children = os.listdir(source_path)
        except WindowsError:
            self.notifier.warning('Unable to find children in %s' % source_path)
            children = []
        return children
    
    def is_excluded(self, item_path):
        return item_path in self.exclusions
    
    def is_reusable(self, item_path):
        if not self.enable_journal:
            return False
        
        if self.previous_name is None:
            return False
        
        source_path = os.path.join(self.source, item_path)
        if os.path.isdir(source_path) and not self.enable_dir_reuse:
            return False
        
        source_path = source_path.replace('\\', '/')
        if source_path[-1] == '/':
            source_path = source_path[:len(source_path)-1]
        
        if self.journal.affected(source_path):
            return False
        
        return True
    
    def backup_item(self, item_path):
        if self.is_excluded(item_path):
            self.notifier.notice('Excluded: %s' % item_path)
            return
        
        if self.is_reusable(item_path):
            try:
                self.reuse_item(item_path)
                self.notifier.notice('Reused: %s' % item_path)
                return
            except Exception:
                self.notifier.notice('Falling back to copy')
                pass
        
        source_path = os.path.join(self.source, item_path)
        if os.path.isfile(source_path):
            self.copy_item(item_path)
        else:
            self.make_dir(item_path)
            for c in self.get_children(item_path):
                self.backup_item(os.path.join(item_path, c))
        self.notifier.notice('Backed up: %s' % item_path)

    def check_target(self):
        if not os.path.exists(self.target):
            self.notifier.notice('Creating new target: %s' % self.target)
            os.mkdir(self.target)
        
        if os.path.exists(os.path.join(self.target, self.name)):
            raise Exception, 'Target with name already exists!'

    def read_exclusions(self):
        self.exclusions = set()
        try:
            f = open(os.path.join(self.target, EXCLUSIONS_FILENAME), 'rt')
            for line in f:
                line = line.strip()
                if line == '':
                    continue
                
                self.exclusions.add(line)
            f.close()
            self.notifier.notice('Read %d exclusions' % len(self.exclusions))
        except IOError:
            self.notifier.warning('Failed to read exclusions file')

    def open_journal(self):
        journal_filename = os.path.join(self.target, JOURNAL_FILENAME)
        try:
            journal_state = unpickle_file(journal_filename)
        except IOError:
            self.notifier.notice('Journal state not found, starting anew')
            journal_state = (None, None, {})
        drive = os.path.splitdrive(self.source)[0]
        self.journal = Journal(drive)
        self.journal.set_state(journal_state)
        self.notifier.notice('Opened journal')

    def close_journal(self):
        journal_filename = os.path.join(self.target, JOURNAL_FILENAME)
        journal_state = self.journal.get_state()
        pickle_to_file(journal_state, journal_filename)
        self.notifier.notice('Closed journal')
    
    def load_manifest(self):
        manifest_filename = os.path.join(self.target, MANIFEST_FILENAME)
        f = open(manifest_filename, 'rb')
        self.manifest = cPickle.load(f)
        f.close()
    
    def save_manifest(self):
        manifest_filename = os.path.join(self.target, MANIFEST_FILENAME)
        f = open(manifest_filename, 'wb')
        cPickle.dump(self.manifest, f)
        f.close()        

    def run(self):
        self.check_target()
        
        try:
            prev_filename = os.path.join(self.target, PREVIOUS_FILENAME)
            self.previous_name = unpickle_file(prev_filename)
        except IOError:
            self.previous_name = None
        
        self.read_exclusions()
        self.exclusions.add(self.target)
        
        if self.enable_journal:
            self.open_journal()
            self.journal.process()
        
        try:
            self.load_manifest()
        except IOError:
            self.manifest = {}
        
        self.backup_item('')
        
        self.save_manifest()
        
        if self.enable_journal:
            self.close_journal()
        
        prev_filename = os.path.join(self.target, PREVIOUS_FILENAME)
        pickle_to_file(self.name, prev_filename)


def parse_command_line(argv=None):
    parser = OptionParser(usage="%prog [options] SOURCE TARGET\n       %prog -h (for help)", add_help_option=True)
    parser.add_option("-n", "--name", default=None, action='store',
                      help="name of backup (defaults to date)")
    parser.add_option("-j", "--use-journal", default=False, action='store_true',
                      help="use USN journal")
    options, args = parser.parse_args(argv[1:])

    if len(args) != 2:
        parser.error('Source and target arguments required')
    
    if options.use_journal and not ALLOW_JOURNAL:
        parser.error('Journal cannot be used on this system')
    
    return options, args


def main(args=None):
    if args is None:
        args = sys.argv
    
    options, args = parse_command_line(args)
    
    backup = Backup()
    backup.notifier = ConsoleNotifier(backup)
    backup.source = args[0]
    backup.target = args[1]
    if options.name is not None:
        backup.name = options.name
    else:
        backup.name = time.strftime('%Y%m%d')
    backup.enable_dir_reuse = True
    if options.use_journal:
        backup.enable_journal = True
    backup.run()


if __name__ == '__main__':
    main()
