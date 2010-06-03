#! /usr/bin/env python


from robotviewer.displayserver import *
from robotviewer.openglaux import *
from robotviewer.camera import *
import sys

import pygtk
pygtk.require('2.0')
import gtk
import gtk.gtkgl

class RvWidget(DisplayServer, gtk.gtkgl.DrawingArea):
    """
    """
    
    def __init__(self):
        """
        """

        major, minor = gtk.gdkgl.query_version()
        print "GLX version = %d.%d" % (major, minor)

        #
        # frame buffer configuration
        #

        # use GLUT-style display mode bitmask
        try:
            # try double-buffered
            self.glconfig = gtk.gdkgl.Config(mode=(gtk.gdkgl.MODE_RGB    |
                                              gtk.gdkgl.MODE_DOUBLE |
                                              gtk.gdkgl.MODE_DEPTH))
        except gtk.gdkgl.NoMatches:
            # try single-buffered
            self.glconfig = gtk.gdkgl.Config(mode=(gtk.gdkgl.MODE_RGB    |
                                              gtk.gdkgl.MODE_DEPTH))

        # use GLX-style attribute list
        # try:
        #     # try double-buffered
        #     self.glconfig = gtk.gdkgl.Config(attrib_list=(gtk.gdkgl.RGBA,
        #                                              gtk.gdkgl.DOUBLEBUFFER,
        #                                              gtk.gdkgl.DEPTH_SIZE, 1))
        # except gtk.gdkgl.NoMatches:
        #     # try single-buffered
        #     self.glconfig = gtk.gdkgl.Config(attrib_list=(gtk.gdkgl.RGBA,
        #                                              gtk.gdkgl.DEPTH_SIZE, 1))

        print "self.glconfig.is_rgba() =",            self.glconfig.is_rgba()
        print "self.glconfig.is_double_buffered() =", self.glconfig.is_double_buffered()
        print "self.glconfig.has_depth_buffer() =",   self.glconfig.has_depth_buffer()

        # get_attrib()
        print "gtk.gdkgl.RGBA = %d"         % self.glconfig.get_attrib(gtk.gdkgl.RGBA)
        print "gtk.gdkgl.DOUBLEBUFFER = %d" % self.glconfig.get_attrib(gtk.gdkgl.DOUBLEBUFFER)
        print "gtk.gdkgl.DEPTH_SIZE = %d"   % self.glconfig.get_attrib(gtk.gdkgl.DEPTH_SIZE)
        gtk.gtkgl.DrawingArea.__init__(self, self.glconfig)
        self._camera = Camera()

        self.set_size_request(300, 300)
        
        self.connect('configure_event', self.reshape)
        self.connect('expose_event', self.DrawGLScene)

#        self.connect('map_event', map)


    def reshape(self, widget , event):
        # get GLContext and GLDrawable
        glcontext = self.get_gl_context()
        gldrawable = self.get_gl_drawable()

        # GL calls
        if not gldrawable.gl_begin(glcontext): return

        x, y, width, height = self.get_allocation()

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if width > height:
            w = float(width) / float(height)
            glFrustum(-w, w, -1.0, 1.0, 5.0, 60.0)
        else:
            h = float(height) / float(width)
            glFrustum(-1.0, 1.0, -h, h, 5.0, 60.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -40.0)

        gldrawable.gl_end()

        return True



    def initGL(self):
        return

        
    def finalInit(self):
        '''
        Final initialization, to be called when an GL context has been created
        '''
        if not ( IsExtensionSupported ("GL_ARB_vertex_buffer_object") and\
                     glInitVertexBufferObjectARB()   ):
            raise Exception('Help!  No VBO support')
        DisplayServer.__init__(self)
        return

    def DrawGLScene(self, widget ,event):
        glcontext = self.get_gl_context()
        gldrawable = self.get_gl_drawable()

        if not gldrawable.gl_begin(glcontext): 
            return

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
#        updateView(self._camera)


        for item in self._element_dict.items():
            ele = item[1]
#            print item[0], item[1]._enabled
            ele.render()
        
        if gldrawable.is_double_buffered():
            gldrawable.swap_buffers()
        else:
            glFlush()
    
        gldrawable.gl_end()

        return True
