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
from ped_test_util import read_str,validate_screen,editor_test_suite,play_macro,screen_size


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
            x += sw_width
            frames.append(editor_manager.BaseFrame( stdscr, x,y,sw_height,sw_width,True))
            x = 0
            y += sw_height
            frames.append(editor_manager.BaseFrame( stdscr, x,y,sw_height,sw_width))
            x += sw_width
            frames.append(editor_manager.BaseFrame( stdscr, x,y,sw_height,sw_width,True))
            stdscr.erase()
            for f in frames:
                f.redraw(True)
                f.win.refresh()
            stdscr.refresh()
            assert(frames[0] < frames[1] and frames[1] < frames[2] and frames[2] < frames[3])
            assert(frames[1].getrect() == (sw_width,0,sw_width,sw_height))
            ox,oy,owidth,oheight = frames[1].getrect()
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
            assert(frames[1].getrect() == (sw_width,0,sw_width-1,sw_height-1))
            ox,oy,owidth,oheight = frames[1].getrect()
            for off_y in range(0,oheight):
                assert(stdscr.inch(oy+off_y,ox) & curses.ACS_VLINE)


        curses.wrapper(main)

def test_EditorFrame(testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
            max_y,max_x = stdscr.getmaxyx()
            frames = []
            sw_height = max_y//2
            sw_width = max_x//2
            y = 0
            x = 0
            frames.append(editor_manager.EditorFrame( stdscr, x,y,sw_height,sw_width))
            x += sw_width
            frames.append(editor_manager.EditorFrame( stdscr, x,y,sw_height,sw_width,True))
            x = 0
            y += sw_height
            frames.append(editor_manager.EditorFrame( stdscr, x,y,sw_height,sw_width))
            x += sw_width
            frames.append(editor_manager.EditorFrame( stdscr, x,y,sw_height,sw_width,True))
            stdscr.erase()
            idx = 0
            for f in frames:
                lines_to_test = "\n".join([(("File %d line %d "%(idx,r))*20).rstrip() for r in range(0,2001)])
                args = { "test_file_%d"%idx: lines_to_test }
                testfile = testdir.makefile(".txt",**args)
                fn = str(testfile)
                ed = editor_common.Editor(stdscr,f.win,fn)
                f.seteditor(ed)
                f.redraw(True)
                f.win.refresh()
                idx += 1
            stdscr.refresh()
            assert(frames[0] < frames[1] and frames[1] < frames[2] and frames[2] < frames[3])
            assert(frames[1].getrect() == (sw_width,0,sw_width,sw_height))
            ox,oy,owidth,oheight = frames[1].getrect()
            for off_y in range(0,oheight):
                assert(stdscr.inch(oy+off_y,ox) & curses.ACS_VLINE)
            for f in frames:
                validate_screen(f.editor)
            stdscr.erase()
            for f in frames:
                f_x,f_y,f_width,f_height = f.getrect()
                f.resize(f_x,f_y,f_width-1,f_height-1)
                f.redraw(True)
                f.win.refresh()
            stdscr.refresh()
            assert(frames[0] < frames[1] and frames[1] < frames[2] and frames[2] < frames[3])
            assert(frames[1].getrect() == (sw_width,0,sw_width-1,sw_height-1))
            ox,oy,owidth,oheight = frames[1].getrect()
            for off_y in range(0,oheight):
                assert(stdscr.inch(oy+off_y,ox) & curses.ACS_VLINE)
            for f in frames:
                validate_screen(f.editor)
            editor_test_suite(frames[3].win,testdir,False,frames[3].editor)

        curses.wrapper(main)

def test_EditorManager(testdir,capsys):
    with capsys.disabled():
        def main(stdscr):
            test_files = []
            for idx in range(0,5):
                lines_to_test = "\n".join([(("File %d line %d "%(idx,r))*20).rstrip() for r in range(0,2001)])
                args = { "test_file_%d"%idx: lines_to_test }
                testfile = testdir.makefile(".txt",**args)
                test_files.append(testfile)

            screen_size( 30, 100 )
            em = editor_manager.EditorManager(stdscr)
            em.addEditor(editor_common.Editor(stdscr,None,str(test_files[0])))
            em.main(False)
            assert(em.getCurrentEditor().getFilename() == str(test_files[0]))
            validate_screen(em.getCurrentEditor())
            play_macro(em,[keytab.KEYTAB_ALTE]+list(test_files[1].basename)+['\n','\n','\n'])
            assert(em.getCurrentEditor().getFilename() == str(test_files[1]))
            validate_screen(em.getCurrentEditor())
            play_macro(em,[keytab.KEYTAB_ALTV,keytab.KEYTAB_F04,keytab.KEYTAB_ALTN])
            cur_rect = em.getCurrentFrame().getrect()
            assert(cur_rect[0] == 0 and cur_rect[1] == 0)
            assert(em.getCurrentEditor().getFilename() == str(test_files[0]))
            validate_screen(em.getCurrentEditor())
            em.nextFrame()
            validate_screen(em.getCurrentEditor())
            play_macro(em,[keytab.KEYTAB_ALTZ,keytab.KEYTAB_ALTH,keytab.KEYTAB_F04,keytab.KEYTAB_ALTN])
            cur_name = em.getCurrentEditor().getFilename()
            validate_screen(em.getCurrentEditor())
            em.nextFrame()
            assert(cur_name != em.getCurrentEditor().getFilename())
            validate_screen(em.getCurrentEditor())
            play_macro(em,[keytab.KEYTAB_ALTV,keytab.KEYTAB_F04])
            em.main(False)
            max_x = em.max_x
            max_y = em.max_y
            if max_x == 100 and max_y == 30:
                assert(len(em.frames) == 3 and em.frames[0].getrect() == (0,0,100,15) and em.frames[1].getrect() == (0,15,50,15) and em.frames[2].getrect() == (50,15,50,15))
                screen_size(24,80)
                em.main(False)
                em.main(False)
                assert(len(em.frames) == 3 and em.frames[0].getrect() == (0,0,80,12) and em.frames[1].getrect() == (0,12,40,12) and em.frames[2].getrect() == (40,12,40,12))
                screen_size(30, 100)
                em.main(False)
                em.main(False)
            em.nextEditor()
            cur_name = em.getCurrentEditor().getFilename()
            play_macro(em,[keytab.KEYTAB_ALTB,keytab.KEYTAB_DOWN,keytab.KEYTAB_DOWN,'\n','\n'])
            assert(cur_name != em.getCurrentEditor().getFilename())
            play_macro(em,[keytab.KEYTAB_ALTF,'\t','\t','\t','\t',keytab.KEYTAB_DOWN]+list("File 4")+['\t','\n',keytab.KEYTAB_DOWN,
            keytab.KEYTAB_DOWN,keytab.KEYTAB_DOWN,'\n','\t','\t','\t','\t','\t','\t','\t','\n'])
            assert(em.getCurrentEditor().getFilename().endswith("test_file_4.txt"))

        curses.wrapper(main)
