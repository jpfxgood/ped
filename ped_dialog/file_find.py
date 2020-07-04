# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement search for files and search for pattern in files used in the ped editor """
import curses
import curses.ascii
import sys
import os
import tempfile
from ped_dialog import dialog
from ped_core import editor_common
import re
import traceback
from array import array
from ped_dialog.message_dialog import message
from ped_dialog.stream_select import StreamSelectComponent
from ped_dialog.file_browse import FileBrowseComponent
from ped_core import keytab

def sanitize( text ):
    """ if a string has binary chunks replace them with hex return fixed up string """
    inbytes = array('B')
    inbytes.fromstring(text)
    hexchars = "0123456789ABCDEF"
    outtext = ""
    index = 0
    for i in inbytes:
        if (i < 32 and (i not in [9,10,13]))  or i > 127:
            hexout = hexchars[i//16] + hexchars[i%16]
            outtext = outtext + hexout
        else:
            outtext = outtext + text[index]
        index = index + 1
    return outtext

def contains(fullpath, pattern, found):
    """ test to see if the file referenced by fullpath contains pattern write result lines to file object found """
    try:
        line = 0
        fl = open(fullpath, "r")
        inline = fl.readline(2048)
        while inline:
            sl = sanitize(inline)
            if re.search(pattern,sl):
                print("%s:%d:%s"%(fullpath,line,sl.rstrip()), file=found)
            inline = fl.readline(2048)
            line += 1
    except Exception as e:
        print("%s:%d:ERROR %s"%(fullpath,line,str(e)), file=found)

def where( path, fpat, cpat, recurse, scr ):
    """ recursively search for a pattern in files starting with path, files matchin re fpat, containing re cpat,
    if recurse == False only do one directory, if scr is non null then report status in a message dialog"""
    found = tempfile.TemporaryFile(mode="w+")
    for (dirpath, dirnames, filenames) in os.walk(path):
        for f in filenames:
            if f[0] == ".":
                continue
            if f[-1] == "~":
                continue
            if f.endswith(".bak") or f.endswith(".pyc"):
                continue
            fullpath = os.path.join(dirpath,f)
            if re.search(r"\.svn",fullpath):
                continue
            try:
                if re.search(fpat,fullpath):
                    if scr and cpat:
                        message(scr,"Searching",fullpath,False)
                    if cpat:
                        contains(fullpath, cpat, found)
                    else:
                        print("%s"%(fullpath), file=found)
            except Exception as e:
                print("%s:0:ERROR:%s"%(fullpath,str(e)), file=found)
        if not recurse:
            break
    found.seek(0,0)
    return found



class FileFindDialog(dialog.Dialog):
    """ dialog subclass that implements a file find dialog with a list of found files/lines preview window
        and fields for file pattern, contents pattern, recursive search, starting path, buttons for opening
        the current file in the editor, search again, and cancel """
    def __init__(self,scr,title = "File Find Dialog",fpat=".*",cpat="",recurse=False):
        """ takes the curses window to pop up over, title to display, will dynamically size to parent window """
        max_y,max_x = scr.getmaxyx()
        pw = (max_x - 4)
        ph = ((max_y-7) // 2)
        cx = max_x // 2
        y = 1
        self.found_list = StreamSelectComponent("found",7,cx-(pw//2),y,pw,ph,"Found",where(os.getcwd(),fpat,cpat,recurse,scr))
        y += ph
        self.preview = FileBrowseComponent("browse",8,cx-(pw//2),y,pw,ph,"Preview",None)
        y += ph
        self.start_dir = dialog.Prompt("dir",1,2,y,"Path: ",max_x-10,os.getcwd())
        y += 1
        self.recurse = dialog.Toggle("recurse",2,2,y,20,1,["Search Subdirs","Don't Search Subdirs"])
        y += 1
        self.file_name = dialog.Prompt("file",2,2,y,"File: ",max_x-10,fpat)
        y += 1
        self.contains = dialog.Prompt("contains",3,2,y,"Contains:",max_x-13,cpat)
        y += 1
        dialog.Dialog.__init__(self,scr,"FileFindDialog", max_y, max_x, [ dialog.Frame(title),
                                                            self.found_list,
                                                            self.preview,
                                                            self.start_dir,
                                                            self.recurse,
                                                            self.file_name,
                                                            self.contains,
                                          dialog.Button("search",4,2,y,"SEARCH",dialog.Component.CMP_KEY_NOP),
                                          dialog.Button("open",5,2+((max_x-4)//3),y,"OPEN",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("cancel",6,2+(((max_x-4)//3)*2),y,"CANCEL",dialog.Component.CMP_KEY_CANCEL)])

    def handle(self,ch):
        """ handles found file selection, populating the preview window, new searches, and opening a file """
        focus_index = self.current
        focus_field = self.focus_list[self.current][1]
        ret_ch = dialog.Dialog.handle(self,ch)
        if ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR]:
            if focus_field == self.found_list:
                line = focus_field.getvalue().rstrip()
                fname = None
                number = 0
                if ":" in line:
                    fname,number,rest = line.split(":",2)
                else:
                    fname = line
                self.preview.setfilename(fname,int(number))
            else:
                values = self.getvalue()
                if values["search"]:
                    (recurse,choices) = values["recurse"]
                    self.found_list.setstream(where(values["dir"],values["file"],values["contains"],not recurse,self.getparent()))
                    values["search"] = False
                    self.setvalue(values)
                    idx = 0
                    while idx < len(self.focus_list):
                        if self.focus_list[idx][1] == self.found_list:
                            self.current = idx
                            break
                        idx += 1

        return ret_ch

def filefind(scr, title = "File Find Dialog", fpat = ".*", cpat = "", recurse = False):
    """ wrapper function for finding files, returns either a (filename, line) tuple, or None if canceled """
    d = FileFindDialog(scr,title,fpat,cpat,recurse)
    values = d.main()
    if "found" in values:
        line = values["found"].rstrip()
        number = 0
        if ":" in line:
            fname,number,rest = line.split(":",2)
        else:
            fname = line
        return (fname,int(number))
    else:
        return None

def main(stdscr):
    """ test main driver for file find dialog """
    try:
        d = FileFindDialog(stdscr)
        d.main()
    except Exception as e:
        log = open("file_find.log","w")
        print(str(e), file=log)
        print(traceback.format_exc(), file=log)

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except Exception as e:
        log = open("file_find.log","w")
        print(str(e), file=log)
        print(traceback.format_exc(), file=log)
