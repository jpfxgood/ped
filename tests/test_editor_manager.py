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
from ped_test_util import read_str


def test_BaseFrame(testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
            max_y,max_x = stdscr.getmaxyx()
            frames = []
            sw_height = max_y//2
            sw_width = max_x//2
            y = 0
            x = 0
            frames.append(editor_manager.BaseFrame( stdscr, x,y,sw_height,sw_width))
            x += sw_width+1
            frames.append(editor_manager.BaseFrame( stdscr, x,y,sw_height,sw_width-1,True))
            x = 0
            y += sw_height
            frames.append(editor_manager.BaseFrame( stdscr, x,y,sw_height,sw_width))
            x += sw_width+1
            frames.append(editor_manager.BaseFrame( stdscr, x,y,sw_height,sw_width-1,True))
            stdscr.erase()
            for f in frames:
                f.redraw(True)
                f.win.refresh()
            stdscr.refresh()
            assert(frames[0] < frames[1] and frames[1] < frames[2] and frames[2] < frames[3])
            assert(frames[1].getrect() == (sw_width+1,0,sw_width-1,sw_height))
            assert(frames[1].getrect(True) == (sw_width,0,sw_width,sw_height))
            ox,oy,owidth,oheight = frames[1].getrect(True)
            for off_y in range(0,oheight):
                assert(stdscr.inch(oy+off_y,ox) & curses.ACS_VLINE)
            stdscr.erase()
            for f in frames:
                f_x,f_y,f_width,f_height = f.getrect()
                f.resize(f_x,f_y,f_width-1,f_height-1)
                f.redraw(True)
                f.win.refresh()
            stdscr.refresh()
            assert(frames[0] < frames[1] and frames[1] < frames[2] and frames[2] < frames[3])
            assert(frames[1].getrect() == (sw_width+1,0,sw_width-2,sw_height-1))
            assert(frames[1].getrect(True) == (sw_width,0,sw_width-1,sw_height-1))
            ox,oy,owidth,oheight = frames[1].getrect(True)
            for off_y in range(0,oheight):
                assert(stdscr.inch(oy+off_y,ox) & curses.ACS_VLINE)


        curses.wrapper(main)
