# Copyright (c) 2008, Nathan Jones <nathanj@insightbb.com>

from xml.dom import minidom
from datetime import datetime
import time
import rfc822

class RSSHandler:
    def __init__(self):
        self.channel = {}
        self.items = []

    def __getitem__(self, item):
        return self.channel[item]

    def load_feed(self, filename, show_descrip, nick):
        self.show_descrip = show_descrip
        self.nick = nick

        self.load_file(filename)
        self.parse()

        self.clean_up()

    def clean_up(self):
        """Clean up"""
        self.xmldoc.unlink()

    def load_file(self, filename):
        """Load the RSS file"""
        self.xmldoc = minidom.parse(filename)

    def parse(self):
        """Parse the channel information"""
        chan = self.xmldoc.getElementsByTagName('channel')[0]
        title = chan.getElementsByTagName('title')[0].firstChild.data
        link = chan.getElementsByTagName('link')[0].firstChild.data

        # not all feeds have description tags, so catch if not
        try:
            description = chan.getElementsByTagName('description')[0].firstChild.data
        except:
            description = ''

        self.channel['title'] = title
        self.channel['link'] = link
        self.channel['description'] = description

        self.parse_items()

    def parse_items(self):
        """Parse the channel items"""
        items = self.xmldoc.getElementsByTagName('item')
        for item in items:
            self.parse_item(item)

    def parse_item(self, item):
        """Parse an item"""
        try:
            link = item.getElementsByTagName('link')[0].firstChild.data
        except:
            link = ''
        try:
            description = item.getElementsByTagName('description')[0].firstChild.data
        except:
            description = ''
        try:
            title = item.getElementsByTagName('title')[0].firstChild.data
        except:
            title = 'No title'
        try:
            pubdate = item.getElementsByTagName('pubDate')[0].firstChild.data
        except Exception, ex:
            pubdate = ''

        pubdate = self.parse_date(pubdate)

        it = {'title': title, 'link': link, 'pubdate': pubdate}
        if self.show_descrip:
            it['description'] = description.replace('\n', '')
        else:
            it['description'] = ''

        it['nick'] = self.nick

        self.items.append(it)

    def parse_date(self, date):
        formats = ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y')

        f = rfc822.parsedate_tz(date)
        if f is not None:
            return time.mktime(f[:9]) - f[9]

        for form in formats:
            try:
                return time.mktime(time.strptime(date, form))
            except:
                pass

        # all else fails, return now
        return time.time()

    def sort_by_date(self):
        self.items.sort(cmp=lambda x, y: cmp(x['pubdate'], y['pubdate']),
                reverse=True)

