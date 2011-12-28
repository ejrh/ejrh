import sys


def error(s):
    print >>sys.stderr, 'ERROR: %s' % s

def warn(s):
    print >>sys.stderr, 'WARNING: %s' % s

def notice(s):
    print >>sys.stderr, 'NOTICE: %s' % s
