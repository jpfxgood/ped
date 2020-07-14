# Copyright 2009 James P Goodwin ped tiny python editor
""" module that implements file open/new dialog for the ped editor """
import curses
import curses.ascii
import sys
import os
from ped_dialog import dialog
from ped_core import keytab

def get_dir(path,showhidden=False):
    """ get a directory listing of path, directories are prefixed with <DIR>
        if showhidden == False hidden files are not include, otherwise they are
        returns the directory path, the list of directories and list of files as a tuple"""
    (dirpath, dirnames, filenames) = next(os.walk(path))
    if not showhidden:
        dirnames = [d for d in dirnames if d[0] != "."]
        filenames = [f for f in filenames if f[0] != "." and f[-1] != "~" and not f.endswith(".bak")]
    dirnames.sort()
    filenames.sort()
    dirnames = ["<DIR> .."] + ["<DIR> "+d for d in dirnames]
    return (dirpath, dirnames, filenames)

class FileListBox(dialog.ListBox):
    """ list box subclass for file lists, handles searching past the <DIR> prefix for incremental searches"""
    def find(self,searchfor):
        """ subclass the find method to find the string either with the dir prefix or without it """
        if not dialog.ListBox.find(self,"<DIR> "+searchfor):
            return dialog.ListBox.find(self,searchfor)
        else:
            return True

class FileDialog(dialog.Dialog):
    """ dialog subclass that implements a file open dialog allowing
        browsing files and directories and selecting a file
        or typing in a file name """
    def __init__(self,scr,title = "File Dialog", path="."):
        """ takes a curses window scr, title for the border, and a starting path """
        (dirpath, dirnames, filenames) = get_dir(path)
        max_y, max_x = scr.getmaxyx()
        dw = max_x - 4

        self.file_list = FileListBox("files",1,2,3,10,dw-4,"Directory Listing",0,dirnames+filenames)
        self.current_dir = dialog.Prompt("dir",5,2,2,"Path: ",dw-10,os.path.abspath(dirpath))
        self.file_name = dialog.Prompt("file",2,2,14,"File: ",dw-10)
        dialog.Dialog.__init__(self,scr,"FileDialog",20,dw, [ dialog.Frame(title),
                                                              self.file_list,
                                                              self.current_dir,
                                                              self.file_name,
                                          dialog.Button("Ok",3,2,16,"OK",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("Cancel",4,9,16,"CANCEL",dialog.Component.CMP_KEY_CANCEL)])

    def handle(self,ch):
        """ key handler for selection from the file and directory list,
            browsing another directory selecting a file or entering one """
        focus_index = self.current
        focus_field = self.focus_list[self.current][1]
        ret_ch = dialog.Dialog.handle(self,ch)
        if focus_field == self.file_list and ch in [keytab.KEYTAB_SPACE,keytab.KEYTAB_CR]:
            (selection, items) = focus_field.getvalue()
            choice = items[selection]
            if choice.startswith('<DIR>'):
                (dirpath,dirnames,filenames) = get_dir(os.path.join(self.current_dir.getvalue(),choice[6:]))
                focus_field.setvalue((0,dirnames+filenames))
                self.setvalue({"dir":os.path.abspath(dirpath)}) # important to do it this way to work with history
                os.chdir(os.path.abspath(dirpath))
                self.current = focus_index
                ret_ch = dialog.Component.CMP_KEY_NOP
            else:
                self.file_name.setvalue(choice)
        elif focus_field == self.current_dir and ch in [keytab.KEYTAB_TAB,keytab.KEYTAB_BTAB,keytab.KEYTAB_CR]:
            dir = focus_field.getvalue()
            (dirpath,dirnames,filenames) = get_dir(dir)
            self.file_list.setvalue((0,dirnames+filenames))
            os.chdir(os.path.abspath(dirpath))
        return ret_ch


def main(stdscr):
    """ test main for the file dialog """
    d = FileDialog(stdscr)
    d.main()

if __name__ == '__main__':
    curses.wrapper(main)
