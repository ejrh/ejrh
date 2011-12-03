import sys
import os


def all_null(name):
    f = open(name, "rb")
    #while True:
    for i in range(1):
        buf = f.read(16*1024)
        if len(buf) == 0:
            break
        for b in buf:
            if b != chr(0):
                f.close()
                return False
    f.close()
    return True


for dirpath, dirnames, filenames in os.walk(sys.argv[1]):
    for filename in filenames:
        filepath = os.path.join(dirpath, filename)
        try:
            if all_null(filepath):
                print filepath
        except:
            pass
