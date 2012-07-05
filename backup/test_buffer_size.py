import journalcmd as jc
import time

def main(argv=None):
    min_size = 4096
    max_size = 1048576
    
    drive = 'C:'
    
    test_size = min_size
    while test_size <= max_size:
        jc.USN_BUFFER_SIZE = test_size
        volh = jc.open_volume(drive)
        tup = jc.query_journal(volh)
        next_usn = tup[2]
        start_time = time.clock()
        for tup,fn in jc.generate_usns(volh, 0, next_usn):
            pass
        stop_time = time.clock()
        jc.close_volume(volh)
        
        print test_size, stop_time - start_time
        
        test_size *= 2


if __name__ == '__main__':
    main()
