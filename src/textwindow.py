#!/usr/bin/env python


import sys
import os
import gtk
import pango

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
            builder = gtk.Builder()
            builder.add_from_file("text.xml") 
        except:
            self.error_message("Failed to load UI XML file: tutorial.xml")
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
        self.text_buffer = self.text_view.get_buffer()
        self.hltag = self.text_buffer.create_tag(background = 'yellow')
        self.highlighted_text = ""
        self.highlight()
        # connect signals
        builder.connect_signals(self)

        # set the text view font
        self.text_view.modify_font(pango.FontDescription("monospace 10"))

        # set the default icon to the GTK "edit" icon
        gtk.window_set_default_icon_name(gtk.STOCK_EDIT)

        # setup and initialize our statusbar
        self.statusbar_cid = self.statusbar.get_context_id("Tutorial GTK+ Text Editor")
        self.reset_default_status()



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
            self.save_menu_item_activate(None, None)

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
            if filename: self.write_file(filename)
        else: self.write_file(None)

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
        text_view = self.text_view
        target = text_view.get_window(gtk.TEXT_WINDOW_LEFT)

        first_y = event.area.y
        last_y = first_y + event.area.height

        x, first_y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_LEFT, 0, first_y)
        x, last_y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_LEFT, 0, last_y)

        numbers = []
        pixels = []
        count = self.get_lines(first_y, last_y, pixels, numbers)

        # Draw fully internationalized numbers!
        layout = text_view.create_pango_layout("")

        for i in range(count):
            x, pos = text_view.buffer_to_window_coords(gtk.TEXT_WINDOW_LEFT, 0, pixels[i])
            string = "%d" % numbers[i]
            layout.set_text(string)
            text_view.style.paint_layout(target, text_view.state, False,
                                      None, text_view, None, 2, pos + 2, layout)

        # don't stop emission, need to draw children
        self.highlight()
        return False

    def run_button_clicked_cb(self, widget,  data = None):
        self.run_file(self.filename)
        

    def step_button_clicked_cb(self, widget,  data = None):
        self.run_cmd(self.highlighted_text)

        if self.current_line < self.text_buffer.get_line_count()-1:
            self.current_line += 1
            self.line_no_entry.set_text(str(self.current_line))
        self.highlight()
        
    def line_no_entry_activate_cb(self, widget,  data = None):
        new_line_no = int(widget.get_text())
        if new_line_no < self.text_buffer.get_line_count()-1:
            self.current_line = int(widget.get_text())
            self.highlight()
        else:
            widget.set_text(str(self.text_buffer.get_line_count()-1))
    #
    #   GUI Callbacks
    ##########################################################################

    def highlight(self):
        # erase previous hightlights
        iter1 = self.text_buffer.get_start_iter()
        iter2 = self.text_buffer.get_end_iter()
        self.text_buffer.remove_all_tags(iter1, iter2)

        iter1 = self.text_buffer.get_iter_at_line(self.current_line)
        try:
            iter2 = self.text_buffer.get_iter_at_line(self.current_line+1)
            iter2.backward_char()
        except:
            iter2 = self.text_buffer.get_end_iter()
        # print self.hltag, iter1, iter2, self.hltag.get_property('background-gdk')
        self.highlighted_text= iter1.get_text(iter2)
        self.text_buffer.apply_tag(self.hltag, iter1, iter2)


    def run_file(self,filename):
        print "TextWindow.run_file(%s)"%filename

    def run_cmd(self,cmd):
        print "TextWindow.run_cmd(%s)"%cmd


    def get_lines(self, first_y, last_y, buffer_coords, numbers):
        text_view = self.text_view
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
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
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
                                       gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                       gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, 
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
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
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
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
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
        while gtk.events_pending(): gtk.main_iteration()

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

    def write_file(self, filename):

        # add Saving message to status bar and ensure GUI is current
        if filename: 
            self.statusbar.push(self.statusbar_cid, "Saving %s" % filename)
        else:
            self.statusbar.push(self.statusbar_cid, "Saving %s" % self.filename)

        while gtk.events_pending(): gtk.main_iteration()

        try:
            # disable text view while getting contents of buffer
            buff = self.text_view.get_buffer()
            self.text_view.set_sensitive(False)
            text = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
            self.text_view.set_sensitive(True)
            buff.set_modified(False)

            # set the contents of the file to the text from the buffer
            if filename: fout = open(filename, "w")
            else: fout = open(self.filename, "w")
            fout.write(text)
            fout.close()

            if filename: self.filename = filename

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

  

def main():
    window = TextWindowBase()
    window.show()
    gtk.main()
    
if __name__ == "__main__":
    main()
