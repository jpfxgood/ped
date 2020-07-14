# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a file browse dialog component for the  ped editor """
import curses
import curses.ascii
from ped_dialog import dialog
from ped_core import editor_common
from ped_core import keytab

class FileBrowseComponent(dialog.Component):
    """ component subclass for embedding a read-only editor in a dialog to do preview of files """
    def __init__(self, name, order, x, y, width, height, label, filename, showname = True ):
        """ name, order== tab order, x,y offset in dialog, width,height size in chars, label title for border, filename file to show in editor """
        dialog.Component.__init__(self, name, order )
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

    def __del__(self):
        """ clean up window, editor and workfile if we get deleted """
        self.reset()

    def reset(self):
        """ reset stuff """
        if self.ewin:
            del self.ewin
            self.ewin = None
        if self.editor:
            self.editor.getWorkfile().close()
            self.editor = None

    def setpos(self, x, y ):
        """ set the position """
        self.reset()
        dialog.Component.setpos(self, x, y)

    def setsize(self, height, width ):
        """ set the size """
        self.reset()
        dialog.Component.setsize(self, height, width )

    def mouse_event(self, ox, oy, mtype):
        """ handle mouse events return key value or -1 for not handled """
        if self.editor and (ox >= self.x and ox < self.x+self.width and oy >= self.y and oy <= self.y+self.height):
            oy = (oy - self.y) - 2
            ox = (ox - self.x) - 1
            if oy >= 0 and ox >= 0 and (mtype & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED)):
                self.editor.goto(self.editor.line+oy,self.editor.left+ox)
                return keytab.KEYTAB_CR

        return -1

    def render(self):
        """ draw the frame for the component and the editor as needed """
        win = self.getparent()
        if win:
            if self.isfocus:
                attr = curses.A_BOLD
            else:
                attr = curses.A_NORMAL

            dialog.rect(win,self.x,self.y,self.width,self.height,self.label,attr,False)

            if not self.ewin:
                self.ewin = win.subwin(self.height-2,self.width-2,self.y+1,self.x+1)

            if not self.editor and self.filename:
                self.editor = editor_common.ReadonlyEditor(win,self.ewin,self.filename, self.showname)
                self.editor.goto(self.start_line,0)
                self.editor.mark_lines()
                self.editor.invalidate_all()
                self.editor.main(False)

            if self.editor:
                self.editor.setfocus(self.isfocus)
                self.editor.redraw()
                win.refresh()

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
            o_line = self.editor.getLine()
            ret_ch = self.editor.main(False,ch)
            if self.editor.getLine() != o_line or not self.editor.isMark():
                if self.editor.isMark():
                    self.editor.mark_lines()
                self.editor.mark_lines()
        else:
            ret_ch = ch
        if ret_ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR,keytab.KEYTAB_TAB,keytab.KEYTAB_ESC,keytab.KEYTAB_BTAB]:
            return ret_ch
        else:
            return dialog.Component.CMP_KEY_NOP
