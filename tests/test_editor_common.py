from ped_core import editor_common
import io
import pprint
import os
import curses
import curses.ascii
import time
import re
from ped_core import keymap
from ped_core import keytab
from ped_core import clipboard
from ped_test_util import read_str, match_attr, undo_all, window_pos, play_macro, validate_mark, validate_screen, editor_test_suite

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
    assert( not w.closed )
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
    assert( not w.closed )
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

def test_Editor_unwrapped(testdir,capsys):
    with capsys.disabled():
        curses.wrapper(editor_test_suite,testdir,False,None)

def test_Editor_wrapped(testdir,capsys):
    with capsys.disabled():
        curses.wrapper(editor_test_suite,testdir,True,None)
