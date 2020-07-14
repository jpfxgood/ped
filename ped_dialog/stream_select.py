# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a select from a stream in a temp file in the ped editor """
import curses
import curses.ascii
import sys
import tempfile
from ped_dialog import dialog
from ped_core import editor_common
from ped_core import keytab


class StreamSelectComponent(dialog.Component):
    """ Component subclass that embeds a StreamEditor in a dialog used for selecting
    from very long lists stored in temp files """
    def __init__(self, name, order, x, y, width, height, label, stream, line_re = None, wait = True ):
        """ takes name, order is tab order, x, y are offset inside dialog, width,height are in characters,
        label is a title for the frame,and stream is a stream to select lines from """
        dialog.Component.__init__(self, name, order )
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.ewin = None
        self.editor = None
        self.stream = stream
        self.label = label
        self.isfocus = None
        self.line_re = line_re
        self.wait = wait

    def __del__(self):
        """ clean up the curses window when we get deleted  and any streams when we get deleted """
        if self.stream:
            self.stream.close()
            self.stream = None
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
        """ draw the frame and embedded editor if needed """
        win = self.getparent()
        if win:
            if self.isfocus:
                attr = curses.A_BOLD
            else:
                attr = curses.A_NORMAL

            dialog.rect(win,self.x,self.y,self.width,self.height,self.label,attr,False)

            if not self.ewin:
                self.ewin = win.subwin(self.height-2,self.width-2,self.y+1,self.x+1)

            if not self.editor:
                self.editor = editor_common.StreamEditor(win,self.ewin,self.name,self.stream,select=True,line_re = self.line_re,wait=self.wait)
                self.editor.invalidate_all()
                self.editor.main(False)

            self.editor.setfocus(self.isfocus)
            self.editor.redraw()

        self.isfocus = False

    def focus(self):
        """ called when we have the focus """
        self.isfocus = True

    def setvalue(self,value):
        """ setvalue for this component is a no op, maybe a goto in the future """
        pass

    def getvalue(self):
        """ our value is always the current line in the embedded editor """
        if self.editor:
            return self.editor.getCurrentLine()
        else:
            return ""

    def setstream(self,stream):
        """ special for this component, allow the stream to be set """
        if self.stream:
            self.stream.close()
        self.stream = stream
        if self.editor:
            self.editor.getWorkfile().close()
        self.editor = None

    def handle(self,ch):
        """ handle characters, delegate to the embedded editor, translate for dialog """
        if self.editor:
            ret_ch = self.editor.main(False,ch)
        else:
            ret_ch = ch
        if ret_ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR,keytab.KEYTAB_TAB,keytab.KEYTAB_ESC,keytab.KEYTAB_BTAB]:
            return ret_ch
        else:
            return dialog.Component.CMP_KEY_NOP
