import editor_common
import io
import pprint
import os
import curses
import curses.ascii
import time
import re
import keymap
import keytab
import clipboard
import extension_manager
from ped_test_util import read_str, match_attr, undo_all, window_pos, play_macro, validate_mark, validate_screen, editor_test_suite, screen_size


def test_extension_manager(testdir,capsys):
    with capsys.disabled():
        lines_to_test = [
            '# Copyright 2014 James P Goodwin ped tiny python editor',
            '""" extension to test the extension_manager  """',
            'from editor_common import Editor',
            'from message_dialog import message',
            '',
            '# register shift-F1 to comment the highlighted block',
            'def ped_ext_info():',
            '    """ return registration information for extension_manager """',
            '    return ( "CMD_COMMENT", "EDITOR", "KEYTAB_F13", "KEYTAB_NOKEY", "comment_extension" )',
            '',
            '',
            'def ped_ext_invoke( cmd_id, target, ch ):',
            '    """ do our thing with the target object """',
            '    if target.isMark():',
            '        target.line_mark = False',
            '        target.span_mark = False',
            '        target.rect_mark = False',
            '        mark_line_start = target.mark_line_start',
            '        mark_line_end = target.getLine()',
            '        if mark_line_start > mark_line_end:',
            '            mark = mark_line_end',
            '            mark_line_end = mark_line_start',
            '            mark_line_start = mark',
            '        line = mark_line_start',
            '        while line <= mark_line_end:',
            '            target.goto(line,0)',
            '            target.insert("#")',
            '            line += 1',
            '    return False'
            ]
        args = { "comment_extension":"\n".join(lines_to_test)}
        testfile = testdir.makefile(".py", **args)
        os.environ["PED_EXTENSION_PATH"] = str(testdir.tmpdir)
        extension_manager.register_extensions()

        def main(stdscr):
            screen_size( 30, 100 )
            curses.resizeterm( 30, 100 )
            ed = editor_common.Editor(stdscr,None,str(testfile))
            ed.setWin(stdscr.subwin(ed.max_y,ed.max_x,0,0))
            ed.main(False)
            ed.main(False)
            validate_screen(ed)

            ed.goto(6,0)
            ed.mark_lines()
            ed.goto(9,0)
            ed.main(False)
            validate_screen(ed)

            ed.main(False,keytab.KEYTAB_F13)
            for line in range(6,10):
                assert(ed.getContent(line)[0] == '#')

            ed.main(False)
            validate_screen(ed)

        curses.wrapper(main)
