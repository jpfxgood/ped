# Copyright 2009 James P Goodwin ped tiny python editor
import curses
import curses.ascii
import sys
import os
from ped_dialog import dialog

class ConfirmDialog(dialog.Dialog):
    def __init__(self,scr, prompt = "Are you sure ?"):
        dialog.Dialog.__init__(self,scr,"ConfirmDialog",5,40, [ dialog.Frame(prompt),
                                          dialog.Button("Yes",2,32,2,"YES",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("No",1,2,2,"NO",dialog.Component.CMP_KEY_CANCEL)])

def confirm( scr, prompt = "Are you sure ?" ):
    d = ConfirmDialog(scr,prompt)
    return d.main()

def main(stdscr):
    return confirm(stdscr,"Test yes no prompt ?")

if __name__ == '__main__':
    if curses.wrapper(main):
        print("Yes")
    else:
        print("No")
