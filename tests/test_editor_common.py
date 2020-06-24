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
from ped_test_util import read_str, match_attr, undo_all, window_pos, play_macro, validate_mark, validate_screen

def test_memline():
    m = editor_common.MemLine( "01234567890123456789" )
    assert( m.length() == 20 )
    assert( m.getContent() == "01234567890123456789" )

def test_EditFile(testdir):
    lines_to_test = ["This is the first line","This is the second line","This is the third line","This is the last line"]
    testfile = testdir.makefile(".txt",lines_to_test[0],lines_to_test[1],lines_to_test[2],lines_to_test[3])
    fn = str(testfile)
    ef = editor_common.EditFile( fn )
    assert(ef.get_tabs() == [ 4, 8 ] )
    ef.set_tabs( [ 8, 16] )
    assert(ef.get_tabs() == [ 8, 16 ] )
    w = ef.getWorking()
    assert( isinstance(w,io.IOBase) and not w.closed )
    assert( ef.getModref() == 0)
    assert( isinstance(ef.getUndoMgr(), editor_common.undo.UndoManager ))
    assert( not ef.isChanged() )
    assert( not ef.isReadOnly() )
    ef.setReadOnly( True )
    assert( ef.isReadOnly() )
    ef.setReadOnly( False )
    assert( not ef.isReadOnly() )
    assert( ef.getFilename() == fn )
    ef.setFilename( "bogus.txt" )
    assert( ef.getFilename() == "bogus.txt" )
    ef.setFilename( fn )
    assert( ef.getFilename() == fn )
    fls = ef.getLines()
    assert( ef.numLines() == 4 )
    ef.close()
    assert( ef.getWorking() == None )
    ef.load()
    w = ef.getWorking()
    assert( isinstance(w,io.IOBase) and not w.closed )
    for line in range(0,len(lines_to_test)):
        assert(ef.length(line) == len(lines_to_test[line]))
        fl = ef.getLine(line)
        assert(fl.rstrip() == lines_to_test[line])
        assert(fls[line].rstrip() == lines_to_test[line])
    fls = ef.getLines(1,3)
    assert(len(fls) == 2 )
    assert(fls[0].rstrip() == lines_to_test[1] and fls[1].rstrip() == lines_to_test[2])
    ef.deleteLine(1)
    fls = ef.getLines()
    assert(fls[0].rstrip() == lines_to_test[0] and fls[1].rstrip() == lines_to_test[2] and fls[2].rstrip() == lines_to_test[3] )
    assert(ef.numLines() == 3 )
    assert(ef.getModref() == 1 )
    assert(ef.isChanged() )
    um = ef.getUndoMgr()
    um.undo_transaction()
    fls = ef.getLines()
    for line in range(0,len(lines_to_test)):
        assert(fls[line].rstrip() == lines_to_test[line])
    assert(ef.numLines() == 4)
    assert(ef.getModref() == 2)
    assert(not ef.isChanged() )
    new_test_line = "This is the line for insert"
    ef.insertLine(2,new_test_line)
    fls = ef.getLines()
    assert(fls[0].rstrip() == lines_to_test[0] and fls[1].rstrip() == lines_to_test[1] and fls[2].rstrip() == new_test_line and fls[3].rstrip() == lines_to_test[2] and fls[4].rstrip() == lines_to_test[3] )
    assert(ef.numLines() == 5 )
    assert(ef.getModref() == 3 )
    assert(ef.isChanged() )
    um = ef.getUndoMgr()
    um.undo_transaction()
    fls = ef.getLines()
    for line in range(0,len(lines_to_test)):
        assert(fls[line].rstrip() == lines_to_test[line])
    assert(ef.numLines() == 4)
    assert(ef.getModref() == 4)
    assert(not ef.isChanged() )
    ef.replaceLine(3,new_test_line)
    fls = ef.getLines()
    assert(fls[0].rstrip() == lines_to_test[0] and fls[1].rstrip() == lines_to_test[1] and fls[2].rstrip() == lines_to_test[2] and fls[3].rstrip() == new_test_line )
    assert(ef.numLines() == 4 )
    assert(ef.getModref() == 5 )
    assert(ef.isChanged() )
    um = ef.getUndoMgr()
    um.undo_transaction()
    fls = ef.getLines()
    for line in range(0,len(lines_to_test)):
        assert(fls[line].rstrip() == lines_to_test[line])
    assert(ef.numLines() == 4)
    assert(ef.getModref() == 6)
    assert(not ef.isChanged() )
    fd = str(testdir.tmpdir)
    backup_filepath = ef.make_backup_dir( fn, fd )
    assert(os.path.exists(os.path.dirname(backup_filepath)))
    ef.insertLine(10,new_test_line)
    ef.backuproot = fd
    ef.save()
    assert(os.path.exists(backup_filepath))
    fls = ef.getLines()
    for line in range(0,len(lines_to_test)):
        assert(fls[line].rstrip() == lines_to_test[line])
    assert(fls[10].rstrip() == new_test_line)
    newname = os.path.join(fd,"1_"+os.path.basename(fn))
    ef.save(newname)
    assert(os.path.exists(newname))
    ef.close()
    ef.load()
    assert(ef.getFilename() == newname)
    fls = ef.getLines()
    for line in range(0,len(lines_to_test)):
        assert(fls[line].rstrip() == lines_to_test[line])
    assert(fls[10].rstrip() == new_test_line)
    assert(ef.get_tab_stop(4) == 8)
    assert(ef.get_tab_stop(10) == 16 )
    assert(ef.get_tab_stop(10,True) == 8)
    tabby_string = "01234\t56789012\t3456789"
    expanded_string = "01234   56789012        3456789"
    assert(ef.expand_tabs(tabby_string) == expanded_string)

def test_Editor(testdir,capsys):
    with capsys.disabled():
        def main(stdscr,wrapped):
            lines_to_test = ["This is the first line","This is the second line","This is the third line","This is the last line"]
            lines_to_test += [ (("This is line %d "%f)*20).rstrip() for f in range(5,2000) ]
            testfile = testdir.makefile(".txt",*lines_to_test)
            fn = str(testfile)

            ed = editor_common.Editor(stdscr,None,fn)
            ed.setWin(stdscr.subwin(ed.max_y,ed.max_x,0,0))
            ed.main(False)
            if wrapped:
                ed.toggle_wrap()
                ed.main(False)

            validate_screen(ed)
            assert(match_attr(ed.scr,0,0,1,ed.max_x,curses.A_REVERSE))
            ef = ed.getWorkfile()

            assert(isinstance(ef,editor_common.EditFile))
            assert(ed.getFilename() == fn)
            assert(isinstance(ed.getUndoMgr(),editor_common.undo.UndoManager))
            assert(not ed.isChanged())
            assert(ed.numLines() == 1999)
            main.target_line = 1000
            main.target_pos = len(lines_to_test[main.target_line])//2

            def do_edit_tests( relative = False ):
                if relative:
                    target_line = ed.getLine()
                    target_pos = ed.getPos()
                else:
                    target_line = main.target_line
                    target_pos = main.target_pos
                    ed.goto(target_line,target_pos)
                ed.main(False)
                line = ed.getLine(True)
                pos = ed.getPos(True)
                (f_line,f_pos) = ed.filePos(line,pos)
                (s_line,s_pos) = ed.filePos(line,ed.left)
                assert(f_line == target_line)
                assert(f_pos == target_pos)
                validate_screen(ed)

                before_string = ed.getContent(f_line)
                ed.insert('X')
                assert(ed.isChanged())
                assert(ed.isLineChanged(target_line))
                ed.main(False)
                after_string = ed.getContent(f_line)
                assert(after_string == before_string[:f_pos]+'X'+before_string[f_pos:])
                validate_screen(ed)
                undo_all(ed)
                assert(ed.getContent(f_line) == before_string)
                validate_screen(ed)

                (cur_line,cur_pos) = ed.filePos(ed.getLine(True),ed.getPos(True))
                before_string = ed.getContent(cur_line)
                if cur_line <= ed.numLines()-1 and cur_pos < len(before_string)-1:
                    ed.delc()
                    assert(ed.isChanged())
                    assert(ed.isLineChanged(cur_line))
                    ed.main(False)
                    after_string = ed.getContent(cur_line)
                    if cur_pos+1 < len(before_string):
                        compare_string = before_string[:cur_pos] + before_string[cur_pos+1:]
                    elif cur_pos == len(before_string) and cur_line+1 < len(lines_to_test):
                        compare_string = before_string[:cur_pos] + lines_to_test[cur_line+1]
                    else:
                        compare_string = before_string
                    assert(after_string == compare_string)
                    validate_screen(ed)
                    undo_all(ed)
                    assert(ed.getContent(cur_line) == before_string)
                    validate_screen(ed)

                ed.backspace()
                assert(ed.isChanged())
                assert(ed.isLineChanged(cur_line))
                ed.main(False)
                if cur_pos+1 < len(before_string):
                    compare_string = before_string[:cur_pos-1] + before_string[cur_pos:]
                else:
                    compare_string = before_string[:cur_pos-1]

                assert(ed.getContent(cur_line) == compare_string)
                validate_screen(ed)
                undo_all(ed)
                assert(ed.getContent(cur_line) == before_string)
                validate_screen(ed)

            do_edit_tests()
            main.target_pos = 5
            do_edit_tests()
            ed.endln()
            assert(ed.getPos() == len(lines_to_test[main.target_line]))
            do_edit_tests(True)
            ed.endfile()
            assert(ed.getLine() == ed.numLines()-1)
            do_edit_tests(True)
            ed.goto(0,0)
            ed.endpg()
            ed.endln()
            ed.main(False)
#TODO figure out why this is different in wrapped mode
            assert(ed.getLine(True) == ed.max_y-1 or ed.getLine(True) == ed.max_y-2)
            do_edit_tests(True)
            ed.endfile()
            ed.endln()
            ed.main(False)
            assert(ed.getLine(True) == ed.numLines(True)-1)
            do_edit_tests(True)
            start_line = ed.getLine(True)
            ed.pageup()
            ed.main(False)
            assert(ed.getLine(True) == start_line - (ed.max_y-2))
            do_edit_tests(True)
            ed.pagedown()
            ed.main(False)
            assert(ed.getLine(True) == start_line)
            do_edit_tests(True)
            ed.cup()
            ed.main(False)
            assert(ed.getLine(True) == start_line -1 )
            do_edit_tests(True)
            ed.cdown()
            ed.main(False)
            assert(ed.getLine(True) == start_line )
            do_edit_tests(True)
            word_pos = []
            in_word = False
            for i in range(0,len(lines_to_test[main.target_line])):
                if lines_to_test[main.target_line][i] != ' ':
                    if not in_word:
                        word_pos.append(i)
                        in_word = True
                else:
                    in_word = False
            word_pos.append(len(lines_to_test[main.target_line]))
            for rfunc,lfunc in [(ed.next_word,ed.prev_word),(ed.cright,ed.cleft),(ed.scroll_right,ed.scroll_left)]:
                if wrapped and rfunc == ed.scroll_right:
                    break
                ed.goto(main.target_line,0)
                ed.main(False)
                prev_pos = ed.getPos()
                while ed.getPos() < len(lines_to_test[main.target_line])-2:
                    rfunc()
                    if rfunc == ed.next_word:
                        assert(ed.getPos() in word_pos)
                    assert(ed.getPos() > prev_pos)
                    prev_pos = ed.getPos()
                    s_line,s_pos = ed.filePos(ed.getLine(True),ed.left)
                    assert(ed.getPos() >= s_pos and ed.getPos() < s_pos+ed.max_x)
                    ed.main(False)
                    validate_screen(ed)

                while ed.getPos() > 0:
                    lfunc()
                    if ed.getLine() != main.target_line:
                        break
                    if lfunc == ed.prev_word:
                        assert(ed.getPos() in word_pos)
                    assert(ed.getPos() < prev_pos)
                    prev_pos = ed.getPos()
                    s_line,s_pos = ed.filePos(ed.getLine(True),ed.left)
                    assert(ed.getPos() >= s_pos and ed.getPos() < s_pos+ed.max_x)
                    ed.main(False)
                    validate_screen(ed)

            ed.search("This is line 1010",True,False)
            assert(ed.getLine() == 1009 and ed.getPos() == 16 and ed.isMark() and ed.mark_line_start == 1009 and ed.mark_pos_start == 0 and ed.getContent(ed.mark_line_start)[ed.mark_pos_start:ed.getPos()+1] == "This is line 1010")
            ed.main(False)
            validate_screen(ed)

            ed.search("This is line 990",False,False)
            assert(ed.getLine() == 989 and ed.getPos() == 338 and ed.isMark() and ed.mark_line_start == 989 and ed.mark_pos_start == 339-len("This is line 990") and ed.getContent(ed.mark_line_start)[ed.mark_pos_start:ed.getPos()+1] == "This is line 990")
            ed.main(False)
            validate_screen(ed)

            success_count = 0
            search_succeeded = ed.search("This is line 100[0,1,2]",down = True, next = False)
            while search_succeeded:
                success_count += 1
                ed.main(False)
                found_str = ""
                if ed.isMark():
                    found_str = ed.getContent(ed.mark_line_start)[ed.mark_pos_start:ed.getPos()+1]
                assert(re.match("This is line 100[0,1,2]",found_str))
                validate_screen(ed)
                search_succeeded = ed.searchagain()

            assert(success_count == 60)

            ed.goto(307,0)
            ed.main(False)
            play_macro(ed, [ 'fk06','down','l','i','n','e',' ','3','0','8','\t','down','l','i','n','e',' ','6','6','6','\t','\n','\t','\t','\n','\n' ] )
            ed.goto(307,0)
            ed.main(False)
            assert(ed.getContent(ed.getLine()) == lines_to_test[ed.getLine()].replace('line 308','line 666'))
            validate_screen(ed)

            ed.goto(main.target_line,0)
            ed.main(False)
            ed.mark_span()
            ed.goto(main.target_line,15)
            ed.main(False)
            validate_mark(ed, lines_to_test, main.target_line, main.target_line, 0, 15 )

            ed.goto(main.target_line,15)
            ed.main(False)
            ed.mark_span()
            ed.goto(main.target_line+5,25)
            ed.main(False)
            validate_mark(ed, lines_to_test, main.target_line, main.target_line+5, 15, 25 )

            ed.goto(main.target_line,15)
            ed.main(False)
            ed.mark_span()
            ed.goto(main.target_line+5,ed.max_x)
            ed.cright()
            ed.main(False)
            validate_mark(ed, lines_to_test, main.target_line,main.target_line+5,15,ed.getPos())

            ed.goto(main.target_line,15)
            ed.main(False)
            ed.mark_span()
            ed.goto(main.target_line+5,ed.max_x)
            ed.cright()
            ed.main(False)
            match_tuple = validate_mark(ed, lines_to_test, main.target_line,main.target_line+5,15,ed.getPos(),False)
            ed.copy_marked()
            ed.goto(main.target_line+25,0)
            ed.paste()
            ed.main(False)
            for line in range(0,5):
                assert(ed.getContent(main.target_line+25+line) == match_tuple[1][line].rstrip())
            assert(ed.getContent(main.target_line+25+5).startswith(match_tuple[1][5]))
            undo_all(ed)
            for line in range(0,6):
                assert(ed.getContent(main.target_line+25+line).startswith(lines_to_test[main.target_line+25+line]))
            ed.goto(main.target_line,15)
            ed.main(False)
            ed.mark_span()
            ed.goto(main.target_line+5,ed.max_x)
            ed.cright()
            f_line = ed.getLine()
            f_pos = ed.getPos()
            ed.main(False)
            ed.copy_marked(True,False)
            ed.main(False)
            assert(ed.getLine()==main.target_line and ed.getPos()==15)
            target_contents = ed.getContent(main.target_line)
            match_contents = lines_to_test[main.target_line][0:15]+lines_to_test[f_line][f_pos+1:]
            assert(target_contents.startswith(match_contents))
            ed.goto(main.target_line+25,0)
            ed.paste()
            ed.main(False)
            for line in range(0,5):
                assert(ed.getContent(main.target_line+25+line) == match_tuple[1][line].rstrip())
            assert(ed.getContent(main.target_line+25+5).startswith(match_tuple[1][5]))
            undo_all(ed)
            for line in range(0,6):
                assert(ed.getContent(main.target_line+25+line).startswith(lines_to_test[main.target_line+25+line]))

            ed.goto(main.target_line,15)
            ed.main(False)
            ed.mark_lines()
            ed.goto(main.target_line+5,25)
            ed.main(False)
            validate_mark(ed,lines_to_test,main.target_line,main.target_line+5,15,25,True, clipboard.LINE_CLIP)

            if not wrapped:
                ed.goto(main.target_line,0)
                ed.main(False)
                ed.goto(main.target_line,15)
                ed.main(False)
                ed.mark_rect()
                ed.goto(main.target_line+5,25)
                ed.main(False)
                validate_mark(ed,lines_to_test,main.target_line,main.target_line+5,15,25,True, clipboard.RECT_CLIP)

            ed.goto(main.target_line,15)
            ed.main(False)
            ed.cr()
            ed.main(False)
            first_line = ed.getContent(main.target_line)
            second_line = ed.getContent(main.target_line+1)
            assert(len(first_line)==15 and first_line == lines_to_test[main.target_line][0:15])
            assert(second_line == lines_to_test[main.target_line][15:].rstrip())
            validate_screen(ed)
            undo_all(ed)
            validate_screen(ed)

            ed.goto(main.target_line,0)
            ed.main(False)
            ed.mark_lines()
            ed.goto(main.target_line+5,0)
            ed.main(False)
            ed.tab()
            ed.main(False)
            for line in range(0,6):
                assert(ed.getContent(main.target_line+line).startswith(' '*ed.workfile.get_tab_stop(0)))
            validate_screen(ed)
            ed.btab()
            ed.main(False)
            for line in range(0,6):
                assert(ed.getContent(main.target_line+line).startswith(lines_to_test[main.target_line+line].rstrip()))
            validate_screen(ed)
            undo_all(ed)       
            validate_screen(ed)
            while ed.isMark():
                ed.mark_lines()

            play_macro(ed, [ keytab.KEYTAB_ALTO ,'\t',keytab.KEYTAB_DOWN,'s','a','v','e','a','s','.','t','x','t','\n','\n',keytab.KEYTAB_REFRESH ] )
            new_fn = ed.getWorkfile().getFilename()
            assert(new_fn.endswith('saveas.txt'))
            lidx = 0
            for line in open(new_fn,'r'):
                assert(line.startswith(lines_to_test[lidx].rstrip()))
                lidx += 1

            ed.invalidate_all()
            ed.goto(main.target_line,15)
            ed.main(False)
            ed.insert('A test change')
            ed.main(False)
            ed.save()

            lidx = 0
            for line in open(new_fn,'r'):
                if lidx == main.target_line:
                    assert(line[15:].startswith('A test change'))
                else:
                    assert(line.startswith(lines_to_test[lidx].rstrip()))
                lidx += 1

            cur_line = ed.getLine()
            cur_pos = ed.getPos()
            play_macro(ed, [ keytab.KEYTAB_CR ] )
            assert(ed.getLine() == cur_line+1 and ed.getPos() == 0)
            start_line = ed.getLine()
            play_macro(ed, [ keytab.KEYTAB_ALTM, keytab.KEYTAB_DOWN,keytab.KEYTAB_DOWN, keytab.KEYTAB_DOWN, keytab.KEYTAB_DOWN, keytab.KEYTAB_RIGHT, keytab.KEYTAB_RIGHT, keytab.KEYTAB_RIGHT, keytab.KEYTAB_CTRLC ] )
            end_line = ed.getLine()
            assert(clipboard.clip_type == clipboard.SPAN_CLIP and len(clipboard.clip) == (end_line-start_line)+1)
            play_macro(ed, [ keytab.KEYTAB_ALTG, 'down', '4','0','0','\n'] )
            assert(ed.getLine() == 400 )

        curses.wrapper(main,False)
        curses.wrapper(main,True)
