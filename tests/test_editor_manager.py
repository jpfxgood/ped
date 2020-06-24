import editor_manager
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


def test_BaseFrame(testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
            pass            
            
        curses.wrapper(main)

