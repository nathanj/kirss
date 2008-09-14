# Copyright (c) 2008, Nathan Jones <nathanj@insightbb.com>

from pprint import pprint
import re

channel_regex = re.compile(r'([^(]*)\s+\(([^)]*)\)\s+(\d+)\s+(\d+)\s+(\w+)')
feed_regex = re.compile(r'(!\s*)?(\[([^\]]+)]\s*)?(.*)')

class InvalidChannelException(Exception): pass

class ChannelHandler(object):
    def __init__(self, filename, quiet):
        self.quiet = quiet

        self.load(filename)

    def __iter__(self):
        return self.channels.__iter__()

    def load(self, filename):
        f = open(filename)
        self.channels = []
        line_number = 0

        for line in f.readlines():
            line_number += 1
            try:
                line = line.rstrip()

                if len(line) == 0:
                    continue

                if line[0] == '#':
                    continue

                if line[0].isspace():
                    match = feed_regex.match(line.lstrip()).groups()
                    descrip, _, nick, url = match
                    descrip = (descrip is not None)
                    feed = {
                            'nick': nick,
                            'descrip': descrip,
                            'url': url,
                            }
                    self.channels[-1]['feeds'].append(feed)
                else:
                    match = channel_regex.match(line).groups()
                    name, url, num, wait, width = match
                    channel = {
                            'name': name,
                            'url': url,
                            'num': int(num),
                            'wait': int(wait),
                            'width': width,
                            'feeds': [],
                            }
                    self.channels.append(channel)
            except:
                if not self.quiet:
                    print 'Error at line %d:' % line_number
                    print line
                f.close()
                raise InvalidChannelException('Could not parse channels file')

        f.close()

