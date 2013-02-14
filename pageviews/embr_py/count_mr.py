import argparse
import csv
import logging
import pprint
from operator import itemgetter

from squid.mapreduce import count_files
from squid import SquidArgumentParser

# this change made from local machine

DEFAULT_PROVIDERS = ['zero-digi-malaysia',
                     'zero-grameenphone-bangladesh',
                     'zero-orange-kenya',
                     'zero-orange-niger',
                     'zero-orange-tunesia',
                     'zero-orange-uganda',
                     'zero-orange-cameroon',
                     'zero-orange-ivory-coast',
                     'zero-telenor-montenegro',
                     'zero-tata-india',
                     'zero-saudi-telecom',
                     'zero-dtac-thailand']


def parse_args():

    parser = SquidArgumentParser(description='Process a collection of squid logs and write certain extracted metrics to file')
    parser.add_argument('providers', 
                        metavar='PROVIDER_IDENTIFIER',
                        nargs='*',
                        default=DEFAULT_PROVIDERS,
                        help='list of provider identifiers used in squid log file names')
    parser.add_argument('--name_format',
                        dest='name_format',
                        type=str,
                        default='%s.log-%.gz',
                        help='a printf style format string which is formatted with the tuple: (provider_name, date_representation')
    parser.set_defaults(datadir='/a/squid/archive/zero')


    args = parser.parse_args()
    # custom logic for which files to grab
    prov_files = {}
    for prov in args.providers:
        args.basename = prov
        logging.info('args prior to ge_files: %s', pprint.pformat(args.__dict__))
        prov_files[prov] = SquidArgumentParser.get_files(args)
    setattr(args, 'squid_files', prov_files)

    
    logging.info(pprint.pformat(args.__dict__))
    return args

def main():
    args = parse_args()

    keepers = ['date', 'project', 'language', 'site']

    criteria = [
            lambda r : r['datetime'] > args.start,
            lambda r : r['datetime'] < args.end,
            lambda r : r['old_init_request']
    ]

    for prov in args.providers:
        counts = count_files(args.squid_files[prov], keepers, criteria, count_event=10)
        rows = [fields + (count,) for fields,count in counts.items()]
        rows = [map(str,row) for row in rows]
        rows.sort(key=itemgetter(*range(len(keepers))))
        with open('%s.counts.csv' % prov, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(keepers + ['count',])
            writer.writerows(rows)

if __name__ == '__main__':
    main()
