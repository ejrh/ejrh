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
        total_records = 0
        total_calls = 0
        
        first_frn = 0
        while True:
            first_frn, tups = jc.enum_usn_data(volh, first_frn, 0, next_usn)
            total_calls += 1
            if len(tups) == 0:
                break
            for t,fn in tups:
                #print first_frn, ",", t, ",", repr(fn)
                total_records += 1
        
        stop_time = time.clock()
        jc.close_volume(volh)
        
        print test_size, stop_time - start_time, total_records, total_calls
        
        test_size *= 2


if __name__ == '__main__':
    main()
