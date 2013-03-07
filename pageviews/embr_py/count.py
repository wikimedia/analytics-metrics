import os.path
import sys
import subprocess
from squidrow import SquidRow

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'usage: count.py SQUID_FILE'
        sys.exit(0)
    fpath = sys.argv[1]
    fname = os.path.split(fpath)[1]
    with open('%s.match' % fname, 'w') as fmatch, open('%s.no_match' % fname, 'w') as fno_match:
        lines = subprocess.Popen(['zcat', fpath], stdout=subprocess.PIPE).stdout
        for line in lines:
            try:
                r = SquidRow(line)
                if r.old_init_request():
                    fmatch.write(line)
                else:
                    fno_match.write(line)
            except:
                fno_match.write(line)
