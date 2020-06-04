# Copyright 2014 James P Goodwin ped tiny python editor
""" extension to test the extension_manager  """
from editor_common import Editor
from message_dialog import message


def ped_ext_info():
    """ return registration information for extension_manager """
    return ( "CMD_COMMENT", "EDITOR", "KEYTAB_F13", "KEYTAB_NOKEY", "comment_extension" )


def ped_ext_invoke( cmd_id, target, ch ):
    """ do our thing with the target object """
    if target.isMark():
        target.line_mark = False
        target.span_mark = False
        target.rect_mark = False
        mark_line_start = target.mark_line_start
        mark_line_end = target.getLine()
        if mark_line_start > mark_line_end:
            mark = mark_line_end
            mark_line_end = mark_line_start
            mark_line_start = mark
        line = mark_line_start
        while line <= mark_line_end:
            target.goto(line,0)
            target.insert("#")
            line += 1
    return False
