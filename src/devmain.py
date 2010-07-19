#! /usr/bin/env python

__author__ = "Duong Dang"

__version__ = "0.3"

from sotwindow import *                                                                                                                       

# try:
#     from sotwindow import *
# except ImportError:    
#     from sotgui.sotwindow import *

def main():
    import optparse
    parser = optparse.OptionParser(
        usage='\n\t%prog [options]',
        version='%%prog %s' % __version__)
    parser.add_option(
        '-f', '--filter',
        type='choice', choices=('dot', 'neato', 'twopi', 'circo', 'fdp'),
        dest='filter', default='dot',
        help='graphviz filter: dot, neato, twopi, '+\
            'circo, or fdp [default: %default]')
    parser.add_option(
        '-t', '--with-term',
        action="store_true", dest="with_term",
        help='enable terminal widget')

    parser.add_option(
        '-o', '--with-OpenGL',
        action="store_true", dest="with_rvwidget",
        help='enable OpenGL tab')


    parser.add_option(
         '--lazy',
         action="store_true", dest="lazy_term",
         help="run lazy script into term, only works on authour's setup on walker.laas.fr")

    parser.add_option(
        '-d', '--debug',
        action="store_true", dest="debug",
        help='output debut msgs in log file')

    parser.add_option(
        '--script-dir',
        action='store', type='string', dest='script_dir', 
        help='specify script directory ')


    (options, args) = parser.parse_args(sys.argv[1:])
    if len(args) > 1:
        parser.error('incorrect number of arguments')

    win = SotWindow(options,args)
    gobject.timeout_add(30, win.widget.reload)

    gtk.main()


# reimplement main
if __name__ == '__main__':
    main()
