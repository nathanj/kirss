# Copyright (c) 2008, Nathan Jones <nathanj@insightbb.com>

import os
import pickle

from sys import argv, exit
from time import time
from threading import Thread
from shutil import copyfile
from socket import setdefaulttimeout
from urllib2 import Request, build_opener
from StringIO import StringIO
from gzip import GzipFile
from os.path import sep
from cgi import escape
from md5 import md5
from optparse import OptionParser

from Kirss.rss_handler import RSSHandler
from Kirss.channel_handler import ChannelHandler, InvalidChannelException

VERSION='0.8'

#KIRSS_DIR = '.%s' % os.path.sep
KIRSS_DIR = os.path.expanduser('~%s.kirss%s' % (sep, sep))
CHANNEL_FILE = '%sconfig' % KIRSS_DIR
DATA_DIR = '%sdata%s' % (KIRSS_DIR, sep)
MAIN_DATA_DIRS = [os.path.dirname(os.path.abspath(argv[0])) + '%sdata' % sep,
        '%susr%sshare%skirss%sdata' % (sep, sep, sep, sep),
        '%susr%slocal%sshare%skirss%sdata' % (sep, sep, sep, sep, sep)]

def local_filename(url):
    return md5(url).hexdigest()

def esc(var):
    return escape(var.encode('utf-8'))

class DownloadThread(Thread):
    def __init__(self, channel, feed, last_update, quiet=False):
        Thread.__init__(self)
        self.channel = channel
        self.feed = feed
        self.last_update = last_update
        self.quiet = quiet

    def download(self, url):
        """Download a url, using compression if possible."""
        request = Request(url)
        request.add_header('Accept-encoding', 'gzip')
        opener = build_opener()
        f = opener.open(request)

        if (f.headers.has_key('content-encoding') and
                f.headers['content-encoding'] == 'gzip'):
            compr = True
            compressed = f.read()
            size = len(compressed)
            stream = StringIO(compressed)
            gzipper = GzipFile(fileobj=stream)
            body = gzipper.read()
        else:
            compr = False
            body = f.read()
            size = len(body)

        return (body, compr, size)

    def run(self):
        link = self.feed['url']
        local = local_filename(link)
        displink = link
        if displink.startswith('http://'):
            displink = displink[7:]
        if len(displink) > 37:
            displink = displink[:37] + '...'

        if self.last_update.has_key(local):
            remaining = int( (self.last_update[local] + self.channel['wait']*60 - time())/60 )
        else:
            remaining = -1

        filename = '%s%s.xml' % (DATA_DIR, local)

        # if enough time has passed or the feed doesn't exist on the
        # file system, download the feed
        if remaining < 0 or not os.path.isfile(filename):
            try:
                body, compr, size = self.download(link)
                f = open(filename, 'w')
                f.write(body)
                f.close()
                self.last_update[local] = int(time())
                if not self.quiet:
                    print '    Fetched  %-40s [ %s %7s ]' % (
                            displink, compr and 'gzip' or 'http',
                            str(size/1024) + 'KB')
            except Exception, ex:
                if not self.quiet:
                    print 'WARNING: %s could not be downloaded.' % link
        else:
            if not self.quiet:
                print 'Not Fetching %-40s [%4d minutes remaining ]' % (
                        displink, remaining)

class Kirss:
    def __init__(self, quiet=False):
        self.quiet = quiet

        # this will keep the info on all the channels
        # it will be initialized when the channels are parsed
        self.channels = None

        # this will keep the current channel info
        # along with the items in the channel
        self.feed = None

        self.right = False

        self.channel_file = CHANNEL_FILE
        self.last_update_file = '%slast_update.dat' % DATA_DIR

        if os.path.isdir(KIRSS_DIR) == False:
            os.mkdir(KIRSS_DIR)

        if os.path.isdir(DATA_DIR) == False:
            os.mkdir(DATA_DIR)

        # load the last update times if possible
        try:
            self.last_update = pickle.load(open(self.last_update_file))
        except:
            self.last_update = {}

        self.parse_channels()

    def parse_all(self):
        """Parse everything and write the output HTML file"""
        f = open('%srss.htm' % KIRSS_DIR, 'w')
        self.make_header(f)
        for channel in self.channels:
            self.curr_channel = channel
            self.parse_rss(channel)
            self.make_html(f, channel)
        self.make_footer(f)
        f.close()

    def parse_rss(self, channel):
        """Parse a RSS file"""
        self.feed = RSSHandler()
        for feed in channel['feeds']:
            filename = '%s%s.xml' % (DATA_DIR, local_filename(feed['url']))
            show_descrip = feed['descrip']
            nick = feed['nick']
            try:
                self.feed.load_feed(filename, show_descrip, nick)
            except:
                if not self.quiet:
                    print 'WARNING: Could not parse %s' % filename

        if (len(channel['feeds'])) > 1:
            self.feed.sort_by_date()

    def make_header(self, f):
        """Write the header to the output HTML file"""
        header = open_data_file('header.htm')
        f.write(header.read())
        header.close()

    def make_footer(self, f):
        """Write the footer to the output HTML file"""
        footer = open_data_file('footer.htm')
        f.write(footer.read())
        footer.close()

    def make_nick(self, nick):
        if nick is None or len(nick) == 0:
            return ''

        return '[%s] ' % esc(nick)

    def make_title(self, name, url):
        if url is None or len(url) == 0:
            return '%s' % esc(name)

        return '<a href="%s">%s</a>' % (esc(url), esc(name))

    def make_html(self, f, channel):
        """Convert the RSS data into HTML form"""
        if len(self.feed.items) > 0:
            #try:
            if channel['width'] == 'half':
                if self.right:
                    f.write('\t\t<div class="rss_channel c2">\n')
                else:
                    f.write('\t\t<div class="rss_channel c1">\n')
                self.right = not self.right
            else:
                f.write('\t\t<div class="rss_channel cfull">\n')
            f.write('\t\t\t<div class="rss_title">%s</div>\n' % self.make_title(channel['name'], channel['url']))
            for i, item in enumerate(self.feed.items):
                if channel['num'] > 0 and channel['num'] > i:
                    f.write('\t\t\t<div class="rss_item">%s<a href="%s">%s</a></div>\n' % (self.make_nick(item['nick']), esc(item['link']), esc(item['title'])))
                    if item['description'] != '':
                        f.write('\t\t\t<div class="rss_body">%s</div>\n' % item['description'].encode('utf-8'))
            f.write('\t\t</div>\n')
            # an IndexError will occur if the RSS feed was not able to be downloaded or parsed
            # TODO maybe not
            #except IndexError:
            #    pass
            #except TypeError:
            #    pass

    def download(self, timeout):
        """Download the RSS feeds"""
        setdefaulttimeout(timeout)

        threads = []
        for channel in self.channels:
            for feed in channel['feeds']:
                s = DownloadThread(channel, feed, self.last_update, self.quiet)
                threads.append(s)
                s.start()

        # wait for all threads to finish
        for s in threads:
            s.join()

        self.save_update_times()

    def save_update_times(self):
        """Save the last update time for each feed"""
        pickle.dump(self.last_update, open(self.last_update_file, 'w'))

    def parse_channels(self):
        """Read channels from config file"""
        try:
            self.channels = ChannelHandler(self.channel_file, self.quiet)
        except InvalidChannelException:
            if not self.quiet:
                print 'ERROR: Could not parse %s' % self.channel_file
            exit(1)

def open_data_file(filename):
    for d in MAIN_DATA_DIRS:
        if os.path.isfile('%s%s%s' % (d, sep, filename)):
            f = open('%s%s%s' % (d, sep, filename), 'r')
            return f
    return None

def copy_file_if_not_exist(filename, quiet):
    ffile = '%s%s' % (KIRSS_DIR, filename)
    if not os.path.isfile(ffile):
        if not quiet:
            print 'Could not find %s, copying it' % ffile

        # make sure the directory exists
        if not os.path.isdir(KIRSS_DIR):
            os.mkdir(KIRSS_DIR)

        found = False
        for d in MAIN_DATA_DIRS:
            if not found and os.path.isfile('%s%s%s' % (d, sep, filename)):
                copyfile('%s%s%s' % (d, sep, filename), ffile)
                found = True
        if not found:
            if not quiet:
                print 'Could not find the default %s' % filename

def copy_files(quiet):
    copy_file_if_not_exist('config', quiet)
    copy_file_if_not_exist('rss.css', quiet)

def get_option_parser():
    parser = OptionParser()
    parser.add_option("-d", "--nodownload", dest="download", action='store_false', default=True,
                      help="do not download new feeds, just generate output")
    parser.add_option("-q", "--quiet", dest="quiet", action='store_true', default=False,
                      help="do not display any output")
    parser.add_option("-t", "--timeout", metavar='TIMEOUT', type='int', dest="timeout", default=15,
                      help="set the download timeout length (default 15)")
    #parser.add_option("-n", "--name", metavar='NAME', dest="name", default=None,
    #                  help="name of the new feed")
    #parser.add_option("-u", "--url", metavar='URL', dest="url", default=None,
    #                  help="url of the new feed")
    parser.add_option("-v", "--version", dest="version", action='store_true', default=False,
                      help="show version")
    return parser

def main(args):
    parser = get_option_parser()
    (options, args) = parser.parse_args(args)

    # create the necessary files if it does not exist
    copy_files(options.quiet)

    if options.version:
        print 'kirss %s' % VERSION
    # add new feed
    #elif options.name and options.url:
    #    kirss = Kirss(options.quiet)
    #    kirss.channels.add_feed(title=options.name, link=options.url)
    #    kirss.channels.write()
    #    if not options.quiet:
    #        print '"%s" <%s> has been added to the channel list' % (options.name, options.url)
    # do the normal operation
    else:
        kirss = Kirss(options.quiet)
        if options.download:
            kirss.download(options.timeout)
        kirss.parse_all()

if __name__ == '__main__':
    main()


