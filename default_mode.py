# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a default mode for the ped editor no colorizing just sets tabs """
import editor_common

def get_tabs(editor):
    """ return the tab stops for this type of file """
    return [4,8]

def detect_mode(editor):
    """ hook called to detect if this mode should be used for a file, returns True if it should be used, False otherwise """
    return True

def handle(editor,ch):
    """ hook called for each keystroke, can be used for auto-indent or auto-complete """
    return ch


def finish(editor):     
    """ this editor is going away do anything required to clean up """
    pass

def redraw(editor):
    """ redraw the colorization based on the current token set, regenerate it if needed """
    return False

def name():
    """ hook to return this mode's human readable name """
    return "default"
