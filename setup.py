#!/usr/bin/env python

from distutils.core import setup

setup(name="kirss",
        version="0.8",
        license="BSD",
        description="A very simple RSS aggregator.",
        long_description="A very simple RSS aggregator that outputs a HTML file.",
        author="Nathan Jones",
        author_email="nathanj@insightbb.com",
        url="http://home.insightbb.com/~nathanj/kirss/",
        packages=["Kirss"],
        scripts=["kirss.py"],
        data_files=[ ( 'share/kirss/data', [ 'data/config', 'data/footer.htm', 'data/header.htm', 'data/rss.css' ] ),
                     ( 'man/man1', [ 'doc/kirss.1' ] ) ],
        platforms="Any")
