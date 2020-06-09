import editor_common 
import io
import pprint
import os
import curses
import curses.ascii
import time

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
            target_line = 1000
            target_pos = len(lines_to_test[1000])//2
            ed.goto(target_line,target_pos)
            ed.main(False)
            line = ed.getLine()
            assert(line == target_line)
            pos = ed.getPos()
            assert(pos == target_pos)
            (y,x) = ed.scrPos(line,ed.left)
            y = (y-ed.line)+1
            x = x-ed.left
            compare_string = lines_to_test[1000][ed.left:target_pos]
            assert(read_str(ed.scr,y,x,ed.max_x-x).startswith(compare_string))
            time.sleep(5)
            ed.insert('X')
            ed.main(False)
            prev_compare_string = compare_string
            compare_string = compare_string[1:]+'X'
            assert(read_str(ed.scr,y,x,ed.max_x-x).startswith(compare_string))
            time.sleep(5)
            ed.undo()
            ed.main(False)
            assert(read_str(ed.scr,y,x,ed.max_x-x).startswith(prev_compare_string))
            time.sleep(5)
                          

    
        curses.wrapper(main)
