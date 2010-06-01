#! /usr/bin/env python
'''Visualize sot graph'''

__author__ = "Duong Dang"

__version__ = "0.1"


from xdot import *
import os,re
import corba_wrapper
import time
from collections import deque
import gobject
import pygtk
pygtk.require('2.0')
import gtk,sys

class SotWidget(DotWidget):
    """
    """

    graph_name = "sotgraph"
    sot_graph_file = "/tmp/sotgraph.dot"
 
    def __init__(self,sw):
        """
        """
        DotWidget.__init__(self)
        self.sotwin = sw

    def fetch_info_and_graph(self):
        self.sotwin.runAndRead("pool.writegraph %s"%self.sot_graph_file)        
        entities_str = deque(self.sotwin.runAndRead\
                                 ("pool.list %s"%self.sot_graph_file).split())

        while len(entities_str) > 0:
            aname = entities_str.popleft()
            atype = entities_str.popleft()
            if aname not in [ row[0] for row in self.sotwin.en_model ]:
                self.sotwin.en_model.append([aname,atype])

        s = open(self.sot_graph_file).read()
        s = s.replace("/%s"%self.graph_name,self.graph_name)
        f = open(self.sot_graph_file,'w')
        f.write(s)
        f.close()

    def reload(self):
        self.fetch_info_and_graph()
        if self.openfilename is not None:
            try:
                fp = file(self.openfilename, 'rt')
                self.set_dotcode(fp.read(), self.openfilename)
                fp.close()
            except IOError:
                pass
        
    def mouse_click_action(self,jump):
        item = jump.item
        str_list = list()

        for shape in item.shapes:
            if isinstance(shape,TextShape):
                str_list.append(shape.t)

        entity_name = None
        sig_name = None
        if isinstance(item,Node):
            if len(str_list)!=1:
                return
            entity_name = str_list[0]

        elif isinstance(item,Edge):
            hls = jump.highlight;
            for hl in hls:
                if hl == item.src:      
                    for shape in item.src.shapes:
                        if isinstance(shape,TextShape):
                            entity_name = shape.t
                            break
                    if len(str_list) >=2 :
                        sig_name = str_list[1]

                elif hl == item.dst:      
                    for shape in item.dst.shapes:
                        if isinstance(shape,TextShape):
                            entity_name = shape.t
                            break
                    if len(str_list) >=1 :    
                        sig_name = str_list[0]

#            print sig_name

        if entity_name == None:
            return
        iter = self.sotwin.en_model.get_iter_first()    
        while self.sotwin.en_model[iter][0] != entity_name:
            iter = self.sotwin.en_model.iter_next(iter)
        self.sotwin.en_selection = self.sotwin.en_tree_view.get_selection()
        self.sotwin.en_selection.select_iter(iter)
        self.sotwin.coshell_entry.set_text('%s.signals'%entity_name)
        self.sotwin.coshell_entry_callback(self.sotwin.coshell_entry)

        if sig_name == None:
            return

        iter = self.sotwin.sig_model.get_iter_first()    
        while self.sotwin.sig_model[iter][1] != sig_name:
            iter = self.sotwin.sig_model.iter_next(iter)
        self.sotwin.sig_selection = self.sotwin.sig_tree_view.get_selection()
        self.sotwin.sig_selection.select_iter(iter)
        self.sotwin.coshell_entry.set_text('get %s.%s'%(entity_name,sig_name))
        self.sotwin.coshell_entry_callback(self.sotwin.coshell_entry)
        return   
        
    def on_area_button_release(self, area, event):
        self.drag_action.on_button_release(event)
        self.drag_action = NullAction(self)
        if event.button == 1 and self.is_click(event):
            x, y = int(event.x), int(event.y)
            url = self.get_url(x, y)
            if url is not None:
                self.emit('clicked', unicode(url.url), event)
            else:
                jump = self.get_jump(x, y)
                if jump is not None:
                    self.mouse_click_action(jump)
            return True

        if event.button == 1 or event.button == 2:
            return True
        
        return False
    


class SotWindow(DotWindow):
    """
    """
    ui = '''
    <ui>
        <toolbar name="ToolBar">
            <toolitem action="Reload"/>
            <separator/>
            <toolitem action="ZoomIn"/>
            <toolitem action="ZoomOut"/>
            <toolitem action="ZoomFit"/>
            <toolitem action="Zoom100"/>
        </toolbar>
    </ui>
    ''' 
   
    def __init__(self, ):
        """
        """
        self.coshell_response_count = -1
        self.coshell_timeout_source_id = None
#        self.coshell_frame = None
        self.en_model = gtk.ListStore(str,str)
        self.en_tree_view = gtk.TreeView(self.en_model)
        rendererText = gtk.CellRendererText()
        self.en_column1 = gtk.TreeViewColumn("Entities", rendererText, text=0)
        self.en_column2 = gtk.TreeViewColumn("Type", rendererText, text=1)
        self.en_column1.set_sort_column_id(0)    
        self.en_column2.set_sort_column_id(1)    
        self.en_tree_view.append_column(self.en_column1)
        self.en_tree_view.append_column(self.en_column2)
        self.en_tree_view.set_enable_search(True)
        self.en_tree_view.set_search_column(0)
        self.en_tree_view.connect('cursor-changed',self.tree_view_sel_callback)


        self.sig_model = gtk.ListStore(str,str,str,str) 
        # entity,sig_name,I/O, type
        self.sig_tree_view = gtk.TreeView(self.sig_model)
        rendererText = gtk.CellRendererText()
        self.sig_column1 = gtk.TreeViewColumn("Sig", rendererText, text=1)
        self.sig_column2 = gtk.TreeViewColumn("I/O", rendererText, text=2)
        self.sig_column3 = gtk.TreeViewColumn("Type", rendererText, text=3)
        self.sig_column1.set_sort_column_id(1)    
        self.sig_column2.set_sort_column_id(2)    
        self.sig_column3.set_sort_column_id(3)    
        self.sig_tree_view.append_column(self.sig_column1)
        self.sig_tree_view.append_column(self.sig_column2)
        self.sig_tree_view.append_column(self.sig_column3)
        self.sig_tree_view.set_enable_search(True)
        self.sig_tree_view.set_search_column(1)

        self.sig_tree_view.connect('cursor-changed',self.tree_view_sel_callback)

        gtk.Window.__init__(self)

        self.graph = Graph()

        window = self

        window.set_title('Dot Viewer')
        window.set_default_size(512, 512)

        table = gtk.Table(rows=1, columns=3, homogeneous=True)
        window.add(table)
        notebook = gtk.Notebook()
        table.attach(notebook,0,2,0,1)

        ############# GUI #####################
        self.widget = SotWidget(self)

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
        vbox_graph = gtk.VBox()
        toolbar = uimanager.get_widget('/ToolBar')
        vbox_graph.pack_start(toolbar, False)
        
        graph_label = gtk.Label("Graph")
        notebook.append_page(vbox_graph, graph_label)

        table_coshell_selection = gtk.Table(rows=2, columns=2, homogeneous=True)
        table.attach(table_coshell_selection,2,3,0,1)


        ############### GRAPH ######################
        vbox_graph.pack_start(self.widget)


        ############## ROBOTVIEWER #################
        rv_label = gtk.Label("Robotviewer")
        vbox_rv = gtk.VBox()
        int_hbox = gtk.HBox()
#        int_label = gtk.Label("INSTRUCTION: run xwininfo on `robotviewer` window the and fill in the Window id below")
        int_label = gtk.Label("Future feature: Embed robotviewer here")
        int_hbox.pack_start(int_label,False,False,0)
        vbox_rv.pack_start(int_hbox,False,False,0)

        hbox_winid = gtk.HBox()
        vbox_rv.pack_start(hbox_winid,False,False,0)
        label_winid = gtk.Label('Window id:')
        hbox_winid.pack_start(label_winid,False,False,0)
        entry_winid = gtk.Entry(20)
#        hbox_winid.pack_start(entry_winid,False,False,0)

        def plugged_event(widget):
            print "I (", widget, ") have just had a plug inserted!"

        socket = gtk.Socket()
        socket.show()

        socket.connect("plug-added", plugged_event)
        vbox_rv.pack_start(socket,False,False,0)

        def winid_activate_cb(entry):
            winid = long(entry.get_text(),16)
            socket.add_id(long(winid))
            socket.show()
        entry_winid.connect('activate',winid_activate_cb)


        notebook.append_page(vbox_rv, rv_label)
        
        ############# COSHELL ######################
        vbox_coshell = gtk.VBox()
        table_coshell_selection.attach(vbox_coshell,0,2,0,1)

        hbox1 = gtk.HBox(False,0)
        cr_hbox = gtk.HBox(False,0)

        vbox_coshell.pack_start(cr_hbox,False,False,0)
        vbox_coshell.pack_start(hbox1,False,False,0)    

        label = gtk.Label("~>")
        hbox1.pack_start(label,False,False,0)
        self.coshell_entry = gtk.Entry(max=1000)
        hbox1.pack_start(self.coshell_entry,True,True,0)
        self.coshell_entry.connect\
            ("activate", self.coshell_entry_callback)

        coshell_entry_checkbutton = gtk.CheckButton("each")
        hbox1.pack_start(coshell_entry_checkbutton,False,False,0)
        coshell_entry_period = gtk.Entry(max=10)
        coshell_entry_period.set_width_chars(2)
        hbox1.pack_start(coshell_entry_period,False,False,0)
        coshell_entry_period_label = gtk.Label("s")
        hbox1.pack_start(coshell_entry_period_label,False,False,0)

        
        def coshell_timeout_update(widget,checkbutton, period_entry):
            try:
                gobject.source_remove(self.coshell_timeout_source_id)
            except Exception,error:
                print "Caught exception %s"%error
            if checkbutton.get_active()==0:
                return True
            else:
                try:
                    period = float(period_entry.get_text())
                except:
                    return True
                if period < 0:
                    return True
                period_ms = int(1000*period)
                self.coshell_timeout_source_id = gobject.timeout_add\
                    ( period_ms, self.coshell_entry_callback , \
                          self.coshell_entry )                
                return True

        coshell_entry_checkbutton.connect('toggled',coshell_timeout_update,\
                                              coshell_entry_checkbutton,\
                                              coshell_entry_period)
        
        coshell_entry_period.connect('activate',coshell_timeout_update,\
                                         coshell_entry_checkbutton,\
                                         coshell_entry_period)
        
        ## scrolled windows

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        self.coshell_response = gtk.TextView()
        self.coshell_response.set_editable(False)

        def word_wrap_cb(widget):
            if widget.get_active()==0:
                self.coshell_response.set_wrap_mode(False)
            else:
                self.coshell_response.set_wrap_mode(True)

        def mat_disp_cb(widget):
            if widget.get_active()==0:
                self.runAndRead('dispmat simple')
                self.coshell_entry_callback(self.coshell_entry)
            else:
                self.runAndRead('dispmat matlab')
                self.coshell_entry_callback(self.coshell_entry)

        disp_opt_label = gtk.Label("Display options  ")
        cr_hbox.pack_start(disp_opt_label,False,False,0)

        word_wrap_button = gtk.CheckButton("Word wrap")
        cr_hbox.pack_start(word_wrap_button,False,False,0)
        word_wrap_button.connect("toggled",word_wrap_cb)

        mat_disp_button = gtk.CheckButton("Matlab matrix")
        cr_hbox.pack_start(mat_disp_button,False,False,0)
        mat_disp_button.connect("toggled",mat_disp_cb)
        mat_disp_button.set_active(True)

        self.coshell_response.set_wrap_mode(False)

        sw.add_with_viewport(self.coshell_response)
        self.coshell_frame = gtk.Frame()        
        self.coshell_frame.add(sw)

        vbox_coshell.pack_start(self.coshell_frame,True,True,0)


        ## signal selection
        label1 = gtk.Label('Ent goes here')
        label2 = gtk.Label('Sig goes here')

        sw2 = gtk.ScrolledWindow()
        sw2.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        sw2.add_with_viewport(self.en_tree_view)
        table_coshell_selection.attach(sw2,0,1,1,2)

        sw3 = gtk.ScrolledWindow()
        sw3.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        sw3.add_with_viewport(self.sig_tree_view)
        table_coshell_selection.attach(sw3,1,2,1,2)

        self.set_focus(self.widget)
        self.show_all()

    def coshell_entry_callback(self, widget):
        self.coshell_response_count += 1
        entry_text = widget.get_text()
        self.coshell_response.get_buffer().set_text(self.runAndRead(entry_text))
        if self.coshell_frame:
            self.coshell_frame.set_label("coshell response <%d>"\
                                             %self.coshell_response_count)
        if re.search(r"new|plug|unplug|destroy|clear|pop|push",entry_text):
            self.widget.reload()
        self.set_title('StackOfTasks GUI')
        return True

    def set_dotcode(self, dotcode, filename='<stdin>'):
         if self.widget.set_dotcode(dotcode, filename):
            self.set_title('StackOfTasks GUI')
            self.widget.zoom_to_fit()

    def set_xdotcode(self, dotcode, filename='<stdin>'):
         if self.widget.set_xdotcode(dotcode, filename):
            self.set_title('StackOfTasks GUI')
            self.widget.zoom_to_fit()

    def tree_view_sel_callback(self,treeview):
        ent = sig = io = cmd = io = None
        if treeview == self.en_tree_view:
            (model, iter) = treeview.get_selection().get_selected()
            row = model[iter]
            cmd = '%s.signals'%row[0]
            self.coshell_entry.set_text(cmd)
            self.coshell_entry_callback(self.coshell_entry)
            list_signals = self.runAndRead(cmd)
            lines = list_signals.splitlines()
            pattern = re.compile(r".*(input|output)\((\w+)\)::(\w+)*")
            self.sig_model.clear()
            for line in lines:
                m = pattern.match(line)
                if m:
                    ent = row[0]
                    io  = m.group(1)
                    if io == "input":
                        io = "I"
                    else:
                        io = "O"
                    type= m.group(2)
                    sig = m.group(3)
                    self.sig_model.append([ent,sig,io,type])
                    del io,type
        elif treeview == self.sig_tree_view:
            (model, iter) = treeview.get_selection().get_selected()
            row = model[iter]
            ent = row[0]
            sig = row[1]
            cmd = 'get %s.%s'%(ent,sig)        
            self.coshell_entry.set_text(cmd)
            self.coshell_entry_callback(self.coshell_entry)
            del cmd
        
        # find node and move there
        if ent == None:
            return
        for node in self.widget.graph.nodes:
            nodeName = None
            for shape in node.shapes:
                if isinstance(shape,TextShape):
                    nodeName = shape.t
                    break
            if nodeName !=None and nodeName == ent:                
                self.widget.animate_to(node.x,node.y)
                self.widget.highlight = [node]
                self.widget.queue_draw()
                return
        # if node not found, highlight nothing
        self.widget.hightlight = []
        
    def runAndRead(self,s):
        while True:
            try:
                result = corba_wrapper.runAndReadWrap(s)
                break
            except:        
                messagedialog = gtk.MessageDialog\
                    (self, 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_YES_NO,\
                         "Corba failed. Retry?")
                response = messagedialog.run()
                messagedialog.destroy()
                if response == gtk.RESPONSE_YES:
                    reload(corba_wrapper)
                elif response == gtk.RESPONSE_NO:
                    sys.exit(1)
        return result

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

    win = SotWindow()
    win.connect('destroy', gtk.main_quit)
    win.set_filter(options.filter)

    win.widget.fetch_info_and_graph()
    
    win.open_file(SotWidget.sot_graph_file)
    win.set_title('Stack Of Tasks GUI')
    gobject.timeout_add(1000, win.update, SotWidget.sot_graph_file)

    gtk.main()


# reimplement main
if __name__ == '__main__':
    main()
