#! /usr/bin/env python


from robotviewer.displayserver import *
from robotviewer.openglaux import *
from robotviewer.camera import *
import sys

import gobject
import pygtk
pygtk.require('2.0')
import gtk
import gtk.gtkgl
import corba_wrapper

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
        self.set_size_request(300, 300)

        self._camera = Camera()
        self.connect('configure_event', self.reshape)
        self.connect('expose_event', self.DrawGLScene)

        def idle(widget):
            # Invalidate whole window.
            while True:
                try:
                    pos = corba_wrapper.get_HRP_pos()
                    wst = corba_wrapper.get_wst()
                    break
                except:                    
                    messagedialog = gtk.MessageDialog\
                    (self.get_toplevel(), 0, gtk.MESSAGE_ERROR, gtk.BUTTONS_YES_NO,\
                         "Corba failed. Retry?")

                    response = messagedialog.run()
                    messagedialog.destroy()

                    if response == gtk.RESPONSE_YES:
                        reload(corba_wrapper)
                    elif response == gtk.RESPONSE_NO:
                        sys.exit(1)
            if len(wst) == 6:                
                for i in range(len(wst)):
                    pos[i] = wst[i]                
                pos[2] += 0.105
                self.updateElementConfig('hrp',pos)  

            else:
                print "Warning! wrong dimension of waist_pos, robot not updated"

            widget.window.invalidate_rect(widget.allocation, False)
            # Update window synchronously (fast).
            widget.window.process_updates(False)
            return True


        def map(widget, event):
            gobject.idle_add(idle, self)
            return True

        self.connect('map_event', map)

 

    def reshape(self, widget , event):
        # get GLContext and GLDrawable
        glcontext = self.get_gl_context()
        gldrawable = self.get_gl_drawable()

        # GL calls
        if not gldrawable.gl_begin(glcontext): return

        x, y, width, height = self.get_allocation()
        updateView(self._camera)

        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if width > height:
             w = float(width) / float(height)
             glFrustum(-w, w, -1.0, 1.0, 2, 10.0)
        else:
             h = float(height) / float(width)
             glFrustum(-1.0, 1.0, -h, h, 2, 10.0)

        # # field of view, aspect ratio, near and far
        # This will squash and stretch our objects as the window is resized.
        # gluPerspective(45.0, float(width)/float(height), 1, 1000.0)    
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        gldrawable.gl_end()

        return True

    def initGL(self):
        return

    def setLight(self):
        
        # Setup GL States
        glClearColor (0.0, 0.0, 0.0, 0.5);
        # # Black Background
        glClearDepth (1.0);	
        # # Depth Buffer Setup
        glDepthFunc (GL_LEQUAL);
        # # The Type Of Depth Testing
        glEnable (GL_DEPTH_TEST);
        # # Enable Depth Testing
        glShadeModel (GL_SMOOTH);
        # # Select Smooth Shading
        glHint (GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST);	
        # # Set Perspective Calculations To Most Accurate
        glEnable(GL_TEXTURE_2D);	
        # # Enable Texture Mapping
        glColor4f (1.0, 6.0, 6.0, 1.0)
    
        glClearColor(0.,0.,0.,1.)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
    
        lightZeroPosition = [-3.0,3.0,3.0,1.0]
        lightZeroColor = [1.0,1.0,1.0,1.0] #green tinged
        glLightfv(GL_LIGHT0, GL_POSITION, lightZeroPosition)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, lightZeroColor)

        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.0)
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.0)
        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.03)

        glEnable(GL_LIGHT0)

    def finalInit(self):
        '''
        Final initialization, to be called when an GL context has been created
        '''
        if not ( IsExtensionSupported ("GL_ARB_vertex_buffer_object") and\
                     glInitVertexBufferObjectARB()   ):
            raise Exception('Help!  No VBO support')
        DisplayServer.__init__(self)
        self.setLight()
        self.connect('configure_event', self.reshape)
        self.connect('expose_event', self.DrawGLScene)

        return

    def DrawGLScene(self, widget ,event):
        glcontext = self.get_gl_context()
        gldrawable = self.get_gl_drawable()

        if not gldrawable.gl_begin(glcontext): 
            return

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        updateView(self._camera)
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
