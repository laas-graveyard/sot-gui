#! /usr/bin/env python
'''Visualize sot graph'''

__author__ = "Duong Dang"

__version__ = "0.2.1"


from xdot import *
import os,re
import corba_wrapper
import time
from collections import deque
import gobject
import pygtk
pygtk.require('2.0')
import gtk,sys
from rvwidget import *
from termwidget import TermWidget
import gtk.glade

class Setting(object):
    """
    """    
    def __init__(self, ):
        """
        """        
        self.simu_dt = 0.02 # integration interval in s
        self.hrp_rvname = 'hrp'
        self.hrp_simuName = 'OpenHRP'



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
            if aname=='OpenHRP':
                self.sotwin.rvwidget.robotType = atype

        s = open(self.sot_graph_file).read()
        s = s.replace("/%s"%self.graph_name,self.graph_name)
        f = open(self.sot_graph_file,'w')
        f.write(s)
        f.close()

    def reload(self,widget):
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
        self.sotwin.tree_view_sel_callback(self.sotwin.en_tree_view,False)

        if sig_name == None:
            return

        iter = self.sotwin.sig_model.get_iter_first()    
        while self.sotwin.sig_model[iter][1] != sig_name:
            iter = self.sotwin.sig_model.iter_next(iter)
        self.sotwin.sig_selection = self.sotwin.sig_tree_view.get_selection()
        self.sotwin.sig_selection.select_iter(iter)
        self.sotwin.tree_view_sel_callback(self.sotwin.sig_tree_view,False)
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
    


class SotWindow(object):
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
        self.setting = Setting()
        src_path = os.path.dirname(os.path.abspath(__file__))
        gladefile = src_path + "/sotwindow.glade"
        builder = gtk.Builder()
        builder.add_from_file(gladefile)
        window = builder.get_object("window")        
        window.show()
        self.win = window
        
        self.coshell_response_cnt_label = builder.get_object("coshell_response_cnt_label")
        self.coshell_response_count = -1
        self.coshell_timeout_source_id = None
#        self.coshell_frame = None

        self.en_model = gtk.ListStore(str,str)
        rendererText = gtk.CellRendererText()
        self.en_column1 = gtk.TreeViewColumn("Entities", rendererText, text=0)
        self.en_column2 = gtk.TreeViewColumn("Type", rendererText, text=1)
        self.en_column1.set_sort_column_id(0)    
        self.en_column2.set_sort_column_id(1)    

        self.sig_model = gtk.ListStore(str,str,str,str) 
        # entity,sig_name,I/O, type
        rendererText = gtk.CellRendererText()
        self.sig_column1 = gtk.TreeViewColumn("Sig", rendererText, text=1)
        self.sig_column2 = gtk.TreeViewColumn("I/O", rendererText, text=2)
        self.sig_column3 = gtk.TreeViewColumn("Type", rendererText, text=3)
        self.sig_column1.set_sort_column_id(1)    
        self.sig_column2.set_sort_column_id(2)    
        self.sig_column3.set_sort_column_id(3)    
        
        
        self.graph = Graph()
        self.widget = SotWidget(self)
        vbox_graph = builder.get_object("vbox_graph")
        vbox_graph.pack_start(self.widget,True,True,0)

        self.coshell_combo_box_entry =  builder.get_object("coshell_combo_box_entry")
        self.coshell_entry = self.coshell_combo_box_entry.child
        self.coshell_hist_model = gtk.ListStore(str)
        self.coshell_combo_box_entry.set_model( self.coshell_hist_model)
        self.coshell_combo_box_entry.set_text_column(0)
        self.coshell_entry.connect('activate',self.coshell_entry_callback)

        self.coshell_response =  builder.get_object("coshell_response")
        self.coshell_frame =  builder.get_object("coshell_frame")
        
        self.en_tree_view = builder.get_object("en_tree_view")
        self.en_tree_view.set_model(self.en_model)
        self.en_tree_view.append_column(self.en_column1)
        self.en_tree_view.append_column(self.en_column2)
        self.en_tree_view.set_enable_search(True)
        self.en_tree_view.set_search_column(0)
        self.en_tree_view.connect('cursor-changed',self.tree_view_sel_callback)

        self.sig_tree_view = builder.get_object("sig_tree_view")
        self.sig_tree_view.set_model(self.sig_model)
        self.sig_tree_view.append_column(self.sig_column1)
        self.sig_tree_view.append_column(self.sig_column2)
        self.sig_tree_view.set_enable_search(True)
        self.sig_tree_view.set_search_column(0)
        self.sig_tree_view.connect('cursor-changed',self.tree_view_sel_callback)


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

        self.rv_cnt = 0
        def rv_incr_cb():
            self.rv_cnt += 1
#            print "inc %d"%self.rv_cnt
            cmd = "%s.inc %f"%(self.setting.hrp_simuName, self.setting.simu_dt)
            self.runAndRead(cmd)
            return True
        self.rv_incr_cb_srcid = None
        def simulate_button_toggled_cb(button):
            if self.rv_incr_cb_srcid:
                gobject.source_remove(self.rv_incr_cb_srcid)
                self.rv_incr_cb_srcid = None

            if button.get_active()!=0:
                for row in self.en_model:
                    if row[0]=='OpenHRP' and row[1]=='(RobotSimu)':
                        self.rv_incr_cb_srcid = gobject.timeout_add\
                            (int(1000*self.setting.simu_dt),rv_incr_cb)
                        return True
                warning_msg = gtk.MessageDialog\
                    (self.win, 0, gtk.MESSAGE_WARNING, \
                         gtk.BUTTONS_YES_NO, \
                         "No OpenHRP of type RobotSimu found\n"+\
                         "Sending OpenHRP.inc command any way?")
                
                response = warning_msg.run()
                warning_msg.destroy()
                if response == gtk.RESPONSE_YES:
                    self.rv_incr_cb_srcid = gobject.timeout_add\
                        (int(1000*self.setting.simu_dt),rv_incr_cb)
                elif response == gtk.RESPONSE_NO:
                    button.set_active(0)
            return True

        self.coshell_each_button = builder.get_object("coshell_each_button")
        self.coshell_period = builder.get_object("coshell_period")

        self.coshell_timeout_source_id = None
        def coshell_period_activate_cb(widget):
            if self.coshell_timeout_source_id:
                try:
                    gobject.source_remove(self.coshell_timeout_source_id)
                except Exception,error:
                    print "Caught exception %s"%error

            if self.coshell_each_button.get_active()==0:
                return True
            else:
                try:
                    period = float(self.coshell_period.get_text())
                except Exception,error:
                    print "caught exception %s"%str(error)
                    return True
                if period < 0:
                    return True
                period_ms = int(1000*period)
                self.coshell_timeout_source_id = gobject.timeout_add\
                    ( period_ms, self.coshell_entry_callback , \
                          self.coshell_entry )                
                return True

        self.rvwidget = RvWidget()
        vbox_rv = builder.get_object("vbox_rv")
        vbox_rv.pack_start(self.rvwidget)

        label_time = builder.get_object("sig_time_lab")
        def update_time():
            time = self.runAndRead("signalTime OpenHRP.state")
            time = time.replace("\n","")
            label_time.set_text("Signal Time: %s"%time)
            return True

        gobject.timeout_add(200,update_time)
        
        self.cursor_state = None
        self.help_cursor = gtk.gdk.Cursor(gtk.gdk.QUESTION_ARROW)
        self.info_cursor = gtk.gdk.Cursor(gtk.gdk.PLUS)

        def help_button_clicked_cb(widget):    
            if self.cursor_state != 'help':
                widget.window.set_cursor(self.help_cursor)
                self.cursor_state = 'help'
            else:
                widget.window.set_cursor(None)
                self.cursor_state = None
            

        def info_button_clicked_cb(widget):
            if self.cursor_state != 'info':
                widget.window.set_cursor(self.info_cursor)                
                self.cursor_state = 'info'
            else:
                widget.window.set_cursor(None)
                self.cursor_state = None

        def signal_button_clicked_cb(widget):
            widget.window.set_cursor(None)
            self.cursor_state = None

        def reset_cam_button_clicked_cb(widget):
            self.rvwidget.camera = Camera()

        action_dict = {"refresh_button_clicked_cb" : self.widget.reload,
                       "zoomin_button_clicked_cb"  : self.widget.on_zoom_in,
                       "zoomout_button_clicked_cb" : self.widget.on_zoom_out,
                       "zoom100_button_clicked_cb" : self.widget.on_zoom_100,
                       "bestfit_button_clicked_cb" : self.widget.on_zoom_fit,
                       "gtk_main_quit"             : gtk.main_quit,     
                       "coshell_entry_changed_cb" : self.coshell_entry_callback,
                       "wordwrap_button_toggled_cb" : word_wrap_cb,
                       "matlab_button_toggled_cb" : mat_disp_cb,
                       "coshell_each_button_toggled_cb"   : coshell_period_activate_cb,
                       "coshell_period_activate_cb"   : coshell_period_activate_cb,
                       "simulate_button_toggled_cb"   : simulate_button_toggled_cb,
                       "help_button_clicked_cb"   : help_button_clicked_cb,
                       "info_button_clicked_cb"   : info_button_clicked_cb,
                       "signal_button_clicked_cb"   : signal_button_clicked_cb, 
                       "reset_cam_button_clicked_cb": reset_cam_button_clicked_cb,
                       }

        builder.connect_signals(action_dict)

        window.show_all()
        notebook = builder.get_object("notebook")
        notebook.set_current_page(1)
        self.rvwidget.finalInit()


    def coshell_entry_callback(self, widget):
        self.coshell_response_count += 1
        entry_text = widget.get_text()
        hist = [row[0] for row in self.coshell_hist_model]
        if entry_text not in hist:
            self.coshell_hist_model.prepend([entry_text])

        self.coshell_response.get_buffer().set_text(self.runAndRead(entry_text))
        if self.coshell_response_cnt_label:
            self.coshell_response_cnt_label.set_text("coshell response <%d>"\
                                             %self.coshell_response_count)
        if re.search(r"new|plug|unplug|destroy|clear|pop|push",entry_text):
            self.widget.reload(widget)
        return True

    def open_file(self, filename):
        try:
            fp = file(filename, 'rt')
            self.set_dotcode(fp.read(), filename)
            fp.close()
        except IOError, ex:
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR,
                                    message_format=str(ex),
                                    buttons=gtk.BUTTONS_OK)
            dlg.set_title('Dot Viewer')
            dlg.run()
            dlg.destroy()


            
    def set_dotcode(self, dotcode, filename='<stdin>'):
         if self.widget.set_dotcode(dotcode, filename):
            self.widget.zoom_to_fit()

    def set_xdotcode(self, dotcode, filename='<stdin>'):
         if self.widget.set_xdotcode(dotcode, filename):
            self.widget.zoom_to_fit()

    def tree_view_sel_callback(self,treeview,animate = True):
        ent = sig = io = cmd = io = None
        if treeview == self.en_tree_view:
            (model, iter) = treeview.get_selection().get_selected()
            row = model[iter]
            if self.cursor_state == 'help':
                cmd = '%s.help'%row[0]
            elif self.cursor_state == 'info':
                cmd = '%s.print'%row[0]
            else :
                cmd = '%s.signals'%row[0]
            self.coshell_entry.set_text(cmd)
            self.coshell_entry_callback(self.coshell_entry)
            list_signals = self.runAndRead('%s.signals'%row[0])
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
            if self.cursor_state == None:
                cmd = 'get %s.%s'%(ent,sig)        
            else:
                cmd = '%s.signalDep %s'%(ent,sig)        

            self.coshell_entry.set_text(cmd)
            self.coshell_entry_callback(self.coshell_entry)
            del cmd
        
        # find node and move there
        if ent == None or animate!= True:
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
                self.en_model.clear()
                messagedialog = gtk.MessageDialog\
                    (self.win, 0, gtk.MESSAGE_ERROR, \
                         gtk.BUTTONS_YES_NO,"Corba failed. Retry?")
                response = messagedialog.run()
                messagedialog.destroy()
                if response == gtk.RESPONSE_YES:
                    reload(corba_wrapper)
                elif response == gtk.RESPONSE_NO:
                    sys.exit(1)
        return result
