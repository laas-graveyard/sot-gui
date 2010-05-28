#! /usr/bin/env python
'''Visualize sot graph'''

__author__ = "Duong Dang"

__version__ = "0.1"


from xdot import *
import os,re
from corba_wrapper import runAndReadWrap
import time
from collections import deque
DotWindow.ui = '''
    <ui>
        <toolbar name="ToolBar">
<!--            <toolitem action="Open"/> -->
            <toolitem action="Reload"/>
            <separator/>
            <toolitem action="ZoomIn"/>
            <toolitem action="ZoomOut"/>
            <toolitem action="ZoomFit"/>
            <toolitem action="Zoom100"/>
        </toolbar>
    </ui>
    '''

graph_name = "sotgraph"
sot_graph_file = "/tmp/sotgraph.dot"
entities = list()
en_model = gtk.ListStore(str,str)
en_tree_view = gtk.TreeView(en_model)
rendererText = gtk.CellRendererText()

en_column1 = gtk.TreeViewColumn("Entities", rendererText, text=0)
en_column2 = gtk.TreeViewColumn("Type", rendererText, text=1)
en_column1.set_sort_column_id(0)    
en_tree_view.append_column(en_column1)
en_tree_view.append_column(en_column2)


def fetch_info_and_graph():
    global en_model,en_tree_view
    runAndReadWrap("pool.writegraph %s"%sot_graph_file)        
    entities_str = deque(runAndReadWrap("pool.list %s"%sot_graph_file).split())
    
    while len(entities_str) > 0:
        aname = entities_str.popleft()
        atype = entities_str.popleft()
        if aname not in [ row[0] for row in en_model ]:
            en_model.append([aname,atype])

    print len(en_model)

    s = open(sot_graph_file).read()
    s = s.replace("/%s"%graph_name,graph_name)
    f = open(sot_graph_file,'w')
    f.write(s)
    f.close()

# redefine reload function
def reload_modified(self):
    fetch_info_and_graph()
    if self.openfilename is not None:
        try:
            fp = file(self.openfilename, 'rt')
            self.set_dotcode(fp.read(), self.openfilename)
            fp.close()
        except IOError:
            pass

def on_area_button_press_modified(self,area,event):
    return

DotWidget.reload = reload_modified


def dwindow_init(self):
    gtk.Window.__init__(self)

    self.graph = Graph()

    window = self
    
    window.set_title('Dot Viewer')
    window.set_default_size(512, 512)

    table = gtk.Table(rows=1, columns=3, homogeneous=True)

    vbox_all = gtk.VBox()
    window.add(vbox_all)

    ############# GUI #####################
    self.widget = DotWidget()

    # Create a UIManager instance
    uimanager = self.uimanager = gtk.UIManager()

    # Add the accelerator group to the toplevel window
    accelgroup = uimanager.get_accel_group()
    window.add_accel_group(accelgroup)

    # Create an ActionGroup
    actiongroup = gtk.ActionGroup('Actions')
    self.actiongroup = actiongroup

    # Create actions
    actiongroup.add_actions((
        ('Open', gtk.STOCK_OPEN, None, None, None, self.on_open),
        ('Reload', gtk.STOCK_REFRESH, None, None, None, self.on_reload),
        ('ZoomIn', gtk.STOCK_ZOOM_IN, None, None, None, self.widget.on_zoom_in),
        ('ZoomOut', gtk.STOCK_ZOOM_OUT, None, None, None, self.widget.on_zoom_out),
        ('ZoomFit', gtk.STOCK_ZOOM_FIT, None, None, None, self.widget.on_zoom_fit),
        ('Zoom100', gtk.STOCK_ZOOM_100, None, None, None, self.widget.on_zoom_100),
    ))

    # Add the actiongroup to the uimanager
    uimanager.insert_action_group(actiongroup, 0)

    # Add a UI descrption
    uimanager.add_ui_from_string(self.ui)

    # Create a Toolbar
    toolbar = uimanager.get_widget('/ToolBar')
    vbox_all.pack_start(toolbar, False)

    vbox_all.pack_start(table)
    vbox_graph = gtk.VBox()
    table.attach(vbox_graph,0,2,0,1)

    table_coshell_selection = gtk.Table(rows=2, columns=1, homogeneous=True)
    table.attach(table_coshell_selection,2,3,0,1)

    vbox_coshell = gtk.VBox()
    table_coshell_selection.attach(vbox_coshell,0,1,0,1)
    hbox_sel = gtk.HBox(False,0)
    table_coshell_selection.attach(hbox_sel,0,1,1,2)


    ############### GRAPH ###################
    vbox_graph.pack_start(self.widget)

    
    ############# COSHELL ######################
    
    hbox1 = gtk.HBox(False,0)
    label = gtk.Label("~>")
    hbox1.pack_start(label,False,False,0)
    self.coshell_entry = gtk.Entry(max=50)
    hbox1.pack_start(self.coshell_entry,True,True,0)
    vbox_coshell.pack_start(hbox1,False,False,0)
    self.coshell_entry.connect\
        ("activate", self.coshell_entry_callback, self.coshell_entry)

    ## scrolled windows

    sw = gtk.ScrolledWindow()
    sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    frame1 = gtk.Frame("coshell response")
    self.coshell_response = gtk.Label("")
    self.coshell_response.set_justify(gtk.JUSTIFY_LEFT)
    self.coshell_response.set_line_wrap(True)
    frame1.add(self.coshell_response)
    sw.add_with_viewport(frame1)
    vbox_coshell.pack_start(sw,True,True,0)


    ## signal selection
    label1 = gtk.Label('Ent goes here')
    label2 = gtk.Label('Sig goes here')

    global en_tree_view    
    sw2 = gtk.ScrolledWindow()
    sw2.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    sw2.add_with_viewport(en_tree_view)
    hbox_sel.pack_start(sw2)

    self.set_focus(self.widget)
    self.show_all()


def coshell_entry_callback(self, widget, entry):
    entry_text = entry.get_text()
    self.coshell_response.set_text(runAndReadWrap(entry_text))
    if re.search(r"new|plug|unplug|destroy|clear|pop|push",entry_text):
        self.widget.reload()


DotWindow.__init__ = dwindow_init
DotWindow.coshell_entry_callback = coshell_entry_callback

def main():
    import optparse

    parser = optparse.OptionParser(
        usage='\n\t%prog [file]',
        version='%%prog %s' % __version__)
    parser.add_option(
        '-f', '--filter',
        type='choice', choices=('dot', 'neato', 'twopi', 'circo', 'fdp'),
        dest='filter', default='dot',
        help='graphviz filter: dot, neato, twopi, circo, or fdp [default: %default]')

    (options, args) = parser.parse_args(sys.argv[1:])
    if len(args) > 1:
        parser.error('incorrect number of arguments')

    win = DotWindow()
    win.connect('destroy', gtk.main_quit)
    win.set_filter(options.filter)

    fetch_info_and_graph()
    
    win.open_file(sot_graph_file)

    gobject.timeout_add(1000, win.update, sot_graph_file)

    gtk.main()


# reimplement main
if __name__ == '__main__':
    main()
