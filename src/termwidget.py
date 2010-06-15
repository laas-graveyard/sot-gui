#! /usr/bin/env python

import gtk
import vte

class TermWidget(gtk.HBox):
    """
    """
    
    def __init__(self):
        """
        """
        def selected_cb(terminal, column, row, cb_data):
            if (row == 15):
		if (column < 40):
			return 1
            return 0

        def restore_cb(terminal):
            (text, attrs) = terminal.get_text(selected_cb, 1)
            print "A portion of the text at restore-time is:"
            print text

        def child_exited_cb(terminal):
            gtk.main_quit()


        gtk.HBox.__init__(self)

        child_pid = -1;
	# Defaults.
	audible = 0
	background = None
	blink = 0
	command = None
	font = "fixed 12"
	scrollback = 100
	transparent = 0
	visible = 0

	self.terminal = vte.Terminal()
	self.terminal.set_cursor_blinks(blink)
	self.terminal.set_emulation('xterm')
	self.terminal.set_font_from_string(font)
	self.terminal.set_scrollback_lines(scrollback)
	self.terminal.set_audible_bell(audible)
	self.terminal.set_visible_bell(visible)
	self.terminal.connect("child-exited", child_exited_cb)
	self.terminal.connect("restore-window", restore_cb)        
        child_pid = self.terminal.fork_command()

	self.terminal.show()

	scrollbar = gtk.VScrollbar()
	scrollbar.set_adjustment(self.terminal.get_adjustment())

	self.pack_start(self.terminal)
	self.pack_start(scrollbar)

        
