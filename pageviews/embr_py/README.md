this approach uses the python library (squipy)[github.com/embr/squidpy] which implements a variety of utility methods for manipulating squid log files.  The squidrow.py file has been copied directly from that library as of revision:

`70807af566efd5e3dfdfd53ce20344b7efd68852`

To run this script on a batch of squid logs, invoke it with:

````
$ python count.py /a/squid/archive/zero/zero-orange-uganda.log-20130101.gz
````

which currently prints to stdout a csv of the following format:

````
# date, project, language, site, count
2012-12-31,wikipedia,ar,X,10
````

## Methodolody

this script does the bare minium in terms of filtering: only checking whether the url path begins with '/wiki', which corresponds to the flow chart below:

![Flow chart](username.github.com/embr/metrics/pageviews/embr_py/Pageview_definition.png)
