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
