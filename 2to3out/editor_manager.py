# Copyright 2009 James P Goodwin ped tiny python editor
import sys
import file_dialog
import time
from confirm_dialog import confirm
from prompt_dialog import prompt
from dialog import rect
from message_dialog import message
import editor_common
import curses
import os
import subprocess
import copy
import io
import ped_help
import file_find
import traceback
import buffer_dialog
from svn_browse import browsesvn, get_file_revision
from ssh_dialog import sftpDialog
import news_browse
import keytab
import cmd_names
import keymap
import extension_manager     

#def debug_print(*argv):
#    f = open(os.path.expanduser("~/ped.log"),"a")
#    print(" ".join([str(f) for f in argv]),file=f)
#    f.close()

class BaseFrame:
    """ Each frame keeps track of a subwindow """
    def __init__(self,parent,x,y,height,width,lborder = False):
        """ parent is the curses window we're embedded in, x,y are our upper left coordinate, height,width are the size in characters """
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.parent = parent
        self.win = parent.subwin(height,width,y,x)
        self.changed = True
        self.lborder = lborder

    def __lt__(self, other):
        if self.y == other.y:
            return self.x < other.x
        else:
            return self.y < other.y
        
    def __gt__(self, other):
        if self.y == other.y:
            return self.x > other.x
        else:
            return self.y > other.y
        
    def __eq__(self, other):
        return (self.y == other.y) and (self.x == other.x)
        
    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)
        
    def __ne__(self, other):
        return not self.__eq__(other)

    def __del__(self):
        """ clean up our subwindow when we close """
        if self.win:
            del self.win
            self.win = None

    def redraw(self,force=True):
        """ redraw the frame updating the frame and the embedded editor as needed, force == True causes full redraw """
        if self.changed or force:
            if self.lborder:
                off = 0
                while off < self.height:
                    self.parent.addch(self.y+off,self.x-1,curses.ACS_VLINE,curses.A_NORMAL)
                    off += 1
            self.changed = False
            

    def setlborder( self, flag ):
        """ our frames only have an optional left border to conserve screen space, this turns on/off the left border which is drawn at x-1 """
        self.lborder = flag

    def getrect(self, adjust = False):
        """ get a rect as (x,y,width,height) optionally adjusted to include the left border if present and adjust == True """
        if adjust and self.lborder:
            return (self.x-1,self.y,self.width+1,self.height)
        else:
            return (self.x,self.y,self.width,self.height)


    def resize(self,x,y,width,height):
        """ resizes the window, and adjusts the size of the embedded editor """
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.win = self.parent.subwin(height,width,y,x)
        if self.x == 0:
            self.lborder = False
        self.changed = True

class EditorFrame ( BaseFrame ):
    """ Each frame keeps track of an editor instance in a subwindow """
    def __init__(self,parent,x,y,height,width, lborder = False):
        """ parent is the curses window we're embedded in, x,y are our upper left coordinate, height,width are the size in characters """
        BaseFrame.__init__( self, parent,x,y,height,width,lborder )
        self.editor = None
        self.chgseq = -1
        
    def __del__(self):
        """ clean up our subwindow when we close """
        BaseFrame.__del__(self)
        self.editor = None
        
    def __copy__(self):
        """ copy of editor frame """
        return EditorFrame( self.parent, self.x, self.y, self.height, self.width, self.lborder )

    def redraw(self,force=True):
        """ redraw the frame updating the frame and the embedded editor as needed, force == True causes full redraw """
        BaseFrame.redraw( self, force )
        if self.editor:
            self.editor.setWin(self.win)
            modRef = self.editor.getModref()
            if modRef > self.chgseq or force:
                if force:
                    self.editor.flushChanges()
                self.editor.redraw()
                self.win.leaveok(1)
                self.win.refresh()
                self.win.leaveok(0)
                self.chgseq = modRef

    def resize(self,x,y,width,height):
        """ resizes the window, and adjusts the size of the embedded editor """
        BaseFrame.resize(self,x,y,width,height)
        if self.editor:
            self.editor.setWin(self.win)
            self.editor.resize()

    def seteditor(self,editor):
        """ installs a new editor into this frame, we copy it each time so we get independent scrolling """
        self.editor = copy.copy(editor)
        self.changed = True
        self.chgseq = -1

class DialogFrame ( BaseFrame ):
    """ Each frame keeps track of an editor instance in a subwindow """
    def __init__(self,parent,x,y,height,width,lborder=False):
        """ parent is the curses window we're embedded in, x,y are our upper left coordinate, height,width are the size in characters """
        BaseFrame.__init__( self, parent,x,y,height,width, lborder )
        self.dialog = None
        self.chgseq = -1
        
    def __del__(self):
        """ clean up our subwindow when we close """
        BaseFrame.__del__(self)
        self.dialog = None
        
    def __copy__(self):
        """ copy of dialog frame """
        return DialogFrame( self.parent, self.x, self.y, self.height, self.width, self.lborder )

    def redraw(self,force=True):
        """ redraw the frame updating the frame and the embedded editor as needed, force == True causes full redraw """
        BaseFrame.redraw( self, force )
        if self.dialog:
            self.dialog.setparent(self.win)
            self.dialog.render()
            self.win.leaveok(1)
            self.win.refresh()
            self.win.leaveok(0)

    def resize(self,x,y,width,height):
        """ resizes the window, and adjusts the size of the embedded editor """
        BaseFrame.resize(self,x,y,width,height)
        if self.dialog:
            self.dialog.setparent(self.win)
            self.dialog.resize()

    def setdialog(self,dialog):
        """ installs a new editor into this frame, we copy it each time so we get independent scrolling """
        self.dialog = copy.copy(dialog)
        self.changed = True
        self.chgseq = -1

class EditorManager:
    """ class manages a collection of editors and editor frames that tile the full terminal service """
    def __init__(self,scr): 
        """ constructed with scr == curses screen or window object to manage within """
        (self.max_y,self.max_x) = scr.getmaxyx()
        self.editors = []
        self.frames = [EditorFrame(scr,0,0,self.max_y,self.max_x)]
        self.current = 0
        self.current_frame = 0
        self.scr = scr    

    def __del__(self):
        self.editors = None
        self.frames = None
        
    def getCurrentFrame(self):
        """ get the current frame """
        return self.frames[self.current_frame]
        
    def getCurrentEditor(self):
        """ return the current editor for the current frame or None if it isn't an editor """
        f = self.getCurrentFrame()
        if isinstance(f,EditorFrame):
            return f.editor
        else:
            return None

    def splitFrame(self,horizontal = True):
        """ split the current frame into two frames either vertically (default) or horizontally if horizontal == True """
        (x,y,width,height) = self.frames[self.current_frame].getrect()
        if horizontal and height <= 6:
            return
        if not horizontal and width <= 20:
            return
        newFrame = copy.copy(self.frames[self.current_frame])
        if  isinstance(newFrame,EditorFrame):
            newFrame.seteditor(self.frames[self.current_frame].editor)
        else:
            newFrame.setdialog(self.frames[self.current_frame].dialog)
        self.frames.insert(self.current_frame,newFrame)
        if horizontal:
            self.frames[self.current_frame].resize(x,y,width,height//2)
            self.frames[self.current_frame+1].resize(x,y+(height//2),width,height-(height//2))
            self.current_frame += 1
        else:
            self.frames[self.current_frame].resize(x,y,width//2,height)
            self.frames[self.current_frame+1].resize(x+(width//2)+1,y,width-(width//2)-1,height)
            self.frames[self.current_frame+1].setlborder(True)
            self.current_frame += 1

    def addEditor( self, e ):
        """ add a new editor to the list of editors to manage make it the editor in the current frame """
        if isinstance(self.frames[self.current_frame],EditorFrame):
            filename = os.path.abspath(e.getWorkfile().getFilename())
            idx = 0
            while idx < len(self.editors):
                cfilename = os.path.abspath(self.editors[idx].getWorkfile().getFilename())
                if cfilename == filename:
                    self.current = idx
                    break
                idx += 1
            else:
                self.editors.insert(self.current,e)
            self.frames[self.current_frame].seteditor(self.editors[self.current])

    def delEditor( self):
        """ close an editor and remove it from the list, fall back to the previous editor in the current frame """
        if isinstance(self.frames[self.current_frame],EditorFrame):
            if len(self.editors) == 1:
                return
            del self.editors[self.current]
            if self.current >= len(self.editors):
                self.current = len(self.editors)-1
            if self.current < 0:
                self.current = 0
            self.frames[self.current_frame].seteditor(self.editors[self.current])

    def nextEditor(self):
        """ set the next editor to be current, wrap around in the list """
        if isinstance(self.frames[self.current_frame],EditorFrame):
            self.current += 1
            if self.current > len(self.editors)-1:
                self.current = 0
            self.frames[self.current_frame].seteditor(self.editors[self.current])

    def prevEditor(self):
        """ set the previous editor to be current, wrap around in the list """
        if isinstance(self.frames[self.current_frame],EditorFrame):
            self.current -= 1
            if self.current < 0:
                self.current = len(self.editors)-1
            self.frames[self.current_frame].seteditor(self.editors[self.current])

    def nextFrame(self):       
        """ set the next frame to be current, wrap around the list """
        self.current_frame += 1
        if self.current_frame > len(self.frames)-1:
            self.current_frame = 0

    def killFrame(self):
        """ kill the current frame and clean up the remaining ones, there are still issues here """
        if (len(self.frames)-1):
            (x,y,width,height) = self.frames[self.current_frame].getrect(True) # width adjusted for any frame
            (x1,y1,width1,height1) = self.frames[self.current_frame].getrect(False) # width not adjusted 
            del self.frames[self.current_frame]
            if self.current_frame > (len(self.frames)-1):
                self.current_frame -= 1
                
            for f in self.frames:
                (fx,fy,fwidth,fheight) = f.getrect(True)
                (ux,uy,uwidth,uheight) = f.getrect(False)
                if fy == y and fheight == height and fx+fwidth == x: # window to left of us
                    f.resize(ux,uy,uwidth+width,uheight)
                    return
                
            for f in self.frames:
                (fx,fy,fwidth,fheight) = f.getrect(True)
                (ux,uy,uwidth,uheight) = f.getrect(False)
                if fy == y and fheight == height and x+width == fx: # window to right of us
                    if fx != ux:
                        f.resize(x1,fy,uwidth+width,fheight)
                    else:
                        f.resize(x,fy,fwidth+width,fheight)
                    return
                
            for f in self.frames:
                (fx,fy,fwidth,fheight) = f.getrect(False)
                if fx == x1 and fwidth == width1 and y1+height1 == fy: # window below us (don't use frame adjustement for this one)
                    f.resize(fx,y1,fwidth,height1+fheight)
                    return
                
            for f in self.frames:
                (fx,fy,fwidth,fheight) = f.getrect(False)
                if fx == x1 and fwidth == width1 and fy+fheight == y1: # window above us (don't use frame adjustement for this one)
                    f.resize(fx,fy,fwidth,height1+fheight)
                    return

    def zoomFrame(self):
        """ make the current frame fill the screen and get rid of all of the others """
        self.frames = [self.frames[self.current_frame]]
        self.current_frame = 0
        max_y,max_x = self.frames[self.current_frame].parent.getmaxyx()
        self.frames[self.current_frame].resize(0,0,max_x,max_y)

    def replaceFrame(self, frameClass ):
        """ replace the current frame with a new frame of frameClass type """
        curframe = self.frames[self.current_frame]
        newframe = frameClass(curframe.parent, curframe.x, curframe.y, curframe.height, curframe.width, curframe.lborder )
        self.frames[self.current_frame] = newframe
        return newframe

    def openEditor(self):
        """ open a new file in the current window, launches the file dialog allowing choosing or typing in a file name """
        if not isinstance(self.frames[self.current_frame],EditorFrame):
            self.replaceFrame(EditorFrame)
            
        f = file_dialog.FileDialog(self.scr,"Open or create file")
        choices = f.main()
        if choices and choices["file"]:
            self.addEditor(editor_common.Editor(self.scr,None,os.path.join(choices["dir"],choices["file"])))

    def resize(self):
        """ handle the resize event from the parent window and re-layout the parent window """
        ymax,xmax = self.scr.getmaxyx()
        sy = float(ymax)/float(self.max_y)
        sx = float(xmax)/float(self.max_x)                 
        fmap = self.frames
        fmap.sort()
        idx = 0
        while idx < len(fmap):
            (x,y,width,height) = fmap[idx].getrect()
            wx = int(round(width*sx))
            hy = int(round(height*sy))
            cx = int(round(x*sx))
            py = int(round(y*sy))
            if cx+wx > xmax:
                wx = xmax - cx
            if py+hy > ymax:
                hy = ymax - py
            fmap[idx].resize(cx,py,wx,hy)
            idx += 1
        idx = 0
        while idx < len(fmap):
            (x,y,width,height) = fmap[idx].getrect()
            jdx = 0
            while jdx < len(fmap):
                if jdx == idx:
                    jdx += 1
                    continue
                (x1,y1,width1,height1) = fmap[jdx].getrect()
                if (y1 < y and y1+height1 <= y) or (y1 >= y+height) or (x1 < x):
                    jdx += 1
                    continue
                diff = abs(width - (x1-x)-1)
                if diff <= 4:
                    width = (x1-x)-1
                    fmap[idx].resize(x,y,width,height)
                jdx += 1
            idx += 1
        self.max_x = xmax
        self.max_y = ymax

    def bufferList( self ):
        """ show the buffer list and allow selection of a new buffer to edit """
        changed = { True:"*", False:" " }
        names = []
        for e in self.editors:
            if e.getFilename():
                name = changed[e.isChanged()] + e.getFilename()
            else:
                name = " "+e.getWorkfile().getFilename()
            names.append(name)
        result = buffer_dialog.choose_buffer(self.scr, names )
        if result:
            self.current = names.index(result)
            self.frames[self.current_frame].seteditor(self.editors[self.current])
            
    def fileFind( self , fpat=".*",cpat="",recurse=False):
        """ launch the file find dialog box """
        result = file_find.filefind(self.scr,fpat=fpat,cpat=cpat,recurse=recurse)
        if result:
            editor = editor_common.Editor(self.scr,None,result[0])
            editor.goto(result[1],0)
            self.addEditor(editor)
            return True
        return False

    def sftpDialog( self , title="SFTP FileManager", remote_path="", ssh_username="", ssh_password="", local_path="."):
        """ launch the file find dialog box """
        result = sftpDialog(self.scr, title = "SFTP File Manager", remote_path=remote_path, ssh_username=ssh_username, ssh_password=ssh_password, local_path=local_path )
        if result:
            editor = editor_common.Editor(self.scr,None,result)
            editor.goto(0,0)
            self.addEditor(editor)
            return True
        return False

    def newsBrowse( self ):
        """ launch the news browser """
        news_browse.newsbrowse( self.scr )
        
    def browseSVN( self, path=".", filename="", revision="" ):
        """ launch  the browse svn dialog """
        values = browsesvn(self.scr,filename=filename,path=path, revision=revision)
        if "path" in values:
            if values["path"]:
                self.addEditor(editor_common.StreamEditor(self.scr,
                                                            None,
                                                            values["path"]+":(r%s)"%values["revision"],
                                                            get_file_revision( values["revision"],values["path"] )))
                return True
        return False
        
    def mouseEvent( self ):
        """ handle mouse events """
        try:
            mid, mx, my, mz, mtype = curses.getmouse()
            cf = 0
            f = None
            while (cf < len(self.frames)):
                if self.frames[cf].win.enclose(my,mx):
                    f = self.frames[cf]
                    break
                cf += 1
            else:
                return
    
            by,bx = f.win.getbegyx()
            oy = my - by - 1
            ox = mx - bx
            if oy < 0:
                return
    
            if isinstance(f,EditorFrame):
                line = f.editor.line + oy
                pos = f.editor.left + ox
    
                if mtype & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED | curses.BUTTON1_RELEASED):
                    (line,pos) = f.editor.filePos(line,pos)
                    f.editor.goto(line,pos)
                    self.current_frame = cf
    
                if mtype & curses.BUTTON1_PRESSED:
                    f.editor.mark_span()
    
                if (mtype & curses.BUTTON1_CLICKED) and f.editor.isMark():
                    f.editor.mark_span()
            else:
                self.current_frame = cf
        except:
            return
                
                
        
    def main(self):
        """ this is the main driver for the editor manager it displays the frames and gets it's keystrokes
        from the current frame, only the key events that are released """
        force = False
        
        curses.mousemask( curses.BUTTON1_PRESSED| curses.BUTTON1_RELEASED| curses.BUTTON1_CLICKED)
        
        while len(self.editors):
            for f in self.frames:
                f.redraw(force)
            if force:
                self.scr.noutrefresh()
            force = True
            if isinstance(self.frames[self.current_frame],EditorFrame):
                # if the buffer has a real filename then when it is current be in its directory
                filename = self.frames[self.current_frame].editor.getFilename()
                if filename:
                    (path,filename) = os.path.split(filename)
                    os.chdir(path)
            
                # run the editor in non blocking mode to have it process keystrokes returns unhandled ones
                cmd_id, seq = keymap.mapseq(keymap.keymap_manager,self.frames[self.current_frame].editor.main(False))
            else:
                # run the dialog non blocking mode to have it process keystrokes returns unhandled ones             
                (seq, values) = self.frames[self.current_frame].dialog.main(False)
                cmd_id, seq = keymap.mapseq(keymap.keymap_manager,seq)
            if extension_manager.is_extension(cmd_id):
                if not extension_manager.invoke_extension( cmd_id, self, seq ):
                    return seq
            if cmd_id == cmd_names.CMD_KILLFRAME and not (len(self.frames)-1):
                cmd_id = cmd_names.CMD_EXITNOSAVE

            if cmd_id == cmd_names.CMD_NEXTEDITOR:
                self.nextEditor()
            elif cmd_id == cmd_names.CMD_RESIZE:
                self.resize()
            elif cmd_id == cmd_names.CMD_REFRESH:
                for f in self.frames:
                    f.redraw(True)
                self.scr.refresh()  # this is here to signal refresh
            elif cmd_id == cmd_names.CMD_NEXTFRAME:
                self.nextFrame()
            elif cmd_id == cmd_names.CMD_BUFFERLIST:
                self.bufferList()
            elif cmd_id == cmd_names.CMD_FILEFIND:
                self.fileFind()
            elif cmd_id == cmd_names.CMD_SFTP:
                self.sftpDialog()
            elif cmd_id == cmd_names.CMD_SAVEEXIT:
                for e in self.editors:
                    if e.isChanged():
                        e.save()
                return seq
            elif cmd_id == cmd_names.CMD_BROWSESVN:
                (path,filename ) = os.path.split(os.path.abspath(self.editors[self.current].getWorkfile().getFilename()))
                self.browseSVN( path=path, filename=filename )
            elif cmd_id == cmd_names.CMD_HELP:
                self.addEditor(editor_common.StreamEditor(self.scr,None,
                                                            "Help",
                                                            io.StringIO(ped_help.get_help())))
            elif cmd_id == cmd_names.CMD_SHELLCMD:
                cmd = prompt(self.scr,"Shell command","> ",-1,name="shell")
                if cmd:
                    self.addEditor(editor_common.StreamEditor(self.scr,None,
                                                              time.asctime()+" > "+cmd,
                                                              subprocess.Popen(cmd,
                                                                               shell=True,
                                                                               bufsize=1024,
                                                                               encoding="utf-8",
                                                                               stdout=subprocess.PIPE,
                                                                               stderr=subprocess.STDOUT).stdout))
            elif cmd_id == cmd_names.CMD_OPENEDITOR:
                self.openEditor()
            elif cmd_id == cmd_names.CMD_PREVEDITOR:
                self.prevEditor()
            elif cmd_id == cmd_names.CMD_HORZSPLIT:
                self.splitFrame()
            elif cmd_id == cmd_names.CMD_VERTSPLIT:
                self.splitFrame(False)
            elif cmd_id == cmd_names.CMD_ZOOMFRAME:
                self.zoomFrame()
            elif cmd_id == cmd_names.CMD_KILLFRAME:
                self.killFrame()
            elif cmd_id == cmd_names.CMD_MOUSE:
                self.mouseEvent()
            elif cmd_id == cmd_names.CMD_DELEDITOR:
                if self.editors[self.current].isChanged():
                    if confirm(self.scr,"File modified, remove anyway?"):
                        self.delEditor()
                else:
                    self.delEditor()
            elif cmd_id == cmd_names.CMD_EXITNOSAVE: # esc
                modified = 0
                for e in self.editors:
                    if e.isChanged():
                        modified += 1
                if modified:
                    if confirm(self.scr,"%d changed files, exit anyway?"%(modified)):
                        return keytab.KEYTAB_ESC
                else:
                    return keytab.KEYTAB_ESC
            elif cmd_id == cmd_names.CMD_READNEWS: # alt-r read news
                self.newsBrowse()
            else:
                force = False        
