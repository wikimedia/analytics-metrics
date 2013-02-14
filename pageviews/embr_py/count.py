import sys
import csv
import logging
import pprint
from operator import itemgetter
from collections import Counter
from subprocess import Popen, PIPE
import multiprocessing
import itertools
from squidrow import SquidRow
import logging

logger = logging.getLogger(__name__)

def count_file(fname):
    counter = Counter()
    f = Popen(['zcat', fname], stdout=PIPE)
    for i, line in enumerate(f.stdout):
        try:
            if i > LIMIT:
                break
            if i % 10000 == 0:
                logger.info('processing %d lines of file %s', i, fname)
            row = SquidRow(line)
            failed = False
            for criterion in CRITERIA:
                if not criterion(row):
                    failed = True
                    break
            if not failed:
                counter[tuple([row[field] for field in FIELDS])] += COUNT_EVENT
        except:
            logger.exception('exception found while processing line: %s', line)
            counter[(None,)*len(FIELDS)] += COUNT_EVENT
    return counter 


def count_files(files, fields, criteria=[lambda r:r['old_init_request']], count_event=1, limit=()):
    """
    Uses zcat to avoid slownss of gzip module
    Arguments:
        -f (str)            : gzipped filename
        -fields (list(str)) : list of fields to extract from each row
        -criteria           : list of predicate functions to be applied to each line
        -count_event (int)  : inverse sampling rate; i.e. how much to increment counter each time a page
                              satisfies all of the criteria
        -limit              : number of lines IN EACH FILE to process before exiting
    """
    global FIELDS, CRITERIA, COUNT_EVENT, LIMIT
    FIELDS = fields
    CRITERIA = criteria
    COUNT_EVENT = count_event
    LIMIT = limit 
    pool = multiprocessing.Pool(min(len(files), 20))
    counters = pool.map(count_file, files)
    merged_counter = reduce(Counter.__or__, counters, Counter())
    return merged_counter


def main():
    if len(sys.argv) < 2:
        print 'usage: count_mr.py SQUID_FILE ... [SQUID_FILE]'
        sys.exit(0)
    files = sys.argv[1:]
    logging.info('processing files:\n%s', pprint.pformat(files))

    keepers = ['date', 'project', 'language', 'site']

    criteria = [
            lambda r : r['old_init_request']
    ]

    counts = count_files(sys.argv[1:], keepers, criteria, count_event=10)
    rows = [fields + (count,) for fields,count in counts.items()]
    rows = [map(str,row) for row in rows]
    rows.sort(key=itemgetter(*range(len(keepers))))
     
    with open('counts.csv' , 'w') as csvfile:
        writer = csv.writer(sys.stdout)
        writer.writerow(keepers + ['count',])
        writer.writerows(rows)

if __name__ == '__main__':
    main()
