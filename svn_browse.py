# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement browsing svn history for files used in the ped editor """
import curses
import curses.ascii
import sys
import os
import tempfile
import dialog                                      
import editor_common
import re
import traceback
from array import array
from message_dialog import message
from file_dialog import get_dir, FileListBox
from file_find import StreamSelectComponent
from dialog import StaticText, Toggle
from StringIO import StringIO
import keytab
import pexpect

password = ""
username = ""
creds = []

def set_userpass( un,pw ):
    """ set the username and password to use for all svn actions """
    global password, username,creds
    username = un
    password = pw
    creds = ["--username",username,"--password",password]

def get_revisions( path ):
    p = pexpect.spawn("svn",creds+["log",path])
    if password:
        p.expect("password:")
        p.sendline(password)
    ret = StringIO(p.read())
    return ret

def get_diff( revision, path, twocolumn = False, width = 240 ):
    if twocolumn:
        p = pexpect.spawn("svn "+" ".join(creds)+" -c %s --diff-cmd diff -x '-W %d -y -t' diff %s"%(revision,width,path))
    else:
        p = pexpect.spawn("svn "+" ".join(creds)+" -c %s --diff-cmd diff -x '-W %d -t' diff %s"%(revision,width,path))
    if password:
        p.expect("password:")
        p.sendline(password)
        p.expect("password:")
        p.sendline(password)
    ret = StringIO(p.read())
    return ret

def get_file_revision( revision, path ):
    if revision:
        p = pexpect.spawn("svn",creds+["-r",revision,"cat",path])
    else:
        p = pexpect.spawn("svn",creds+["cat",path])
    if password:
        p.expect("password:")
        p.sendline(password)
    ret = StringIO(p.read())
    return ret

def get_file_blame( path ):
    p = pexpect.spawn("svn",creds+["blame",path])
    if password:
        p.expect("password:")
        p.sendline(password)
    ret = StringIO(p.stdout.read())
    return ret


class SvnBrowseDialog(dialog.Dialog):
    """ dialog subclass that implements a svn browse dialog with a list of files, a list of revisions, and a diff viewer window  """
    def __init__(self,scr,title = "Svn Browse",filename="",path = ".",revision = ""):
        """ takes the curses window to pop up over, title to display, will dynamically size to parent window """
        max_y,max_x = scr.getmaxyx()                         
        pw = (max_x - 4)
        lw = pw / 3
        self.rw = pw - lw
        ph = (max_y - 5) / 2
        cx = max_x / 2
        y = 1
        (dirpath, dirnames, filenames) = get_dir(path)
        self.dirpath = dirpath
        revisions = None
        diff = None
        self.filename = filename
        self.old_diff = "Normal Diff"
        fidx = 0        
        if self.filename in filenames:
            fidx = filenames.index(filename) + len(dirnames)
            revisions = get_revisions(os.path.join(self.dirpath,self.filename))
            if revision:
                diff = get_diff( revision, os.path.join(self.dirpath,self.filename),False,self.rw-2)

        self.files = FileListBox("files",1,1,y,ph,lw,"Files",fidx,dirnames+filenames)
        y += ph        
        self.revisions = StreamSelectComponent("revisions",2,1,y,lw,ph,"Revisions",revisions,r"^r[0-9]+ \|")
        y += ph
        self.diff = StreamSelectComponent("diff",3,lw+1,1,self.rw,ph*2,"Diff",diff)
        self.path = StaticText("path",cx - (pw/2), y,"Path: ", pw-6, "%s"%(os.path.join(self.dirpath,self.filename)))
        y += 1
        self.revision = StaticText("revision",cx - (pw/2), y,"Revision: ", pw-10, revision )
        y += 1                                                                           
        self.diffstyle = Toggle("diffstyle",4,2,y,15,0,["Normal Diff","Two Column Diff","Blame"])
        dialog.Dialog.__init__(self,scr,"SvnBrowseDialog", max_y, max_x, [ dialog.Frame(title),
                                                            self.files,
                                                            self.revisions,
                                                            self.diff, 
                                                            self.path,
                                                            self.revision,
                                                            self.diffstyle,
                                          dialog.Button("open",5,2+((max_x-4)/3),y,"OPEN",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("cancel",6,2+(((max_x-4)/3)*2),y,"CANCEL",dialog.Component.CMP_KEY_CANCEL)])

    def handle(self,ch):
        """ handles found file selection, populating the preview window, new searches, and opening a file """
        focus_index = self.current
        focus_field = self.focus_list[self.current][1]
        ret_ch = dialog.Dialog.handle(self,ch)
        if ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR]:
            if focus_field == self.files:
                (item,selection) = focus_field.getvalue()
                path = selection[item]
                if path.startswith("<DIR> "):
                    (self.dirpath, dirnames, filenames) = get_dir(os.path.join(self.dirpath,path[6:]))
                    self.path.setvalue(os.path.abspath(self.dirpath))
                    self.revision.setvalue("")
                    focus_field.setvalue((0,dirnames+filenames))
                else:                                      
                    self.filename = path
                    self.revisions.setstream(get_revisions(os.path.join(self.dirpath,self.filename)))
                    self.path.setvalue(os.path.abspath(os.path.join(self.dirpath,self.filename)))
                    self.revision.setvalue("")
                    self.diff.setstream(None)
                self.current = focus_index
            elif focus_field == self.revisions:
                fields = focus_field.getvalue().split("|")
                twocolumn = False
                (item, selection) = self.diffstyle.getvalue()
                if item == 1:
                    twocolumn = True
                self.diff.setstream(get_diff(fields[0][1:].strip(),os.path.join(self.dirpath,self.filename),twocolumn,self.rw-2))
                self.revision.setvalue(fields[0][1:].strip())
                self.current = focus_index     
            elif focus_field == self.diffstyle:
                if self.revision.getvalue() and self.diffstyle.getvalue() != self.old_diff:
                    twocolumn = False
                    (item, selection) = self.diffstyle.getvalue()
                    if item == 1:
                        twocolumn = True
                        
                    self.old_diff = self.diffstyle.getvalue()
                    if item == 2:
                        self.diff.setstream(get_file_blame(os.path.join(self.dirpath,self.filename)))
                    else:
                        self.diff.setstream(get_diff(self.revision.getvalue(),os.path.join(self.dirpath,self.filename),twocolumn,self.rw-2))
        return ret_ch

def browsesvn(scr, title = "Browse SVN", filename = "", path = ".", revision = ""):
    """ wrapper function for browsing the svn history for a file """
    d = SvnBrowseDialog(scr,title,filename, path, revision)
    values = d.main()
    return values

def main(stdscr):
    """ test main driver for file find dialog """
    try:
        browsesvn(stdscr,filename=sys.argv[1])
    except Exception, e:
        log = open("file_find.log","w")
        print >>log,str(e)
        print >>log,traceback.format_exc()

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except Exception, e:
        log = open("file_find.log","w")
        print >>log,str(e)
        print >>log,traceback.format_exc()
