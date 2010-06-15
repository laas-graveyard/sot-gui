#! /usr/bin/env python

__author__ = "Duong Dang"

__version__ = "0.2.2"


try:
    from sotwindow import *
except ImportError:    
    from sotgui.sotwindow import *

def main():
    import optparse
    parser = optparse.OptionParser(
        usage='\n\t%prog [file]',
        version='%%prog %s' % __version__)
    parser.add_option(
        '-f', '--filter',
        type='choice', choices=('dot', 'neato', 'twopi', 'circo', 'fdp'),
        dest='filter', default='dot',
        help='graphviz filter: dot, neato, twopi, '+\
            'circo, or fdp [default: %default]')
    parser.add_option(
        '-n', 
        action="store_true", dest="nw",
        help='start sot_gui without 3D display of the robot')

    (options, args) = parser.parse_args(sys.argv[1:])
    if len(args) > 1:
        parser.error('incorrect number of arguments')

    win = SotWindow(options,args)
    win.widget.fetch_info_and_graph()
    win.open_file(SotWidget.sot_graph_file)
    gobject.timeout_add(30, win.widget.reload)

    gtk.main()


# reimplement main
if __name__ == '__main__':
    main()
