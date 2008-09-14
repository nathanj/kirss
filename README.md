KIRSS 0.8
=========

What is it?
-----------
KIRSS is a RSS aggregator. It allows you to download small RSS feeds and
view them in your web browser all in one page.

You can view an
[example of the output](http://home.insightbb.com/~nathanj/kirss/rss.htm) to
determine if kirss is right for you.

Requirements
------------
Python - I have version 2.5 installed, earlier versions may work.

Install
-------
    $ python setup.py install

Usage
-----
Run kirss.py to create the output HTML file (~/.kirss/rss.htm). You can
then view the file in any web browser. Edit ~/.kirss/config to add or remove
feeds.

Features
--------
- Allows turning off the description, good for conserving space if
  you're going to click the link anyway or just like keeping things
  neat.
- Choose how many items you want to see, which is nice for those feeds
  that have a month's worth of comics, but you only want to see maybe
  the latest one or two.

TODO
----
- Test more RSS feeds. Not all may work.

