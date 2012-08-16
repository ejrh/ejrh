import os, stat, time
import hashlib, codecs
import re
import platform
import socket
from optparse import OptionParser

from importer import Importer, Item, exception_info


WINDOWS = (platform.system() == 'Windows')


class Model(object):
    def __init__(self):
        if WINDOWS:
            fs_codec = 'latin_1'
        else:
            fs_codec = 'utf_8'
        self.fs_decode = codecs.getdecoder(fs_codec)
        self.fs_encode = codecs.getencoder(fs_codec)
    
        self.hostname = socket.gethostname()

        self.drive_re = re.compile('[A-Za-z]:$')
        self.leading_slash_re = re.compile('^/')

    def get_list(self, path):
        list = []
        
        if path in ['']:
            item = Item()
            item.name = self.hostname
            item.path = '/' + self.hostname
            item.actual_path = '/'
            item.is_dir = True
            item.is_drive = True
            item.total_space,item.free_space = None,None
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
                
                # If it's a drive, try to get drive info.
                if item.is_drive:
                    try:
                        import win32file
                        dummy,item.total_space,item.free_space = win32file.GetDiskFreeSpaceEx(item.actual_path)
                    except:
                        item.total_space,item.free_space = None,None
                
                list.append(item)
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
        return list

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
    
    os.stat_float_times(False)
    
    model = Model()
    
    imp = Importer(model)
    imp.run(path, options.db_host)
