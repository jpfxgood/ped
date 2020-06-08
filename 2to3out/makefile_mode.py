# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a makefile mode for the ped editor does colorizing of code """
import editor_common
import curses
from message_dialog import message
import re

def get_tabs(editor):
    """ return the tab stops for this type of file """
    return [8,16]

def detect_mode(editor):
    """ hook called to detect if this mode should be used for a file, returns True if it should be used, False otherwise """
    workfile = editor.getWorkfile()
    if re.search(r"([Mm]akefile.*$)|([Mm]akefile.*\:\(r.*\)$)",workfile.getFilename()):
        return True
    elif re.search(r"(\.mak$)|(\.mak\:\(r.*\)$)",workfile.getFilename()):
        return True
    else:
        return False

def handle(editor,ch):
    """ hook called for each keystroke, can be used for auto-indent or auto-complete """
#    if editor.ch == 10:
#        editor.cr()
#        wf = editor.getWorkfile()
#        line = editor.line + editor.vpos
#        above = wf.getLine(line-1)
#        match = re.match("^\s*(if|for|while|else|elif|try|except|def|class|finally)\W",above)
#        if match:
#            stop = wf.get_tab_stop(match.start(1))
#            editor.insert(stop*' ')
#        else:
#            match = re.match("^\s*(\S+)",above)
#            if match:
#                editor.insert(match.start(1)*' ')
#        return 0
        
    return ch


def finish(editor):     
    """ this editor is going away do anything required to clean up """
    pass

def redraw(editor):
    """ redraw the colorization based on the current token set, regenerate it if needed """
    return False
    
def name():
    """ hook to return this mode's human readable name """
    return "makefile_mode"
