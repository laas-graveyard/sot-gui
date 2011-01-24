#! /usr/bin/env python
'''Visualize sot graph'''

__author__ = "Duong Dang"

__version__ = "0.2.1"


from xdot import *
import os,re
import time
from collections import deque
import gobject
import pygtk
pygtk.require('2.0')
import gtk,sys
from termwidget import TermWidget
from textwindow import TextWindowBase
import gtk.glade
from collections import deque
import corba_util
import logging
import logging.handlers
import pickle

sys.path = [os.path.dirname(os.path.abspath(__file__))
            +"/idl"] + sys.path

class MyHandler(logging.handlers.RotatingFileHandler):

    def __init__(self, filename, mode='a',
                 maxBytes=0, backupCount=0, encoding=None) :
        logging.handlers.RotatingFileHandler.__init__\
            (self, filename, mode, maxBytes, backupCount, encoding)
        self.last_warning = ""
        self.last_error = ""
        self.last_warning_t = None
        self.last_error_t = None

    def emit(self,record):
        """
        """
        logging.handlers.RotatingFileHandler.emit(self,record)
        if record.levelno >= 40:
            self.last_error_t = time.time()
            self.last_error = record.getMessage()

        elif record.levelno == 30:
            self.last_warning_t = time.time()
            self.last_warning = record.getMessage()

class TextWindow(TextWindowBase):
    """
    """

    def __init__(self, sw):
        """

        Arguments:
        - `sw`:
        """
        TextWindowBase.__init__(self)
        self.sotwin = sw
        self.script_dir = self.sotwin.setting.script_dir
        self.sotwin.text_window_destroyed = False
    def run_file(self,filename):
        """

        Arguments:
        - `filename`:
        """
        self.sotwin.coshell_entry.set_text("run %s"%filename)
        self.sotwin.coshell_entry_activate_cb(
            self.sotwin.coshell_entry)

    def run_cmd(self,cmd):
        """

        Arguments:
        - `filename`:
        """
        self.sotwin.coshell_entry.set_text("%s"%cmd)
        self.sotwin.coshell_entry_activate_cb(
            self.sotwin.coshell_entry)

    def window_destroy_cb(self, widget, data=None):
        self.sotwin.text_window_destroyed = True
        self.sotwin.view_editor.set_active(False)
        self.destroy()


class TimedMsg(object):
    """
    """

    def __init__(self, time,msg):
        """

        Arguments:
        - `time`:
        - `msg`:
        """
        self._time = time
        self._msg = msg

class Setting(object):
    """
    """
    def __init__(self, ):
        """
        """
        self.simu_dt = 0.05 # integration interval in s
        self.hrp_rvname = 'hrp'
        self.lazy_commands = ["zsh","use_profile sotdev","rlwrap $ROBOTPKG_BASE/bin/sot/test_shell",\
#                                  "run /local/nddang/profiles/sotdev/install/stable/script/simu",\
                                  "run /local/nddang/profiles/sotdev/install/stable/script/base",\
                                  "run /local/nddang/profiles/sotdev/install/stable/script/coshell",\
                                  ]

        self.script_dir = os.environ['ROBOTPKG_BASE']+'/script'

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
        self.openfilename = self.sot_graph_file

    def fetch_info_and_graph(self):
        self.sotwin.runAndRead("pool.writegraph %s"%self.sot_graph_file)

        return_str = self.sotwin.runAndRead("pool.list")
        if not return_str:
            return

        entities_str = deque(return_str.split())
        graph_names = set()
        graph_types = dict()
        while len(entities_str) > 0:
            aname = entities_str.popleft()
            atype = entities_str.popleft()
            graph_names.add(aname)
            graph_types[aname] = atype

        model_names = set()
        model_iters = dict()

        try:
            tree_iter = self.sotwin.en_model.get_iter_first()
        except:
            self.sotwin.logger.exception("Caught exception")
        else:
            while tree_iter:
                aname = self.sotwin.en_model[tree_iter]
                model_names.add(aname)
                model_iters[aname] = tree_iter
                tree_iter = self.sotwin.en_model.iter_next(tree_iter)


        new_names = graph_names.difference(model_names)
        old_names = model_names.difference(graph_names)

        for aname in new_names:
            atype = graph_types[aname]
            self.sotwin.en_model.append([aname,atype])
            if aname=='OpenHRP':
                self.sotwin.hrp_simuName = aname
                self.sotwin.robotType = atype
            elif aname == 'dyn':
                self.sotwin.has_dyn = True

        for aname in old_names:
            self.sotwin.en_model.remove(model_iters[aname])


        time.sleep(0.1)

        if os.path.isfile(self.sot_graph_file):
            s = open(self.sot_graph_file).read()
            s = s.replace("/%s"%self.graph_name,self.graph_name)
            f = open(self.sot_graph_file,'w')
            f.write(s)
            f.close()
            self.sotwin.graph_text = s
        return

    def reload(self):
        self.fetch_info_and_graph()
        if self.openfilename is not None:
            try:
                fp = file(self.openfilename, 'rt')
                self.set_dotcode(fp.read(), self.openfilename)
                fp.close()
            except IOError:
                self.sotwin.logger.exception("Caught exception")

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

        # select the appropriate entity and signal in treeviews
        try:
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
        except Exception,error:
            self.sotwin.logger.exception("Caught exception %s"%error)

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



class SotWindow(gtk.Window):
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

    def __getattr__(self, a):
        try:
            return self.builder.get_object(a)
        except:
            raise AttributeError("Invalid attribute/widget name %s "%a)

    def __init__(self, options=None,args=None):
        """
        """
        gtk.Window.__init__(self)
        os.system("rm -f %s"%SotWidget.sot_graph_file)
        self.win = self
        self.setting = Setting()
        self.is_offline = False
        self.graph_text = ""
        ######################################################################
        #   Main window
        #
        src_path = os.path.dirname(os.path.abspath(__file__))
        mainxml = src_path + "/main.xml"
        self.builder = gtk.Builder()
        self.builder.add_from_file(mainxml)
        window = self.builder.get_object("window")
        window.child.reparent(self)
        self.setting = Setting()
        if options and options.script_dir:
            self.setting.script_dir = options.script_dir

        ######################################################################
        #   Child widget names
        #
#        self.coshell_response_cnt_label = self.builder.get_object("coshell_response_cnt_label")
#        self.status = self.builder.get_object("status")
#        self.statusicon = self.builder.get_object("statusicon")
        self.coshell_response_count = -1
        self.coshell_timeout_source_id = None
        ## coshell history
        coshell_hist_text_view = self.builder.get_object("coshell_hist_text_view")
        self.coshell_hist_text_view_buffer = coshell_hist_text_view.get_buffer()
#        self.view_editor = self.builder.get_object("view_editor")

        ######################################################################
        #    Mis
        #
        self.hrp_simuName = None
        self.robotType = None
        self.has_dyn = False
        self.rv_incr_cb_srcid = None
        self.rv_cnt = 0
        self.text_window_destroyed = False

        ######################################################################
        #   Term widget
        #
        if options and options.with_term:
            term_vbox = self.builder.get_object("term_vbox")
            self.termwidget = TermWidget()
            term_vbox.pack_start(self.termwidget)
            if options.lazy_term:
                for cmd in self.setting.lazy_commands:
                    cmd = "%s\n"%cmd
                    self.termwidget.terminal.feed_child(cmd,len(cmd))
        else:
            notebook = self.builder.get_object("notebook")
            notebook.remove_page(2)


        ######################################################################
        #   Treeviews
        #
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
        vbox_graph = self.builder.get_object("vbox_graph")
        vbox_graph.pack_start(self.widget,True,True,0)

#        self.coshell_combo_box_entry =  self.builder.get_object("coshell_combo_box_entry")
        self.coshell_entry = self.coshell_combo_box_entry.child
        self.coshell_hist_model = gtk.ListStore(str)
        self.coshell_combo_box_entry.set_model( self.coshell_hist_model)
        self.coshell_combo_box_entry.set_text_column(0)
        self.coshell_entry.connect('activate',self.coshell_entry_activate_cb)
        self.coshell_cached = {}
#        self.coshell_response =  self.builder.get_object("coshell_response")
#        self.coshell_frame =  self.builder.get_object("coshell_frame")

#        self.en_tree_view = self.builder.get_object("en_tree_view")
        self.en_tree_view.set_model(self.en_model)
        self.en_tree_view.append_column(self.en_column1)
        self.en_tree_view.append_column(self.en_column2)
        self.en_tree_view.set_enable_search(True)
        self.en_tree_view.set_search_column(0)
        self.en_tree_view.connect('cursor-changed',self.tree_view_sel_callback)

#        self.sig_tree_view = self.builder.get_object("sig_tree_view")
        self.sig_tree_view.set_model(self.sig_model)
        self.sig_tree_view.append_column(self.sig_column1)
        self.sig_tree_view.append_column(self.sig_column2)
        self.sig_tree_view.set_enable_search(True)
        self.sig_tree_view.set_search_column(0)
        self.sig_tree_view.connect('cursor-changed',self.tree_view_sel_callback)
        #
        #   End treeviews
        ######################################################################

#        self.coshell_each_button = self.builder.get_object("coshell_each_button")
#        self.coshell_period = self.builder.get_object("coshell_period")

        self.coshell_timeout_source_id = None

        ######################################################################
        #   Logger
        #
        os.system('mkdir -p %s/.sot-gui/scripts'%os.environ['HOME'])
        os.system('mkdir -p %s/.sot-gui/log'%os.environ['HOME'])
        self.log_filename = '%s/.sot-gui/log/SotWindow.log'%os.environ['HOME']
        self.logger = logging.getLogger('SotWindow')
        self.log_level = logging.WARNING
        if options and options.debug:
            self.log_level = logging.DEBUG
        self.logger.setLevel(self.log_level)

        formatter = logging.Formatter("%(asctime)s : %(name)s : %(levelname)s : %(message)s")
        self.handler = MyHandler(self.log_filename, maxBytes = 10000000, backupCount=5)
        self.handler.setFormatter(formatter)

        self.logger.addHandler(self.handler)


        ######################################################################
        #   OpenGL widget
        #
        self.rvthread = None
        if options and options.with_rvwidget:
            from robotviewer.rvwidget import RvWidget
            self.rvwidget = RvWidget()
            vbox_rv = self.builder.get_object("vbox_rv")
            vbox_rv.pack_start(self.rvwidget)
            def update_HRP_config():
                pos = self.get_HRP_config()
                if pos:
                    self.rvwidget.updateElementConfig(self.setting.hrp_rvname,pos)
                else:
                    self.logger.warning('Couldnt get robot config')
                return True
            gobject.timeout_add(40,update_HRP_config)


        else:
            notebook = self.builder.get_object("notebook")
            notebook.remove_page(1)

#        self.label_time = self.builder.get_object("sig_time_lab")
        self.cursor_state = None
        self.help_cursor = gtk.gdk.Cursor(gtk.gdk.QUESTION_ARROW)
        self.info_cursor = gtk.gdk.Cursor(gtk.gdk.PLUS)
        rv_script_filename = self.builder.get_object("rv_script_filename")
        if os.path.isfile('%s/.sot-gui/scripts/los.py'%os.environ['HOME']):
            rv_script_filename.set_text('%s/.sot-gui/scripts/los.py'%os.environ['HOME'])

        ######################################################################
        #  Connnect signals
        #
        self.connect('destroy', gtk.main_quit)
        self.builder.connect_signals(self)
        gobject.timeout_add(200,self.house_keep)


        ######################################################################
        #   Final main widow inits
        #
        self.show_all()
        if  ( options and options.with_rvwidget):
            notebook = self.builder.get_object("notebook")
            notebook.set_current_page(1)
            self.rvwidget.finalInit()
        else:
            time.sleep(1)

        self.widget.reload()

        ######################################################################
        #   Text window
        #
        self.text_window = TextWindow(self)
        self.sotobj = corba_util.GetObject("CorbaServer",'CorbaServer.SOT_Server_Command',[('sot','context'),('coshell','servant')])



    #
    # END __init__
    ######################################################################




    ######################################################################
    #   House keeping callback
    #
    def house_keep(self):
        # update time
        result_str = None
        self.runAndRead("echo")
        if not self.hrp_simuName:
            self.logger.warning("SotWindow.house_keep Can't find OpenHRP entity")
        else:
            result_str = self.runAndRead("signalTime %s.state"%self.hrp_simuName)

        if result_str:
            try:
                ticks = int(result_str)
            except:
                self.logger.warning("wrong time format %s"%result_str )
            else:
                period = 0.005
                robottime = 0.0
                if self.robotType == '(RobotSimu)':
                    period = 0.05
                    robottime = ticks*period
                self.sig_time_lab.set_text("Signal Time: %3.3f (%d ticks)"%(robottime,ticks))


        if self.handler.last_error_t and time.time() - self.handler.last_error_t < 0.2 :
            self.status.set_text("%s" %(self.handler.last_error))
            self.statusicon.set_from_stock(gtk.STOCK_DIALOG_ERROR,gtk.ICON_SIZE_BUTTON)
            return True

        if self.handler.last_warning_t and time.time() - self.handler.last_warning_t < 0.2 :
            self.status.set_text("%s" %(self.handler.last_warning))
            self.statusicon.set_from_stock(gtk.STOCK_DIALOG_WARNING,gtk.ICON_SIZE_BUTTON)
            return True

        self.statusicon.set_from_stock(gtk.STOCK_YES,gtk.ICON_SIZE_BUTTON)
        self.status.set_text("")
        return True


    def open_file(self, filename):
        try:
            fp = file(filename, 'rt')
            self.set_dotcode(fp.read(), filename)
            fp.close()
        except IOError, ex:
            self.logger.exception("%s"%ex)

    def set_dotcode(self, dotcode, filename='<stdin>'):
         if self.widget.set_dotcode(dotcode, filename):
            self.widget.zoom_to_fit()

    def set_xdotcode(self, dotcode, filename='<stdin>'):
         if self.widget.set_xdotcode(dotcode, filename):
            self.widget.zoom_to_fit()


    def take_snapshot_button_clicked_cb(self, widget, data=None):
        # cached the following:
        # for all entity:
        #       entity.help
        #       entity.print
        #       entity.signals
        #       for all signals:
        #           get signal
        #           entity.signalDep signal
        #
        sig_pattern = re.compile(r".*(input|output)\((\w+)\)::(\w+)*")
        for line in self.en_model:
            ent = line[0]
            ent_type = line[1]
            self.runAndRead("%s.help"%ent)
            self.runAndRead("%s.print"%ent)
            list_signals = self.runAndRead("%s.signals"%ent)
            for line in list_signals.splitlines():
                m = sig_pattern.match(line)
                if m:
                    sig = m.group(3)
                    self.runAndRead('get %s.%s'%(ent,sig))
                    self.runAndRead('%s.signalDep %s'%(ent,sig))

    def tree_view_sel_callback(self,treeview,animate = True):
        ent = sig = io = cmd = io = None
        # click on an entity entry:
        #   * update signal treeview
        #   * display appropriate info

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
            self.coshell_entry_activate_cb(self.coshell_entry)
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
            self.coshell_entry_activate_cb(self.coshell_entry)
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


    def corba_broken_cb(self):
        ## robot settings
        self.hrp_simuName = None
        self.robotType = None
        self.has_dyn = False
        self.en_model.clear()
        self.sig_model.clear()
        os.system('rm -f %s'%SotWidget.sot_graph_file)
        self.widget.graph=Graph()
        self.widget.queue_draw()

    def runAndRead(self,s):
        if self.is_offline:
            if s in self.coshell_cached.keys():
                return self.coshell_cached[s]
            else:
                return ""


        try:
            self.logger.debug("coshell-> %s"%s)
            result = self.sotobj.runAndRead(s)
            self.coshell_cached[s] = result
        except Exception,error:
            self.logger.exception("Caught exception %s"%error)
            # self.sotobj = corba_util.GetObject("CorbaServer",'CorbaServer.SOT_Server_Command',[('sot','context'),('coshell','servant')])

#            self.corba_broken_cb()
            return ""
        return result


    def get_HRP_config(self):
        if not self.hrp_simuName:
            self.logger.warning("SotWindow.get_HRP_config Can't find OpenHRP entity")
            self.widget.reload()
            return None

        if not self.has_dyn:
            self.logger.warning("SotWindow.get_HRP_config Can't find dyn entity")
            return None

        try:
            self.logger.debug("calling self.sotobj.req_obj.readVector('OpenHRP.state')")
            pos = self.sotobj.readVector("OpenHRP.state")
            self.logger.debug("calling self.sotobj.req_obj.readVector('dyn.ffposition')")
            wst = self.sotobj.readVector("dyn.ffposition")
        except Exception,error:
            self.logger.exception("Caught exception %s"%error)
            # self.corba_broken_cb()
            return None

        if len(wst) != 6:
            self.logger.warning("RvWidget: Wrong dimension of waist_pos, robot not updated")
            return None

        for i in range(len(wst)):
            pos[i] = wst[i]

        if self.robotType == "(RobotSimu)":
            pos[2] += 0.105

        # dynsmall thingy
        if len(pos) == 36:
            pos_full = [0 for i in range(46)]
            for i in range(29):
                pos_full[i] = pos[i]
            for i in range(29,36):
                pos_full[i+5] = pos[i]
            return pos_full

        return pos



    ######################################################################
    #   GUI callbacks
    #
    #
    #
    def coshell_entry_activate_cb(self, widget, data = None):
        self.coshell_response_count += 1
        entry_text = widget.get_text()
        self.coshell_hist_text_view_buffer.insert_at_cursor("%s\n"%entry_text)
        hist = [row[0] for row in self.coshell_hist_model]
        if entry_text not in hist:
            self.coshell_hist_model.prepend([entry_text])

        self.coshell_response.get_buffer().set_text(self.runAndRead(entry_text))
        if self.coshell_response_cnt_label:
            self.coshell_response_cnt_label.set_text("coshell response <%d>"\
                                             %self.coshell_response_count)
        if re.search(r"run|new|plug|unplug|destroy|clear|pop|push",entry_text):
            self.widget.reload()

        return True


    def wordwrap_button_toggled_cb(self, widget, data = None):
        if widget.get_active()==0:
            self.coshell_response.set_wrap_mode(False)
        else:
            self.coshell_response.set_wrap_mode(True)

    def matlab_button_toggled_cb(self, widget, data = None):
        if widget.get_active()==0:
            self.runAndRead('dispmat simple')
            self.coshell_entry_activate_cb(self.coshell_entry)
        else:
            self.runAndRead('dispmat matlab')
            self.coshell_entry_activate_cb(self.coshell_entry)

    def simulate_button_toggled_cb(self, button, data = None):
        def rv_incr_cb():
            self.rv_cnt += 1
            if not self.hrp_simuName:
                self.logger.warning("SotWindow.rv_incr_cb Can't find OpenHRP entity")
                return True
            cmd = "%s.inc %f"%(self.hrp_simuName, self.setting.simu_dt)
            self.runAndRead(cmd)
            return True


        if self.rv_incr_cb_srcid:
            gobject.source_remove(self.rv_incr_cb_srcid)
            self.rv_incr_cb_srcid = None

        if button.get_active()!=0:
            if self.robotType =='(RobotSimu)':
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

    def coshell_period_activate_cb(self, widget, data = None):
        if self.coshell_timeout_source_id:
            try:
                gobject.source_remove(self.coshell_timeout_source_id)
            except Exception,error:
                self.logger.exception("Caught exception %s"%error)

        if self.coshell_each_button.get_active()==0:
            return True
        else:
            try:
                period = float(self.coshell_period.get_text())
            except Exception,error:
                self.logger.exception("Caught exception %s"%error)
                return True
            if period < 0:
                return True
            period_ms = int(1000*period)
            self.coshell_timeout_source_id = gobject.timeout_add\
                ( period_ms, self.coshell_entry_activate_cb , \
                      self.coshell_entry )
            return True

    def coshell_each_button_toggled_cb(self, widget, data = None):
        self.coshell_period_activate_cb(widget, data )

    def help_button_clicked_cb(self, widget, data = None):
        if self.cursor_state != 'help':
            widget.window.set_cursor(self.help_cursor)
            self.cursor_state = 'help'
        else:
            widget.window.set_cursor(None)
            self.cursor_state = None

    def rv_script_open_button_clicked_cb(self, widget, data = None):
        chooser = gtk.FileChooserDialog("Save File...", self,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            rv_script_filename = self.builder.get_object("rv_script_filename")
            rv_script_filename.set_text(filename)
        chooser.destroy()

    def rv_script_run_button_clicked_cb(self, widget, data = None):
        rv_script_filename = self.builder.get_object("rv_script_filename")
        filename = rv_script_filename.get_text()
        s = open(filename).read()
        exec(s)


    def info_button_clicked_cb(self, widget, data = None):
        if self.cursor_state != 'info':
            widget.window.set_cursor(self.info_cursor)
            self.cursor_state = 'info'
        else:
            widget.window.set_cursor(None)
            self.cursor_state = None

    def signal_button_clicked_cb(self, widget, data = None):
        widget.window.set_cursor(None)
        self.cursor_state = None

    def reset_cam_button_clicked_cb(self, widget, data = None):
        self.rvwidget.camera = Camera()

    def about_item_activate_cb(self, widget, data = None):
        aboutdialog = self.builder.get_object("aboutdialog")
        aboutdialog.run()
        aboutdialog.hide()

    def statusicon_button_press_event_cb(self, widget , event = None, data = None):
        log_window = self.builder.get_object('log_window')
        log_text_view = self.builder.get_object('log_text_view')
        log_buffer = log_text_view.get_buffer()
        log_buffer.set_text(open(self.log_filename).read())
#            log_scrolled_window = self.builder.get_object('log_scrolled_window')
#            vscrollbar = log_scrolled_window.get_vscrollbar()
#            vscrollbar.adjustment.set_value(vscrollbar.adjustment.get_upper())
        log_window.run()
        log_window.hide()

    def view_log_activate_cb(self, widget, data = None):
        self.statusicon_button_press_event_cb(widget)

    def view_editor_toggled_cb(self, widget, data = None):
        if not widget.get_active():
            self.text_window.hide()
        else:
            if  self.text_window_destroyed:
                self.text_window = TextWindow(self)
            self.text_window.show_all()

    def view_coshell_hist_activate_cb(self, widget, data = None):
        self.logger.debug("view_coshell_hist_menu_activate_cb called")
        coshell_hist_window = self.builder.get_object('coshell_hist_window')
        coshell_hist_window.run()
        coshell_hist_window.hide()

    def init_corba_button_clicked_cb(self, widget, data = None):
        self.sotobj = corba_util.GetObject("CorbaServer",'CorbaServer.SOT_Server_Command',[('sot','context'),('coshell','servant')])


    def gtk_main_quit(self, widget, data = None):
        if self.rvthread:
            self.rvthread.quit = True
        gtk.main_quit()

    def refresh_button_clicked_cb(self, widget, data = None):
        self.widget.reload()

    def run_menu_activate_cb(self, widget, data = None):
        chooser = gtk.FileChooserDialog\
            (title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,\
                 buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,\
                              gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_current_folder(self.setting.script_dir)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            self.logger.debug("User selects %s script"%filename)
            if filename:
                self.coshell_entry.set_text("run %s"%filename)
                self.coshell_entry_activate_cb(self.coshell_entry)

        elif response == gtk.RESPONSE_CANCEL:
            self.logger.debug("Run script canceled by user")

        chooser.destroy()
        return

    def viewer_console_activate_cb(self, widget, data = None):
        text = widget.get_text()
        words = text.split()
        cmd = str_arg = ""
        l = []
        if words[:]:
            cmd = words[0]
        if words[1:]:
            str_arg = word[1]
        if words[2:]:
            l = eval(words[2:])
        ret = self.rvwidget.run_cmd(cmd, str_arg, l)
        self.coshell_response.get_buffer().set_text(ret)


    def clear_button_clicked_cb(self, widget, data = None):
        self.coshell_entry.set_text("")

    def zoomin_button_clicked_cb(self, widget, data = None):
        self.widget.on_zoom_in(  widget  )

    def zoomout_button_clicked_cb(self, widget, data = None):
        self.widget.on_zoom_out(  widget )

    def zoom100_button_clicked_cb(self, widget, data = None):
        self.widget.on_zoom_100(  widget )

    def bestfit_button_clicked_cb(self, widget, data = None):
        self.widget.on_zoom_fit(  widget )

    def debug_menu_item_toggled_cb(self, widget, data = None):
        if widget.get_active() == 0:
            self.logger.setLevel(logging.CRITICAL)
        if widget.get_active() == 0:
            self.logger.setLevel(self.log_level)

    def offline_button_toggled_cb(self, widget, data = None):
        self.is_offline = widget.get_active()
        self.coshell_entry.set_editable(not self.is_offline)
        self.init_corba_button.set_sensitive(not self.is_offline)
        self.take_snapshot_button.set_sensitive(not self.is_offline)
        self.refresh_button.set_sensitive(not self.is_offline)
        self.save_snapshot.set_sensitive(not self.is_offline)

    def save_snapshot_activate_cb(self, widget, data = None):
        chooser = gtk.FileChooserDialog("Open File...", self,
                                        gtk.FILE_CHOOSER_ACTION_SAVE,
                                        (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filt = gtk.FileFilter()
        response = chooser.run()
        filename = None
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
        chooser.destroy()
        if not filename:
            return
        self.logger.info("Saving snapshot to %s"%filename)
        f = open(filename, 'w')
        pickle.dump([self.graph_text, self.coshell_cached], f)
        f.close()

    def open_snapshot_activate_cb(self, widget, data = None):
        if not self.offline_button.get_active():
            self.offline_button.clicked()
        self.is_offline = True
        chooser = gtk.FileChooserDialog("Open File...", self,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        filt = gtk.FileFilter()
        response = chooser.run()
        filename = None
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
        chooser.destroy()
        if not filename:
            return
        f = open(filename, 'r')
        self.graph_text, self.coshell_cached = pickle.load(f)
        f.close()
        f = open(SotWidget.sot_graph_file,'w')
        f.write(self.graph_text)
        f.close()
        self.widget.fetch_info_and_graph()
        self.widget.reload()
