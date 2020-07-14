# Copyright 2009 James P Goodwin ped tiny python editor
import sys
from ped_dialog import file_dialog
import time
from ped_dialog.confirm_dialog import confirm
from ped_dialog.prompt_dialog import prompt
from ped_dialog.dialog import rect
from ped_dialog.message_dialog import message
from ped_core import editor_common
import curses
import os
import subprocess
import copy
import io
from ped_core import ped_help
from ped_dialog import file_find
import traceback
from ped_dialog import buffer_dialog
from ped_ssh_dialog.ssh_dialog import sftpDialog
from ped_core import keytab
from ped_core import cmd_names
from ped_core import keymap
from ped_core import extension_manager
import math

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
        self.changed = True
        self.lborder = lborder
        if self.lborder:
           self.win = parent.subwin(height,width-1,y,x+1)
        else:
           self.win = parent.subwin(height,width,y,x)

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
                    try:
                        self.parent.addch(self.y+off,self.x,curses.ACS_VLINE,curses.A_NORMAL)
                    except:
                        pass
                    off += 1
            self.changed = False


    def setlborder( self, flag ):
        """ our frames only have an optional left border to conserve screen space, this turns on/off the left border which is drawn at x-1 """
        if self.lborder == flag:
            return

        self.lborder = flag
        if flag:
            self.win = self.parent.subwin(self.height,self.width-1,self.y,self.x+1)
        else:
            self.win = self.parent.subwin(self.height,self.width,self.y,self.x)
        self.changed = True

    def getrect(self):
        """ get a rect as (x,y,width,height) always includes the left border"""
        return (self.x,self.y,self.width,self.height)


    def resize(self,x,y,width,height):
        """ resizes the window, and adjusts the size of the embedded editor """
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        if self.lborder:
            self.win = self.parent.subwin(height,width-1,y,x+1)
        else:
            self.win = self.parent.subwin(height,width,y,x)
        self.changed = True

class EditorFrame ( BaseFrame ):
    """ Each frame keeps track of an editor instance in a subwindow """
    def __init__(self,parent,x,y,height,width, lborder = False):
        """ parent is the curses window we're embedded in, x,y are our upper left coordinate, height,width are the size in characters """
        BaseFrame.__init__( self, parent,x,y,height,width,lborder )
        self.editor = None

    def __del__(self):
        """ clean up our subwindow when we close """
        BaseFrame.__del__(self)
        self.editor = None

    def __copy__(self):
        """ copy of editor frame """
        ef = EditorFrame( self.parent, self.x, self.y, self.height, self.width, self.lborder )
        return ef

    def redraw(self,force=True):
        """ redraw the frame updating the frame and the embedded editor as needed, force == True causes full redraw """
        BaseFrame.redraw( self, force )
        if self.editor:
            self.editor.setWin(self.win)
            if self.editor.has_changes() or force:
                if force:
                    self.editor.invalidate_screen()
                self.editor.redraw()
                self.win.leaveok(1)
                self.win.refresh()
                self.win.leaveok(0)

    def resize(self,x,y,width,height):
        """ resizes the window, and adjusts the size of the embedded editor """
        BaseFrame.resize(self,x,y,width,height)
        if self.editor:
            self.editor.setWin(self.win)
            self.editor.resize()

    def seteditor(self,editor):
        """ installs a new editor into this frame, we copy it each time so we get independent scrolling """
        self.editor = editor
        if self.editor:
            self.editor.setWin(self.win)
            self.editor.resize()
        self.changed = True

class DialogFrame ( BaseFrame ):
    """ Each frame keeps track of an editor instance in a subwindow """
    def __init__(self,parent,x,y,height,width,lborder=False):
        """ parent is the curses window we're embedded in, x,y are our upper left coordinate, height,width are the size in characters """
        BaseFrame.__init__( self, parent,x,y,height,width, lborder )
        self.dialog = None

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
        if self.editors:
            for e in self.editors:
                e.close()
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

    def setEditor(self, frame, editor):
        """ maintain relationship between frames list and editors list so that each editor in the editor's list occurs only 0 or 1 times in the frames list """
        for f in self.frames:
            if f.editor == editor:
                if repr(f) == repr(frame):
                    return
                else:
                    frame.seteditor(copy.copy(editor))
                    return
        frame.seteditor(editor)

    def splitFrame(self,horizontal = True):
        """ split the current frame into two frames either vertically (default) or horizontally if horizontal == True """
        (x,y,width,height) = self.frames[self.current_frame].getrect()
        if horizontal and height <= 6:
            return
        if not horizontal and width <= 20:
            return
        newFrame = copy.copy(self.frames[self.current_frame])
        if  isinstance(newFrame,EditorFrame):
            self.setEditor(newFrame,self.frames[self.current_frame].editor)
        else:
            newFrame.setdialog(self.frames[self.current_frame].dialog)
        self.frames.insert(self.current_frame,newFrame)
        if horizontal:
            self.frames[self.current_frame].resize(x,y,width,height//2)
            self.frames[self.current_frame+1].resize(x,y+(height//2),width,height-(height//2))
            self.current_frame += 1
        else:
            self.frames[self.current_frame].resize(x,y,width//2,height)
            self.frames[self.current_frame+1].resize(x+(width//2),y,width-(width//2),height)
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
            self.setEditor(self.frames[self.current_frame],self.editors[self.current])

    def delEditor( self):
        """ close an editor and remove it from the list, fall back to the previous editor in the current frame """
        if isinstance(self.frames[self.current_frame],EditorFrame):
            editor = self.editors[self.current]
            filename = editor.workfile.filename
            self.editors.remove(editor)
            if self.current >= len(self.editors):
                self.current = len(self.editors)-1
            if self.current < 0:
                self.current = 0
            if not len(self.editors):
                for f in self.frames:
                    self.setEditor(f,None)
                editor.close()
                return
            else:
                self.setEditor(self.frames[self.current_frame],self.editors[self.current])

            foundFilename = True

            while foundFilename:
                for idx in range(0,len(self.frames)):
                    if isinstance(self.frames[idx],EditorFrame):
                        if self.frames[idx].editor.workfile.filename == filename:
                            cur_frame = self.frames[self.current_frame]
                            self.current_frame = idx
                            self.killFrame()
                            for jdx in range(0,len(self.frames)):
                                if self.frames[jdx] == cur_frame:
                                    self.current_frame = jdx
                            break
                else:
                    foundFilename = False
            editor.close()

    def nextEditor(self):
        """ set the next editor to be current, wrap around in the list """
        if isinstance(self.frames[self.current_frame],EditorFrame):
            self.current += 1
            if self.current > len(self.editors)-1:
                self.current = 0
            self.setEditor(self.frames[self.current_frame],self.editors[self.current])

    def prevEditor(self):
        """ set the previous editor to be current, wrap around in the list """
        if isinstance(self.frames[self.current_frame],EditorFrame):
            self.current -= 1
            if self.current < 0:
                self.current = len(self.editors)-1
            self.setEditor(self.frames[self.current_frame],self.editors[self.current])

    def syncFrameEditor(self):
        """ sync the current frame's editor with the current editor """
        if isinstance(self.frames[self.current_frame],EditorFrame):
            for idx in range(0,len(self.editors)):
                if self.frames[self.current_frame].editor.workfile.filename == self.editors[idx].workfile.filename:
                    self.current = idx
                    break

    def nextFrame(self):
        """ set the next frame to be current, wrap around the list """
        self.current_frame += 1
        if self.current_frame > len(self.frames)-1:
            self.current_frame = 0
        self.syncFrameEditor()

    def killFrame(self):
        """ kill the current frame and clean up the remaining ones, there are still issues here """
        if (len(self.frames)-1):
            (x,y,width,height) = self.frames[self.current_frame].getrect() # width adjusted for border if needed
            del self.frames[self.current_frame]
            if self.current_frame > (len(self.frames)-1):
                self.current_frame -= 1

            frames_to_adjust = []
            total_height = 0
            for f in self.frames:
                (fx,fy,fwidth,fheight) = f.getrect()
                if fy >= y and fy+fheight <= y+height and fx+fwidth == x: # window to left of us
                    frames_to_adjust.append ((f,fx,fy,fwidth+width,fheight))
                    total_height += fheight
            if total_height == height:
                for f,fx,fy,fwidth,fheight in frames_to_adjust:
                    f.resize(fx,fy,fwidth,fheight)
                    f.setlborder(fx != 0)
                return

            frames_to_adjust = []
            total_height = 0
            for f in self.frames:
                (fx,fy,fwidth,fheight) = f.getrect()
                if fy >= y and fy+fheight <= y+height and x+width == fx: # window to right of us
                    frames_to_adjust.append((f,x,fy,fwidth+width,fheight))
                    total_height += fheight
            if total_height == height:
                for f,fx,fy,fwidth,fheight in frames_to_adjust:
                    f.resize(fx,fy,fwidth,fheight)
                    f.setlborder(fx != 0)
                return

            frames_to_adjust = []
            total_width = 0
            for f in self.frames:
                (fx,fy,fwidth,fheight) = f.getrect()
                if fx >= x and fx+fwidth <= x+width and y+height == fy: # window below us (don't use frame adjustement for this one)
                    frames_to_adjust.append((f,fx,y,fwidth,height+fheight))
                    total_width += fwidth
            if total_width == width:
                for f,fx,fy,fwidth,fheight in frames_to_adjust:
                    f.resize(fx,fy,fwidth,fheight)
                    f.setlborder(fx != 0)
                return

            frames_to_adjust = []
            total_width = 0
            for f in self.frames:
                (fx,fy,fwidth,fheight) = f.getrect()
                if fx >= x and fx+fwidth <= x+width and fy+fheight == y: # window above us (don't use frame adjustement for this one)
                    frames_to_adjust.append((f,fx,fy,fwidth,height+fheight))
                    total_width += fwidth
            if total_width == width:
                for f,fx,fy,fwidth,fheight in frames_to_adjust:
                    f.resize(fx,fy,fwidth,fheight)
                    f.setlborder(fx != 0)
                return

            self.syncFrameEditor()

    def zoomFrame(self):
        """ make the current frame fill the screen and get rid of all of the others """
        self.frames = [self.frames[self.current_frame]]
        self.current_frame = 0
        max_y,max_x = self.frames[self.current_frame].parent.getmaxyx()
        self.frames[self.current_frame].resize(0,0,max_x,max_y)
        self.frames[self.current_frame].setlborder(False)
        self.syncFrameEditor()

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
        if self.max_x == xmax and self.max_y == ymax:
            return

        temp_frames = []
        for f in self.frames:
            (x,y,width,height) = f.getrect()
            temp_frames.append((f,x,y,width,height))

        if self.max_x != xmax:
            already_horizontal = []

            for oy in range(0,max(ymax,self.max_y)):
                frames_to_adjust = []
                for fidx in range(0,len(temp_frames)):
                    (f,x,y,width,height) = temp_frames[fidx]
                    if y <= oy and y+height > oy:
                        frames_to_adjust.append(fidx)
                remaining_width = xmax
                frames_to_adjust.sort(key=lambda x: temp_frames[x][1])
                start_x = 0
                for idx in range(0,len(frames_to_adjust)):
                    f,x,y,width,height = temp_frames[frames_to_adjust[idx]]
                    if f in already_horizontal:
                        pass
                    elif idx == len(frames_to_adjust)-1:
                        width = remaining_width
                        temp_frames[frames_to_adjust[idx]] = (f,start_x,y,width,height)
                        already_horizontal.append(f)
                    else:
                        width = remaining_width // (len(frames_to_adjust)-idx)
                        temp_frames[frames_to_adjust[idx]] = (f,start_x,y,width,height)
                        already_horizontal.append(f)
                    start_x += width
                    remaining_width -= width

        if self.max_y != ymax:
            already_vertical = []

            for ox in range(0,max(self.max_x,xmax)):
                frames_to_adjust = []
                for fidx in range(0,len(temp_frames)):
                    (f,x,y,width,height) = temp_frames[fidx]
                    if x <= ox and x+width > ox:
                        frames_to_adjust.append(fidx)
                remaining_height = ymax
                frames_to_adjust.sort(key=lambda x: temp_frames[x][2])
                start_y = 0
                for idx in range(0,len(frames_to_adjust)):
                    f,x,y,width,height = temp_frames[frames_to_adjust[idx]]
                    if f in already_vertical:
                        pass
                    elif idx == len(frames_to_adjust)-1:
                        height = remaining_height
                        temp_frames[frames_to_adjust[idx]] = (f,x,start_y,width,height)
                        already_vertical.append(f)
                    else:
                        height = remaining_height // (len(frames_to_adjust)-idx)
                        temp_frames[frames_to_adjust[idx]] = (f,x,start_y,width,height)
                        already_vertical.append(f)
                    start_y += height
                    remaining_height -= height

        for f,x,y,width,height in temp_frames:
            f.resize(x,y,width,height)

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
            self.setEditor(self.frames[self.current_frame],self.editors[self.current])

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
                    self.syncFrameEditor()

                if mtype & curses.BUTTON1_PRESSED:
                    f.editor.mark_span()

                if (mtype & curses.BUTTON1_CLICKED) and f.editor.isMark():
                    f.editor.mark_span()
            else:
                self.current_frame = cf
        except:
            return

    def redraw(self, force = False):
        """ redraw the editor manager and all the subframes, do minimal updates unless force is True """
        for f in self.frames:
            if isinstance(f,EditorFrame):
                new_cursor_state = (f == self.frames[self.current_frame])
                old_cursor_state = f.editor.showcursor(new_cursor_state)
                f.editor.setfocus(new_cursor_state)
                force = force or (old_cursor_state != new_cursor_state)
            f.redraw(force)
        self.scr.leaveok(1)
        self.scr.refresh()
        self.scr.leaveok(0)


    def main(self,blocking = True):
        """ this is the main driver for the editor manager it displays the frames and gets it's keystrokes
        from the current frame, only the key events that are released """
        force = not blocking

        curses.mousemask( curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION )
        self.scr.keypad(1)

        while len(self.editors):
            self.redraw(force)
#            if force:
#                self.scr.noutrefresh()
#            force = True
            if isinstance(self.frames[self.current_frame],EditorFrame):
                # if the buffer has a real filename then when it is current be in its directory
                filename = self.frames[self.current_frame].editor.getFilename()
                if filename:
                    (path,filename) = os.path.split(filename)
                    if os.path.exists(path):
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
                self.redraw(True)
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
            elif cmd_id == cmd_names.CMD_HELP:
                self.addEditor(editor_common.StreamEditor(self.scr,None,
                                                            "Help",
                                                            io.StringIO(ped_help.get_help()),wait=True))
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
            if seq == keytab.KEYTAB_REFRESH:
                self.redraw(True)
#            else:
#                force = False

            if not blocking:
                self.scr.refresh()
                return seq
