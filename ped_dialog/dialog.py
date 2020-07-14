# Copyright 2009 James P Goodwin ped tiny python editor
""" Dialog and UI Component module for the ped editor """
import curses
import curses.ascii
import sys
import os
from ped_core import clipboard
from ped_core import cmd_names
from ped_core import keytab
from ped_core import keymap
from ped_core import extension_manager

# utility functions
def distribute( buttons, xstart, width ):
    """ distribute a bunch of buttons across a given width """
    width_per_button = width // len(buttons)
    x = xstart + (width_per_button//2)
    for b in buttons:
        b.x = x - (b.width//2)
        x += width_per_button


def pad(value,size):
    """ pad a string with spaces to the size provided """
    if len(value) < size:
        value += ' '*(size-len(value))
    return value

def rect( win, x,y,w,h,label,attr,fill=True ):
    """ draw a rectangle in the curses window provided at the offset
    x,y with a w,h width and height, if label is non-empty center it in
    the top border, if fill is true, fill the rectangle with spaces """
    win.addch(y,x,curses.ACS_ULCORNER,attr)
    off = 1
    while off < w-1:
        win.addch(y,x+off,curses.ACS_HLINE,attr)
        off += 1
    win.addch(y,x+(w-1),curses.ACS_URCORNER,attr)
    if label:
        win.addstr(y,x+(w//2)-(len(label)//2),label,attr)
    y += 1
    bh = h-2
    while bh:
        try:
            win.addch(y,x,curses.ACS_VLINE,attr)
        except:
            pass
        if fill:
            off = 1
            while off < w-1:
                try:
                    win.addch(y,x+off,' ',attr)
                except:
                    pass
                off += 1
        try:
            win.addch(y,x+(w-1),curses.ACS_VLINE,attr)
        except:
            pass
        bh -= 1
        y += 1
    try:
        win.addch(y,x,curses.ACS_LLCORNER,attr)
    except:
        pass
    off = 1
    while off < w-1:
        try:
            win.addch(y,x+off,curses.ACS_HLINE,attr)
        except:
            pass
        off += 1
    try:
        win.addch(y,x+(w-1),curses.ACS_LRCORNER,attr)
    except:
        pass

class Component:
    """ base class for UI components defines the standard interface, not useable by itself """
    CMP_KEY_CANCEL = keytab.KEYTAB_DLGCANCEL             # user has canceled the dialog
    CMP_KEY_OK = keytab.KEYTAB_DLGOK                  # user has accepted the dialog
    CMP_KEY_NOP = keytab.KEYTAB_DLGNOP                  # the most recent key requires no action

    def __init__(self, name, order ):
        """ all components have a name and a tab order, order == -1 means exclude from tab """
        self.name = name
        self.order = order
        self.parent = None

    def render(self):
        """ render the component use parent as target """
        pass

    def focus(self):
        """ called when component is the focus """
        pass

    def isempty(self):
        """ test if the component entry is empty """
        return False

    def setvalue(self,value):
        """ set the components value, may be tuple or other data structure """
        pass

    def getvalue(self):
        """ return the current value of the component """
        return None

    def handle(self, ch ):
        """ handle keystrokes for this component """
        pass

    def mouse_event(self, ox, oy, mtype):
        """ handle mouse events return key value or -1 for not handled """
        return -1

    def getorder(self):
        """ get this component's tab order number """
        return self.order

    def getparent(self):
        """ get this component's curses target window """
        return self.parent

    def setparent(self,parent):
        """ set the parent curses target window """
        self.parent = parent

    def getname(self):
        """ get the name of this component """
        return self.name

    def setpos(self, x, y ):
        """ set the position of this component """
        self.x = x
        self.y = y

    def setsize(self, height, width ):
        """ set the width of this component """
        self.height = height
        self.width = width

class Frame(Component):
    """ frame component for surrounding dialog with a border """
    def __init__(self, title, x = -1 , y = -1, w = -1, h = -1 ):
        """ takes title for frame not on tab order """
        Component.__init__(self,None,-1)
        self.title = title
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def render(self):
        """ frame renders itself as a rectangle with title around window """
        win = self.getparent()
        if win:
            if self.x >= 0:
                x = self.x
                y = self.y
                my = self.h
                mx = self.w
            else:
                x = 0
                y = 0
                my,mx = win.getmaxyx()

            rect(win, x, y, mx, my, self.title, curses.A_NORMAL, False)
            if self.title:
                win.addstr(y,x+(mx//2)-(len(self.title)//2),self.title)


class ListBox(Component):
    def __init__(self, name, order, x, y, height, width, label, selection = 0, lst = []):
        Component.__init__(self,name,order)
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.label = label
        self.selection = selection
        self.search = ""
        self.top = selection
        if self.top < 0:
            self.top = 0
        self.list = lst
        self.isfocus = False

    def render(self):
        win = self.getparent()
        if win:
            if self.isfocus:
                lattr = curses.A_BOLD
            else:
                lattr = curses.A_NORMAL
            x = self.x
            y = self.y
            width = self.width
            height = self.height
            rect(win,x,y,width,height,self.label,lattr)

            x+=1
            y+=1
            width -=2
            height -=2

            top = self.top
            off = 0
            cy = -1
            while top < len(self.list) and off < height:
                if top == self.selection:
                    rattr = curses.A_REVERSE
                    cy = y+off
                else:
                    if self.isfocus:
                        rattr = curses.A_BOLD
                    else:
                        rattr = curses.A_NORMAL
                win.addstr(y+off,x,pad(self.list[top],width)[0:width],rattr)
                top += 1
                off += 1

            if self.isfocus and cy > 0:
                win.move(cy,x)

            self.isfocus = False

    def focus(self):
        self.isfocus = True

    def setvalue(self,value):
        self.selection = value[0]
        self.list = value[1]
        if self.selection < self.top:
            self.top = self.selection
        if self.selection > self.top+(self.height-3):
            self.top = self.selection-(self.height-3)

    def getvalue(self):
        return (self.selection,self.list)

    def cpgdn(self):
        if len(self.list):
            self.selection += (self.height-2)
            if self.selection >= len(self.list):
               self.selection = len(self.list)-1
            if self.selection < self.top:
                self.top = self.selection
            if self.selection > self.top+(self.height-3):
                self.top = self.selection-(self.height-3)

    def cpgup(self):
        if len(self.list):
            self.selection -= (self.height-2)
            if self.selection < 0:
                self.selection = 0
            if self.selection < self.top:
                self.top = self.selection
            if self.selection > self.top+(self.height-3):
                self.top = self.selection-(self.height-3)

    def cup(self):
        if len(self.list):
            self.selection -= 1
            if self.selection < 0:
                self.selection = 0
            if self.selection < self.top:
                self.top = self.selection
            if self.selection > self.top+(self.height-3):
                self.top = self.selection-(self.height-3)

    def cdown(self):
        if len(self.list):
            self.selection += 1
            if self.selection >= len(self.list):
                self.selection = len(self.list)-1
            if self.selection < self.top:
                self.top = self.selection
            if self.selection > self.top+(self.height-3):
                self.top = self.selection-(self.height-3)

    def home(self):
        if len(self.list):
            self.selection = 0
            self.top = 0

    def end(self):
        if len(self.list):
            self.selection = len(self.list)-1
            self.top = self.selection-(self.height-3)
            if self.top < 0:
                self.top = 0

    def find(self, searchfor ):
        found = False
        if len(self.list):
            idx = self.selection
            while idx < len(self.list):
                if self.list[idx].startswith(searchfor):
                    self.selection = idx
                    found = True
                    break
                idx += 1
            if self.selection < self.top:
                self.top = self.selection
            if self.selection > self.top+(self.height-3):
                self.top = self.selection-(self.height-3)
        return found

    def mouse_event(self, ox, oy, mtype):
        if ox >= self.x and ox < self.x+self.width and oy >= self.y and oy <= self.y+self.height:
            oy = (oy - self.y) - 1
            if oy >= 0:
                if mtype & curses.BUTTON1_CLICKED:
                    if self.top+oy < len(self.list):
                        self.selection = self.top+oy
                        return keytab.KEYTAB_CR
        return -1

    def handle(self,ch):
        if len(ch) == 1 and curses.ascii.isprint(ord(ch[0])):
            self.search += ch
            self.find(self.search)
        elif ch == keytab.KEYTAB_BACKSPACE:
            if self.search:
                self.search = self.search[0:-1]
                self.find(self.search)
        elif ch == keytab.KEYTAB_F03:
            if self.search:
                self.cdown()
                if not self.find(self.search):
                    self.cup()
        elif ch == keytab.KEYTAB_LEFT or ch == keytab.KEYTAB_UP:
            self.cup()
        elif ch == keytab.KEYTAB_RIGHT or ch == keytab.KEYTAB_DOWN:
            self.cdown()
        elif ch == keytab.KEYTAB_HOME:
            self.home()
        elif ch == keytab.KEYTAB_END:
            self.end()
        elif ch == keytab.KEYTAB_PAGEUP:
            self.cpgup()
        elif ch == keytab.KEYTAB_PAGEDOWN:
            self.cpgdn()
        elif ch == keytab.KEYTAB_RESIZE:
            return ch
        elif ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR,keytab.KEYTAB_TAB,keytab.KEYTAB_ESC,keytab.KEYTAB_BTAB]:
            self.search = ""
            return ch
        return Component.CMP_KEY_NOP

class Toggle(Component):
    def __init__(self, name, order, x, y, width, selection = 0, lst = []):
        Component.__init__(self,name,order)
        self.x = x
        self.y = y
        self.width = width
        self.selection = selection
        self.list = lst
        self.isfocus = False

    def render(self):
        win = self.getparent()
        if win:
            if self.isfocus:
                lattr = curses.A_REVERSE
            else:
                lattr = curses.A_NORMAL
            x = self.x
            y = self.y
            width = self.width
            win.addstr(y,x,pad(self.list[self.selection],width)[0:width],lattr)
            if self.isfocus:
                win.move(y,x)
            self.isfocus = False

    def focus(self):
        self.isfocus = True

    def setvalue(self,value):
        self.selection = value[0]
        self.list = value[1]

    def getvalue(self):
        return (self.selection,self.list)

    def cup(self):
        if len(self.list):
            self.selection -= 1
            if self.selection < 0:
                self.selection = len(self.list)-1

    def cdown(self):
        if len(self.list):
            self.selection += 1
            if self.selection >= len(self.list):
                self.selection = 0

    def home(self):
        if len(self.list):
            self.selection = 0

    def end(self):
        if len(self.list):
            self.selection = len(self.list)-1

    def mouse_event(self, ox, oy, mtype):
        if ox >= self.x and ox < self.x+self.width and oy == self.y:
            if mtype & curses.BUTTON1_CLICKED:
                self.cdown()
                return Component.CMP_KEY_NOP
        return -1

    def handle(self,ch):
        if ch == keytab.KEYTAB_LEFT or ch == keytab.KEYTAB_UP:
            self.cup()
        elif ch == keytab.KEYTAB_SPACE or ch == keytab.KEYTAB_RIGHT or ch == keytab.KEYTAB_DOWN:
            self.cdown()
        elif ch == keytab.KEYTAB_HOME:
            self.home()
        elif ch == keytab.KEYTAB_END:
            self.end()
        elif ch == keytab.KEYTAB_RESIZE:
            return ch
        elif ch in [keytab.KEYTAB_CR,keytab.KEYTAB_TAB,keytab.KEYTAB_ESC,keytab.KEYTAB_BTAB]:
            return ch

        return Component.CMP_KEY_NOP

class Button(Component):
    def __init__(self, name, order, x, y, label, key ):
        Component.__init__(self,name,order)
        self.x = x
        self.y = y
        self.label = label
        self.width = len(label)+2
        self.key = key
        self.isfocus = False
        self.value = False

    def render(self):
        win = self.getparent()
        if self.isfocus:
            battr = curses.A_REVERSE
        else:
            battr = curses.A_NORMAL

        if win:
            win.addstr(self.y,self.x,"["+self.label+"]",battr)
            if self.isfocus:
                win.move(self.y,self.x+(len(self.label)+2)//2)

        self.isfocus = False

    def focus(self):
        self.isfocus = True

    def setvalue(self,value):
        if value:
            self.value = True
        else:
            self.value = False

    def getvalue(self):
        return self.value

    def mouse_event(self, ox, oy, mtype):
        if ox >= self.x and ox < self.x+self.width and oy == self.y:
            if mtype & curses.BUTTON1_CLICKED:
                self.setvalue(True)
                return self.key
        return -1

    def handle(self,ch):
        if ch == keytab.KEYTAB_SPACE:
            self.setvalue(True)
            return self.key
        elif ch == keytab.KEYTAB_CR:
            self.setvalue(True)
            return self.key
        elif ch == keytab.KEYTAB_RESIZE:
            return ch
        elif ch in [keytab.KEYTAB_CR,keytab.KEYTAB_TAB,keytab.KEYTAB_ESC,keytab.KEYTAB_BTAB]:
            return ch
        return Component.CMP_KEY_NOP

class StaticText(Component):
    def __init__(self, name, x, y, prompt, width, value= "" ):
        Component.__init__(self,name,-1)
        self.x = x
        self.y = y
        self.prompt = prompt
        self.width = width
        self.value = value

    def setvalue(self,value):
        self.value = value

    def getvalue(self):
        return self.value

    def render(self):
        win = self.getparent()

        if win:
            try:
                max_y,max_x = win.getmaxyx()
                width = (max_x - self.x) - 1
                x = self.x
                win.addstr(self.y,x,self.prompt[-width:],curses.A_NORMAL)
                x += len(self.prompt[-width:])
                width -= len(self.prompt[-width:])
                if width > 0:
                    win.addstr(self.y,x,pad(self.value,self.width)[-width:],curses.A_NORMAL)
            except Exception as e:
                raise Exception("%d,%d,%d,%s,%s"%(x,self.y,width,self.prompt,str(e)))

class Prompt(Component):

    def __init__(self, name, order, x, y, prompt, width, value= "" ):
        Component.__init__(self,name,order)
        self.x = x
        self.y = y
        self.prompt = prompt
        self.width = width
        self.value = value
        self.pos = 0
        self.left = 0
        self.isfocus = False
                            
    def setvalue( self, value ):
        self.pos = 0
        self.left = 0
        Component.setvalue(self,value)
        
    def render(self):
        win = self.getparent()
        if self.isfocus:
            pattr = curses.A_BOLD
            fattr = curses.A_REVERSE
        else:
            pattr = curses.A_NORMAL
            fattr = curses.A_NORMAL

        if win:
            if self.width < 0:
                (max_y,max_x) = win.getmaxyx()
                self.width = max_x - (self.x+len(self.prompt)+2)

            win.addstr(self.y,self.x,self.prompt,pattr)
            if not self.isfocus:
                self.left = 0
                self.pos = 0
            win.addstr(self.y,self.x+len(self.prompt),pad(self.value[self.left:self.left+self.width],self.width),fattr)
            if self.isfocus:
                win.move(self.y,self.x+len(self.prompt)+(self.pos-self.left))

        self.isfocus = False

    def isempty(self):
        return (len(self.value.strip()) == 0)

    def focus(self):
        self.isfocus = True

    def setvalue(self,value):
        self.value = value

    def getvalue(self):
        return self.value

    def cleft(self):
        self.pos -= 1
        if self.pos < 0:
            self.pos = 0
        if self.pos < self.left:
            self.left = self.pos

    def cright(self,offset = 1):
        self.pos += offset
        if self.pos > self.width-1:
            self.left = self.pos - (self.width-1)

    def home(self):
        self.pos = 0
        self.left = 0

    def end(self):
        self.pos = len(self.value)
        self.left = self.pos - (self.width-1)

    def delc(self):
        if self.pos < len(self.value):
            self.value = self.value[0:self.pos]+self.value[self.pos+1:]

    def backspace(self):
        self.cleft()
        self.delc()

    def mouse_event(self, ox, oy, mtype):
        if ox >= self.x and ox < self.x+self.width and oy == self.y:
            if mtype & curses.BUTTON1_CLICKED:
                return Component.CMP_KEY_NOP
        return -1

    def insert(self,ch):
        if self.pos > len(self.value):
            self.value = self.value + ' '*(self.pos-len(self.value)) + ch
        else:
            self.value = self.value[0:self.pos]+ch+self.value[self.pos:]
        self.cright(len(ch))

    def handle(self,ch):
        if len(ch) == 1 and curses.ascii.isprint(ord(ch[0])):
            self.insert(ch[0])
        elif ch == keytab.KEYTAB_LEFT:
            self.cleft()
        elif ch == keytab.KEYTAB_RIGHT:
            self.cright()
        elif ch == keytab.KEYTAB_DELC:
            self.delc()
        elif ch == keytab.KEYTAB_BACKSPACE:
            self.backspace()
        elif ch == keytab.KEYTAB_HOME:
            self.home()
        elif ch == keytab.KEYTAB_END:
            self.end()
        elif ch == keytab.KEYTAB_DOWN:
            self.value = ""
            self.pos = 0
            self.left = 0
        elif ch == keytab.KEYTAB_RESIZE:
            return ch
        elif ch == keytab.KEYTAB_CTRLV or ch == keytab.KEYTAB_INSERT:
            if clipboard.clip_type:
                for clip in clipboard.clip:
                    for ichar in clip:
                        self.insert(ichar)
        elif ch == keytab.KEYTAB_CTRLC:
            if self.value:
                clipboard.clip_type = editor_common.Editor.SPAN_CLIP
                clipboard.clip = [ self.value ]
        elif ch in [keytab.KEYTAB_CR,keytab.KEYTAB_TAB,keytab.KEYTAB_ESC,keytab.KEYTAB_BTAB,keytab.KEYTAB_UP]:
            return ch

        return Component.CMP_KEY_NOP

class PasswordPrompt(Prompt):
    def __init__(self, name, order, x, y, prompt, width, value=""):
        Prompt.__init__(self, name, order, x, y, prompt, width, value)

    def render(self):
        win = self.getparent()
        if self.isfocus:
            pattr = curses.A_BOLD
            fattr = curses.A_REVERSE
        else:
            pattr = curses.A_NORMAL
            fattr = curses.A_NORMAL

        if win:
            if self.width < 0:
                (max_y,max_x) = win.getmaxyx()
                self.width = max_x - (self.x+len(self.prompt)+2)

            win.addstr(self.y,self.x,self.prompt,pattr)
            win.addstr(self.y,self.x+len(self.prompt),pad(len(self.value)*"*",self.width),fattr)
            if self.isfocus:
                win.move(self.y,self.x+len(self.prompt)+self.pos)

        self.isfocus = False

class Dialog(Component):
    history = {}

    def __init__(self, parent, name, height, width, children, y = -1, x = -1 ):
        Component.__init__(self,name,0)
        self.height = height
        self.width = width
        self.children = children
        max_y,max_x = parent.getmaxyx()
        curses.raw()
        if x < 0:
            self.win = parent.subwin(height,width,(max_y//2)-(height//2),(max_x//2)-(width//2))
        else:
            self.win = parent.subwin(height,width,y,x)

        self.win.clear()
        self.win.keypad(1)
        curses.meta(1)
        self.max_y,self.max_x = self.win.getmaxyx()
        self.setparent(parent)
        for c in self.children:
            c.setparent(self.win)
        self.current = 0
        self.focus_list = []
        self.hist_idx = 0
        self.enable_history = True
        self.focus()

    def __del__(self):
        if hasattr(self,"win") and self.win:
            del self.win
            self.win = None

    def set_history( self, state ):
        self.enable_history = state

    def push_history( self, child ):
        if not self.enable_history:
            return
        if not issubclass(child.__class__, Prompt):
            return
        if self.getname() and child.getname() and child.getorder() >= 0 and not child.isempty():
            key = (self.getname(), child.getname())
            if key in Dialog.history:
                if Dialog.history[key][-1] != child.getvalue():
                    Dialog.history[key].append(child.getvalue())
            else:
                Dialog.history[key] = [child.getvalue()]

    def pop_history( self, child ):
        if not self.enable_history:
            return
        if not issubclass(child.__class__, Prompt):
            return
        if self.getname() and child.getname() and child.getorder() >= 0:
            key = (self.getname(), child.getname())
            if key in Dialog.history:
                hist = Dialog.history[key]
                self.hist_idx += 1
                if self.hist_idx > len(hist):
                    self.hist_idx = 0
                child.setvalue(hist[-self.hist_idx])

    def render(self):
        self.win.leaveok(1)
        for c in self.children:
            if not self.focus_list or self.focus_list[self.current][1] != c:
                c.render()
        self.win.leaveok(0)
        if self.focus_list:
            self.focus_list[self.current][1].focus()
            self.focus_list[self.current][1].render()
        self.win.refresh()

    def focus(self):
        self.focus_list = []
        for c in self.children:
            self.pop_history(c)
            if c.getorder() > 0:
                self.focus_list.append((c.getorder(),c))

        if not self.focus_list:
            self.current = 0
            return

        self.focus_list.sort(key=lambda x: x[0])
        self.current = 0

    def setvalue(self, value):
        for c in self.children:
            if c.getname() in value:
                c.setvalue(value[c.getname()])

    def getvalue(self):
        value = {}
        for c in self.children:
            if c.getname():
                value[c.getname()] = c.getvalue()
        return value

    def tab(self):
        if self.focus_list:
            self.push_history(self.focus_list[self.current][1])
            self.current += 1
            if self.current >= len(self.focus_list):
                self.current = 0

    def btab(self):
        if self.focus_list:
            self.push_history(self.focus_list[self.current][1])
            self.current -= 1
            if self.current < 0:
                self.current = len(self.focus_list)-1

    def goto(self, component):
        """ move focus to this component """
        for i in range(0,len(self.focus_list)):
            if self.focus_list[i][1] == component:
                self.current = i
                return True
        return False

    def handle_mouse(self):
        if self.focus_list and self.win:
            try:
                mid, mx, my, mz, mtype = curses.getmouse()
                by,bx = self.win.getbegyx()
                oy = my - by
                ox = mx - bx

                for i in range(0,len(self.focus_list)):
                    c = self.focus_list[i][1]
                    ret = c.mouse_event(ox,oy,mtype)
                    if ret >= 0:
                        self.current = i
                        return ret
                else:
                    return -1
            except:
                return -1

    def handle(self, ch):
        if self.focus_list and ch != keytab.KEYTAB_MOUSE:
            ch = self.focus_list[self.current][1].handle(ch)

        cmd_id,ch = keymap.mapseq( keymap.keymap_dialog, ch)

        if extension_manager.is_extension(cmd_id):
            if not extension_manager.invoke_extension( cmd_id, self, ch ):
                return ch

        if cmd_id == cmd_names.CMD_DLGNEXT:
            self.tab()
        elif cmd_id == cmd_names.CMD_DLGPREV:
            self.btab()
        elif cmd_id == cmd_names.CMD_DLGUP:
            if self.focus_list:
                self.pop_history(self.focus_list[self.current][1])
            ch = Component.CMP_KEY_NOP
        elif cmd_id == cmd_names.CMD_DLGMOUSE:
            ret = self.handle_mouse()
            if ret >= 0:
                ch = ret
        elif cmd_id == cmd_names.CMD_DLGRESIZE:
            self.resize()

        return ch

    def resize(self):
        pass

    def main(self,blocking = True,force=False,ch_in = None):
        curses.mousemask( curses.BUTTON1_PRESSED| curses.BUTTON1_RELEASED| curses.BUTTON1_CLICKED)
        self.win.nodelay(1)
        self.win.notimeout(0)
        self.win.timeout(0)
        old_cursor = curses.curs_set(1)
        while (1):
            if (not keymap.keypending(self.win)) or force:
                self.render()
            if not ch_in:
                ch = self.handle(keymap.get_keyseq(self.win,keymap.getch(self.win)))
            else:
                ch = self.handle(ch_in)

            if blocking:
                if ch == Component.CMP_KEY_CANCEL:
                    curses.curs_set(old_cursor)
                    return {}
                elif ch == Component.CMP_KEY_OK:
                    curses.curs_set(old_cursor)
                    return self.getvalue()
            else:
                if ch == Component.CMP_KEY_CANCEL:
                    curses.curs_set(old_cursor)
                    return (ch, {})
                else:
                    curses.curs_set(old_cursor)
                    return (ch, self.getvalue())

def main(stdscr):
    d = Dialog(stdscr,"TestDialog",20,40,[ Frame("Test Dialog"),
                                          ListBox("List",1,2,2,7,20,"Select",0,["item 1","another item","third item","four","five","six","seven","eight","nine","ten"]),
                                          StaticText("Text",2,10,"Static: ",10,"A string that is longer"),
                                          Prompt("TestPrompt",2,2,15,"Enter something: ",10),
                                          Button("Ok",3,2,16,"OK",Component.CMP_KEY_OK),
                                          Button("Cancel",4,9,16,"CANCEL",Component.CMP_KEY_CANCEL)])
    d.main()


if __name__ == '__main__':
    curses.wrapper(main)
