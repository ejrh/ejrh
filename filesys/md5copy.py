import sys
import os
import hashlib


BLOCK_SIZE = 4*1048576


def copy_item(path1, path2, subpath):
    if not os.path.exists(path1):
        raise Exception, 'Source does not exist: ' + path1
    if os.path.isdir(path1):
        if not os.path.exists(path2):
            os.mkdir(path2)
        elif not os.path.isdir(path2):
            raise Exception, 'Target is wrong type: ' + path2
        for child_path in os.listdir(path1):
            new_path1 = os.path.join(path1, child_path)
            new_path2 = os.path.join(path2, child_path)
            new_subpath = os.path.join(subpath, child_path)
            copy_item(new_path1, new_path2, new_subpath)
    else:
        if os.path.exists(path2):
            return
        infile = open(path1, 'rb')
        outfile = open(path2, 'wb')
        m = hashlib.md5()
        while True:
            buffer = infile.read(BLOCK_SIZE)
            if len(buffer) == 0:
                break
            outfile.write(buffer)
            m.update(buffer)
        
        infile.close()
        outfile.close()
        print '%s *%s' %(m.hexdigest(), subpath)
        sys.stdout.flush()


from_path = sys.argv[1]
to_path = sys.argv[2]
copy_item(from_path, to_path, '')
