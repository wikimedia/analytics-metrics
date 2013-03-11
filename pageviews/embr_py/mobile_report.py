#!/usr/bin/python
import os.path
import sys
import subprocess
from pprint import pprint
from squidrow import SquidRow

if __name__ == '__main__':
    files_to_parse=[]

    while True:
      try:
        i = raw_input()
        files_to_parse.append(i)
      except:
        break

    # report data after parsing
    rdata={}

    if len(files_to_parse) > 0:
      print "error: no filenames came through STDIN"
      sys.exit(0)

    #if len(sys.argv) < 2:
        #print 'usage: find /home/user/comparative_test_evan/ -maxdepth 1 -name "*201211*" -o -name "*201212*" -o -name "sampled-1000.log-20130101.gz" | ./mobile_pageviews.py'
        #sys.exit(0)
    for fpath in files_to_parse:
      print "Processing file => "+fpath
      fname = os.path.split(fpath)[1]
      with open('%s.match' % fname, 'w') as fmatch, open('%s.no_match' % fname, 'w') as fno_match:
          lines = subprocess.Popen(['zcat', fpath], stdout=subprocess.PIPE).stdout
          for line in lines:
              try:
                  r = SquidRow(line)
                  if r.old_init_request() and r.lang() and r.site() == "M":
                    #fmatch.write(line)
                    time_key = str(r.datetime().year) + '-' + str(r.datetime().month)
                    if time_key not in rdata:
                      rdata[time_key] = {}

                    rdata[time_key][r.lang()] = rdata[time_key].get(r.lang(),0) + 1
                    #fno_match.write(line)
              except:
                  fno_match.write(line)
    pprint(rdata)

