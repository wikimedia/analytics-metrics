#!/usr/bin/python
import os.path
import sys
import subprocess
import operator
import json
from collections import Counter
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
  rdata=defaultdict(Counter)

  ## url count with/without spaces
  #rspace={}


  if len(files_to_parse) < 1:
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
            if ( r.old_init_request()           and r.lang()                      and 
                r.lang()    != "meta"           and r.site()  == "M"              and 
                r.project() == "wikipedia"      and r.title() != "Special:Search" and 
                r.title()   != "Special:Random" and r.title() != "Special:BannerRandom"
                ):
              #print "[DBG]"+r.url()
              time_key = str(r.datetime().year) + '-' + str(r.datetime().month)
              rdata[time_key]['lang='        + r.lang()]        += 1
              rdata[time_key]['site='        + r.site()]        += 1
              rdata[time_key]['status_code=' + r.status_code()] += 1
              rdata[time_key]['host='        + r.host()]        += 1
              rdata[time_key]['mime_type'    + r.mime_type()]   += 1
              rdata[time_key]['netloc='      + r.netloc()]      += 1
              for arg_key in r.url_args().__keys__:
                rdata[time_key]['arg_key='+arg_key] += 1
              for arg_key in r.url_args().values():
                rdata[time_key]['arg_val='+arg_val] += 1
          except:
            1
  top_10_languages = sorted(rdata.items(), key=operator.itemgetter(1))[-10:]
  #pprint(top_10_languages)
  #json.dump(top_10_languages, open("/tmp/nov.json", 'w'))

