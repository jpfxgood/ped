# Copyright 2009 James P Goodwin ped tiny python editor
""" module that implements a simple prompt dialog for the ped editor """
import curses
import curses.ascii
import sys
import os
from ped_dialog import dialog
from ped_core import keytab

class PromptDialog(dialog.Dialog):
    """ Dialog subclass that pops up a simple prompt over the provided screen """
    def __init__(self,scr, title = "Prompt", prompt = "Enter something : ", width= -1, name = "value"):
        """ takes window to pop up over, title of dialog, prompt string, and width of input field,
            if width is -1 it'll auto fit remaining space in the prompt window, otherwise
            the width of the input will be set to that number of characters
            the dialog will fit the parent window """

        max_y, max_x = scr.getmaxyx()
        if width == -1:
            width = (max_x - 8) - len(prompt)
        dw = max_x - 4

        self.prompt = dialog.Prompt(name,1,2,2,prompt,width)
        dialog.Dialog.__init__(self,scr,"PromptDialog",5,dw, [ dialog.Frame(title),
                                          self.prompt])

    def handle(self,ch):
        """ override the dialog handling to allow enter to do ok and esc to do cancel since we have no buttons """
        ret_ch = dialog.Dialog.handle(self,ch)
        if ch == keytab.KEYTAB_CR: # enter
            return dialog.Component.CMP_KEY_OK
        elif ch == keytab.KEYTAB_ESC: # esc
            return dialog.Component.CMP_KEY_CANCEL
        else:
            return ret_ch

def prompt( scr, title = "Prompt", prompt = "Enter something: ", width = 10, name = "value" ):
    """ wrapper function takes curses window to pop up over, title, prompt, and width of field -1 means size field to window """
    d = PromptDialog(scr,title,prompt,width,name)
    value = d.main()
    if name in value:
        return value[name]
    else:
        return None

def main(stdscr):
    """ test main for prompt dialog """
    return prompt(stdscr,"Test Prompt","Enter a number: ", 8 )

if __name__ == '__main__':
    print(int(curses.wrapper(main)))
