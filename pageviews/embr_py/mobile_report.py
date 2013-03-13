#!/usr/bin/python
import os.path
import sys
import subprocess
import operator
import json
from collections import Counter, defaultdict
import pprint
from pprint import pprint
from squidrow import SquidRow
import copy
import matplotlib


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
        for i, line in enumerate(lines):
          if i > 10000000:
              break
          try:
            r = SquidRow(line)
            if ( r.old_init_request()           and r.lang()                      and 
                r.lang()    != "meta"           and r.site()  == "M"              and 
                r.project() == "wikipedia"      and r.title() != "Special:Search" and 
                r.title()   != "Special:Random" and r.title() != "Special:BannerRandom"
                ):
              #print "[DBG]"+r.url()
              #time_key = str(r.datetime().year) + '-' + str(r.datetime().month)
              time_key = str(r.date())
              rdata[time_key]['lang='        + r.lang()]             += 1
              rdata[time_key]['site='        + r.site()]             += 1
              rdata[time_key]['status_code=' + str(r.status_code())] += 1
              rdata[time_key]['host='        + r.host()]             += 1
              rdata[time_key]['mime_type'    + r.mime_type()]        += 1
              rdata[time_key]['netloc='      + str(r.netloc())]      += 1
              for arg_key in r.url_args().keys():
                rdata[time_key]['arg_key='+arg_key] += 1
              for item    in r.url_args().items():
                rdata[time_key]['arg_val='+str(item)] += 1
          except:
            1

  #
  # We decided on some features above ^^
  # And now we get the features with the biggest difference between each two consecutive days
  # Hopefuly among those, we will be able to find some features which explain the bump.
  #

  sorted_rdata = sorted(rdata.items())
  #pprint(sorted_rdata[1:])
  for (first_date, first_counter), (second_date, second_counter) in zip(sorted_rdata, sorted_rdata[1:]) + zip(sorted_rdata[:1], sorted_rdata[-1:]):
  #for (first_date, first_counter), (second_date, second_counter) in zip(sorted_rdata[:1], sorted_rdata[-1:]):
      difference = copy.deepcopy(second_counter)
      difference.subtract(first_counter)
      print '###########################################'
      print 'first_date: %s, second_date: %s' % (first_date, second_date)
      pprint(difference.most_common(10))

