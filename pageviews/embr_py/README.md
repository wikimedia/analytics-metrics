## Usage

this approach uses the python library [squidpy](github.com/embr/squidpy) which implements a variety of utility methods for manipulating squid log files.  The squidrow.py file has been copied directly from that library as of revision:

`c83856652f2af416185b8c83aadf93d9cfdcf8ea`

To run this script on a batch of squid logs, invoke it with:

````
$ python count.py /a/squid/archive/zero/zero-orange-uganda.log-20130101.gz
````

which currently generates three files: %s.match, %s.no_match, consisting of the respective lines from the input files

## Methodology

this script does the bare minium in terms of filtering: only checking whether the url path begins with '/wiki', which corresponds to the flow chart below:

![Flow chart](https://raw.github.com/embr/metrics/master/pageviews/embr_py/Pageview_definition.png)
