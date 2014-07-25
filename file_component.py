# Copyright 2014 James P Goodwin ped tiny python editor
""" module to implement file editor dialog component  ped """
import curses
import curses.ascii
from dialog import Dialog, Component, ListBox, Button, Frame, Prompt, Toggle, rect
from editor_common import Editor
import keytab

# pull this out to make it easier to reuse it
class FileEditorComponent(Component):
    """ component subclass for embedding an editor in a dialog to do editing of files """
    def __init__(self, name, order, x, y, width, height, label, filename, showname = True, wrap = False ):
        """ name, order== tab order, x,y offset in dialog, width,height size in chars, label title for border, filename file to show in editor """
        Component.__init__(self, name, order )
        self.x = x
        self.y = y
        self.width = width
        self.height = height  
        self.ewin = None
        self.editor = None
        self.filename = filename
        self.start_line = 0
        self.label = label
        self.isfocus = None
        self.showname = showname
        self.wrap = wrap

    def __del__(self):  
        """ clean up window, editor and workfile if we get deleted """
        self.reset()
                                    
    def reset(self):
        """ reset things """
        if self.ewin:
            del self.ewin
            self.ewin = None
        if self.editor:
            self.editor.getWorkfile().close()
            self.editor = None  
        
    def setpos(self, x, y ):
        """ set the position """
        self.reset()
        Component.setpos(self, x, y)
        
    def setsize(self, height, width ):
        """ set the size """
        self.reset()
        Component.setsize(self, height, width )
    
    def render(self):
        """ draw the frame for the component and the editor as needed """
        win = self.getparent()
        if win:
            if not self.ewin:
                max_y,max_x = win.getmaxyx()
                min_y,min_x = win.getbegyx()
                try:
                    self.ewin = win.subwin(self.height-2,self.width-2,min_y+self.y+1,min_x+self.x+1)
                except:
                    raise Exception("Error creating FileEditorComponent window %d,%d,%d,%d,%d,%d,%d,%d"%(min_x,min_y,max_x,max_y,self.height-2,self.width-2,self.y+1,self.x+1))
                    
            if not self.editor and self.filename:
                self.editor = Editor(win,self.ewin,self.filename, None, self.showname, self.wrap)
                if self.start_line >= 0:
                    self.editor.goto(self.start_line,0)
                else:
                    self.editor.goto(self.editor.numLines(True)-1,0)
            if self.isfocus:
                attr = curses.A_BOLD
            else:
                attr = curses.A_NORMAL

            rect(win,self.x,self.y,self.width,self.height,self.label,attr)
            if self.editor:
                self.editor.redraw()
                self.editor.scr.leaveok(1)
                self.editor.scr.refresh()
                self.editor.scr.leaveok(0)
                
        self.isfocus = False

    def focus(self):
        """ indicates that we have the focus """
        self.isfocus = True

    def setvalue(self,value):
        """ this component doesn't really do setvalue """
        pass

    def getvalue(self):
        """ returns the current line in the editor """
        if self.editor:
            return self.editor.getCurrentLine()
        else:
            return ""

    def setfilename(self,filename,number):
        """ set a new file to view and a line number to scroll to, clean up the old one """
        self.filename = filename
        self.start_line = number
        if self.editor:
            self.editor.getWorkfile().close()
        del self.editor
        self.editor = None

    def handle(self,ch):
        """ translate the editor keys for component use """
        if self.editor:
            self.editor.scr.leaveok(0)
            self.editor.scr.move(self.editor.vpos+1,self.editor.pos)
            self.editor.scr.cursyncup()
            ret_ch = self.editor.main(False,ch)
        else:
            ret_ch = ch
        if ret_ch in [keytab.KEYTAB_ESC]:
            return ret_ch
        elif ret_ch in [ keytab.KEYTAB_ALTX, keytab.KEYTAB_ALTW, keytab.KEYTAB_ALTN ]:
            return keytab.KEYTAB_TAB
        elif ret_ch in [ keytab.KEYTAB_ALTP ]:
            return keytab.KEYTAB_BTAB
        
        return Component.CMP_KEY_NOP

def main(stdscr):
    max_y,max_x = stdscr.getmaxyx()
    editor = FileEditorComponent("TestFile",1,1,1,max_x-2,max_y-3,"Chat","./test.out",False)
    d = Dialog(stdscr,"TestDialog",max_y,max_x,[ Frame("Test Dialog"),
                                          editor,
                                          Button("Ok",2,2,max_y-2,"OK",Component.CMP_KEY_OK),
                                          Button("Cancel",3,9,max_y-2,"CANCEL",Component.CMP_KEY_CANCEL)])
    
    d.render()
#    curses.doupdate()
    
    ed = editor.editor
           
    
    ed.goto(ed.numLines(True)-1,0)
    ed.endln()
    ed.cr()
    target = editor.editor.getLine()
    ed.workfile.insertLine(target,"This is a test")
    ed.workfile.setReadOnly()
    
    d.main()
               

if __name__ == '__main__':
    curses.wrapper(main)
