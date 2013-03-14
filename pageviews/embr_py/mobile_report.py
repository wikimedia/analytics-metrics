#!/usr/bin/python
from jinja2 import Template
import re
import os.path
import sys
from itertools import chain
from sets import Set
import subprocess
import operator
import json
from collections import Counter, defaultdict
import pprint
from pprint import pprint
from squidrow import SquidRow
import copy
import matplotlib
import numpy as np
import matplotlib.pyplot as plt



class SimpleBarChart:
  def __init__(self):
    self.fig = plt.figure()
    self.ax  = self.fig.add_subplot(111)
    self.fig.set_figheight( 9)
    self.fig.set_figwidth( 27)
  def setTitle(self,title):
    self.ax.set_title(title)
  def populate(self,bars,labels):
    # Generating bar charts for each of the features
    N = len(bars)
    heights = bars

    ind = np.arange(N)  # the x locations for the groups
    width = 0.35      # the width of the bars

    self.rects = self.ax.bar(ind, heights, width, color='r')

    # add some
    self.ax.set_ylabel('Counts')
    self.ax.set_xticks(ind+width)
    self.ax.set_xticklabels( labels )
    self.ax.set_ylim(top=1.2*max(heights))

    plt.xticks(rotation=90)

  def saveToDisk(self,path):
    def autolabel(rects):
        ## attach some text labels
        for rect in rects:
            height = rect.get_height()
            self.ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),
                    ha='center', va='bottom')
    autolabel(self.rects)
    self.fig.savefig(path)





if __name__ == '__main__':
  files_to_parse=[]

  limit_rows = 300000000000
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
          if i > limit_rows:
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
              rdata[time_key]['lang='        + str(r.lang())]        += 1
              rdata[time_key]['site='        + str(r.site())]        += 1
              rdata[time_key]['status_code=' + str(r.status_code())] += 1
              rdata[time_key]['host='        + str(r.host())]        += 1
              rdata[time_key]['mime_type='   + str(r.mime_type())]   += 1
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


  print "Generating bar charts"

  # Collect present keys in features
  keys_lang       = Set()
  keys_mimetype   = Set()
  keys_site       = Set()
  keys_host       = Set()
  keys_netloc     = Set()
  keys_statuscode = Set()


  for key in list(chain.from_iterable(
      [x[1].keys() for x in sorted_rdata])
    ):
    if   key.startswith("lang"):
      keys_lang.add(key)
    elif key.startswith("mime_type"):
      keys_mimetype.add(key)
    elif key.startswith("site"):
      keys_site.add(key)
    elif key.startswith("status_code"):
      keys_statuscode.add(key)
    elif key.startswith("host"):
      keys_host.add(key)
    elif key.startswith("netloc"):
      keys_netloc.add(key)
  print(keys_mimetype)


  dates=sorted(rdata.keys())

  #g.populate(map(lambda x: 300,range(1,60)),map(lambda x: "lbl"+str(x),range(1,60)  ))


  
  filenames_charts = []

  for key_class in [keys_lang,keys_site,keys_statuscode,keys_host,keys_netloc,keys_mimetype]:
    for k in key_class:
      v = []
      for d in dates:
        if rdata[d][k]:
          v.append(rdata[d][str(k)])
        else:
          v.append(0)

      g = SimpleBarChart()
      g.populate(v,dates)
      g.setTitle("Chart for key => "+k)

      filename = "chart_"+k+".png"
      filename = re.sub("[\/\s]","_",filename)
      filenames_charts.append(filename)
      g.saveToDisk(filename)


  tmpl = Template(u'''\
  <!DOCTYPE html>
  <html>
    <head>
      <title>Charts</title>
    </head>
    <body>
    {%- for item in filenames_charts %}
      <img src="{{ item }}"/>
      <br/>
    {%- endfor %}
    </body>
  </html>
  ''')

  with open("charts.html", "wb") as fh:
    fh.write(tmpl.render(filenames_charts = filenames_charts))


