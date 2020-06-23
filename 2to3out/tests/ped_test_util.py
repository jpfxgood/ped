import keymap
import clipboard
import curses
import pprint

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

def validate_screen( ed, lines_to_test = None, start_line=-1, end_line=-1, start_pos=-1, end_pos=-1, do_validation=True ):
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
