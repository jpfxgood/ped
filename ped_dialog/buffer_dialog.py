# Copyright 2009 James P Goodwin ped tiny python editor
import curses
import curses.ascii
import sys
import os
from ped_dialog import dialog

class BufferDialog(dialog.Dialog):
    def __init__(self,scr,title = "Choose a Buffer", buffers = []):
        max_y,max_x = scr.getmaxyx()
        dw = max_x - 4
        lw = dw - 4
        lx = dw//2 - lw//2
        self.buffer_list = dialog.ListBox("buffers",1,lx,2,12,lw,"Buffers",0,buffers)
        dialog.Dialog.__init__(self,scr,"BufferDialog",20,dw, [ dialog.Frame(title),
                                                              self.buffer_list,
                                          dialog.Button("Ok",2,2,16,"OK",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("Cancel",3,9,16,"CANCEL",dialog.Component.CMP_KEY_CANCEL)])

def choose_buffer(scr,buffers):
    d = BufferDialog(scr,buffers=buffers)
    values = d.main()
    if values:
        (selection,items) = values["buffers"]
        return items[selection]
    else:
        return None

def main(stdscr):
    choose_buffer(stdscr,["one","two","three"])

if __name__ == '__main__':
    curses.wrapper(main)
