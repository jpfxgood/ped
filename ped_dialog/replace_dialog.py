# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement the search and replace dialog for ped """
import curses
import curses.ascii
import sys
import os
from ped_dialog import dialog
from ped_dialog import confirm_dialog

class ReplaceDialog(dialog.Dialog):
    """ Dialog subclass that prompts for pattern, replacement string, sizes itself to the containing window """
    def __init__(self,scr):
        """ takes parent curses window or screen to pop up over """
        (max_y,max_x) = scr.getmaxyx()
        dialog.Dialog.__init__(self, scr, "ReplaceDialog", 5, max_x-4, [ dialog.Frame("Search and Replace"),
                                          dialog.Prompt("pattern",1,2,1,"Pattern: ",-1),
                                          dialog.Prompt("replace",2,2,2,"Replace: ",-1),
                                          dialog.Button("ok",3,2,3,"OK",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("cancel",4,29,3,"CANCEL",dialog.Component.CMP_KEY_CANCEL)
                                          ])

class ConfirmReplaceDialog(dialog.Dialog):
    """ Dialog subclass to confirm replacement, prompts for yes, no or all """
    def __init__(self,scr):
        """ takes parent curses window or screen to pop up over """
        dialog.Dialog.__init__(self, scr, "ConfirmReplaceDialog", 5, 40, [ dialog.Frame("Do replace?"),
                                          dialog.Button("yes",1,2,3,"YES",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("no",2,10,3,"NO",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("all",3,15,3,"ALL",dialog.Component.CMP_KEY_OK),
                                          dialog.Button("cancel",4,21,3,"CANCEL",dialog.Component.CMP_KEY_OK)
                                          ])


def replace( scr ):
    """ wrapper function for replace dialog, launches dialog over the passed curses window and returns
        a tuple of (pattern, replace) or (None,None) if canceled """
    d = ReplaceDialog(scr)
    value = d.main()
    if not "pattern" in value:
        return (None,None)
    else:
        return (value["pattern"],value["replace"])

def confirm_replace( scr ):
    """ wrapper function for the confirm replace dialog, returns 1 == yes, 2 == no, 3 == all, 4 == cancel
        returns 4 == cancel if canceled """
    d = ConfirmReplaceDialog(scr)
    value = d.main()
    if "yes" in value:
        if value["yes"]:
            return 1
        elif value["no"]:
            return 2
        elif value["all"]:
            return 3
        elif value["cancel"]:
            return 4
    else:
        return 4




def main(stdscr):
    return prompt(stdscr,"Test Replace","Enter a number: ", 8 )

if __name__ == '__main__':
    print(int(curses.wrapper(main)))
