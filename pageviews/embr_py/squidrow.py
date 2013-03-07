import os
import os.path
import pprint
import datetime
from urlparse import urlparse, parse_qs
import urllib
import inspect
import re
import logging
import json
import netaddr
import pygeoip
"""
logging set up
"""
root_logger = logging.getLogger()
ch = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s]\t[%(threadName)s]\t[%(funcName)s:%(lineno)d]\t%(message)s')
ch.setFormatter(formatter)
root_logger.addHandler(ch)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

"""

Initialize file pointers and fail with warning message.
this way thing work as expected if you have the files in the
default location, otherwise, you can just call squidrow.load...
(not that squidrow is the module, not the class)
with the relevant file path after squidrow has been imported
"""

cidr_ranges = None
cidr_ranges_full = None
gi = None
mcc_mnc = None

def load_cidr_ranges(path = os.path.join(os.path.split(__file__)[0], 'cidr_ranges.json')):
    global cidr_ranges, cidr_ranges_full
    #logger.debug('calling load_cidr_ranges')
    try:
        cidr_ranges = json.load(open(path))
        cidr_ranges_full = {}
        for prov, cidrs in cidr_ranges.items():
            for cidr in cidrs:
                cidr_ranges_full[cidr] = prov
        cidr_ranges = {prov : netaddr.IPSet([netaddr.IPNetwork(cidr) for cidr in cidrs]) for prov, cidrs in cidr_ranges.items()}
        logger.debug('cidr_ranges: %s', cidr_ranges)
    except:
        logger.exception('could not load cidr_range_file from: %s', path)

def load_pygeoip_dat(path = '/usr/share/GeoIP/GeoIPCity.dat'):
    global gi
    try:
        # MaxMind GeoIP setup
        gi = pygeoip.GeoIP(path)
        # print 'gi: %s' % gi
    except:
        logger.exception('could not load geoip database from: %s', path)

def load_pygeoip_archive(path = '/home/erosen/tmp/geoip/'):
    global gi_archive
    gi_archive = {}
    for version_dir in os.listdir(path):
        logger.debug('processing dir: %s', version_dir)
        try:
            # 133 is city data, 106 is country level only
            m = re.match('GeoIP-133_(\d{8})', version_dir)
            logger.debug('m: %s', m)
            if m:
                logger.debug('m.groups(): %s', m.groups())
                d_str = m.groups()[0]
                d = datetime.datetime.strptime(d_str, '%Y%m%d').date()
                dat_path = os.path.join(path, version_dir, 'GeoIPCity-133.dat')
                if not os.path.exists(dat_path):
                    dat_path = os.path.join(path, version_dir, 'GeoIPCity.dat')
                gi_archive[d] = pygeoip.GeoIP(dat_path)
        except ValueError:
            logger.exception('error when parsing date from version_dir: %s', version_dir)
        except:
            logger.exception('error when parsing version_dir: %s', version_dir)
            raise

def load_mcc_mnc(path = os.path.join(os.path.split(__file__)[0], 'mcc_mnc.json')):
    global mcc_mnc
    try:
        mcc_mnc = json.load(open(path))
    except:
        logger.exception('could not load mcc_mnc file from: %s', path)


logger.debug('doing module level initialization')
load_cidr_ranges()
load_pygeoip_archive()
load_mcc_mnc()



class SquidRow(object):
    """ Class to represent a row from a squid file, giving access to both the literal field values
        and various derived classes.  It has a little fanciness to deal with lazily computing
        and caching infrequently-used derived fields so that it is still fast for basic file scanning.
        Specifically use the @cache decorator to specify that a function 'field_name' should be invoked when
        a row instance is called with  __getitem__('field_name').

        Example:
        >>> import squid
        >>> raw_row = 'amssq44.esams.wikimedia.org 639333046 2012-09-18T06:49:35.030 1 0.0.0.0 TCP_MISS/200 9988 GET http://da.wikipedia.org/wiki/Drakestr%C3%A6det CARP/91.198.174.55 text/html http://www.google.dk/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&sqi=2&ved=0CCAQFjAA&url=http%3A%2F%2Fda.wikipedia.org%2Fwiki%2FDrakestr%25C3%25A6det&ei=fBlYUNrTCsjOswap-oG4Bw&usg=AFQjCNG4qsU7flSVpnLD8RR79yrL5FRoPA&sig2=AZnQmKDYxtVwds284S8fiA - Mozilla/5.0%20(Windows%20NT%206.1)%20AppleWebKit/537.1%20(KHTML,%20like%20Gecko)%20Chrome/21.0.1180.89%20Safari/537.1'
        >>> row = squid.SquidRow(raw_row)
        >>> row.status_code()
        200
        >>> row.lang()
        'da'
        >>> row.project()
        'wikipedia'
        >>> row.date()
        '2012-09-18'

    """


    ids = ['host',              #1
            'seq',              #2
            'timestamp',        #3
            'req_time',         #4
            'ip',               #5
            'status',           #6
            'reply_size',       #7
            'method',           #8
            'url',              #9
            'squid_hierarchy',  #10
            'mime_type_raw',    #11
            'ref_header',       #12
            'xff_header',       #13
            'agent_header_raw', #14
            'accepted_langs',   #15
            'x-cs']             #16

    
    def cache(fn):
        
        def decorated_function(*args, **kwargs):
            slf = args[0]
            key = (fn.__name__, args[1:], tuple(sorted(kwargs.items())))
            #print 'key: %s' % (key,)
            if key in slf.__cache__:
                return slf.__cache__[key]
            else:
                rval = fn(*args,**kwargs)
                slf.__cache__[key] = rval
                return rval
        return decorated_function


    def __init__(self, line):
        self.__line__ = line
        self.__cache__ = {}
        toks = line.strip().split()
        ntoks = len(toks)
        if ntoks == 14:
            self.__deleted_tok__ = False
            self.__row__ = toks + [None,None]
        elif ntoks == 15:
            del toks[11]
            self.__deleted_tok__ = True
            self.__row__ = toks + [None,None]
        elif ntoks == 16:
            self.__deleted_tok__ = False
            self.__row__ = toks
        elif ntoks == 17:
            del toks[11]
            self.__deleted_tok__ = True
            self.__row__ = toks

        else:
            logging.exception('malformed line disovered with %d toks:\n\n%s\n', ntoks, line)
            raise ValueError('malformed line disovered with %d toks:\n\nt%s\n', ntoks, line)


    def __repr__(self):
        return 'line: %s\n__row__:%s' %  (self.__line__, pprint.pformat(self.__row__))




    # getters for the basic raw fields
    def host(self):
        return self.__row__[0]
    def seq(self):
        return self.__row__[1]
    def timestamp(self):
        return self.__row__[2]
    def req_time(self):
        return self.__row__[3]
    def ip(self):
        return self.__row__[4]
    def status(self):
        return self.__row__[5]
    def reply_size(self):
        return self.__row__[6]
    def method(self):
        return self.__row__[7]
    def url(self):
        return self.__row__[8]
    def squid_hierarchy(self):
        return self.__row__[9]
    def mime_type_raw(self):
        return self.__row__[10]
    def ref_header(self):
        return self.__row__[11]
    def xff_header(self):
        return self.__row__[12]
    def agent_header_raw(self):
        return self.__row__[13]
    def accepted_langs(self):
        return self.__row__[14]
    def x_cs(self):
        return self.__row__[15]

    def deleted_tok(self):
        return self.__deleted_tok__

    @cache
    def agent_header(self):
        """returns an unquoted version of the agent header"""
        return urllib.unquote(self.agent_header_raw())

    @cache
    def mime_type(self):
        """
        returns a canonicalized version of the mimetype string--specifically just removes a trailing `;` which
        is always present in mobile requests.
        """
        if self.mime_type_raw() and self.mime_type_raw()[-1] == ';':
            return self.mime_type_raw()[:-1]
        else:
            return self.mime_type_raw()

    @cache
    def action(self):
        """parsed out the action url param if present, otherwise returns None"""
        return self.url_args().get('action', [None])[0]

    @cache
    def url_args(self):
        """returns a dict of url parameters"""
        return parse_qs(self.url_parsed().query)

    @cache
    def xff_parsed(self):
        """
        returns the an instance of urllib2.ParseResult from callig urllib2.urlparse on the raw xff_header field.
        This provides things like the schema, domain name, url parameters, port number and lots of other goodies
        """
        return urlparse(self.xff_header())

    @cache
    def xff_args(self):
        """ returns the url parameters from the xff_header url"""
        return parse_qs(self.xff_parsed())

    @cache
    def url_parsed(self):
        """
        returns the an instance of urllib2.ParseResult from callig urllib2.urlparse on the raw url field.
        This provides things like the schema, domain name, url parameters, port number and lots of other goodies
        """
        return urlparse(self.url())

    @cache
    def netloc(self):
        """returns a list of subdomains"""
        return self.url_parsed().netloc.split('.')

    @cache
    def netloc_parsed(self):
        """
        returns a dict of the form {'project' : project, 'site' : site, 'lang' : lang}
        where:
        * project is in the set {wikipedia, meta.wikimedia, wiktionary, ...}
        * site is in the set {M,Z.X} which correspond to urls with the m., zero. or no subdomain, respectively
        * lang is in the set {en, de, fr, nl, it, ...}
        """
        lang_ids = ['en', 'de', 'fr', 'nl', 'it', 'pl', 'es', 'ru', 'ja', 'pt', 'sv', 'zh', 'uk', 'ca', 'no', 'fi', 'cs', 'hu', 'tr', 'ro', 'ko', 'vi', 'da', 'ar', 'eo', 'sr', 'id', 'lt', 'vo', 'sk', 'he', 'fa', 'bg', 'sl', 'eu', 'war', 'lmo', 'et', 'hr', 'new', 'te', 'nn', 'th', 'gl', 'el', 'ceb', 'simple', 'ms', 'ht', 'bs', 'bpy', 'lb', 'ka', 'is', 'sq', 'la', 'br', 'hi', 'az', 'bn', 'mk', 'mr', 'sh', 'tl', 'cy', 'io', 'pms', 'lv', 'ta', 'su', 'oc', 'jv', 'nap', 'nds', 'scn', 'be', 'ast', 'ku', 'wa', 'af', 'be-x-old', 'an', 'ksh', 'szl', 'fy', 'frr', 'yue', 'ur', 'ia', 'ga', 'yi', 'sw', 'als', 'hy', 'am', 'roa-rup', 'map-bms', 'bh', 'co', 'cv', 'dv', 'nds-nl', 'fo', 'fur', 'glk', 'gu', 'ilo', 'kn', 'pam', 'csb', 'kk', 'km', 'lij', 'li', 'ml', 'gv', 'mi', 'mt', 'nah', 'ne', 'nrm', 'se', 'nov', 'qu', 'os', 'pi', 'pag', 'ps', 'pdc', 'rm', 'bat-smg', 'sa', 'gd', 'sco', 'sc', 'si', 'tg', 'roa-tara', 'tt', 'to', 'tk', 'hsb', 'uz', 'vec', 'fiu-vro', 'wuu', 'vls', 'yo', 'diq', 'zh-min-nan', 'zh-classical', 'frp', 'lad', 'bar', 'bcl', 'kw', 'mn', 'haw', 'ang', 'ln', 'ie', 'wo', 'tpi', 'ty', 'crh', 'jbo', 'ay', 'zea', 'eml', 'ky', 'ig', 'or', 'mg', 'cbk-zam', 'kg', 'arc', 'rmy', 'gn', '(closed)', 'so', 'kab', 'ks', 'stq', 'ce', 'udm', 'mzn', 'pap', 'cu', 'sah', 'tet', 'sd', 'lo', 'ba', 'pnb', 'iu', 'na', 'got', 'bo', 'dsb', 'chr', 'cdo', 'hak', 'om', 'my', 'sm', 'ee', 'pcd', 'ug', 'as', 'ti', 'av', 'bm', 'zu', 'pnt', 'nv', 'cr', 'pih', 'ss', 've', 'bi', 'rw', 'ch', 'arz', 'xh', 'kl', 'ik', 'bug', 'dz', 'ts', 'tn', 'kv', 'tum', 'xal', 'st', 'tw', 'bxr', 'ak', 'ab', 'ny', 'fj', 'lbe', 'ki', 'za', 'ff', 'lg', 'sn', 'ha', 'sg', 'ii', 'cho', 'rn', 'mh', 'chy', 'ng', 'kj', 'ho', 'mus', 'kr', 'hz', 'mwl', 'pa', 'xmf', 'lez']
        site_ids = {'m' : 'M', 'zero' : 'Z'}
        netloc = self.netloc()

        ## make sure www isn't in here
        if netloc[0] == 'www':
            netloc = netloc[1:]

        # strip www prefix if present
        if netloc[0] == 'www':
            netloc = netloc[1:]

        # get lang if present
        if netloc[0] in lang_ids:
            lang = netloc[0]
            netloc = netloc[1:]
        else:
            lang = None

        # get site if present
        if netloc[0] in site_ids:
            site = site_ids[netloc[0]]
            netloc = netloc[1:]
        else:
            site = 'X'

        # get project
        project = '.'.join(netloc[:-1])
        return {'project' : project, 'site' : site, 'lang' : lang}

    @cache
    def site(self):
        """
        returns a value in the set {M,Z.X} which correspond to whether the  m., or zero. s
        ubdomains were present or no subdomain at all, respectively
        """
        return self.netloc_parsed()['site']

    @cache
    def lang(self):
        """returns the language code in the url if present, else None"""
        return self.netloc_parsed()['lang']

    @cache
    def language(self):
        """returns the language code in the url if present, else None"""
        return self.netloc_parsed()['lang']

    @cache
    def project(self):
        """returns the project subdomains--that is everything other than the language code
        the site version ('m.','zero.') and the trailing .org"""
        return self.netloc_parsed()['project']

    @cache
    def bot(self):
        """simple regex to catch bots which identify themselves in the agent header using varints of the word bot or spider"""
        bot_pat = ".*([Bb][Oo][Tt])|([Cc]rawl(er)?)|([Ss]pider)|(http://).*"
        return bool(re.match(bot_pat, self.agent_header()))

    @cache
    def url_path(self):
        return self.url_parsed().path.split('/')[1:]

    @cache
    def datetime(self):
        """returns a datetime.datetime instance of the timestamp"""
        # format: 2012-07-16T06:51:29.534
        try:
            return datetime.datetime.strptime(self.timestamp(), '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            # sometimes there are no seconds ...
            return datetime.datetime.strptime(self.timestamp(), '%Y-%m-%dT%H:%M:%S')

    @cache
    def date(self):
        """returns a datetime.date instance of the timestamp"""
        return self.datetime().date()

    @cache
    def title(self):
        """returns the title of the page, if it is a standard /wiki/<Title> article url"""
        path = self.url_path()
        if path[0] != 'wiki':
            return None
        return path[-1]

    @cache
    def device_type(self):
        """
        this function uses regexes found in Erik Zachte and Andre Engels code:
        
           https://svn.wikimedia.org/viewvc/mediawiki/trunk/wikistats/squids/SquidCountArchiveProcessLogRecord.pm?view=markup

        (with some minor perl-to-python modifications) to tag user agent strings with device type.
        When a string is tagged as multiple categories i user a handwritten ordering of tag precedence
        in attempt to compensate for the broad nature of the mobile category
        """
        tags = {}
        tags['-'] = '^-$'
        tags['wiki_mobile'] = "CFNetwork|Dalvik|WikipediaMobile|Appcelerator|WiktionaryMobile|Wikipedia Mobile"
        tags['mobile'] = "Android|BlackBerry|Windows CE|DoCoMo|iPad|iPod|iPhone|HipTop|Kindle|LGE|Linux arm|MIDP|NetFront|Nintendo|Nokia|Obigo|Opera Mini|Opera Mobi|Palm|Playstation|Samsung|SoftBank|SonyEricsson|Symbian|UP\.Browser|Vodafone|WAP|webOS|HTC[^P]|KDDI|FOMA|Polaris|Teleca|Silk|ZuneWP|HUAwei|Sunrise XP|Sunrise/|AUDIOVOX|LG/U|AU-MIC|Motorola|portalmmm|Amoi|GINGERBREAD|Spice|lgtelecom|PlayBook|KYOCERA|Opera Tablet|Windows Phone|UNTRUSTED|Sensation|UCWEB|Nook|XV6975|EBRD1|Rhodium|UPG|Symbian|Pantech|MeeGo|Tizen"
        tags['tablet'] = "iPad|Android 3|SCH-I800|Kindle Fire|Xoom|GT-P|Transformer|SC-01C|pandigital|SPH-P|STM803HC|K080|SGH-T849|CatNova|NookColor|M803HC|A1_|SGH-I987|Ideos S7|SHW-M180|HomeManager|HTC_Flyer|PlayBook|Streak|Kobo Touch|LG-V905R|MID7010|CT704|Silk|MID7024|ARCHM|Iconia|TT101|CT1002|; A510|MID_Serials|ZiiO10|MID7015|001DL|MID Build|PM1152|RBK-490|Tablet|A100 Build|ViewPad|PMP3084|PG41200|; A500|A7EB|A80KSC"
        matches = {}
        for device_type, tags in tags.items():
            match = re.match('.*(?:%s).*' % (tags), self.agent_header())
            if match:
                matches[device_type] = match
        # use inverse popularity as precedence ordering
        #logging.debug('matches: %s' % (matches.keys()))
        if 'tablet' in matches:
            return 'tablet'
        if 'wiki_mobile' in matches:
            return 'wiki_mobile'
        if 'mobile' in matches:
            return 'mobile'
        if '-' in matches:
            return '-'
        else:
            #logging.debug('no matches found. ua: %s' % (ua))
            return 'unknown'

    @cache
    def status_code(self):
        """
        returns the numerical http status code for the request.  Deals with the squid log tendency 
        to combine the cache status with the http status
        """
        if '/' in self.status():
            status_str = self.status().split('/')[1]
        else:
            logging.debug('found non-backslash delimited status field: %s', self.status())
            status_str = self.status()
        try:
            status = int(status_str)
        except ValueError:
            logging.warning('could not decode status: %s', self.status())
            status = None
        return status

    @cache
    def init_request(self):
        """returns whether the log line represents a text/html request with status code < 300 whose url path starts with /wiki/"""
        return self.mime_type() == 'text/html' and self.status_code() < 300 and self.url_path() and self.url_path()[0] == 'wiki'

    @cache
    def old_init_request(self):
        """returns whether the log line represents a request to an article with url format /wiki/<title>"""
        return self.url_path() and self.url_path()[0] == 'wiki'




    # GeoIP Stuff
    @cache
    def geoip_db_date(self, date):
        return next(d for d in sorted(gi_archive.keys(), reverse=True) if d < date)

    @cache
    def geo_record(self, date=None):
        if date is None:
            date = self.date()
        if gi_archive is None:
            return None
        gi_recent_date = self.geoip_db_date(date)
        gi_recent = gi_archive[gi_recent_date]
        # find most recent maxmind db at time of query
        try:
            rec = gi_recent.record_by_addr(self.ip())
        except:
            logger.error('failed to find record for ip: %s, using geoip db from %s', self.ip(), gi_recent_date)
        return rec
   
    @cache
    def country(self, date=None):
        rec = self.geo_record(date)
        return rec['country_code'] if rec else None

    @cache
    def country_code2(self, date=None):
        rec = self.geo_record(date)
        return rec['country_code'] if rec else None

    @cache
    def country_code3(self, date=None):
        rec = self.geo_record(date)
        return rec['country_code3'] if rec else None

    @cache
    def country_name(self, date=None):
        rec = self.geo_record(date)
        return rec['country_name'] if rec else None

    @cache
    def city(self, date=None):
        rec = self.geo_record(date)
        return rec['city'] if rec else None
    
    @cache
    def region(self, date=None):
        rec = self.geo_record(date)
        return rec['region'] if rec else None

    @cache
    def lat_long(self, date=None):
        rec = self.geo_record(date)
        return (rec['latitude'], rec['longitude']) if rec else None



    # X-CS Zero Carrier Stuff

    @cache
    def providers_full(self):
        if cidr_ranges_full is None:
            return ()
        provs = []
        for cidr, prov in cidr_ranges_full.items():
            if netaddr.IPAddress(self.ip()) in netaddr.IPSet([cidr]):
                provs.append((prov, cidr))
        return tuple(sorted(provs))
      
    @cache
    def providers(self):
        if cidr_ranges is None:
            return ()
        provs = []
        for prov, cidr in cidr_ranges.items():
            if netaddr.IPAddress(self.ip()) in cidr:
                provs.append((prov, cidr))
        return tuple(sorted(provs))

    @cache
    def provider(self):
        if len(self.providers()) == 0:
            return None
        # elif len(self.providers()) > 1:
        #     logger.warning('found more than one matching CIDR range for address %s, %s', self.ip(), str(sorted(self.providers())))
        return sorted(self.providers())[0][0]

    @cache
    def x_cs_parsed(self):
        return map(int, self.x_cs().split('-'))

    @cache
    def x_cs_str(self):
        return mcc_mnc.get(self.x_cs(),None)
    
