import keymap
import clipboard
import curses
import pprint
import gc
import editor_common
import re
import keymap
import keytab
import subprocess
from dialog import Frame,ListBox,Toggle,Button,StaticText,Prompt,PasswordPrompt,Dialog,pad
from file_browse import FileBrowseComponent
from stream_select import StreamSelectComponent
from editor_common import Editor

def screen_size( rows, columns ):
    cmd = "resize -s %d %d >/dev/null 2>/dev/null"%(rows,columns)
    subprocess.Popen(cmd,shell=True)
    curses.resizeterm( rows, columns )

def read_str( win, y, x, width ):
    out_str = ''
    for ix in range(x,x+width):
        rc = win.inch(y,ix)
        out_str += chr(rc & curses.A_CHARTEXT)
    return out_str

def match_chr( win, y, x, width, match_chr ):
    for ix in range(x,x+width):
        if match_chr != (win.inch(y,ix) & (curses.A_ALTCHARSET | curses.A_CHARTEXT)):
            return False
    return True

def match_attr( win, y, x, height, width, attr ):
    for iy in range(y,y+height):
        for ix in range(x,x+width):
            rc = win.inch(iy,ix)
            cc = chr(rc & curses.A_CHARTEXT)
            r_attr = (rc & (curses.A_ATTRIBUTES|curses.A_COLOR))&0xFFBFFFFF
            if not (attr == r_attr) and not cc.isspace():
                return(False)
    return(True)

def match_attr_str( win, y, x, width, attr ):
    return match_attr( win, y, x, 1, width, attr)

def undo_all(ed):
    while ed.isChanged():
        ed.undo()
    ed.main(False)

def window_pos(ed,line,pos):
    sc_line,sc_pos = ed.scrPos(line,pos)
    return((sc_line-ed.line)+1,sc_pos-ed.left)

def play_macro( ed_or_dialog, macro ):
    keymap.start_recording()
    for seq in macro:
        keymap.record_seq(seq)
    keymap.stop_recording()
    keymap.start_playback()
    while keymap.is_playback():
        ed_or_dialog.main(False)

def validate_mark( ed, lines_to_test, start_line, end_line, start_pos, end_pos, do_validation = True, clip_type = clipboard.SPAN_CLIP ):
    wait_for_screen(ed)
    match_tuple = ( clip_type, [ "" for f in range(start_line,end_line+1)  ] )
    lidx = 0
    for f_line in range(start_line,end_line+1):
        s_pos = 0
        e_pos = len(lines_to_test[f_line])

        if clip_type == clipboard.RECT_CLIP:
            s_pos = start_pos
            e_pos = end_pos+1
        elif clip_type == clipboard.SPAN_CLIP:
            if f_line == start_line:
                s_pos = start_pos
            if f_line == end_line:
                e_pos = end_pos+1

        if e_pos > len(lines_to_test[f_line]):
            e_pos = len(lines_to_test[f_line])

        for f_pos in range(s_pos,e_pos):
            sc_line,sc_pos = window_pos(ed,f_line,f_pos)
            c_to_test = lines_to_test[f_line][f_pos]
            match_tuple[1][lidx] += c_to_test
            if do_validation and (sc_line >= 1 and sc_line < ed.max_y and sc_pos >= 0 and sc_pos < ed.max_x):
                assert(match_attr(ed.scr,sc_line,sc_pos,1,1,curses.A_REVERSE))
                assert(read_str(ed.scr,sc_line,sc_pos,1) == c_to_test)
        if clip_type == clipboard.SPAN_CLIP and f_line != end_line and start_line != end_line:
            match_tuple[1][lidx] += '\n'
        lidx += 1
    if do_validation:
        marked_tuple = ed.get_marked()
        assert(marked_tuple == match_tuple)
    return match_tuple

def wait_for_screen(ed):
    while ed.has_changes():
        ed.main(False)

def validate_screen( ed, lines_to_test = None, start_line=-1, end_line=-1, start_pos=-1, end_pos=-1, do_validation=True ):

    wait_for_screen(ed)

    if start_line < 0:
        start_line = ed.line
    if end_line < 0:
        end_line = ed.line + (ed.max_y-1)
    if start_pos < 0:
        start_pos = ed.left
    if end_pos < 0:
        end_pos = ed.left+ed.max_x

    matched_screen = []
    error_screen = []
    lidx = 0
    for f_line in range(start_line,end_line+1):
        matched_line = ""
        error_line = ""
        s_pos = ed.left
        if lines_to_test:
            test_line = lines_to_test[f_line]
        else:
            test_line = ed.getContent(f_line)

        e_pos = len(test_line)
        if f_line == start_line:
            s_pos = start_pos
        elif f_line == end_line:
            e_pos = end_pos+1
        e_pos = min(e_pos,len(test_line))

        for f_pos in range(s_pos,e_pos):
            sc_line,sc_pos = window_pos(ed,f_line,f_pos)
            if sc_line >= 1 and sc_line < ed.max_y and sc_pos >= 0 and sc_pos < ed.max_x:
                c_to_test = test_line[f_pos]
                c_from_scr = read_str(ed.scr,sc_line,sc_pos,1)
                matched_line += c_from_scr
                error_line += ' '
                marked_error = False
                if ed.isMark() and (f_line >= min(ed.getLine(),ed.mark_line_start) and f_line <= max(ed.getLine(),ed.mark_line_start)) and (f_pos >= min(ed.getPos(),ed.mark_pos_start) and f_pos <= max(ed.getPos(),ed.mark_pos_start)):
                    if not match_attr(ed.scr,sc_line,sc_pos,1,1,curses.A_REVERSE):
                        error_line = error_line[:-1] + '#'
                        marked_error = True
                if not marked_error and (c_from_scr != c_to_test):
                    error_line = error_line[:-1] + c_from_scr
        lidx += 1
        matched_screen.append(matched_line)
        error_screen.append(error_line)

    any_errors = False
    for le in error_screen:
        if le.rstrip():
            any_errors = True
            break

    if do_validation:
        assert not any_errors, "Screen rendering error:\n%s"%pprint.pformat((any_errors,matched_screen,error_screen))

    return (any_errors,matched_screen,error_screen)

def editor_test_suite(stdscr,testdir,wrapped,editor = None ):
    screen_size( 30, 100 )
    lines_to_test = ["This is the first line","This is the second line","This is the third line","This is the last line"]
    lines_to_test += [ (("This is line %d "%f)*20).rstrip() for f in range(5,2000) ]
    testfile = testdir.makefile(".txt",*lines_to_test)
    fn = str(testfile)

    if not editor:
        max_y,max_x = stdscr.getmaxyx()
        ed = editor_common.Editor(stdscr,stdscr.subwin(max_y,max_x,0,0),fn)
    else:
        ed = editor
        ed.workfile.close()
        if ed.mode:
            ed.mode.finish(ed)
        ed.workfile.filename = fn
        ed.workfile.load()
        ed.undo_mgr.flush_undo()
        ed.flushChanges()
        ed.invalidate_all()
        gc.collect()

    if wrapped:
        ed.toggle_wrap()

    validate_screen(ed)
    assert(match_attr(ed.scr,0,0,1,ed.max_x,curses.A_REVERSE))
    ef = ed.getWorkfile()

    assert(isinstance(ef,editor_common.EditFile))
    assert(ed.getFilename() == fn)
    assert(isinstance(ed.getUndoMgr(),editor_common.undo.UndoManager))
    assert(not ed.isChanged())
    assert(ed.numLines() == 1999)
    editor_test_suite.target_line = 1000
    editor_test_suite.target_pos = len(lines_to_test[editor_test_suite.target_line])//2

    def do_edit_tests( relative = False ):
        if relative:
            target_line = ed.getLine()
            target_pos = ed.getPos()
        else:
            target_line = editor_test_suite.target_line
            target_pos = editor_test_suite.target_pos
            ed.goto(target_line,target_pos)
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
        assert(ed.isLineChanged(target_line,False))
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
            assert(ed.isLineChanged(cur_line,False))
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
        assert(ed.isLineChanged(cur_line,False))
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
    editor_test_suite.target_pos = 5
    do_edit_tests()
    ed.endln()
    assert(ed.getPos() == len(lines_to_test[editor_test_suite.target_line]))
    do_edit_tests(True)
    ed.endfile()
    assert(ed.getLine() == ed.numLines()-1)
    do_edit_tests(True)
    ed.goto(0,0)
    ed.endpg()
    ed.endln()
    sc_line,sc_pos = window_pos(ed,ed.getLine(),ed.getPos())
    assert(sc_line == ed.max_y-1)
    do_edit_tests(True)
    ed.endfile()
    ed.endln()
    assert(ed.getLine(True) == ed.numLines(True)-1)
    do_edit_tests(True)
    start_line = ed.getLine(True)
    ed.pageup()
    assert(ed.getLine(True) == start_line - (ed.max_y-2))
    do_edit_tests(True)
    ed.pagedown()
    assert(ed.getLine(True) == start_line)
    do_edit_tests(True)
    ed.cup()
    assert(ed.getLine(True) == start_line -1 )
    do_edit_tests(True)
    ed.cdown()
    assert(ed.getLine(True) == start_line )
    do_edit_tests(True)
    word_pos = []
    in_word = False
    for i in range(0,len(lines_to_test[editor_test_suite.target_line])):
        if lines_to_test[editor_test_suite.target_line][i] != ' ':
            if not in_word:
                word_pos.append(i)
                in_word = True
        else:
            in_word = False
    word_pos.append(len(lines_to_test[editor_test_suite.target_line]))
    for rfunc,lfunc in [(ed.next_word,ed.prev_word),(ed.cright,ed.cleft),(ed.scroll_right,ed.scroll_left)]:
        if wrapped and rfunc == ed.scroll_right:
            break
        ed.goto(editor_test_suite.target_line,0)
        prev_pos = ed.getPos()
        while ed.getPos() < len(lines_to_test[editor_test_suite.target_line])-2:
            rfunc()
            if rfunc == ed.next_word:
                assert(ed.getPos() in word_pos)
            assert(ed.getPos() > prev_pos)
            prev_pos = ed.getPos()
            s_line,s_pos = ed.filePos(ed.getLine(True),ed.left)
            assert(ed.getPos() >= s_pos and ed.getPos() < s_pos+ed.max_x)
            validate_screen(ed)

        while ed.getPos() > 0:
            lfunc()
            if ed.getLine() != editor_test_suite.target_line:
                break
            if lfunc == ed.prev_word:
                assert(ed.getPos() in word_pos)
            assert(ed.getPos() < prev_pos)
            prev_pos = ed.getPos()
            s_line,s_pos = ed.filePos(ed.getLine(True),ed.left)
            assert(ed.getPos() >= s_pos and ed.getPos() < s_pos+ed.max_x)
            validate_screen(ed)

    ed.search("This is line 1010",True,False)
    assert(ed.getLine() == 1009 and ed.getPos() == 16 and ed.isMark() and ed.mark_line_start == 1009 and ed.mark_pos_start == 0 and ed.getContent(ed.mark_line_start)[ed.mark_pos_start:ed.getPos()+1] == "This is line 1010")
    validate_screen(ed)

    ed.search("This is line 990",False,False)
    assert(ed.getLine() == 989 and ed.getPos() == 338 and ed.isMark() and ed.mark_line_start == 989 and ed.mark_pos_start == 339-len("This is line 990") and ed.getContent(ed.mark_line_start)[ed.mark_pos_start:ed.getPos()+1] == "This is line 990")
    validate_screen(ed)

    success_count = 0
    search_succeeded = ed.search("This is line 100[0,1,2]",down = True, next = False)
    while search_succeeded:
        success_count += 1
        found_str = ""
        if ed.isMark():
            found_str = ed.getContent(ed.mark_line_start)[ed.mark_pos_start:ed.getPos()+1]
        assert(re.match("This is line 100[0,1,2]",found_str))
        validate_screen(ed)
        search_succeeded = ed.searchagain()

    assert(success_count == 60)

    ed.goto(307,0)
    play_macro(ed, [ 'fk06','down','l','i','n','e',' ','3','0','8','\t','down','l','i','n','e',' ','6','6','6','\t','\n','\t','\t','\n','\n' ] )
    ed.goto(307,0)
    assert(ed.getContent(ed.getLine()) == lines_to_test[ed.getLine()].replace('line 308','line 666'))
    validate_screen(ed)

    ed.goto(editor_test_suite.target_line,0)
    ed.mark_span()
    ed.goto(editor_test_suite.target_line,15)
    validate_mark(ed, lines_to_test, editor_test_suite.target_line, editor_test_suite.target_line, 0, 15 )

    ed.goto(editor_test_suite.target_line,15)
    ed.mark_span()
    ed.goto(editor_test_suite.target_line+5,25)
    validate_mark(ed, lines_to_test, editor_test_suite.target_line, editor_test_suite.target_line+5, 15, 25 )

    ed.goto(editor_test_suite.target_line,15)
    ed.mark_span()
    ed.goto(editor_test_suite.target_line+5,ed.max_x)
    ed.cright()
    validate_mark(ed, lines_to_test, editor_test_suite.target_line,editor_test_suite.target_line+5,15,ed.getPos())

    ed.goto(editor_test_suite.target_line,15)
    ed.mark_span()
    ed.goto(editor_test_suite.target_line+5,ed.max_x)
    ed.cright()
    match_tuple = validate_mark(ed, lines_to_test, editor_test_suite.target_line,editor_test_suite.target_line+5,15,ed.getPos(),False)
    ed.copy_marked()
    ed.goto(editor_test_suite.target_line+25,0)
    ed.paste()
    for line in range(0,5):
        assert(ed.getContent(editor_test_suite.target_line+25+line) == match_tuple[1][line].rstrip())
    assert(ed.getContent(editor_test_suite.target_line+25+5).startswith(match_tuple[1][5]))
    undo_all(ed)
    for line in range(0,6):
        assert(ed.getContent(editor_test_suite.target_line+25+line).startswith(lines_to_test[editor_test_suite.target_line+25+line]))
    ed.goto(editor_test_suite.target_line,15)
    ed.mark_span()
    ed.goto(editor_test_suite.target_line+5,ed.max_x)
    ed.cright()
    f_line = ed.getLine()
    f_pos = ed.getPos()
    ed.copy_marked(True,False)
    assert(ed.getLine()==editor_test_suite.target_line and ed.getPos()==15)
    target_contents = ed.getContent(editor_test_suite.target_line)
    match_contents = lines_to_test[editor_test_suite.target_line][0:15]+lines_to_test[f_line][f_pos+1:]
    assert(target_contents.startswith(match_contents))
    ed.goto(editor_test_suite.target_line+25,0)
    ed.paste()
    for line in range(0,5):
        assert(ed.getContent(editor_test_suite.target_line+25+line) == match_tuple[1][line].rstrip())
    assert(ed.getContent(editor_test_suite.target_line+25+5).startswith(match_tuple[1][5]))
    undo_all(ed)
    for line in range(0,6):
        assert(ed.getContent(editor_test_suite.target_line+25+line).startswith(lines_to_test[editor_test_suite.target_line+25+line]))

    ed.goto(editor_test_suite.target_line,15)
    ed.mark_lines()
    ed.goto(editor_test_suite.target_line+5,25)
    validate_mark(ed,lines_to_test,editor_test_suite.target_line,editor_test_suite.target_line+5,15,25,True, clipboard.LINE_CLIP)

    if not wrapped:
        ed.goto(editor_test_suite.target_line,0)
        ed.goto(editor_test_suite.target_line,15)
        ed.mark_rect()
        ed.goto(editor_test_suite.target_line+5,25)
        validate_mark(ed,lines_to_test,editor_test_suite.target_line,editor_test_suite.target_line+5,15,25,True, clipboard.RECT_CLIP)

    ed.goto(editor_test_suite.target_line,15)
    ed.cr()
    first_line = ed.getContent(editor_test_suite.target_line)
    second_line = ed.getContent(editor_test_suite.target_line+1)
    assert(len(first_line)==15 and first_line == lines_to_test[editor_test_suite.target_line][0:15])
    assert(second_line == lines_to_test[editor_test_suite.target_line][15:].rstrip())
    validate_screen(ed)
    undo_all(ed)
    validate_screen(ed)

    while ed.isMark():
        ed.mark_lines()
    ed.goto(editor_test_suite.target_line,0)
    ed.mark_lines()
    ed.goto(editor_test_suite.target_line+5,0)
    ed.tab()
    for line in range(0,6):
        assert(ed.getContent(editor_test_suite.target_line+line).startswith(' '*ed.workfile.get_tab_stop(0)))
    validate_screen(ed)
    ed.btab()
    for line in range(0,6):
        assert(ed.getContent(editor_test_suite.target_line+line).startswith(lines_to_test[editor_test_suite.target_line+line].rstrip()))
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
    ed.goto(editor_test_suite.target_line,15)
    ed.insert('A test change')
    ed.save()

    lidx = 0
    for line in open(new_fn,'r'):
        if lidx == editor_test_suite.target_line:
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

def validate_rect( win,y,x,height,width,title,attr = curses.A_NORMAL ):
    """ validate that a rect is rendered correctly """
    assert(read_str(win,y,x+(width//2)-(len(title)//2),len(title)) == title)
    assert(match_attr_str(win,y,x+(width//2)-(len(title)//2),len(title),attr))
    assert(match_chr(win,y,x,1,curses.ACS_ULCORNER))
    assert(match_attr_str(win,y,x,1,attr))
    assert(match_chr(win,y,x+1,(width//2)-(len(title)//2)-1,curses.ACS_HLINE))
    assert(match_chr(win,y,x+(width//2-len(title)//2)+len(title),width-((width//2-len(title)//2)+len(title))-1,curses.ACS_HLINE))
    assert(match_attr_str(win,y,x+1,width-2,attr))
    assert(match_chr(win,y+height-1,x+1,width-2,curses.ACS_HLINE))
    assert(match_attr_str(win,y+height-1,x+1,width-2,attr))
    assert(match_chr(win,y,x+width-1,1,curses.ACS_URCORNER))
    assert(match_attr_str(win,y,x+width-1,1,attr))
    for oy in range(0,height-2):
        assert(match_chr(win,y+oy+1,x,1,curses.ACS_VLINE))
        assert(match_attr_str(win,y+oy+1,x,1,attr))
        assert(match_chr(win,y+oy+1,x+width-1,1,curses.ACS_VLINE))
        assert(match_attr_str(win,y+oy+1,x+width-1,1,attr))
    assert(match_chr(win,y+height-1,x,1,curses.ACS_LLCORNER))
    assert(match_attr_str(win,y+height-1,x,1,attr))
    assert(match_chr(win,y+height-1,x+width-1,1,curses.ACS_LRCORNER))
    assert(match_attr_str(win,y+height-1,x+width-1,1,attr))

def validate_dialog( d ):
    """ validate that a dialog is rendering it's state correctly """
    for c in d.children:
        if d.focus_list[d.current][1] == c:
            c.focus()

        if isinstance(c,Frame):
            win = c.getparent()
            if c.x >= 0:
                x = c.x
                y = c.y
                height = c.h
                width = c.w
            else:
                x = 0
                y = 0
                height,width = win.getmaxyx()
            validate_rect( win, y,x,height,width,c.title)
        elif isinstance(c,ListBox):
            win = c.getparent()
            x = c.x
            y = c.y
            height = c.height
            width = c.width
            validate_rect( win, y,x,height,width,c.label,(curses.A_BOLD if c.isfocus else curses.A_NORMAL))
            x+=1
            y+=1
            width -= 2
            height -= 2

            top = c.top
            off = 0
            cy = -1
            while top < len(c.list) and off < height:
                if top == c.selection:
                    rattr = curses.A_REVERSE
                    cy = y+off
                else:
                    if c.isfocus:
                        rattr = curses.A_BOLD
                    else:
                        rattr = curses.A_NORMAL
                assert(read_str(win,y+off,x,width) == pad(c.list[top],width)[0:width])
                assert(match_attr_str(win,y+off,x,width,rattr))
                top += 1
                off += 1
        elif isinstance(c,Toggle):
            win = c.getparent()
            if c.isfocus:
                lattr = curses.A_REVERSE
            else:
                lattr = curses.A_NORMAL
            x = c.x
            y = c.y
            width = c.width
            assert(read_str(win,y,x,width)==pad(c.list[c.selection],width)[0:width])
            assert(match_attr_str(win,y,x,width,lattr))
        elif isinstance(c,Button):
            win = c.getparent()
            if c.isfocus:
                battr = curses.A_REVERSE
            else:
                battr = curses.A_NORMAL
            label = "["+c.label+"]"
            width = len(label)
            assert(read_str(win,c.y,c.x,width) == label)
            assert(match_attr_str(win,c.y,c.x,width,battr))
        elif isinstance(c,StaticText):
            win = c.getparent()
            max_y,max_x = win.getmaxyx()
            width = (max_x - c.x) - 1
            x = c.x
            assert(read_str(win,c.y,x,len(c.prompt[-width:])) == c.prompt[-width:])
            assert(match_attr_str(win,c.y,x,len(c.prompt[-width:]),curses.A_NORMAL))
            x += len(c.prompt[-width:])
            width -= len(c.prompt[-width:])
            if width > 0:
                assert(read_str(win,c.y,x,c.width) == pad(c.value,c.width)[-width:])
                assert(match_attr_str(win,c.y,x,c.width,curses.A_NORMAL))
        elif isinstance(c,PasswordPrompt):
            win = c.getparent()
            if c.isfocus:
                pattr = curses.A_BOLD
                fattr = curses.A_REVERSE
            else:
                pattr = curses.A_NORMAL
                fattr = curses.A_NORMAL

            if c.width < 0:
                (max_y,max_x) = win.getmaxyx()
                c.width = max_x - (c.x+len(c.prompt)+2)

            assert(read_str(win,c.y,c.x,len(c.prompt)) == c.prompt)
            assert(match_attr_str(win,c.y,c.x,len(c.prompt),pattr))
            assert(read_str(win,c.y,c.x+len(c.prompt),c.width) == pad(len(c.value)*"*",c.width))
            assert(match_attr_str(win,c.y,c.x+len(c.prompt),c.width,fattr))
        elif isinstance(c,Prompt):
            win = c.getparent()
            if c.isfocus:
                pattr = curses.A_BOLD
                fattr = curses.A_REVERSE
            else:
                pattr = curses.A_NORMAL
                fattr = curses.A_NORMAL

            if c.width < 0:
                (max_y,max_x) = win.getmaxyx()
                c.width = max_x - (c.x+len(c.prompt)+2)

            assert(read_str(win,c.y,c.x,len(c.prompt)) == c.prompt)
            assert(match_attr_str(win,c.y,c.x,len(c.prompt),pattr))
            assert(read_str(win,c.y,c.x+len(c.prompt),c.width) == pad(c.value,c.width)[0:c.width])
            assert(match_attr_str(win,c.y,c.x+len(c.prompt),c.width,fattr))
        elif isinstance(c,FileBrowseComponent) or isinstance(c,StreamSelectComponent):
            win = c.getparent()
            if c.isfocus:
                attr = curses.A_BOLD
            else:
                attr = curses.A_NORMAL

            validate_rect(win,c.y,c.x,c.height,c.width,c.label,attr)
            c.editor.main(False)
            c.editor.main(False)
            validate_screen(c.editor)

        if d.focus_list[d.current][1] == c:
            c.render()
            c.getparent().refresh()
