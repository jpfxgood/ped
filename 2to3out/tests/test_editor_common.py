import editor_common 
import io
import pprint
import os
import curses
import curses.ascii
import time
import re
import keymap
import clipboard

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
    pprint.pprint(fls)
    assert( ef.numLines() == 4 )
    ef.close()
    assert( ef.getWorking() == None )
    ef.load()
    w = ef.getWorking()
    assert( isinstance(w,io.IOBase) and not w.closed )
    for line in range(0,len(lines_to_test)):
        assert(ef.length(line) == len(lines_to_test[line])+1)
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
    assert(fls[9].rstrip() == new_test_line) 
    newname = os.path.join(fd,"1_"+os.path.basename(fn))
    ef.save(newname)
    assert(os.path.exists(newname))
    ef.close()
    ef.load()
    assert(ef.getFilename() == newname)
    fls = ef.getLines()
    for line in range(0,len(lines_to_test)):
        assert(fls[line].rstrip() == lines_to_test[line])
    assert(fls[9].rstrip() == new_test_line) 
    assert(ef.get_tab_stop(4) == 8)
    assert(ef.get_tab_stop(10) == 16 )
    assert(ef.get_tab_stop(10,True) == 8)  
    tabby_string = "01234\t56789012\t3456789"
    expanded_string = "01234   56789012        3456789"
    assert(ef.expand_tabs(tabby_string) == expanded_string)
    
def test_Editor(testdir,capsys):
    with capsys.disabled():
        lines_to_test = ["This is the first line","This is the second line","This is the third line","This is the last line"]
        lines_to_test += [ ("This is line %d "%f)*20 for f in range(5,2000) ]
        testfile = testdir.makefile(".txt",*lines_to_test)
        fn = str(testfile)
        
        def read_str( win, y, x, width ):
            out_str = ''
            for ix in range(x,x+width):
                rc = win.inch(y,ix)
                out_str += chr(rc & 0x00FF)
            return out_str

        def match_attr( win, y, x, height, width, attr ):
            for iy in range(y,y+height):
                for ix in range(x,x+width):
                    rc = win.inch(iy,ix)
                    if not (attr & rc):
                        return(False)
            return(True)
                        
            
        def main(stdscr):
            ed = editor_common.Editor(stdscr,None,fn)
            ed.setWin(stdscr.subwin(ed.max_y,ed.max_x,0,0))
            ed.main(False)
            for y in range(1,ed.max_y):
                assert(read_str(ed.scr,y,0,ed.max_x).startswith(lines_to_test[y-1][:ed.max_x-1]))
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
                line = ed.getLine()
                assert(line == target_line)
                pos = ed.getPos()
                assert(pos == target_pos)
                (y,x) = ed.scrPos(line,ed.left)
                y = (y-ed.line)+1
                x = x-ed.left
                compare_string = lines_to_test[target_line][ed.left:ed.left+ed.max_x]
                assert(read_str(ed.scr,y,x,ed.max_x).startswith(compare_string))
                ed.insert('X')
                assert(ed.isChanged())
                assert(ed.isLineChanged(target_line))
                ed.main(False)
                prev_compare_string = compare_string
                compare_string = lines_to_test[target_line][ed.left:pos] + 'X' + lines_to_test[target_line][pos]
                assert(read_str(ed.scr,y,x,ed.max_x).startswith(compare_string))
                ed.undo()
                ed.main(False)
                assert(read_str(ed.scr,y,x,ed.max_x).startswith(prev_compare_string))
                ed.delc()
                cur_line = ed.getLine()
                cur_pos = ed.getPos()
                if cur_line < ed.numLines()-1 and cur_pos < len(lines_to_test[cur_line]):
                    assert(ed.isChanged())
                    assert(ed.isLineChanged(target_line))
                    ed.main(False)
                    if pos+1 < len(lines_to_test[target_line]):
                        compare_string = lines_to_test[target_line][ed.left:pos] + lines_to_test[target_line][pos+1]
                    elif pos == len(lines_to_test[target_line]) and target_line+1 < len(lines_to_test):
                        compare_string = lines_to_test[target_line][ed.left:pos] + lines_to_test[target_line+1][0]
                    else:
                        compare_string = lines_to_test[target_line][ed.left:pos]
                    assert(read_str(ed.scr,y,x,ed.max_x).startswith(compare_string))
                    ed.undo()
                    ed.main(False)

                assert(read_str(ed.scr,y,x,ed.max_x).startswith(prev_compare_string))
                ed.backspace()
                assert(ed.isChanged())
                assert(ed.isLineChanged(target_line))
                ed.main(False)
                if pos+1 < len(lines_to_test[target_line]):
                    compare_string = lines_to_test[target_line][ed.left:pos-1] + lines_to_test[target_line][pos:pos+1]
                else:
                    compare_string = lines_to_test[target_line][ed.left:pos-1]
                    
                assert(read_str(ed.scr,y,x,ed.max_x).startswith(compare_string))
                ed.undo()
                ed.main(False)
                assert(read_str(ed.scr,y,x,ed.max_x).startswith(prev_compare_string))
            do_edit_tests()
            main.target_pos = 5
            do_edit_tests()
            ed.endln()
            assert(ed.getPos() == len(lines_to_test[main.target_line])-1)
            do_edit_tests(True)
            ed.endfile()
            assert(ed.getLine() == ed.numLines()-1)
            do_edit_tests(True)
            ed.goto(0,0)
            ed.endpg()
            ed.endln()
            assert(ed.getLine() == ed.max_y-2)
            do_edit_tests(True)
            ed.endfile()
            ed.endln()                                                   
            assert(ed.getLine() == ed.numLines(True)-1)
            do_edit_tests(True)
            start_line = ed.getLine()
            ed.pageup()
            assert(ed.getLine() == start_line - (ed.max_y-2))
            do_edit_tests(True)
            ed.pagedown()
            assert(ed.getLine() == start_line)
            do_edit_tests(True)
            ed.cup()
            assert(ed.getLine() == start_line -1 )
            do_edit_tests(True)
            ed.cdown()
            assert(ed.getLine() == start_line )
            do_edit_tests(True)
            word_pos = []                        
            in_word = False
            for i in range(0,len(lines_to_test[main.target_line])-1):
                if lines_to_test[main.target_line][i] != ' ':
                    if not in_word:
                        word_pos.append(i)
                        in_word = True
                else:
                    in_word = False
            word_pos.append(len(lines_to_test[main.target_line])-1)
            for rfunc,lfunc in [(ed.next_word,ed.prev_word),(ed.cright,ed.cleft),(ed.scroll_right,ed.scroll_left)]:
                ed.goto(main.target_line,0)
                ed.main(False)
                prev_pos = ed.getPos()
                while ed.getPos() < len(lines_to_test[main.target_line])-1:
                    rfunc()
                    if rfunc == ed.next_word:
                        assert(ed.getPos() in word_pos)
                    assert(ed.getPos() > prev_pos)
                    prev_pos = ed.getPos()
                    assert(ed.getPos() >= ed.left and ed.getPos() < ed.left+ed.max_x)
                    ed.main(False)
                    assert(read_str(ed.scr,(main.target_line-ed.line)+1,0,ed.max_x).startswith(lines_to_test[main.target_line][ed.left:ed.left+ed.max_x]))
    
                while ed.getPos() > 0:
                    lfunc()
                    if lfunc == ed.prev_word:
                        assert(ed.getPos() in word_pos)
                    assert(ed.getPos() < prev_pos)
                    prev_pos = ed.getPos()
                    assert(ed.getPos() >= ed.left and ed.getPos() < ed.left+ed.max_x)
                    ed.main(False)
                    assert(read_str(ed.scr,(main.target_line-ed.line)+1,0,ed.max_x).startswith(lines_to_test[main.target_line][ed.left:ed.left+ed.max_x]))
            ed.search("This is line 1010",True,False)
            assert(ed.getLine() == 1009 and ed.getPos() == 16) 
            ed.main(False)
            assert(read_str(ed.scr,(ed.getLine()-ed.line)+1,0,ed.max_x).startswith(lines_to_test[ed.getLine()][ed.left:ed.left+ed.max_x]))
            ed.search("This is line 990",False,False)
            assert(ed.getLine() == 989 and ed.getPos() == 338)
            ed.main(False)
            assert(read_str(ed.scr,(ed.getLine()-ed.line)+1,0,ed.max_x).startswith(lines_to_test[ed.getLine()][ed.left:ed.left+ed.max_x]))
            
            success_count = 0
            search_succeeded = ed.search("This is line 100[0,1,2]",down = True, next = False)
            while search_succeeded:
                success_count += 1
                ed.main(False)
                found_str = read_str(ed.scr,(ed.getLine()-ed.line)+1,ed.mark_pos_start-ed.left,(ed.getPos()-ed.mark_pos_start)+1)
                assert(re.match("This is line 100[0,1,2]",found_str))
                print("search loop =",ed.getLine(),ed.getPos(),found_str,success_count,search_succeeded,file=open("/home/james/ped.log","a"))
                search_succeeded = ed.searchagain()
            assert(success_count == 60)
            
            def play_macro( macro ):
                keymap.start_recording()
                for seq in macro:
                    keymap.record_seq(seq)
                keymap.stop_recording()
                keymap.start_playback()
                while keymap.is_playback():
                    ed.main(False)

            ed.goto(0,0)
            ed.main(False)
            play_macro( [ 'fk06','down','l','i','n','e',' ','3','0','8','\t','l','i','n','e',' ','6','6','6','\t','\n','\x00','\t','\t','\n','\x00','\n','refresh' ] )
            ed.goto(307,0)
            ed.main(False)
            assert(read_str(ed.scr,(ed.getLine()-ed.line)+1,0,ed.max_x).startswith(lines_to_test[307].replace('line 308','line 666')[0:ed.max_x]))
            
            ed.goto(main.target_line,0)
            ed.main(False)
            ed.mark_span()
            ed.goto(main.target_line,15)
            ed.main(False)
            assert(match_attr(ed.scr,(main.target_line-ed.line)+1,0,1,15,curses.A_REVERSE))
            assert(ed.get_marked() == ( clipboard.SPAN_CLIP, [ lines_to_test[main.target_line][0:16] ] ))
            ed.goto(main.target_line,15)
            ed.main(False)
            ed.mark_span()
            ed.goto(main.target_line+5,25)
            ed.main(False)
            assert(match_attr(ed.scr,(main.target_line-ed.line)+1,15,1,ed.max_x-15,curses.A_REVERSE))
            assert(match_attr(ed.scr,(main.target_line-ed.line)+2,0,4,ed.max_x,curses.A_REVERSE))
            assert(match_attr(ed.scr,(main.target_line-ed.line)+6,0,1,25,curses.A_REVERSE))
            match_tuple = ( clipboard.SPAN_CLIP, [  lines_to_test[main.target_line][15:]+'\n',
                                                                lines_to_test[main.target_line+1]+'\n',
                                                                lines_to_test[main.target_line+2]+'\n',
                                                                lines_to_test[main.target_line+3]+'\n',
                                                                lines_to_test[main.target_line+4]+'\n',
                                                                lines_to_test[main.target_line+5][0:26]] )
            assert(ed.get_marked() == match_tuple)
            ed.goto(main.target_line,15)
            ed.main(False)
            ed.mark_lines()
            ed.goto(main.target_line+5,25)
            ed.main(False)
            assert(match_attr(ed.scr,(main.target_line-ed.line)+1,0,5,ed.max_x,curses.A_REVERSE))
            match_tuple = ( clipboard.LINE_CLIP, [  lines_to_test[main.target_line]+'\n',
                                                    lines_to_test[main.target_line+1]+'\n',
                                                    lines_to_test[main.target_line+2]+'\n',
                                                    lines_to_test[main.target_line+3]+'\n',
                                                    lines_to_test[main.target_line+4]+'\n',
                                                    lines_to_test[main.target_line+5]+'\n'] )
            assert(ed.get_marked() == match_tuple )   
            
            ed.goto(main.target_line,0)
            ed.main(False)
            ed.goto(main.target_line,15)
            ed.main(False)
            ed.mark_rect()
            ed.goto(main.target_line+5,25)
            ed.main(False)
            assert(match_attr(ed.scr,(main.target_line-ed.line)+1,15,5,11,curses.A_REVERSE))
            match_tuple = ( clipboard.RECT_CLIP, [  lines_to_test[main.target_line][15:26],
                                                    lines_to_test[main.target_line+1][15:26],
                                                    lines_to_test[main.target_line+2][15:26],
                                                    lines_to_test[main.target_line+3][15:26],
                                                    lines_to_test[main.target_line+4][15:26],
                                                    lines_to_test[main.target_line+5][15:26]] )
            assert(ed.get_marked() == match_tuple )
            
                      
        curses.wrapper(main)
