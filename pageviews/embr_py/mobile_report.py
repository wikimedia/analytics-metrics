import os.path
import sys
import subprocess
from pprint import pprint
from squidrow import SquidRow


# rdata
rdata={}



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
                if r.old_init_request() and r.lang() and r.site() == "M":
                  fmatch.write(line)
                  time_key = str(r.datetime().year) + '-' + str(r.datetime().month)
                  if time_key not in rdata:
                    rdata[time_key] = {}

                  rdata[time_key][r.lang()] = rdata[time_key].get(r.lang(),0) + 1
                else:
                  fno_match.write(line)
            except:
                fno_match.write(line)
        pprint(rdata)


