#!/usr/bin/python
import sys
import string
import getopt
import gtk
import vte
from termwidget import TermWidget


if __name__ == '__main__':
        window = gtk.Window()
        box = TermWidget("bash")
	window.add(box)
	window.show_all()
	gtk.main()
