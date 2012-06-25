import os
import struct
import win32file
import winioctlcon
import pywintypes


def make_hardlink(dest_path, link_path):
    win32file.CreateHardLink(dest_path, link_path)


def make_symlink(dest_path, link_path):
    try:    
        win32file.CreateSymbolicLink(dest_path, link_path, 1)   # SYMBOLIC_LINK_FLAG_DIRECTORY
    except NotImplementedError:
        make_reparse_point(dest_path, link_path)


# Reference: http://msdn.microsoft.com/en-us/library/cc232007%28PROT.13%29.aspx
def make_reparse_point(dest, link):
    if dest[-1] == '/' or dest[-1] == '\\':
        dest = dest[:len(dest)-1]
    
    link = os.path.abspath(link)
    
    if link[-1] == '/' or link[-1] == '\\':
        link = link[:len(link)-1]
    os.mkdir(dest)
    dirh = win32file.CreateFile(dest, win32file.GENERIC_READ | win32file.GENERIC_WRITE, 0, None, 
            win32file.OPEN_EXISTING, win32file.FILE_FLAG_OPEN_REPARSE_POINT| win32file.FILE_FLAG_BACKUP_SEMANTICS, None)
    tag = 0xA0000003L
    link = '\\??\\' + link
    link = link.encode('utf-16')[2:]
    datalen = len(link)
    inp = struct.pack('LHHHHHH', tag, datalen+8+4, 0, 0, datalen, datalen+2, 0) + link + '\0\0\0\0'
    try:
        win32file.DeviceIoControl(dirh, winioctlcon.FSCTL_SET_REPARSE_POINT, inp, None)
    except:
        os.rmdir(dest)
        raise
    finally:
        win32file.CloseHandle(dirh)


def print_info(dest):
    if dest[-1] == '/' or dest[-1] == '\\':
        dest = dest[:len(dest)-1]
    dirh = win32file.CreateFile(dest, win32file.GENERIC_READ, 0, None, 
            win32file.OPEN_EXISTING, win32file.FILE_FLAG_OPEN_REPARSE_POINT| win32file.FILE_FLAG_BACKUP_SEMANTICS, None)
    MAX_SIZE = 1024
    buf = win32file.DeviceIoControl(dirh, winioctlcon.FSCTL_GET_REPARSE_POINT, None, MAX_SIZE)
    print buf.encode('hex')
    print repr(buf)
