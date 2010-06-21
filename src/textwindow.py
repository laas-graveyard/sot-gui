#!/usr/bin/env python


import sys
import os
import gtk
import pango
import gobject
from collections import deque
import pygrep
from pygrep import TextRef, Match
class TextBuffer(gtk.TextBuffer):
    """
    """
    
    def __init__(self, tbuffer = None):
        """
        """
        gtk.TextBuffer.__init__(self,tbuffer)
        self.hltag = self.create_tag(background = 'yellow')
        self.hltext = None

    def highlight_line(self,lineno, start=None, end=None):
        """Highlight a line in buffer, return highlighted text        
        Arguments:
        - `self`:
        - `lineno`:
        
        """
        self.unhighlight_all()
        iter1 = self.get_iter_at_line(lineno)

        if start:
            iter1.forward_chars(start)

        if end:
            iter2 =  self.get_iter_at_line(lineno)
            iter2.forward_chars(end)
        else:
            try:
                iter2 = self.get_iter_at_line(lineno + 1)
                iter2.backward_char()
            except:
                iter2 = self.get_end_iter()
        self.apply_tag(self.hltag, iter1, iter2)
        self.hltext = iter1.get_text(iter2)

    def unhighlight_all(self):
        """
        
        Arguments:
        - `self`:
        """
        # erase previous hightlights
        iter1 = self.get_start_iter()
        iter2 = self.get_end_iter()
        self.remove_all_tags(iter1, iter2)
        
       

class TextWindowBase(gtk.Window):
    ##########################################################################
    #   Init
    #
    def __init__(self):    
        # Default values
        gtk.Window.__init__(self)
        self.connect('destroy', self.window_destroy_cb)
        self.filename = None

        # use GtkBuilder to build our interface from the XML file 
        try:
            src_path = os.path.dirname(os.path.abspath(__file__))
            builder = gtk.Builder()
            builder.add_from_file(src_path+"/text.xml") 
        except:
            self.error_message("Failed to load UI XML file: text.xml")
            sys.exit(1)
        
        self.current_line = 0
        self.script_dir = None
        # get the widgets which will be referenced in callbacks
        window = builder.get_object("window")
        window.child.reparent(self)

        self.statusbar = builder.get_object("statusbar")
        self.text_view = builder.get_object("text_view")
        self.text_view.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 30)
        self.line_no_entry = builder.get_object("line_no_entry")
        self.line_no_entry.set_text(str(self.current_line))

        self.text_buffer = TextBuffer()
        self.text_view.set_buffer(self.text_buffer)

        self.text_buffer.highlight_line(self.current_line)
        self.find_entry = builder.get_object("find_entry")
        ##########################################################################
        #   treeviews
        #
        def cell_text_func(treeviewcolumn, cell_renderer, model, iter):
            obj = model.get_value(iter, 0)
            if isinstance(obj, Entity):                
                render_text = obj._name
            elif isinstance(obj, TextRef):
                render_text = "%d:%s"%(obj._lineno, obj._linetext)
            elif isinstance(obj, Match):
                render_text = "%s"%obj._filename
            cell_renderer.set_property('text', render_text)
            return


        def sort_func(model, iter1, iter2):
            ob1 = model[iter1][0]
            ob2 = model[iter2][0]
            if ob1._name == ob2._name:
                return 0
            elif  ob1._name > ob2._name:
                return 1
            else:
                return -1       
        SORT_COL = 1000        
        self.en_tree_view = builder.get_object("en_tree_view")
        self.en_model = gtk.ListStore(object)
        self.en_tree_view.set_model(self.en_model)
        renderer = gtk.CellRendererText()
        treeviewcolumn = gtk.TreeViewColumn('Entity', renderer)
        treeviewcolumn.set_cell_data_func( renderer, cell_text_func)
        self.en_model.set_sort_func(SORT_COL, sort_func)
        treeviewcolumn.set_sort_column_id(SORT_COL)
        self.en_tree_view.append_column(treeviewcolumn)
        self.en_tree_view.set_rules_hint(True)

        self.tr_tree_view = builder.get_object("tr_tree_view")
        self.tr_model = gtk.TreeStore(object)
        self.tr_tree_view.set_model(self.tr_model)
        renderer = gtk.CellRendererText()
        treeviewcolumn = gtk.TreeViewColumn('Entity', renderer)
        treeviewcolumn.set_cell_data_func( renderer, cell_text_func)
        self.tr_tree_view.append_column(treeviewcolumn)
        self.tr_tree_view.set_rules_hint(True)

        self.ent_list_iter_dict = dict()
        self.ent_tree_iter_dict = dict()

        self.find_tree_view = builder.get_object("find_tree_view")
        self.find_model = gtk.TreeStore(object)
        self.find_tree_view.set_model(self.find_model)
        renderer = gtk.CellRendererText()
        treeviewcolumn = gtk.TreeViewColumn(None, renderer)
        treeviewcolumn.set_cell_data_func( renderer, cell_text_func)
        self.find_tree_view.append_column(treeviewcolumn)
        self.find_tree_view.set_rules_hint(True)
        
        #   
        #   treeviews
        ##########################################################################

        self.script_text_view = builder.get_object("script_text_view")
        tb = TextBuffer()
        self.script_text_view.set_buffer(tb)
        self.script_text_view.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 30)
        self.script_text_view.connect("expose_event",\
                                          self.script_text_view_expose_event_cb)
        self.script_scrolled_window = \
            builder.get_object("script_scrolled_window")
        # connect signals
        builder.connect_signals(self)

        # set the text view font
        self.text_view.modify_font(pango.FontDescription("monospace 10"))

        # set the default icon to the GTK "edit" icon
        gtk.window_set_default_icon_name(gtk.STOCK_EDIT)

        # setup and initialize our statusbar
        self.statusbar_cid = \
            self.statusbar.get_context_id("Tutorial GTK+ Text Editor")
        self.reset_default_status()
        self.tree = None


    ##########################################################################
    #   GUI Callbacks
    #
    def window_destroy_cb(self, widget, data=None):    
        gtk.main_quit()

    def window_delete_event_cb(self, widget, event, data=None):    
        if self.check_for_save(): self.save_menu_item_activate(None, None)
        return False 


    def new_menu_item_activate_cb(self, menuitem, data=None):    
        if self.check_for_save(): 
            self.save_menu_item_activate_cb(None, None)

        buff = self.text_view.get_buffer()
        buff.set_text("")
        buff.set_modified(False)
        self.filename = None
        self.reset_default_status()


    def open_menu_item_activate_cb(self, menuitem, data=None):

        if self.check_for_save(): self.save_menu_item_activate(None, None)

        filename = self.get_open_filename()
        if filename: self.load_file(filename)

    def save_menu_item_activate_cb(self, menuitem, data=None):
        if self.filename == None: 
            filename = self.get_save_filename()
            if filename:
                self.write_file(filename)
        else: 
            self.write_file(None)

    def save_as_menu_item_activate_cb(self, menuitem, data=None):

        filename = self.get_save_filename()
        if filename: self.write_file(filename)


    def quit_menu_item_activate_cb(self, menuitem, data=None):
        if self.check_for_save(): 
            self.save_menu_item_activate(None, None)
        self.window_destroy_cb(menuitem, data=None)

    def cut_menu_item_activate_cb(self, menuitem, data=None):

        buff = self.text_view.get_buffer();
        buff.cut_clipboard (gtk.clipboard_get(), True);

    def copy_menu_item_activate_cb(self, menuitem, data=None):

        buff = self.text_view.get_buffer();
        buff.copy_clipboard (gtk.clipboard_get());

    def paste_menu_item_activate_cb(self, menuitem, data=None):

        buff = self.text_view.get_buffer();
        buff.paste_clipboard (gtk.clipboard_get(), None, True);

    def delete_menu_item_activate_cb(self, menuitem, data=None):

        buff = self.text_view.get_buffer();
        buff.delete_selection (False, True);

    def text_view_expose_event_cb(self, widget, event, data = None):
        text_view = widget
        text_buffer = text_view.get_buffer()
        target = text_view.get_window(gtk.TEXT_WINDOW_LEFT)

        first_y = event.area.y
        last_y = first_y + event.area.height

        x, first_y = text_view.window_to_buffer_coords(\
            gtk.TEXT_WINDOW_LEFT, 0, first_y)
        x, last_y = text_view.window_to_buffer_coords(\
            gtk.TEXT_WINDOW_LEFT, 0, last_y)

        numbers = []
        pixels = []
        count = self.get_lines(text_view, first_y, last_y, pixels, numbers)

        # Draw fully internationalized numbers!
        layout = text_view.create_pango_layout("")

        for i in range(count):
            x, pos = text_view.buffer_to_window_coords(\
                gtk.TEXT_WINDOW_LEFT, 0, pixels[i])
            string = "%d" % numbers[i]
            layout.set_text(string)
            text_view.style.paint_layout(target, text_view.state, False,
                                      None, text_view, None, 2, \
                                             pos + 2, layout)

        # don't stop emission, need to draw children
        return False

    def script_text_view_expose_event_cb(self, widget, event, data = None):
        self.text_view_expose_event_cb(widget, event, data )

    def run_button_clicked_cb(self, widget,  data = None):
        self.run_file(self.filename)
        

    def step_button_clicked_cb(self, widget,  data = None):
        self.run_cmd(self.text_buffer.hltext)
        if self.current_line < self.text_buffer.get_line_count()-1:
            self.current_line += 1
            self.line_no_entry.set_text(str(self.current_line))
        self.text_buffer.highlight_line(self.current_line)
        
    def line_no_entry_activate_cb(self, widget,  data = None):
        new_line_no = int(widget.get_text())
        if new_line_no < self.text_buffer.get_line_count()-1:
            self.current_line = int(widget.get_text())
            self.text_buffer.highlight_line(self.current_line)
        else:
            widget.set_text(str(self.text_buffer.get_line_count()-1))


    def index_button_clicked_cb(self, widget,  data = None):
        self.parse_tree()
        self.en_model.clear()
        self.tr_model.clear()
        self.en_list_iter_dict = dict()
        self.en_tree_iter_dict = dict()
        if self.tree:
            pile = deque()
            pile.append(self.tree) 
            while not len(pile) == 0:
                an_element = pile.pop()
                for child in an_element._children:
                    pile.append(child)

                # append element to list/tree
                self.en_list_iter_dict[an_element] = \
                    self.en_model.append([an_element])

                if an_element._parent == None:
                    parent_iter = None
                else:
                    parent_iter = self.en_tree_iter_dict[an_element._parent]
                self.en_tree_iter_dict[an_element] = \
                    self.tr_model.append(parent_iter,[an_element])
        self.tr_tree_view.expand_all()
            
    def find_entry_activate_cb(self, widget,  data = None):
        querry = self.find_entry.get_text()
        self.find_model.clear()
        if self.tree:
            pile = deque()
            pile.append(self.tree) 
            foundfiles = []
            while not len(pile) == 0:
                an_element = pile.pop()
                for child in an_element._children:
                    pile.append(child)
                if not isinstance(an_element,Script):
                    continue
                match = pygrep.find(querry,an_element._name)
                if match:
                    foundfiles.append(match._filename)
                    par_iter = self.find_model.append(None,[match])
                    for ref in match._refs:
                        self.find_model.append(par_iter,[ref])

        self.find_tree_view.expand_all()

    def en_tree_view_cursor_changed_cb(self, widget,  data = None):
        treeview = widget
        (model, iter) = treeview.get_selection().get_selected()
        row = model[iter]
        entity = row[0]
        text_buffer = self.script_text_view.get_buffer()

        tree_iter = self.en_tree_iter_dict[entity]
        self.tr_tree_view.get_selection().select_iter(tree_iter)

        if entity._ref  == None:
            text_buffer.set_text("")
            return

        fname = entity._ref[0]
        lineno = entity._ref[1]

        text_buffer = self.script_text_view.get_buffer()
        text_buffer.set_text(open(fname).read())
        text_buffer.highlight_line(lineno)
        self.script_scrolled_window.queue_draw()


    def tr_tree_view_cursor_changed_cb(self, widget,  data = None):
        treeview = widget
        (model, iter) = treeview.get_selection().get_selected()
        row = model[iter]
        entity = row[0]
        text_buffer = self.script_text_view.get_buffer()

        list_iter = self.en_list_iter_dict[entity]
        self.en_tree_view.get_selection().select_iter(list_iter)

        if entity._ref  == None:
            text_buffer.set_text("")
            return

        fname = entity._ref[0]
        lineno = entity._ref[1]

        text_buffer = self.script_text_view.get_buffer()
        text_buffer.set_text(open(fname).read())
        text_buffer.highlight_line(lineno)
        self.script_scrolled_window.queue_draw()

    def find_tree_view_cursor_changed_cb(self, widget,  data = None):
        treeview = widget
        (model, iter) = treeview.get_selection().get_selected()
        obj = model[iter][0]
        text_buffer = TextBuffer()
        self.script_text_view.set_buffer(text_buffer)

        text_buffer.set_text(open(obj._filename).read())
        text_buffer.unhighlight_all()

        if isinstance(obj, Match):
            self.script_scrolled_window.queue_draw()
            return
        elif isinstance(obj, TextRef):
            print (obj._lineno,obj._start, obj._end)
            text_buffer.highlight_line(obj._lineno,obj._start, obj._end)
            self.script_scrolled_window.queue_draw()

    #
    #   GUI Callbacks
    ##########################################################################

   
    def run_file(self,filename):
        print "TextWindow.run_file(%s)"%filename

    def run_cmd(self,cmd):
        print "TextWindow.run_cmd(%s)"%cmd


    def get_lines(self, text_view, first_y, last_y, buffer_coords, numbers):
        # Get iter at first y
        iter, top = text_view.get_line_at_y(first_y)

        # For each iter, get its location and add it to the arrays.
        # Stop when we pass last_y
        count = 0
        size = 0

        while not iter.is_end():
            y, height = text_view.get_line_yrange(iter)
            buffer_coords.append(y)
            line_num = iter.get_line()
            numbers.append(line_num)
            count += 1
            if (y + height) >= last_y:
                break
            iter.forward_line()

        return count

    def error_message(self, message):

        # log to terminal window
        print message

        # create an error message dialog and display modally to the user
        dialog = gtk.MessageDialog(None,
                                   gtk.DIALOG_MODAL | \
                                       gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message)

        dialog.run()
        dialog.destroy()


    def check_for_save (self):

        ret = False
        buff = self.text_view.get_buffer()

        if buff.get_modified():

            # we need to prompt for save
            message = "Do you want to save the changes you have made?"
            dialog = gtk.MessageDialog(self,
                                       gtk.DIALOG_MODAL | \
                                           gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_QUESTION, 
                                       gtk.BUTTONS_YES_NO, 
                                       message)
            dialog.set_title("Save?")

            if dialog.run() == gtk.RESPONSE_NO: 
                ret = False
            else: 
                ret = True

            dialog.destroy()

        return ret    


    def get_open_filename(self):

        filename = None
        chooser = gtk.FileChooserDialog("Open File...", self,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL, 
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        if self.script_dir:
            chooser.set_current_folder(self.script_dir)

        response = chooser.run()
        if response == gtk.RESPONSE_OK: filename = chooser.get_filename()
        chooser.destroy()

        return filename


    def get_save_filename(self):
        filename = None
        chooser = gtk.FileChooserDialog("Save File...", self,
                                        gtk.FILE_CHOOSER_ACTION_SAVE,
                                        (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL, 
                                         gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        if self.script_dir:
            chooser.set_current_folder(self.script_dir)

        response = chooser.run()
        if response == gtk.RESPONSE_OK: filename = chooser.get_filename()
        chooser.destroy()

        return filename


    def load_file(self, filename):
        # add Loading message to status bar and ensure GUI is current
        self.statusbar.push(self.statusbar_cid, "Loading %s" % filename)

        try:
            # get the file contents
            fin = open(filename, "r")
            text = fin.read()
            fin.close()

            # disable the text view while loading the buffer with the text
            self.text_view.set_sensitive(False)
            buff = self.text_view.get_buffer()
            buff.set_text(text)
            buff.set_modified(False)
            self.text_view.set_sensitive(True)

            # now we can set the current filename since loading was a success
            self.filename = filename

        except:
            # error loading file, show message to user
            self.error_message ("Could not open file: %s" % filename)

        # clear loading status and restore default 
        self.statusbar.pop(self.statusbar_cid)
        self.reset_default_status()
        self.index_button_clicked_cb( None )
        self.text_buffer.highlight_line(self.current_line)
        
    def write_file(self, filename):
        # add Saving message to status bar and ensure GUI is current
        if filename: 
            self.statusbar.push(self.statusbar_cid, "Saving %s" % filename)
        else:
            self.statusbar.push(self.statusbar_cid, "Saving %s" \
                                    % self.filename)

        try:
            # disable text view while getting contents of buffer
            buff = self.text_view.get_buffer()
            self.text_view.set_sensitive(False)
            text = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
            self.text_view.set_sensitive(True)
            buff.set_modified(False)

            # set the contents of the file to the text from the buffer
            if filename: 
                fout = open(filename, "w")
            else: 
                fout = open(self.filename, "w")
            fout.write(text)
            fout.close()

            if filename: 
                self.filename = filename

        except:
            # error writing file, show message to user
            self.error_message ("Could not save file: %s" % filename)

        # clear saving status and restore default     
        self.statusbar.pop(self.statusbar_cid)
        self.reset_default_status()

    def reset_default_status(self):

        if self.filename: status = "File: %s" % os.path.basename(self.filename)
        else: status = "File: (UNTITLED)"

        self.statusbar.pop(self.statusbar_cid)
        self.statusbar.push(self.statusbar_cid, status)


    def parse_tree(self):
        if not self.filename:
            self.tree = None
            return
        self.tree = Script(self.filename)


# a ref: (filename,line_no)

class Entity(object):
    """
    """
    
    def __init__(self, name = None, parent = None, ref = (None,-1)):
        """
        
        Arguments:
        - `name`:
        - `coor`:
        - `-1)`:
        """
        self._name = name
        self._ref  = ref
        self._parent = parent
        self._children = []

    def __str__(self):
        return "Entity " + self._name + " located at %s"%str(self._coor)


import re


class Script(Entity):
    """
    """
    run_pattern = re.compile(r"run\s+(\S+)")
    new_pattern = re.compile(r"new\s+(\S+)\s+(\S+)")
    comment_pattern = re.compile(r"#.+")     

    def __init__(self, name = None, parent = None, ref = None):
        """
        
        Arguments:
        - `name`:
        - `coor`:
        - `-1)`:
        """
        Entity.__init__(self,name,parent,ref)
        self.parse()
    
    def __str__(self):
        return "Script " + self._name + " located at %s"\
            %str(self._coor) + " with %s children"%len(self._children)
    
    def parse(self):
        lines = open(self._name).readlines()
        for i in range(len(lines)):
            line = lines[i]
            line = self.comment_pattern.sub("",line)
            m = self.run_pattern.search(line)
            if m:
                script_child = Script(name = m.group(1), parent = self, ref = (self._name,i))
                self._children.append(script_child)                
                continue

            m = self.new_pattern.search(line)
            if m:
                entity_child = Entity(name = m.group(2),parent = self,ref = (self._name,i))
                self._children.append(entity_child)
                continue
        # print "parsed ", self

    def find_string(self,querry):
        """Find a string in itself and its tree
        return a list of entities
        Arguments:
        - `self`:
        - `querry`:
        """
        l = []

        

        return l


def main():
    window = TextWindowBase()
    window.show()
    window.script_dir = "/local/nddang/profiles/sotdev/install/stable/script/"
    gtk.main()

def main2():
    window = TextWindowBase()
    window.parse_tree()

    
if __name__ == "__main__":
    main()
