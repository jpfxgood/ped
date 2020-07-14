# Copyright 2009-2012 James P Goodwin ped tiny python editor
""" module that implements the guts of the ped editor, the file abstraction and the editor """
import curses
import curses.ascii
import sys
import os
import shutil
import tempfile
import re
import gc
from ped_dialog.prompt_dialog import prompt
from ped_dialog.message_dialog import message
from ped_dialog.replace_dialog import replace,confirm_replace
from ped_dialog.confirm_dialog import confirm
from ped_dialog import file_dialog
from ped_core import undo
from ped_core import python_mode
from ped_core import java_mode
from ped_core import cpp_mode
from ped_core import guess_mode
import copy
from ped_core import clipboard
import subprocess
from ped_core import cmd_names
from ped_core import keytab
from ped_core import keymap
from ped_core import extension_manager
from ped_core import changes
import traceback
import locale
import codecs
import tempfile
import threading
import logging
import time

locale.setlocale(locale.LC_ALL,'')
def_encoding = locale.getpreferredencoding()

class EditLine:
    """ Interface for each editable line in a file, a fly-weight object """
    def __init__(self):
        """ should initialize any content or references to external objects """
        pass

    def length(self):
        """ return the length of the line """
        pass

    def flush(self):
        """ flush cached length if you have one """
        pass

    def getContent(self):
        """ should return line representing this line in the source file """
        pass

class FileLine(EditLine):
    """ Instance of a line in a file that hasn't been changed, stored on disk """
    def __init__(self, parent, pos, len = -1 ):
        """ FileLine(s) are pointers to a line on disk the EditFile reference and offset are stored """
        EditLine.__init__(self)
        self.parent = parent
        self.pos = pos
        self.len = len

    def length(self):
        """ return length of line """
        if self.len < 0:
            self.len = len(self.parent.expand_tabs(self.getContent()))
        return self.len

    def flush(self):
        """ flush cached length """
        self.len = -1

    def getContent(self):
        """ gets the file from its parent, seeks to position, reads line and returns it """
        working = self.parent.getWorking()
        working.seek(self.pos,0)
        txt = working.readline().rstrip()
        return txt

    def __del__(self):
        self.parent = None

class MemLine(EditLine):
    """ Instance of a line in memory that has been edited """
    def __init__(self, content ):
        """ MemLine(s) are in memory strings that represent a line that has been edited, it is initialized from the original file content"""
        EditLine.__init__(self)
        self.content = content

    def length(self):
        """ return the length of the content """
        return len(self.content)

    def flush(self):
        """ flush cached length """
        pass

    def getContent(self):
        """ just return the string reference """
        return self.content

class ReadOnlyError(Exception):
    """ Exception when modification to readonly file attempted """
    pass

class EditFile:
    """ Object that manages one file that is open for editing,
    lines are either pointers to lines on disk, or in-memory copies
    for edited lines """

    default_readonly = False
    default_backuproot = "~"

    def __init__(self, filename=None ):
        """ takes an optional filename to either load or create """
        # store the filename
        self.filename = filename
        # the root of the backup directory
        self.backuproot = EditFile.default_backuproot
        # set the default tab stops
        self.tabs = [ 4, 8 ]
        # set the changed flag to false
        self.changed = False
        # read only flag
        self.readonly = EditFile.default_readonly
        # undo manager
        self.undo_mgr = undo.UndoManager()
        # change manager
        self.change_mgr = changes.ChangeManager()
        # modification reference incremented for each change
        self.modref = 0
        # the file object
        self.working = None
        # the lines in this file
        self.lines = []
        # load the file
        if filename:
            self.load()

    def __copy__(self):
        """ override copy so that copying manages file handles and intelligently copies the lists """
        result = EditFile()
        result.filename = self.filename
        result.tabs = self.tabs
        result.changed = self.changed
        result.readonly = True
        result.undo_mgr = copy.copy(self.undo_mgr)
        result.change_mgr = copy.copy(self.change_mgr)
        result.modref = self.modref
        result.lines = []
        for l in self.lines:
            if isinstance(l,MemLine):
                result.lines.append(copy.deepcopy(l))
            elif isinstance(l,FileLine):
                result.lines.append(FileLine(result,l.pos,l.len))
        result.working = None
        if self.working:
            result.working = open(self.working.name,"r",buffering=1,encoding="utf-8")
        return result

    def __del__(self):
        """ make sure we close file when we are destroyed """
        self.undo_mgr = None
        self.change_mgr = None
        self.close()

    def set_tabs(self, tabs ):
        """ set the tab stops for this file to something new """
        if tabs != self.tabs:
            self.tabs = tabs
            for l in self.lines:
                l.flush()

    def get_tabs(self):
        """ return the list of tab stops """
        return self.tabs

    def getWorking(self):
        """ return the file object """
        return self.working

    def getModref(self):
        """ modref is a serial number that is incremented for each change to a file, used to detect changes externally """
        return self.modref

    def setUndoMgr(self,undo_mgr):
        """ sets the undo manager object for this EditFile, undo manager is used to record undo records to enable undo in the editor """
        self.undo_mgr = undo_mgr

    def getUndoMgr(self):
        """ returns our undo_manager """
        return self.undo_mgr

    def isChanged(self):
        """ true if there are unsaved changes, false otherwise """
        return self.changed

    def isReadOnly(self):
        """ true if the file is read only, false otherwise """
        return self.readonly

    def setReadOnly(self,flag = True):
        """ mark this file as read only """
        self.readonly = flag

    def getFilename(self):
        """ get the filename for this file """
        return self.filename

    def setFilename(self,filename):
        """ set the filename for this object """
        self.filename = filename

    def numLines(self):
        """ get the number of lines in this file """
        return len(self.lines)

    def open(self):
        """ open the file or create it if it doesn't exist """
        abs_name = os.path.abspath(self.filename)
        abs_path = os.path.dirname(abs_name)
        if os.path.exists(abs_name):
            self.working = tempfile.NamedTemporaryFile(mode="w+",buffering=1,encoding="utf-8",prefix="ped_",dir=EditFile.get_backup_dir(self.backuproot))
            shutil.copyfile(abs_name,self.working.name)
            if not self.readonly:
                self.setReadOnly(not os.access(abs_name,os.W_OK))
        elif not self.readonly:
            self.working = tempfile.NamedTemporaryFile(mode="w+",buffering=1,encoding="utf-8",prefix="ped_",dir=EditFile.get_backup_dir(self.backuproot))
        else:
            raise Exception("File %s does not exist!"%(self.filename))
        self.filename = abs_name
        self.working.seek(0,0)

    def isModifiedOnDisk(self):
        """ return true if the file we're editing has been modified since we started """
        if os.path.exists(self.filename):
            disk_stat = os.stat(self.filename)
            temp_stat = os.stat(self.working.name)
            return disk_stat.st_mtime > temp_stat.st_mtime
        else:
            return False

    def close(self):
        """ close the file """
        if self.working:
            self.working.close()
        self.working = None
        self.lines = None

    def load(self):
        """ open the file and load the lines into the array """
        self.open()
        self.lines = []
        pos = 0
        lidx = 0
        while True:
            line = self.working.readline()
            if not line:
                break
            line = line.rstrip()
            lidx = lidx + 1
            self.lines.append(FileLine(self,pos,len(self.expand_tabs(line))))
            pos = self.working.tell()
        while len(self.lines) and not self.lines[-1].getContent().strip():
            del self.lines[-1]
        if not len(self.lines):
            self.lines.append(MemLine(""))
        self.changed = False
        self.modref = 0

    def hasChanges(self,view):
        """ return true if there are pending screen updates """
        return self.change_mgr.has_changes(view)

    def isLineChanged(self,view,line):
        """ return true if a particular line is changed """
        if self.change_mgr and line < len(self.lines):
            return self.change_mgr.is_changed(view,line)
        else:
            return True

    def flushChanges(self,view):
        """ reset the change tracking for full screen redraw events """
        if self.change_mgr:
            self.change_mgr.flush(view)

    def _deleteLine(self,line,changed = True):
        """ delete a line """
        if self.undo_mgr:
            self.undo_mgr.get_transaction().push(self._insertLine,(line,self.lines[line],self.changed))
        del self.lines[line]
        self.changed = changed
        self.modref += 1
        if self.change_mgr:
            self.change_mgr.changed(line,len(self.lines))

    def _insertLine(self,line,lineObj,changed = True):
        """ insert a line """
        if self.undo_mgr:
            self.undo_mgr.get_transaction().push(self._deleteLine,(line,self.changed))
        self.lines.insert(line,lineObj)
        self.changed = changed
        self.modref += 1
        if self.change_mgr:
            self.change_mgr.changed(line,len(self.lines))


    def _replaceLine(self,line,lineObj,changed = True):
        """ replace a line """
        if self.undo_mgr:
            self.undo_mgr.get_transaction().push(self._replaceLine,(line,self.lines[line],self.changed))
        self.lines[line] = lineObj
        self.changed = changed
        self.modref += 1
        if self.change_mgr:
            self.change_mgr.changed(line,line)


    def _appendLine(self,lineObj,changed = True):
        """ add a line """
        if self.undo_mgr:
            self.undo_mgr.get_transaction().push(self._deleteLine,(len(self.lines),self.changed))
        self.lines.append(lineObj)
        self.changed = changed
        self.modref += 1
        if self.change_mgr:
            self.change_mgr.changed(len(self.lines)-1,len(self.lines)-1)

    def touchLine(self, line_start, line_end):
        """ touch a line so it will redraw"""
        if self.change_mgr:
            self.change_mgr.changed(min(line_start,line_end),max(line_start,line_end))

    def length(self, line ):
        """ return the length of the line """
        if line < len(self.lines):
            return self.lines[line].length()
        else:
            return 0

    def getLine( self, line, pad = 0, trim = False ):
        """ get a line """
        if line < len(self.lines):
            orig = self.lines[line].getContent()
        else:
            orig = ""
        if trim:
            orig = orig.rstrip()
        if pad > len(orig):
            orig = orig + ' '*(pad-len(orig))
        return self.expand_tabs(orig)

    def getLines( self, line_start = 0, line_end = -1):
        """ get a list of a range of lines """
        if line_end < 0:
            line_end = len(self.lines)
        if line_end > len(self.lines):
            line_end = len(self.lines)
        lines = []
        while line_start < line_end:
            lines.append(self.expand_tabs(self.lines[line_start].getContent()))
            line_start += 1
        return lines

    def deleteLine( self, line ):
        """ delete a line, high level interface """
        if self.isReadOnly():
            raise ReadOnlyError()

        if line < len(self.lines):
            self._deleteLine(line)

    def insertLine( self, line, content ):
        """ insert a line, high level interface """
        if self.isReadOnly():
            raise ReadOnlyError()

        if line >= len(self.lines):
            lidx = len(self.lines)
            while lidx <= line:
                self._appendLine(MemLine(""))
                lidx += 1

        self._insertLine(line,MemLine(content))

    def replaceLine( self, line, content ):
        """ replace a line, high level interface """
        if self.isReadOnly():
            raise ReadOnlyError()

        if line >= len(self.lines):
            lidx = len(self.lines)
            while lidx <= line:
                self._appendLine(MemLine(""))
                lidx += 1

        self._replaceLine(line, MemLine(content))

    @staticmethod
    def get_backup_dir( base = "~" ):
        """ get the backup directory, create it if it doesn't exist """
        base = os.path.expanduser(base)
        if not os.path.exists(base):
            base = os.path.expanduser("~")
        pedbackup = os.path.join(base,".pedbackup")
        if not os.path.exists(pedbackup):
            os.mkdir(pedbackup)
        return pedbackup

    @staticmethod
    def make_backup_dir( filename, base = "~" ):
        """ make a backup directory under ~/.pedbackup for filename and return it's name """
        pedbackup = EditFile.get_backup_dir( base )

        (filepath,rest) = os.path.split(os.path.abspath(filename))
        for part in filepath.split("/"):
            if part:
                pedbackup = os.path.join(pedbackup,part)
                if not os.path.exists(pedbackup):
                    os.mkdir(pedbackup)

        return os.path.join(pedbackup,rest)

    def save( self, filename = None ):
        """ save the file, if filename is passed it'll be saved to that filename and reopened """
        if filename:
            if filename == self.filename and self.isReadOnly():
                raise ReadOnlyError()

            o = open(filename,"w",buffering=1,encoding="utf-8")
            for l in self.lines:
                txt = l.getContent()+'\n'
                o.write(txt)
            o.close()
            self.close()
            self.filename = filename
            self.load()
        else:
            if self.isReadOnly():
                raise ReadOnlyError()
            if not self.changed:
                return
            o = open(self.filename+".sav","w",buffering=1,encoding="utf-8")
            for l in self.lines:
                txt = l.getContent()+'\n'
                o.write(txt)
            o.close()
            self.working.close()
            if os.path.exists(self.filename):
                fstat = os.stat(self.filename)
                backup_path = EditFile.make_backup_dir(self.filename,self.backuproot)
                retval = shutil.move(self.filename,backup_path)
                os.rename(self.filename+".sav",self.filename)
                os.chmod(self.filename,fstat.st_mode)
            else:
                os.rename(self.filename+".sav",self.filename)
            self.load()

    def get_tab_stop(self, idx, before=False ):
        """ return the next tab stop before or after a given offset """
        prev = 0
        for stop in self.tabs:
            if stop > idx:
                if before:
                    return prev
                else:
                    return stop
            prev = stop

        incr = self.tabs[-1]-self.tabs[-2]
        while stop <= idx:
            prev = stop
            stop += incr

        if before:
            return prev
        else:
            return stop

    def expand_tabs(self, content ):
        """ expand tabs in a line """
        idx = 0
        while idx < len(content):
            if content[idx] == '\t':
                stop = self.get_tab_stop(idx)
                content = content[0:idx] + ' '*(stop-idx) + content[idx+1:]
                idx += (stop-idx)
            else:
                idx += 1
        return content


class Editor:
    """ class that implements the text editor, operates on a file abstraction EditFile """

    modes = [python_mode,cpp_mode,java_mode,guess_mode]

    def __init__(self, parent, scr, filename, workfile = None, showname = True, wrap = False ):
        """ takes parent curses screen we're popped up over, scr our curses window, filename we should edit, optionally an already open EditFile """
        if workfile:
            self.workfile = workfile
        else:
            self.workfile = EditFile(filename)
        self.workfile.change_mgr.add_view(self)
        self.undo_mgr = self.workfile.getUndoMgr()
        self.parent = parent
        self.scr = scr
        if scr:
            self.max_y,self.max_x = self.scr.getmaxyx()
        else:
            self.max_y = 0
            self.max_x = 0
        self.line = 0
        self.pos = 0
        self.vpos = 0
        self.left = 0
        self.prev_cmd = cmd_names.CMD_NOP
        self.cmd_id = cmd_names.CMD_NOP
        self.home_count = 0
        self.end_count = 0
        self.line_mark = False
        self.span_mark = False
        self.rect_mark = False
        self.search_mark = False
        self.mark_pos_start = 0
        self.mark_line_start = 0
        self.last_search = None
        self.last_search_dir = True
        self.mode = None
        self.showname = showname
        self.wrap = wrap
        self.wrap_lines = []
        self.unwrap_lines = []
        self.wrap_modref = -1
        self.wrap_width = -1
        self.show_cursor = True
        self.prev_pos = (0,0)
        self.focus = True
        self.invalidate_all()
        curses.raw()
        curses.meta(1)

    def __copy__(self):
        """ override to just copy the editor state and not the underlying file object """
        result = Editor(self.parent,self.scr,None,self.workfile,self.showname,self.wrap)
        result.line = self.line
        result.pos = self.pos
        result.vpos = self.vpos
        result.left = self.left
        result.prev_cmd = self.prev_cmd
        result.cmd_id = self.cmd_id
        result.home_count = self.home_count
        result.end_count = self.end_count
        result.line_mark = self.line_mark
        result.span_mark = self.span_mark
        result.rect_mark = self.rect_mark
        result.search_mark = self.search_mark
        result.mark_pos_start = self.mark_pos_start
        result.mark_line_start = self.mark_line_start
        result.last_search = self.last_search
        result.last_search_dir = self.last_search_dir
        result.mode = self.mode
        result.wrap_lines = copy.copy(self.wrap_lines)
        result.unwrap_lines = copy.copy(self.unwrap_lines)
        result.wrap_modref = self.wrap_modref
        result.wrap_width = self.wrap_width
        result.show_cursor = self.show_cursor
        result.focus = self.focus
        result.prev_pos = copy.copy(self.prev_pos)
        return result


    def __del__(self):
        """ if we're closing then clean some stuff up """
        # let the mode clean up if it needs to
        if self.workfile and self.workfile.change_mgr:
            self.workfile.change_mgr.remove_view(self)

        if self.mode:
            self.mode.finish(self)
            self.mode = None
        self.workfile = None
        self.undo_mgr = None

    def close(self):
        """ by default it is a no-op but editors overriding this can hook the close to clean things up """
        pass

    def pushUndo(self):
        """ push an undo action onto the current transaction """
        self.undo_mgr.get_transaction().push(self.applyUndo,(self.line,
                                                             self.pos,
                                                             self.vpos,
                                                             self.left,
                                                             self.prev_cmd,
                                                             self.cmd_id,
                                                             self.home_count,
                                                             self.end_count,
                                                             self.line_mark,
                                                             self.span_mark,
                                                             self.rect_mark,
                                                             self.search_mark,
                                                             self.mark_pos_start,
                                                             self.mark_line_start,
                                                             self.last_search,
                                                             self.last_search_dir,
                                                             clipboard.clip,
                                                             clipboard.clip_type,
                                                             self.show_cursor,
                                                             self.focus,
                                                             self.wrap))
    def applyUndo(self,*args):
        """ called by undo to unwind one undo action """
        ( self.line,
        self.pos,
        self.vpos,
        self.left,
        self.prev_cmd,
        self.cmd_id,
        self.home_count,
        self.end_count,
        self.line_mark,
        self.span_mark,
        self.rect_mark,
        self.search_mark,
        self.mark_pos_start,
        self.mark_line_start,
        self.last_search,
        self.last_search_dir,
        clipboard.clip,
        clipboard.clip_type,
        self.show_cursor,
        self.focus,
        self.wrap ) = args
        self.invalidate_screen()
        self.invalidate_mark()

    def undo(self):
        """ undo the last transaction, actually undoes the open transaction and the prior closed one """
        line = self.line
        left = self.left
        self.undo_mgr.undo_transaction() # undo the one we're in... probably empty
        self.undo_mgr.undo_transaction() # undo the previous one... probably not empty
        if self.line != line or self.left != left:
            self.invalidate_screen()

    def setWin(self,win):
        """ install a new window to render to """
        self.scr = win

    def getModref(self):
        """ return the current modref of this editor """
        return self.workfile.getModref()

    def getWorkfile(self):
        """ return the workfile that this editor is attached to """
        return self.workfile

    def getFilename(self):
        """ return the filename for this editor """
        return self.workfile.getFilename()

    def getUndoMgr(self):
        """ get the undo manager that we're using """
        return self.undo_mgr

    def isChanged(self):
        """ returns true if the file we're working on has unsaved changes """
        return self.workfile.isChanged()

    def isLineChanged(self, line, display=True ):
        """ return true if line is changed for the current revisions """
        if self.workfile:
            if display:
                return self.workfile.isLineChanged( self, self.filePos(line,0)[0])
            else:
                return self.workfile.isLineChanged( self, line )
        else:
            return True

    def flushChanges( self ):
        """ flush change tracking to show we're done updating """
        if self.workfile:
            self.workfile.flushChanges(self)

    def isMark(self):
        """ returns true if there is a mark set """
        return (self.line_mark or self.span_mark or self.rect_mark or self.search_mark)

    def getCurrentLine(self,display=False):
        """ returns the current line in the file """
        return self.getContent(self.getLine(display),display)

    def getPos(self,display=False):
        """ get the character position in the current line that we're at """
        if self.wrap:
            if not display:
                r_line,r_pos = self.filePos(self.line+self.vpos,self.left+self.pos)
                return r_pos
        return self.left+self.pos

    def getLine(self,display=False):
        """ get the line that we're on in the current file """
        if self.wrap:
            if not display:
                r_line,r_pos = self.filePos(self.line+self.vpos,0)
                return r_line

        return self.line+self.vpos

    def filePos(self, line, pos ):
        """ translate display line, pos to file line, pos """
        if self.wrap:
            if line < len(self.wrap_lines):
                return (self.wrap_lines[line][0],self.wrap_lines[line][1]+pos)
            else:
                return (self.numLines()+(line-len(self.wrap_lines)),pos)
        else:
            return (line,pos)

    def scrPos(self, line, pos ):
        """ translate file pos to screen pos """
        if self.wrap:
            nlines = len(self.unwrap_lines)
            if line >= nlines:
                r_line,r_pos = self.scrPos(self.numLines()-1,self.getLength(self.numLines()-1)-1)
                return (r_line+(line-self.numLines())+1,pos)
            sline = self.unwrap_lines[line]
            while sline < len(self.wrap_lines) and self.wrap_lines[sline][0] == line:
                if pos >= self.wrap_lines[sline][1] and pos < self.wrap_lines[sline][2]:
                    return (sline,pos-self.wrap_lines[sline][1])
                sline = sline + 1
            else:
                return (sline-1,pos - self.wrap_lines[sline-1][1])
        else:
            return (line,pos)

    def getContent(self, line, pad = 0, trim= False, display=False ):
        """ get a line from the file """
        if self.wrap:
            if display:
                orig = ""
                if line < len(self.wrap_lines):
                    orig = self.workfile.getLine(self.wrap_lines[line][0])[self.wrap_lines[line][1]:self.wrap_lines[line][2]]
                if trim:
                    orig = orig.rstrip()
                if pad > len(orig):
                    orig = orig + ' '*(pad-len(orig))
                return orig
        orig = self.workfile.getLine(line,pad,trim)
        return orig

    def getLength(self, line, display=False ):
        """ get the length of a line """
        length = 0
        if self.wrap and display:
            if line < len(self.wrap_lines):
                length = self.workfile.length(self.wrap_lines[line][0])
        else:
            length = self.workfile.length(line)

        return length

    def numLines(self,display=False):
        """ get the number of lines in the editor """
        if self.wrap and display:
            return len(self.wrap_lines)

        return self.workfile.numLines()

    def rewrap(self, force = False):
        """ compute the wrapped line array """
        if self.wrap and (force or self.workfile.getModref() != self.wrap_modref or self.wrap_width != self.max_x-1):
            self.wrap_modref = self.workfile.getModref()
            self.wrap_width = self.max_x
            self.wrap_lines = []
            self.unwrap_lines = []
            for l in range(0,self.workfile.numLines()):
                line_len = self.workfile.length(l)
                start = 0
                self.unwrap_lines.append(len(self.wrap_lines))
                if not line_len:
                    self.wrap_lines.append((l,0,0))
                else:
                    while start < line_len:
                        self.wrap_lines.append((l,start,min(line_len,start+self.wrap_width)))
                        start += self.wrap_width
            self.invalidate_after_cursor()

    def addstr(self,row,col,str,attr = curses.A_NORMAL):
        """ write properly encoded string to screen location """
        try:
            return self.scr.addstr(row,col,codecs.encode(str,"utf-8"),attr)
        except:
            return 0

    def window_pos(self,line,pos):
        sc_line,sc_pos = self.scrPos(line,pos)
        return((sc_line-self.line)+1,sc_pos-self.left)

    def showcursor(self,state):
        """ set flag to turn cursor on or off """
        old_cursor_state = self.show_cursor
        self.show_cursor = state
        return old_cursor_state

    def setfocus(self,state):
        """ set this editor to have focus or not """
        old_focus_state = self.focus
        self.focus = state
        return old_focus_state

    def draw_cursor(self):
        """ worker function to draw the current cursor position """
        if self.show_cursor:
            line = self.getLine()
            pos = self.getPos()
            if pos < self.getLength(line):
                cursor_ch = self.getContent(line)[pos]
            else:
                cursor_ch = ' '
            sc_line,sc_pos = self.window_pos(line,pos)
            self.addstr(sc_line,sc_pos,cursor_ch,curses.A_REVERSE)

    def draw_mark(self):
        """ worker function to draw the marked section of the file """
        if not self.isMark():
            return

        (mark_top,mark_left) = self.scrPos(self.mark_line_start,self.mark_pos_start)
        mark_line_start = mark_top
        mark_pos_start = mark_left
        mark_right = self.getPos(True)
        mark_bottom = self.getLine(True)

        if (self.rect_mark or self.line_mark) and mark_left > mark_right:
            mark = mark_left
            mark_left = mark_right
            mark_right = mark

        if mark_top > mark_bottom:
            mark = mark_bottom
            mark_bottom = mark_top
            mark_top = mark

        if mark_top < self.line:
            mark_top = self.line
            if self.span_mark:
                mark_left = 0

        mark_right = mark_right + 1

        s_left = mark_left - self.left
        s_left = max(0,s_left)
        s_right = mark_right - self.left
        s_right = min(self.max_x,s_right)
        s_top = (mark_top - self.line)+1
        s_top = max(1,s_top)
        s_bottom = (mark_bottom - self.line)+1
        s_bottom = min(self.max_y-1,s_bottom)
        mark_left = max(mark_left,self.left)
        mark_right = min(mark_right,self.left+self.max_x)

        if self.line_mark:
            s_right = self.max_x
            mark_right = self.left+s_right
            mark_left = max(mark_left,self.left)

        if s_top == s_bottom:
            if s_right > s_left:
                self.addstr(s_top,
                                s_left,
                                self.getContent(mark_top,
                                                      mark_right,
                                                      True,
                                                      True)[mark_left:mark_right],
                                curses.A_REVERSE)
        elif self.rect_mark:
            if mark_top < self.line:
                mark_top = self.line
            while s_top <= s_bottom:
                self.addstr(s_top,
                                s_left,
                                self.getContent(mark_top,
                                                      mark_right,
                                                      True,
                                                      True)[mark_left:mark_right],
                                curses.A_REVERSE)
                s_top += 1
                mark_top += 1
        elif self.span_mark:
            cur_line = mark_top
            while s_top <= s_bottom:
                if cur_line == mark_top:
                    offset = s_left
                    width = self.max_x-offset
                    self.addstr(s_top,
                                    offset,
                                    self.getContent(cur_line,
                                                          self.left+offset+width,
                                                          True,
                                                          True)[self.left+offset:self.left+offset+width],
                                    curses.A_REVERSE)
                elif cur_line == mark_bottom:
                    self.addstr(s_top,
                                    0,
                                    self.getContent(cur_line,
                                                          self.getPos(True),
                                                          True,
                                                          True)[self.left:self.getPos(True)+1],
                                    curses.A_REVERSE)
                else:
                    self.addstr(s_top,
                                    0,
                                    self.getContent(cur_line,
                                                          self.left+self.max_x,
                                                          True,
                                                          True)[self.left:self.left+self.max_x],
                                    curses.A_REVERSE)
                s_top += 1
                cur_line += 1
        elif self.line_mark:
            cur_line = mark_top
            while s_top <= s_bottom:
                self.addstr(s_top,
                                0,
                                self.getContent(cur_line,
                                                      self.left+self.max_x,
                                                      True,
                                                      True)[self.left:self.left+self.max_x],
                                curses.A_REVERSE)
                s_top += 1
                cur_line += 1

    def resize(self):
        """ resize the editor to fill the window """
        if self.scr:
            self.max_y,self.max_x = self.scr.getmaxyx()
            self.rewrap()
            bottom_y = max(min((self.numLines(True)-1)-self.line,(self.max_y-2)),0)
            if self.vpos > bottom_y:
                self.vpos = bottom_y
            right_x = self.max_x-1
            if self.pos > right_x:
                self.left += self.pos-right_x
                self.pos = right_x
            self.invalidate_screen()

    def move(self):
        """ update the previous cursor position from the current """
        self.prev_pos = (self.getLine(),self.getPos())

    def prevPos(self):
        """ get the previous cursor position """
        return self.prev_pos

    def redraw(self):
        """ redraw  the editor as needed """
        try:
            if not self.scr or keymap.is_playback():
                return

            self.max_y,self.max_x = self.scr.getmaxyx()
            self.scr.keypad(1)
            if self.workfile.isChanged():
                changed = "*"
            elif self.workfile.isReadOnly():
                changed = "R"
            else:
                changed = " "

            if self.mode:
                changed = changed + " " + self.mode.name()
            filename = self.workfile.getFilename()
            if not self.showname:
                filename = ""
            status = "%d : %d : %d : %s : %s : %s"%(self.numLines(),self.getLine(),self.getPos(),changed,filename, "REC" if keymap.is_recording() else "PBK" if keymap.is_playback() else "   " )
            if len(status) < self.max_x:
                status += (self.max_x-len(status))*' '

            if self.focus:
                self.addstr(0,0,status[0:self.max_x],curses.A_REVERSE|curses.A_BOLD)
            else:
                self.addstr(0,0,status[0:self.max_x],curses.A_REVERSE)
            # if the mode is rendering then don't do the default rendering as well
            mode_redraw = False
            if self.mode:
                mode_redraw = self.mode.redraw(self)
            if not mode_redraw:
                cursor_line,cursor_pos = self.window_pos(*self.prevPos())
                y = 1
                lidx = self.line
                while lidx < self.line+(self.max_y-1):
                    try:
                        line_changed = self.isLineChanged(lidx)
                        is_cursor_line = (y == cursor_line)
                        if line_changed or is_cursor_line:
                            l = self.getContent(lidx,self.left+self.max_x,True,True)
                            if line_changed:
                                self.addstr(y,0,l[self.left:self.left+self.max_x])
                            else:
                                self.addstr(y,cursor_pos,l[self.left+cursor_pos])
                    except Exception as e:
                        pass
                    y = y + 1
                    lidx = lidx + 1
            self.draw_mark()
            self.move()
            self.draw_cursor()
            if mode_redraw:
                self.flushChanges()
        except:
            raise

    def insert(self, c ):
        """ insert a character or string at the cursor position """
        self.pushUndo()

        if self.isMark():
            self.copy_marked(True,True) # delete the marked block first then insert

        orig = self.getContent(self.getLine()).rstrip()
        offset = self.getPos()
        pad = ""
        if offset > len(orig):
            pad = " "*(offset - len(orig))
        orig = orig[0:offset] + pad + c + orig[offset:]
        insert_line = self.getLine()
        self.workfile.replaceLine(insert_line,orig)
        self.rewrap()
        self.goto(insert_line,offset+len(c))

    def delc(self):
        """ deletes one character at the cursor position """
        self.pushUndo()

        if self.isMark():
            self.copy_marked(True,True) # delete the marked block instead and return
            return

        orig = self.getContent(self.getLine())
        offset = self.getPos()
        if offset > len(orig):
            return
        elif offset == len(orig):
            next_idx = self.getLine()+1
            if next_idx > self.numLines():
                return
            next = self.getContent(next_idx)
            orig = orig[0:offset] + next
            self.workfile.replaceLine(self.getLine(),orig)
            self.workfile.deleteLine(next_idx)
        else:
            orig = orig[0:offset]+orig[offset+1:]
            self.workfile.replaceLine(self.getLine(),orig)
        self.rewrap()


    def backspace(self):
        """ delete a character at the cursor and move back one character """
        self.pushUndo()

        if self.isMark():
            self.copy_marked(True,True) # delete the marked block instead and return
            return

        line = self.getLine()
        pos = self.getPos()
        if pos:
            if pos <= self.getLength(line):
                self.goto(line,pos-1)
                self.delc()
            else:
                self.goto(line,pos-1)
        elif line:
            pos = self.getLength(line-1)-1
            self.goto(line-1,pos)
            self.delc()

    def goto(self,line, pos ):
        """ goto a line in the file and position the cursor to pos offset in the line """
        self.pushUndo()
        self.invalidate_mark()

        if line < 0:
            line = 0
        if pos < 0:
            pos = 0

        (line,pos) = self.scrPos(line,pos)

        if line >= self.line and line <= self.line+(self.max_y-2):
            self.vpos = line - self.line
        elif line < self.line:
            self.line = line
            self.vpos = 0
            self.invalidate_screen()
        elif line > self.line+(self.max_y-2):
            self.line = line - (self.max_y-2)
            self.vpos = (self.max_y-2)
            self.invalidate_screen()

        if pos >= self.left and pos < self.left+(self.max_x-1):
            self.pos = pos - self.left
        elif pos >= self.left+(self.max_x-1):
            self.left = pos-(self.max_x-1)
            self.pos = self.max_x-1
            self.invalidate_screen()
        else:
            self.left = pos
            self.pos = 0
            self.invalidate_screen()

    def endln(self):
        """ go to the end of a line """
        self.pushUndo()
        self.invalidate_mark()

        orig = self.getContent(self.getLine())
        offset = len(orig)
        self.goto(self.getLine(),offset)

    def endpg(self):
        """ go to the end of a page """
        self.pushUndo()
        self.invalidate_mark()

        ldisp = (self.numLines(True)-1)-self.line
        self.vpos = min(self.max_y-2,ldisp)

    def endfile(self):
        """ go to the end of the file """
        self.pushUndo()

        ldisp = (self.numLines(True)-1)-self.line
        if ldisp < self.max_y-2:
            return
        self.line = (self.numLines(True)-1) - (self.max_y-2)
        self.vpos = min(self.max_y-2,ldisp)
        self.invalidate_screen()

    def end(self):
        """ once go to end of line, twice end of page, thrice end of file """
        self.pushUndo()

        if self.cmd_id == cmd_names.CMD_END and self.prev_cmd == cmd_names.CMD_END:
            self.end_count += 1
            self.end_count = self.end_count % 3
        else:
            self.end_count = 0

        if self.end_count == 0:
            self.endln()
        elif self.end_count == 1:
            self.endpg()
            self.endln()
        elif self.end_count == 2:
            self.endfile()
            self.endln()

    def home(self):
        """ once to to start of line, twice start of page, thrice start of file """
        self.pushUndo()
        self.invalidate_mark()

        if self.cmd_id == cmd_names.CMD_HOME and self.prev_cmd == cmd_names.CMD_HOME:
            self.home_count += 1
            self.home_count = self.home_count % 3
        else:
            self.home_count = 0

        if self.home_count == 0:
            self.goto(self.getLine(),0)
        elif self.home_count == 1:
            self.vpos = 0
        elif self.home_count == 2:
            self.line = 0
            self.invalidate_screen()

    def pageup(self):
        """ go back one page in the file """
        self.pushUndo()
        self.invalidate_mark()

        offset = self.line - (self.max_y-2)
        if offset < 0:
            offset = 0
        self.line = offset
        self.invalidate_screen()


    def pagedown(self):
        """ go forward one page in the file """
        self.pushUndo()
        self.invalidate_mark()

        offset = self.line + (self.max_y-2)
        if offset > self.numLines(True)-1:
            return
        self.line = offset
        ldisp = (self.numLines(True)-1)-self.line
        if self.vpos > ldisp:
            self.vpos = ldisp
        self.invalidate_screen()


    def cup(self):
        """ go back one line in the file """
        self.pushUndo()
        self.invalidate_mark()

        if self.vpos:
            self.vpos -= 1
        elif self.line:
            self.line -= 1
            self.invalidate_screen()

        self.goto(self.getLine(),self.getPos())

    def cdown(self,rept = 1):
        """ go forward one or rept lines in the file """
        self.pushUndo()
        self.invalidate_mark()

        while rept:
            if self.vpos < min((self.numLines(True)-1)-self.line,(self.max_y-2)):
                self.vpos += 1
            elif self.line <= self.numLines(True)-self.max_y:
                self.line += 1
                self.invalidate_screen()
            rept = rept - 1

        self.goto(self.getLine(),self.getPos())

    def prev_word( self ):
        """ scan left until you get to the previous word """
        self.pushUndo()
        orig = self.getContent(self.getLine()).rstrip()

        pos = self.getPos()
        if pos >= len(orig):
            pos = len(orig)-1
        if pos and  pos < len(orig):
            pos -= 1
            while pos and orig[pos] == ' ':
                pos -= 1
            while pos and orig[pos-1] != ' ':
                pos -= 1
        elif pos >= len(orig):
            pos = len(orig)
        else:
            pos = 0
        self.goto(self.getLine(),pos)

    def next_word( self ):
        """ scan left until you get to the previous word """
        self.pushUndo()
        orig = self.getContent(self.getLine()).rstrip()

        pos = self.getPos()
        if pos < len(orig):
            if orig[pos] == ' ':
                while pos < len(orig) and orig[pos] == ' ':
                    pos += 1
            else:
                while pos < len(orig) and orig[pos] != ' ':
                    pos += 1
                while pos < len(orig) and orig[pos] == ' ':
                    pos += 1
        else:
            pos = len(orig)
        self.goto(self.getLine(),pos)


    def cleft(self,rept = 1):
        """ go back one or rept characters in the current line """
        self.pushUndo()

        pos = self.getPos()
        line = self.getLine()
        if pos >= rept:
            self.goto(line,pos-rept)
            return

        if self.wrap:
            if line:
                offset = self.getLength(line-1)-(rept-pos)
                self.goto(line-1,offset)
        else:
            self.goto(line,0)

    def cright(self,rept = 1):
        """ go forward one or rept characters in the current line """
        self.pushUndo()

        pos = self.getPos()
        line = self.getLine()
        if self.wrap:
            llen = self.getLength(line)
            if pos + rept < llen:
                self.goto(line,pos+rept)
                return
            if line < self.numLines()-1:
                self.goto(line+1,llen-(pos+rept))
                return
            self.goto(line,llen)
        else:
            self.goto(line,pos+rept)

    def scroll_left(self):
        """ scroll the page left without moving the current cursor position """
        self.pushUndo()
        if self.left:
            self.left -= 1
            self.invalidate_screen()

    def scroll_right(self):
        """ scroll the page right without moving the current cursor position """
        self.pushUndo()
        self.left += 1
        self.invalidate_screen()

    def searchagain(self):
        """ repeat the previous search if any """
        self.pushUndo()
        self.invalidate_mark()
        if self.isMark():
            if not self.last_search_dir:
                self.goto(self.mark_line_start,self.mark_pos_start)
            self.mark_span()
        if self.last_search:
            return self.search(self.last_search,self.last_search_dir,True)
        else:
            return False

    def search(self, pattern, down = True, next = True):
        """ search for a regular expression forward or back if next is set then skip one before matching """
        self.pushUndo()
        self.invalidate_mark()

        self.last_search = pattern
        self.last_search_dir = down
        first_line = self.getLine()
        line = first_line
        if down:
            while line < self.numLines():
                content = self.getContent(line)
                if line == first_line:
                    content = content[self.getPos():]
                    offset = self.getPos()
                else:
                    offset = 0
                match = None
                try:
                    match = re.search(pattern,content)
                except:
                    pass
                if match:
                    if self.isMark():
                        self.mark_span()
                    self.goto(line,match.start()+offset)
                    self.mark_span()
                    self.goto(line,match.end()+offset-1)
                    self.search_mark = True
                    return True
                line += 1
        else:
            while line >= 0:
                content = self.getContent(line)
                if line == first_line:
                    content = content[:self.getPos()]
                match = None
                try:
                    match = re.search(pattern,content)
                except:
                    pass
                last_match = None
                offset = 0
                while match:
                    last_match = match
                    last_offset = offset
                    offset += match.end()
                    match = re.search(pattern,content[offset:])
                if last_match:
                    if self.isMark():
                        self.mark_span()
                    self.goto(line,last_match.start()+last_offset)
                    self.mark_span()
                    self.goto(line,last_match.end()+last_offset-1)
                    self.search_mark = True
                    return True
                line -= 1
        return False

    def invalidate_mark(self):
        """ touch the marked lines so that they'll redraw when we change the shape of the mark or do a copy or paste """
        if self.isMark():
            self.workfile.touchLine(self.mark_line_start, self.getLine())
        if self.search_mark:
            self.span_mark = False
            self.search_mark = False

    def invalidate_all(self):
        """ touch all the lines in the file so everything will redraw """
        self.workfile.touchLine(0,self.workfile.numLines())

    def invalidate_screen(self):
        """ touch all the lines on the screen so everything will redraw """
        line,pos = self.filePos(self.line,self.left)
        self.workfile.touchLine(line,line+self.max_y)

    def invalidate_after_cursor(self):
        """ touch all the lines from the current position to the end of the screen """
        line,pos = self.filePos(self.line,self.left)
        self.workfile.touchLine(self.getLine(),line+self.max_y)

    def has_changes(self):
        """ return true if there are any pending changes """
        return self.workfile.hasChanges(self)

    def mark_span(self):
        """ mark a span of characters that can start and end in the middle of a line """
        self.pushUndo()

        self.invalidate_mark()
        if not self.span_mark:
            self.span_mark = True
            self.rect_mark = False
            self.line_mark = False
            self.mark_pos_start = self.getPos()
            self.mark_line_start = self.getLine()
        else:
            self.span_mark = False

    def mark_rect(self):
        """ mark a rectangular or column selection across lines """

        # no column cut in wrapped mode, it doesn't make sense
        if self.wrap:
            return

        self.pushUndo()

        self.invalidate_mark()
        if not self.rect_mark:
            self.rect_mark = True
            self.span_mark = False
            self.line_mark = False
            self.mark_pos_start = self.getPos()
            self.mark_line_start = self.getLine()
        else:
            self.rect_mark = False

    def mark_lines(self):
        """ mark whole lines """
        self.pushUndo()

        self.invalidate_mark()
        if not self.line_mark:
            self.line_mark = True
            self.span_mark = False
            self.rect_mark = False
            self.mark_pos_start = 0
            self.mark_line_start = self.getLine()
        else:
            self.line_mark = False

    def get_marked(self, delete=False, nocopy = False):
        """ returns marked text as tuple ( cliptype, [list of clipped] ) returns () if no mark """
        if not self.isMark():
            return ()

        self.pushUndo()

        if delete:
            self.invalidate_screen()

        mark_pos_start = self.mark_pos_start
        mark_line_start = self.mark_line_start
        mark_pos_end = self.getPos()
        mark_line_end = self.getLine()

        if mark_line_start > mark_line_end:
            mark = mark_line_start
            mark_line_start = mark_line_end
            mark_line_end = mark
            mark = mark_pos_start
            mark_pos_start = mark_pos_end
            mark_pos_end = mark
        elif mark_line_start == mark_line_end and mark_pos_start > mark_pos_end:
            mark = mark_pos_start
            mark_pos_start = mark_pos_end
            mark_pos_end = mark

        clip = []
        clip_type = clipboard.LINE_CLIP

        line_idx = mark_line_start
        if self.line_mark:
            if not nocopy:
                clip_type = clipboard.LINE_CLIP
                while line_idx <= mark_line_end:
                    clip.append(self.getContent(line_idx))
                    line_idx += 1
            if delete:
                line_idx = mark_line_start
                while line_idx <= mark_line_end:
                    self.workfile.deleteLine(mark_line_start)
                    line_idx += 1
                self.rewrap()
        elif self.span_mark:
            if not nocopy:
                clip_type = clipboard.SPAN_CLIP
                if line_idx == mark_line_end:
                    clip.append(self.getContent(line_idx)[mark_pos_start:mark_pos_end+1])
                else:
                    clip.append(self.getContent(line_idx)[mark_pos_start:]+'\n')
                    line_idx += 1
                    while line_idx < mark_line_end:
                        clip.append(self.getContent(line_idx)+'\n')
                        line_idx += 1
                    clip.append(self.getContent(line_idx)[0:mark_pos_end+1])
            if delete:
                line_idx = mark_line_start
                if line_idx == mark_line_end:
                    orig = self.getContent(line_idx)
                    orig = orig[0:mark_pos_start] + orig[mark_pos_end+1:]
                    self.workfile.replaceLine(line_idx,orig)
                    self.rewrap()
                else:
                    first_line = self.getContent(mark_line_start)
                    last_line = self.getContent(mark_line_end)
                    while line_idx <= mark_line_end:
                        self.workfile.deleteLine(mark_line_start)
                        line_idx += 1
                    self.workfile.insertLine(mark_line_start,first_line[0:mark_pos_start] + last_line[mark_pos_end+1:])
                    self.rewrap()
        elif self.rect_mark:
            if not nocopy:
                clip_type = clipboard.RECT_CLIP
                while line_idx <= mark_line_end:
                    clip.append(self.getContent(line_idx,mark_pos_end,True)[mark_pos_start:mark_pos_end+1])
                    line_idx += 1
            if delete:
                line_idx = mark_line_start
                while line_idx <= mark_line_end:
                    orig = self.getContent(line_idx,mark_pos_end,True)
                    self.workfile.replaceLine(line_idx,orig[0:mark_pos_start]+orig[mark_pos_end+1:])
                    line_idx += 1

        # sync the x clipboard
        self.transfer_clipboard()

        if self.line_mark:
            self.line_mark = False
        if self.rect_mark:
            self.rect_mark = False
        if self.span_mark:
            self.span_mark = False

        if delete:
            self.goto(mark_line_start,mark_pos_start)

        self.invalidate_screen()

        return (clip_type, clip)

    def copy_marked(self,delete=False,nocopy = False):
        """ copy the marked text to the clipboard, delete== True means cut, nocopy == True will just delete """
        if not self.isMark():
            return

        self.pushUndo()

        cp = self.get_marked(delete,nocopy)
        if cp:
            clipboard.clip_type = cp[0]
            clipboard.clip = cp[1]


    def paste(self):
        """ paste the current clip at the cursor position """
        if clipboard.clip:
            # no column cut or paste when in wrap mode
            if self.wrap and clipboard.clip_type == clipboard.RECT_CLIP:
                return
            self.pushUndo()

            if clipboard.clip_type == clipboard.LINE_CLIP:
                target = self.getLine()
                pos = self.getPos()
                for line in clipboard.clip:
                    self.workfile.insertLine(target,line)
                    target += 1
                self.rewrap()
                self.goto(target,pos)
            elif clipboard.clip_type == clipboard.SPAN_CLIP:
                target = self.getLine()
                pos = self.getPos()
                idx = 0
                for line in clipboard.clip:
                    orig = self.getContent(target,pos,True)
                    if (not line) or line[-1] == '\n':
                        line = line.rstrip()
                        if not idx:
                            self.workfile.replaceLine(target,orig[0:pos]+line)
                            self.workfile.insertLine(target+1,orig[pos:])
                            self.rewrap()
                            self.goto(target, pos+len(line))
                            target += 1
                        else:
                            self.workfile.insertLine(target,line)
                            self.rewrap()
                            self.goto(target, len(line))
                            target += 1
                    else:
                        if not idx:
                            self.workfile.replaceLine(target,orig[0:pos]+line+orig[pos:])
                            self.rewrap()
                            self.goto(target, pos+len(line))
                        else:
                            self.workfile.replaceLine(target,line+orig)
                            self.rewrap()
                            self.goto(target, len(line))
                    idx += 1
            elif clipboard.clip_type == clipboard.RECT_CLIP:
                target = self.getLine()
                pos = self.getPos()
                for line in clipboard.clip:
                    orig = self.getContent(target,self.getPos(),True)
                    self.workfile.replaceLine(target,orig[0:self.getPos()]+line+orig[self.getPos():])
                    target += 1
                self.rewrap()
                self.goto(target,pos)

    def cr(self):
        """ insert a carriage return, split the current line at cursor """
        self.pushUndo()
        orig = self.getContent(self.getLine(),self.getPos(),True)
        self.workfile.replaceLine(self.getLine(),orig[0:self.getPos()])
        self.workfile.insertLine(self.getLine()+1,orig[self.getPos():])
        self.rewrap()
        self.goto(self.getLine()+1,0)

    def instab(self, line, pos, move_cursor = True ):
        """ insert a tab at a line and position """
        orig = self.getContent(line,pos,True)
        stop = self.workfile.get_tab_stop(pos)
        orig = orig[0:pos] + ' '*(stop-(pos)) + orig[pos:]
        self.workfile.replaceLine(line,orig)
        self.rewrap()
        if move_cursor:
            self.goto(line,stop)

    def tab(self):
        """ tab in the correct distance to the next tab stop """
        self.pushUndo()
        if self.isMark() and self.line_mark:
            oline = self.getLine()
            opos = self.getPos()
            mark_line_start = self.mark_line_start
            mark_line_end = oline
            if mark_line_start > mark_line_end:
                mark = mark_line_start
                mark_line_start = mark_line_end
                mark_line_end = mark
            while mark_line_start <= mark_line_end:
                self.instab( mark_line_start, 0, False )
                mark_line_start += 1
            self.goto(oline,opos)
        else:
            self.instab( self.getLine(), self.getPos() )

    def deltab(self, line, pos, move_cursor = True ):
        """ remove a tab from the line at position provided optionally move the cursor """
        orig = self.getContent(line,pos+1,True)
        idx = pos
        start = 0
        stop = 0
        while idx:
            while idx and orig[idx] != ' ':
                idx -= 1
            start = idx
            stop = self.workfile.get_tab_stop(idx,True)
            while idx and idx >= stop:
                if orig[idx] != ' ':
                    break
                idx -= 1
            else:
                if start > stop:
                    break
        if start > stop:
            orig = orig[0:stop]+orig[start+1:]
            self.workfile.replaceLine(line,orig)
            self.rewrap()
            if move_cursor:
                self.goto(line,stop)

    def btab(self):
        """ remove white space to the previous tab stop, or shift the line back to the previous tab stop """
        self.pushUndo()
        if self.isMark() and self.line_mark:
            mark_line_start = self.mark_line_start
            mark_line_end = self.getLine()
            if mark_line_start > mark_line_end:
                mark = mark_line_start
                mark_line_start = mark_line_end
                mark_line_end = mark
            while mark_line_start <= mark_line_end:
                self.deltab( mark_line_start, self.workfile.get_tab_stop(0), False )
                mark_line_start += 1
        else:
            self.deltab( self.getLine(), self.getPos() )

    def prmt_goto(self):
        """ prompt for a line to go to and go there """
        self.invalidate_screen()
        goto_line = prompt(self.parent,"Goto","Enter line number 0-%d :"%(self.numLines()-1),10,name="goto")
        if goto_line:
            self.goto(int(goto_line),self.getPos())

    def saveas(self):
        """ open the file dialog and enter or point to a file and then save this buffer to that path """
        f = file_dialog.FileDialog(self.parent,"Save file as")
        choices = f.main()
        if choices and choices["file"]:
            self.workfile.save(os.path.join(choices["dir"],choices["file"]))
        self.undo_mgr.flush_undo()
        self.invalidate_all()
        gc.collect()

    def save(self):
        """ save the current buffer """
        if self.workfile.isModifiedOnDisk():
            if not confirm(self.parent, "File has changed on disk, overwrite?"):
                self.invalidate_screen()
                self.redraw()
                return
        self.workfile.save()
        self.undo_mgr.flush_undo()
        self.goto(self.getLine(),self.getPos())
        self.invalidate_all()
        self.redraw()
        gc.collect()

    def prmt_search(self,down=True):
        """ prompt for a search string then search for it and either put up a message that it was not found or position the cursor to the occurrance """
        self.invalidate_screen()
        if down:
            title = "Search Forward"
        else:
            title = "Search Backward"
        pattern = prompt(self.parent,title,"Pattern: ",-1,name="search")
        if pattern:
            if not self.search(pattern,down):
                message(self.parent,"Search","Pattern not found.")

    def prmt_replace(self):
        """ prompt for search pattern and replacement string, then confirm replacment or replace all for the occurrences until no more are found """
        (pattern,rep) = replace(self.parent)
        if pattern and rep:
            found = self.search(pattern)
            replace_all = False
            do_replace = False
            while found:
                self.redraw()
                self.scr.refresh()

                if not replace_all:
                    answer = confirm_replace(self.parent)
                    self.invalidate_screen()
                    if answer == 1:
                        do_replace = True
                    elif answer == 2:
                        do_replace = False
                    elif answer == 3:
                        replace_all = True
                    elif answer == 4:
                        message(self.parent,"Canceled","Replace canceled.")
                        return

                if do_replace or replace_all:
                    self.insert(rep)

                found = self.searchagain()
            else:
                message(self.parent,"Replace","Pattern not found.")
        self.invalidate_screen()

    def prmt_searchagain(self):
        """ search again and put up a message if no more are found """
        self.invalidate_screen()
        if not self.searchagain():
            if self.isMark():
                self.mark_span()
            message(self.parent,"Search","Pattern not found.")

    def transfer_clipboard(self, from_xclip = False):
        """ use xclip to transfer out clipboard to x or vice/versa """
        if os.path.exists("/dev/clipboard"):
            if from_xclip:
                clipboard.clip = []
                clipboard.clip_type = clipboard.SPAN_CLIP
                for line in open("/dev/clipboard","r",buffering=1,encoding="utf-8"):
                    clipboard.clip.append(line)
            else:
                cld = open("/dev/clipboard","w",buffering=0,encoding="utf-8")
                for line in clipboard.clip:
                    cld.write(line)
                cld.close()
        elif os.path.exists("/usr/bin/xclip"):
            cmd = [ "xclip", ]
            if from_xclip:
                cmd += ["-out","-selection","clipboard"]
            else:
                cmd += ["-in","-selection","clipboard"]

            try:
                proc = subprocess.Popen( cmd, encoding="utf-8", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
                if from_xclip:
                    clipboard.clip = []
                    clipboard.clip_type = clipboard.SPAN_CLIP
                    for l in proc.stdout:
                        clipboard.clip.append(l)
                else:
                    for l in clipboard.clip:
                        print(l.rstrip(), file=proc.stdin)
                proc.stdout.close()
                proc.stdin.close()
                proc.stderr.close()
                proc.wait()
            except:
                pass

    def toggle_wrap(self):
        """ toggle wrapping for this editor """
        # don't toggle wrapping while we're marking a rectangle
        if self.rect_mark:
            return
        self.pushUndo()
        oline = self.getLine()
        opos = self.getPos()
        self.wrap = not self.wrap
        self.rewrap(True)
        self.invalidate_all()
        self.goto(oline,opos)

    def handle(self,ch):
        """ main character handler dispatches keystrokes to execute editor commands returns characters meant to be processed
            by containing manager or dialog """

        self.prev_cmd = self.cmd_id
        if isinstance(ch,int):
            self.cmd_id, ret = keymap.mapkey( self.scr, keymap.keymap_editor, ch )
        else:
            self.cmd_id, ret = keymap.mapseq( keymap.keymap_editor, ch )
        if extension_manager.is_extension(self.cmd_id):
            if not extension_manager.invoke_extension( self.cmd_id, self, ch ):
                return ret

        if self.cmd_id == cmd_names.CMD_RETURNKEY:
            if ret in [keytab.KEYTAB_NOKEY,keytab.KEYTAB_REFRESH,keytab.KEYTAB_RESIZE]:
                self.cmd_id = self.prev_cmd
        elif self.cmd_id == cmd_names.CMD_INSERT:
            self.insert(chr(ret))
            ret = keytab.KEYTAB_NOKEY
        elif self.cmd_id == cmd_names.CMD_MARKSPAN:
            self.mark_span()
        elif self.cmd_id == cmd_names.CMD_MARKRECT:
            self.mark_rect()
        elif self.cmd_id == cmd_names.CMD_COPYMARKED:
            self.copy_marked()
        elif self.cmd_id == cmd_names.CMD_PRMTGOTO:
            self.prmt_goto()
        elif self.cmd_id == cmd_names.CMD_BACKSPACE:
            self.backspace()
        elif self.cmd_id == cmd_names.CMD_FILENAME:
            if self.getFilename():
                message(self.parent,"Filename",self.getFilename())
        elif self.cmd_id == cmd_names.CMD_CUTMARKED:
            self.copy_marked(True)
        elif self.cmd_id == cmd_names.CMD_PASTE:
            self.paste()
        elif self.cmd_id == cmd_names.CMD_MARKLINES:
            self.mark_lines()
        elif self.cmd_id == cmd_names.CMD_CR:
            self.cr()
        elif self.cmd_id == cmd_names.CMD_TAB:
            self.tab()
        elif self.cmd_id == cmd_names.CMD_SAVE:
            self.save()
        elif self.cmd_id == cmd_names.CMD_SAVEAS:
            self.saveas()
        elif self.cmd_id == cmd_names.CMD_UNDO:
            self.undo()
        elif self.cmd_id == cmd_names.CMD_TOGGLEWRAP:
            self.toggle_wrap()
        elif self.cmd_id == cmd_names.CMD_MARKCOPYLINE:
            if not self.isMark():
                self.mark_lines()
            self.copy_marked()
        elif self.cmd_id == cmd_names.CMD_MARKCUTLINE:
            if not self.isMark():
                self.mark_lines()
            self.copy_marked(True)
        elif self.cmd_id == cmd_names.CMD_BTAB:
            self.btab()
        elif self.cmd_id == cmd_names.CMD_PREVWORD:
            self.prev_word()
        elif self.cmd_id == cmd_names.CMD_NEXTWORD:
            self.next_word()
        elif self.cmd_id == cmd_names.CMD_HOME1:
            self.pushUndo()
            self.prev_cmd = cmd_names.CMD_HOME
            self.cmd_id = cmd_names.CMD_HOME
            self.home_count = 0
            self.home()
            self.home()
            self.home()
        elif self.cmd_id == cmd_names.CMD_END1:
            self.pushUndo()
            self.prev_cmd = cmd_names.CMD_END
            self.cmd_id = cmd_names.CMD_END
            self.end_count = 0
            self.end()
            self.end()
            self.end()
        elif self.cmd_id == cmd_names.CMD_UP:
            self.cup()
        elif self.cmd_id == cmd_names.CMD_DOWN:
            self.cdown()
        elif self.cmd_id == cmd_names.CMD_LEFT:
            self.cleft()
        elif self.cmd_id == cmd_names.CMD_RIGHT:
            self.cright()
        elif self.cmd_id == cmd_names.CMD_DELC:
            self.delc()
        elif self.cmd_id == cmd_names.CMD_HOME:
            self.home()
        elif self.cmd_id == cmd_names.CMD_END:
            self.end()
        elif self.cmd_id == cmd_names.CMD_PAGEUP:
            self.pageup()
        elif self.cmd_id == cmd_names.CMD_PAGEDOWN:
            self.pagedown()
        elif self.cmd_id == cmd_names.CMD_PRMTSEARCH:
            self.prmt_search()
        elif self.cmd_id == cmd_names.CMD_PRMTREPLACE:
            self.prmt_replace()
        elif self.cmd_id == cmd_names.CMD_TRANSFERCLIPIN:
            self.transfer_clipboard(False)
        elif self.cmd_id == cmd_names.CMD_TRANSFERCLIPOUT:
            self.transfer_clipboard(True)
        elif self.cmd_id == cmd_names.CMD_PRMTSEARCHBACK:
            self.prmt_search(False)
        elif self.cmd_id == cmd_names.CMD_SEARCHAGAIN:
            self.prmt_searchagain()
        elif self.cmd_id == cmd_names.CMD_TOGGLERECORD:
            keymap.toggle_recording()
        elif self.cmd_id == cmd_names.CMD_PLAYBACK:
            keymap.start_playback()

        return ret

    def main(self,blocking = True, start_ch = None):
        """ main driver loop for editor, if blocking = False exits on each keystroke to allow embedding,
            start_ch is a character read externally that hould be processed on startup """
        curses.curs_set(0)
        self.rewrap()
        self.scr.nodelay(1)
        self.scr.notimeout(0)
        self.scr.timeout(0)
        while (1):
            if not self.scr:
                return 27

            if not self.mode:
                for m in Editor.modes:
                    if m.detect_mode(self):
                        self.mode = m
                        self.getWorkfile().set_tabs(m.get_tabs(self))
                        break
                else:
                    self.mode = None

            self.redraw()

            if start_ch:
                ch = start_ch
                start_ch = None
            else:
                ch = keymap.getch(self.scr)
            try:
                self.undo_mgr.new_transaction()
                if self.mode:
                    ch = self.mode.handle(self,ch)
                modref = self.workfile.getModref()
                ret_seq = self.handle(ch)
                if self.wrap and modref != self.workfile.getModref():
                    self.rewrap()
                if ret_seq or not blocking:
                    return ret_seq
            except ReadOnlyError as e:
                message(self.parent,"Read Only File Error","Changes not allowed.")
                if not blocking:
                    return keytab.KEYTAB_REFRESH

class StreamThread:
    """ Thread to read from a stream blocking as needed adding lines to the owning EditFile object """
    def __init__(self, ef, stream ):
        self.ef = ef
        self.stream = stream
        self.thread = None
        self.read_worker_stop = False

    def __del__( self ):
        self.stop_stream()

    def start_stream( self ):
        self.thread = threading.Thread(target = self.read_worker)
        self.thread.start()

    def wait(self):
        if self.thread:
            self.thread.join()

    def stop_stream( self ):
        self.read_worker_stop = True
        if self.thread and self.thread.is_alive():
            self.thread.join()
        if self.stream:
            self.stream.close()
        self.stream = None
        self.thread = None
        self.read_worker_stop = False

    def read_worker( self ):
        pos = 0
        lidx = 0
        while not self.read_worker_stop:
            line = self.stream.readline()
            if not line:
                break
            try:
                self.ef.lines_lock.acquire()
                self.ef.modref += 1
                self.ef.working.seek(0,2)
                self.ef.working.write(line)
                line = line.rstrip()
                self.ef.lines.append(FileLine(self.ef,pos,len(self.ef.expand_tabs(line))))
                if self.ef.change_mgr:
                    self.ef.change_mgr.changed(lidx,lidx)
                pos = self.ef.working.tell()
                lidx += 1
            finally:
                self.ef.lines_lock.release()
                time.sleep( 0 )

        try:
            self.ef.lines_lock.acquire()

            while len(self.ef.lines) and not self.ef.lines[-1].getContent().strip():
                del self.ef.lines[-1]
            if not len(self.ef.lines):
                self.ef.lines.append(MemLine(""))
        finally:
            self.ef.lines_lock.release()

        self.ef.changed = False
        self.ef.modref = 0
        if self.stream:
            self.stream.close()
            self.stream = None
        self.thread = None
        self.read_worker_stop = False

class StreamFile(EditFile):
    """ Class reads a stream to the end and writes it to a temp file which
    is opened and loaded read only, used for capturing the output of
    shell commands to a read-only editor """

    def __init__(self,name,stream,wait=False):
        """ takes name which is a display name for this stream, stream is the input stream to read """
        self.stream = stream
        self.stream_thread = None
        self.lines_lock = threading.Lock()
        self.wait = wait
        # store the filename
        self.filename = name
        # the root of the backup directory
        self.backuproot = EditFile.default_backuproot
        # set the default tab stops
        self.tabs = [ 4, 8 ]
        # set the changed flag to false
        self.changed = False
        # read only flag
        self.readonly = EditFile.default_readonly
        # undo manager
        self.undo_mgr = undo.UndoManager()
        # change manager
        self.change_mgr = changes.ChangeManager()
        # modification reference incremented for each change
        self.modref = 0
        # the file object
        self.working = None
        # the lines in this file
        self.lines = []
        # load the file
        self.load()

    def __del__(self):
        """ clean up stream thread and stream """
        self.stream_thread = None
        EditFile.__del__(self)

    def open(self):
        """ override of the open method, starts a thread that reads the stream into a tempfile which then becomes the file for the editor """
        if self.stream and not self.working:
            self.working = tempfile.NamedTemporaryFile(mode="w+")
            self.setReadOnly(True)
            self.stream_thread = StreamThread(self,self.stream)
            self.stream_thread.start_stream()
            if self.wait:
                self.stream_thread.wait()
                self.stream_thread = None
            return
        else:
            EditFile.open(self)

    def load(self):
        if self.stream and not self.working:
            self.open()
            return
        else:
            EditFile.load()

    def close(self):
        """ override of close method, make sure the stream gets closed """
        if self.stream_thread:
            self.stream_thread.stop_stream()
            self.stream = None
        elif self.stream:
            self.stream.close()
            self.stream = None
        EditFile.close(self)

    def set_tabs(self, tabs):
        try:
            self.lines_lock.acquire()
            EditFile.set_tabs(self, tabs)
        finally:
            self.lines_lock.release()

    def numLines(self):
        try:
            self.lines_lock.acquire()
            return EditFile.numLines(self)
        finally:
            self.lines_lock.release()

    def length(self,line):
        try:
            self.lines_lock.acquire()
            return EditFile.length(self,line)
        finally:
            self.lines_lock.release()

    def getLine(self, line, pad = 0, trim = False ):
        try:
            self.lines_lock.acquire()
            return EditFile.getLine(self,line,pad,trim)
        finally:
            self.lines_lock.release()

    def getLines(self, line_start = 0, line_end = -1 ):
        try:
            self.lines_lock.acquire()
            return EditFile.getLines(self,line_start,line_end)
        finally:
            self.lines_lock.release()


class StreamEditor(Editor):
    """ this is a read only editor that wraps a stream it has a select
        option for use when embedding in a control to select lines
        from the stream """
    def __init__(self, par, scr, name, stream, select = False, line_re = None, follow = False, wait = False, workfile=None ):
        """ takes parent curses screen, screen to render to, name for
            stream, stream to read in, and select to indicate if
            line selection is requested """
        self.select = select
        self.line_re = line_re
        self.follow = follow
        self.wait = wait
        self.o_nlines = 0
        if workfile:
            self.sfile = workfile
        else:
            self.sfile = StreamFile(name,stream,self.wait)

        Editor.__init__(self, par, scr, self.sfile.getFilename(), self.sfile)

    def __copy__(self):
        """ override to just copy the editor state and not the underlying file object """
        result = StreamEditor(self.parent,self.scr,None,None,self.select, self.line_re, self.follow, self.wait, self.workfile)
        result.o_nlines = 0
        result.line = self.line
        result.pos = self.pos
        result.vpos = self.vpos
        result.left = self.left
        result.prev_cmd = self.prev_cmd
        result.cmd_id = self.cmd_id
        result.home_count = self.home_count
        result.end_count = self.end_count
        result.line_mark = self.line_mark
        result.span_mark = self.span_mark
        result.rect_mark = self.rect_mark
        result.search_mark = self.search_mark
        result.mark_pos_start = self.mark_pos_start
        result.mark_line_start = self.mark_line_start
        result.last_search = self.last_search
        result.last_search_dir = self.last_search_dir
        result.mode = self.mode
        result.wrap_lines = copy.copy(self.wrap_lines)
        result.unwrap_lines = copy.copy(self.unwrap_lines)
        result.wrap_modref = self.wrap_modref
        result.wrap_width = self.wrap_width
        result.show_cursor = self.show_cursor
        result.focus = self.focus
        result.prev_pos = copy.copy(self.prev_pos)
        return result

    def __del__(self):
        """ clean up the StreamFile """
        self.sfile = None

    def close(self):
        """ close and shut down the stream file """
        if self.sfile:
            self.sfile.close()
            self.sfile = None

    def getFilename(self):
        """ override getFilename so we can return None to indicate no file stuff should be done """
        return None

    def handle(self,ch):
        """ override normal keystroke handling if in select mode
        and move about doing selection and return on enter """

        if self.follow:
            nlines = self.numLines()
            if self.o_nlines != nlines:
                self.endfile()
                self.o_nlines = nlines

        if ch in keymap.keydef_map and keymap.keydef_map[ch][-1] == keytab.KEYTAB_CTRLF:
            self.follow = not self.follow
            return keytab.KEYTAB_NOKEY
        elif not self.select:
            return Editor.handle(self,ch)

        o_line = self.getLine()

        if isinstance(ch,int):
            ch = keymap.get_keyseq( self.scr, ch )
        ret_ch = keytab.KEYTAB_NOKEY
        direction = 0

        if ch in [keytab.KEYTAB_F02,keytab.KEYTAB_F04,keytab.KEYTAB_F10,keytab.KEYTAB_F01,keytab.KEYTAB_RESIZE, keytab.KEYTAB_CR, keytab.KEYTAB_BTAB, keytab.KEYTAB_TAB, keytab.KEYTAB_ESC]:
            ret_ch = ch
        elif ch == keytab.KEYTAB_UP:
            self.cup()
            direction = -1
        elif ch == keytab.KEYTAB_DOWN:
            self.cdown()
            direction = 1
        elif ch == keytab.KEYTAB_LEFT:
            self.scroll_left()
        elif ch == keytab.KEYTAB_RIGHT:
            self.scroll_right()
        elif ch == keytab.KEYTAB_BACKSPACE:
            direction = -1
            self.cup()
        elif ch == keytab.KEYTAB_HOME:
            self.pushUndo()
            self.left = 0
            self.pos = 0
            self.line = 0
            self.vpos = 0
            direction = 1
        elif ch == keytab.KEYTAB_END:
            self.endfile()
            direction = -1
        elif ch == keytab.KEYTAB_PAGEUP:
            self.pageup()
            direction = -1
        elif ch == keytab.KEYTAB_PAGEDOWN:
            self.pagedown()
            direction = 1
        elif ch == keytab.KEYTAB_F05:
            self.prmt_search()
            direction = 1
        elif ch == keytab.KEYTAB_F17: # shift f5:
            self.prmt_search(False)
            direction = -1
        elif ch == keytab.KEYTAB_F03:
            self.prmt_searchagain()
            if self.last_search_dir:
                direction = 1
            else:
                direction = -1

        if self.line_re and direction:
            if direction > 0:
                while True:
                    if re.search(self.line_re, self.getCurrentLine()):
                        self.line = self.getLine()
                        self.vpos = 0
                        break
                    line = self.getLine()
                    self.cdown()
                    if line == self.getLine():
                        self.undo_mgr.undo_transaction()
                        break
            elif direction < 0:
                while True:
                    if re.search(self.line_re, self.getCurrentLine()):
                        self.line = self.getLine()
                        self.vpos = 0
                        break
                    line = self.getLine()
                    self.cup()
                    if line == self.getLine():
                        self.undo_mgr.undo_transaction()
                        break

        if self.getLine() != o_line or not self.isMark():
            if self.isMark():
                self.mark_lines()
            self.mark_lines()

        return ret_ch

class ReadonlyEditor(Editor):
    """ editor subclass implements read only editor for viewing files """
    def __init__(self, par, scr, name, showname = True):
        """ parent curses screen, screen to render to, filename to open """
        self.showname = showname
        sfile = EditFile(name)
        sfile.setReadOnly()
        Editor.__init__(self, par, scr, name, sfile, showname)

    def getFilename(self):
        """ override getFilename so we can return None to indicate no file stuff should be done """
        if self.showname:
            return Editor.getFilename(self)
        else:
            return None

    def handle(self,ch):
        """ handle override to only do read only actions to the file """

        o_line = self.getLine()

        if isinstance(ch,int):
            ch = keymap.get_keyseq( self.scr, ch )
        ret_ch = keytab.KEYTAB_NOKEY

        if ch in [keytab.KEYTAB_F02,keytab.KEYTAB_F04,keytab.KEYTAB_F10,keytab.KEYTAB_F01,keytab.KEYTAB_RESIZE, keytab.KEYTAB_CR, keytab.KEYTAB_BTAB, keytab.KEYTAB_TAB, keytab.KEYTAB_ESC]:
            ret_ch = ch
        elif ch == keytab.KEYTAB_CTRLW: # ctrl-w (toggle wrap in readonly editor)
            self.toggle_wrap()
        elif ch == keytab.KEYTAB_UP:
            self.cup()
        elif ch == keytab.KEYTAB_DOWN:
            self.cdown()
        elif ch == keytab.KEYTAB_LEFT:
            self.scroll_left()
        elif ch == keytab.KEYTAB_RIGHT:
            self.scroll_right()
        elif ch == keytab.KEYTAB_BACKSPACE:
            self.cup()
        elif ch == keytab.KEYTAB_HOME:
            self.home()
        elif ch == keytab.KEYTAB_END:
            self.end()
        elif ch == keytab.KEYTAB_PAGEUP:
            self.pageup()
        elif ch == keytab.KEYTAB_PAGEDOWN:
            self.pagedown()
        elif ch == keytab.KEYTAB_F05:
            self.prmt_search()
        elif ch == keytab.KEYTAB_F17: # shift f5:
            self.prmt_search(False)
        elif ch == keytab.KEYTAB_F03:
            self.prmt_searchagain()

        if self.getLine() != o_line or not self.isMark():
            if self.isMark():
                self.mark_lines()
            self.mark_lines()

        return ret_ch

def main(stdscr):
    """ test driver for the editor """
    open("test.txt","w").write("""This is line one
    This is line two
\tThis is line three
\t\tThis is line four
    This is line five
    aaaaaaaaaaaaaaaa
    bbbbbbbbbbbbbbbb
    cccccccccccccccc
    dddddddddddddddd
    eeeeeeeeeeeeeeee
    ffffffffffffffff
    gggggggggggggggg
    hhhhhhhhhhhhhhhh
    iiiiiiiiiiiiiiii
    jjjjjjjjjjjjjjjj
    kkkkkkkkkkkkkkkk
    llllllllllllllll
    mmmmmmmmmmmmmmmm
Aa23456789b23456789c23456789d23456789d23456789e23456789f23456789g23456789h23456789A
Ba23456789b23456789c23456789d23456789d23456789e23456789f23456789g23456789h23456789B
Ca23456789b23456789c23456789d23456789d23456789e23456789f23456789g23456789h23456789C
Da23456789b23456789c23456789d23456789d23456789e23456789f23456789g23456789h23456789D
Ea23456789b23456789c23456789d23456789d23456789e23456789f23456789g23456789h23456789E
Fa23456789b23456789c23456789d23456789d23456789e23456789f23456789g23456789h23456789F
Ga23456789b23456789c23456789d23456789d23456789e23456789f23456789g23456789h23456789G
    asdkfjlkjaslkfjj
    asfdkljsa;dfkljas;dflksajdf;laskdfjas;kfdljas;dlkfjas safkjsf;kljsf
    askdfj;sa asdkfj as;lkfjs fksadfjs;lkfj asdjdfkljsaf
    al;slkfdj asdlkfj asdlfkj asldkfj asdf;lkj as;lkdfj
    as;ldkfj adsflk asdlfkj aslfkj
    aslfj adflkj alkjasdflk aksdfj
    asdflj asldkfj asdflkj asldkfj aslkfj
    aslfdkjalksfjd aslfjd asdlfkj ;askfdj alskdfj
    asldfkj ksaldfj slkdfj kasdfj
    asdflkja aljkjjlk asdkfljlaksfjd aslkdjf alskdjf alskdfj
    aslfkj alkjdfslkj aldkfj alskdfj asldkfj
    asldfj aslkdfj alskdfj alkdfj aslkdfj aslkdfj""")

    e1 = Editor(stdscr, curses.newwin(0,0),"test.txt",None,True,True)
    e1.main()

if __name__ == '__main__':
    curses.wrapper(main)
