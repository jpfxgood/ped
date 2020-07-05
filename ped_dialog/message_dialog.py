# Copyright 2009 James P Goodwin ped tiny python editor
""" message dialog with button to close implementation for ped editor """
import curses
import curses.ascii
import sys
import os
from ped_dialog import dialog
import traceback

class MessageDialog(dialog.Dialog):
    """ dialog subclass to implement a simple message popup that either comes and goes or blocks waiting for done button to be pressed """
    def __init__(self,scr, title = "Message", message = "This is a message!", blocking = True):
        """ takes curses window to pop up over, title, message, and blocking == True to show
         button and wait, or blocking == False to just display and leave """
        max_y, max_x = scr.getmaxyx()
        min_y, min_x = scr.getbegyx()
        dw = max_x - 4
        dh = 5

        if blocking:
            dialog.Dialog.__init__(self,scr,"MessageDialog",dh,dw, [ dialog.Frame(title),
                                              dialog.StaticText("message",max(1,(dw//2)-(len(message)//2)),(dh//2-2)+2,message,0),
                                              dialog.Button("done",1,(dw//2)-(6//2),(dh//2-2)+3,"DONE",dialog.Component.CMP_KEY_OK)],min_y,min_x)
        else:
            dialog.Dialog.__init__(self,scr,"MessageDialog",dh,dw, [ dialog.Frame(title),
                                              dialog.StaticText("message",max(1,(dw//2)-(len(message)//2)),(dh//2-2)+2,message,0)],min_y,min_x)


def message( scr, title = "Message", message = "A message!", blocking=True ):
    """ wrapper function to launch a message dialog, takes curses window to pop up over, title, message, and blocking == True
    to show button and wait, or False to just display and leave """

    try:
        d = MessageDialog(scr,title,message,blocking)
        if blocking:
            d.main()
        else:
            d.focus()
            d.render()
    except Exception as e:
        raise


def main(stdscr):
    """ test driver for message dialog """
    return message(stdscr,"Test Message","This is a test message!")

if __name__ == '__main__':
    curses.wrapper(main)
