# Copyright 2009-2012 James P Goodwin ped tiny python editor
""" module that implements the keymapping and translation of keys to command identifiers """
import curses
import curses.ascii
import sys
import os
from ped_core import cmd_names
from ped_core import keytab
import pprint
import time

# default keymap for the editor manager
keymap_manager = {
    keytab.KEYTAB_CTRLN: (cmd_names.CMD_NEXTEDITOR,keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ALTN: (cmd_names.CMD_NEXTEDITOR,keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_RESIZE: (cmd_names.CMD_RESIZE,keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_REFRESH: (cmd_names.CMD_REFRESH,keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_F12: (cmd_names.CMD_REFRESH,keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_F04: (cmd_names.CMD_NEXTFRAME,keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ALTB: (cmd_names.CMD_BUFFERLIST,keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_ALTF: (cmd_names.CMD_FILEFIND,keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_F22: (cmd_names.CMD_SFTP,keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_ALTX: (cmd_names.CMD_SAVEEXIT,keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_F01: (cmd_names.CMD_HELP, keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ALTI: (cmd_names.CMD_HELP, keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_F10: (cmd_names.CMD_SHELLCMD, keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_CTRLO: (cmd_names.CMD_OPENEDITOR, keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_ALTE: (cmd_names.CMD_OPENEDITOR, keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_CTRLP: (cmd_names.CMD_PREVEDITOR, keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ALTP: (cmd_names.CMD_PREVEDITOR, keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ALTH: (cmd_names.CMD_HORZSPLIT, keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ALTV: (cmd_names.CMD_VERTSPLIT, keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ALTZ: (cmd_names.CMD_ZOOMFRAME, keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ALTK: (cmd_names.CMD_KILLFRAME, keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_CTRLD: (cmd_names.CMD_DELEDITOR, keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_ALTD: (cmd_names.CMD_DELEDITOR, keytab.KEYTAB_NOKEY),
    keytab.KEYTAB_ESC: (cmd_names.CMD_EXITNOSAVE, keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_DLGCANCEL: (cmd_names.CMD_EXITNOSAVE, keytab.KEYTAB_REFRESH),
    keytab.KEYTAB_MOUSE: (cmd_names.CMD_MOUSE, keytab.KEYTAB_NOKEY),
    }

# default keymap for the editor
keymap_editor = {
    keytab.KEYTAB_CTRLK:       (cmd_names.CMD_MARKSPAN,        keytab.KEYTAB_NOKEY),    # CTRL-K
    keytab.KEYTAB_CTRLR:       (cmd_names.CMD_MARKRECT,        keytab.KEYTAB_NOKEY),    # CTRL-R
    keytab.KEYTAB_CTRLC:       (cmd_names.CMD_COPYMARKED,      keytab.KEYTAB_NOKEY),    # CTRL-C
    keytab.KEYTAB_CTRLG:       (cmd_names.CMD_PRMTGOTO,        keytab.KEYTAB_REFRESH),    # CTRL-G
    keytab.KEYTAB_BACKSPACE:   (cmd_names.CMD_BACKSPACE,       keytab.KEYTAB_NOKEY),    # CTRL-H
    keytab.KEYTAB_CTRLF:       (cmd_names.CMD_FILENAME,        keytab.KEYTAB_REFRESH),    # CTRL-F
    keytab.KEYTAB_CTRLX:       (cmd_names.CMD_CUTMARKED,       keytab.KEYTAB_NOKEY),    # CTRL-X
    keytab.KEYTAB_CTRLV:       (cmd_names.CMD_PASTE,           keytab.KEYTAB_NOKEY),    # ctrl-v
    keytab.KEYTAB_CTRLL:       (cmd_names.CMD_MARKLINES,       keytab.KEYTAB_NOKEY),    # ctrl-l
    keytab.KEYTAB_CR:          (cmd_names.CMD_CR,              keytab.KEYTAB_NOKEY),    # ctrl-m (enter)
    keytab.KEYTAB_TAB:         (cmd_names.CMD_TAB,             keytab.KEYTAB_NOKEY),    # tab
    keytab.KEYTAB_CTRLS:       (cmd_names.CMD_SAVE,            keytab.KEYTAB_NOKEY),    # ctrl-s (save)
    keytab.KEYTAB_CTRLW:       (cmd_names.CMD_SAVEAS,          keytab.KEYTAB_REFRESH),  # ctrl-w (save as)
    keytab.KEYTAB_ALTL:        (cmd_names.CMD_MARKLINES,       keytab.KEYTAB_NOKEY),    # alt-L
    keytab.KEYTAB_ALTM:        (cmd_names.CMD_MARKSPAN,        keytab.KEYTAB_NOKEY),    # alt-M
    keytab.KEYTAB_ALTC:        (cmd_names.CMD_MARKRECT,        keytab.KEYTAB_NOKEY),    # alt-C
    keytab.KEYTAB_ALTW:        (cmd_names.CMD_SAVE,            keytab.KEYTAB_REFRESH),    # alt-W
    keytab.KEYTAB_ALTo:        (cmd_names.CMD_SAVEAS,          keytab.KEYTAB_REFRESH),  # alt-o
    keytab.KEYTAB_ALTG:        (cmd_names.CMD_PRMTGOTO,        keytab.KEYTAB_REFRESH),    # alt-G
    keytab.KEYTAB_ALTU:        (cmd_names.CMD_UNDO,            keytab.KEYTAB_NOKEY),    # alt-U
    keytab.KEYTAB_ALTJ:        (cmd_names.CMD_TOGGLEWRAP,      keytab.KEYTAB_NOKEY),    # alt-J
    keytab.KEYTAB_KEYPADPLUS:  (cmd_names.CMD_MARKCOPYLINE,    keytab.KEYTAB_NOKEY),    # keypad +
    keytab.KEYTAB_KEYTPADMINUS:(cmd_names.CMD_MARKCUTLINE,     keytab.KEYTAB_NOKEY),    # keypad -
    keytab.KEYTAB_ALTO:        (cmd_names.CMD_SAVEAS,          keytab.KEYTAB_REFRESH),  # alt-O
    keytab.KEYTAB_BACKTAB:     (cmd_names.CMD_BTAB,            keytab.KEYTAB_NOKEY),    # BACKTAB
    keytab.KEYTAB_CTRLLEFT:    (cmd_names.CMD_PREVWORD,        keytab.KEYTAB_NOKEY),    # ctrl-leftarrow
    keytab.KEYTAB_CTRLRIGHT:   (cmd_names.CMD_NEXTWORD,        keytab.KEYTAB_NOKEY),    # ctrl-rightarrow
    keytab.KEYTAB_CTRLHOME:    (cmd_names.CMD_HOME1,           keytab.KEYTAB_NOKEY),    # home
    keytab.KEYTAB_CTRLEND:     (cmd_names.CMD_END1,            keytab.KEYTAB_NOKEY),    # end
    keytab.KEYTAB_RESIZE:      (cmd_names.CMD_RETURNKEY,       keytab.KEYTAB_RESIZE),   # resize
    keytab.KEYTAB_UP:          (cmd_names.CMD_UP,              keytab.KEYTAB_NOKEY),    # up
    keytab.KEYTAB_DOWN:        (cmd_names.CMD_DOWN,            keytab.KEYTAB_NOKEY),    # down
    keytab.KEYTAB_LEFT:        (cmd_names.CMD_LEFT,            keytab.KEYTAB_NOKEY),    # left
    keytab.KEYTAB_RIGHT:       (cmd_names.CMD_RIGHT,           keytab.KEYTAB_NOKEY),    # right
    keytab.KEYTAB_DELC:        (cmd_names.CMD_DELC,            keytab.KEYTAB_NOKEY),    # del
    keytab.KEYTAB_BACKSPACE:   (cmd_names.CMD_BACKSPACE,       keytab.KEYTAB_NOKEY),    # backspace
    keytab.KEYTAB_HOME:        (cmd_names.CMD_HOME,            keytab.KEYTAB_NOKEY),    # home
    keytab.KEYTAB_END:         (cmd_names.CMD_END,             keytab.KEYTAB_NOKEY),    # end
    keytab.KEYTAB_PAGEUP:      (cmd_names.CMD_PAGEUP,          keytab.KEYTAB_NOKEY),    # pageup
    keytab.KEYTAB_PAGEDOWN:    (cmd_names.CMD_PAGEDOWN,        keytab.KEYTAB_NOKEY),    # pagedown
    keytab.KEYTAB_BTAB:        (cmd_names.CMD_BTAB,            keytab.KEYTAB_NOKEY),    # backtab
    keytab.KEYTAB_INSERT:      (cmd_names.CMD_PASTE,           keytab.KEYTAB_NOKEY),    # paste
    keytab.KEYTAB_F05:         (cmd_names.CMD_PRMTSEARCH,      keytab.KEYTAB_REFRESH),  # F5
    keytab.KEYTAB_F06:         (cmd_names.CMD_PRMTREPLACE,     keytab.KEYTAB_REFRESH),  # F6
    keytab.KEYTAB_F07:         (cmd_names.CMD_TRANSFERCLIPIN,  keytab.KEYTAB_NOKEY),    # F7
    keytab.KEYTAB_F08:         (cmd_names.CMD_TRANSFERCLIPOUT, keytab.KEYTAB_NOKEY),    # f8
    keytab.KEYTAB_F17:         (cmd_names.CMD_PRMTSEARCHBACK,  keytab.KEYTAB_REFRESH),  # SHIFT F5
    keytab.KEYTAB_F03:         (cmd_names.CMD_SEARCHAGAIN,     keytab.KEYTAB_REFRESH),  # F3
    keytab.KEYTAB_F09:         (cmd_names.CMD_TOGGLERECORD,    keytab.KEYTAB_NOKEY),    # F9
    keytab.KEYTAB_ALTA:        (cmd_names.CMD_PLAYBACK,        keytab.KEYTAB_NOKEY),   # alt-a
    keytab.KEYTAB_F11:         (cmd_names.CMD_PLAYBACK,        keytab.KEYTAB_NOKEY),    # F11
    }

# default keymap for dialogs
keymap_dialog = {
    keytab.KEYTAB_TAB: (cmd_names.CMD_DLGNEXT, keytab.KEYTAB_DLGNOP),
    keytab.KEYTAB_CR: (cmd_names.CMD_DLGNEXT, keytab.KEYTAB_DLGNOP),
    keytab.KEYTAB_BTAB: (cmd_names.CMD_DLGPREV, keytab.KEYTAB_DLGNOP),
    keytab.KEYTAB_UP: (cmd_names.CMD_DLGUP, keytab.KEYTAB_DLGNOP ),
    keytab.KEYTAB_ESC: (cmd_names.CMD_RETURNKEY, keytab.KEYTAB_DLGCANCEL ),
    keytab.KEYTAB_RESIZE: (cmd_names.CMD_DLGRESIZE, keytab.KEYTAB_DLGNOP ),
    keytab.KEYTAB_MOUSE: (cmd_names.CMD_DLGMOUSE, keytab.KEYTAB_NOKEY),
    }

recording = False
playback = False
macro = []
macro_idx = 0
keydef_map = {}

def insert_keydef( km, oseq, kt ):
    """ insert into the keydef_map an ordinal sequence and a keytab key to map it to """
    try:
        if len(oseq) == 1:
            km[oseq[0]] = kt
        else:
            if oseq[0] not in km:
                km[oseq[0]] = {}
            insert_keydef( km[oseq[0]], oseq[1:], kt )
    except:
        raise

def compile_keydef():
    """ compile ketab.keydef into keydef_map for lookup of ordinal key strings """
    global keydef_map
    keydef_map = {}
    for kd in keytab.keydef:
        insert_keydef( keydef_map, kd[0], kd[1] )

def start_recording():
    """ start recording key sequences into macro list """
    global recording, macro, macro_idx
    recording = True
    macro = []
    macro_idx = 0

def stop_recording():
    """ stop recording key sequences into macro list """
    global recording
    recording = False

def toggle_recording():
    """ flip recording on or off """
    global recording,macro
    if recording:
        macro.pop()
        stop_recording()
    else:
        start_recording()

def is_recording():
    """ return current state of recording key macro """
    global recording
    return recording

def start_playback():
    """ start playback from macro """
    global playback, macro_idx
    playback = True
    macro_idx = 0
    if is_recording():
        stop_recording()

def stop_playback():
    """ stop playback from macro """
    global playback, macro_index
    playback = False
    macro_index = 0

def record_seq( seq ):
    """ record a key sequence into the buffer """
    global macro
    if (len(seq) == 1 and seq[0] == -1) or seq == '\x00':
        return
    macro.append(seq)

def playback_seq():
    """ get the next sequence to play back """
    global macro, macro_idx
    if macro and macro_idx < len(macro):
        seq = macro[macro_idx]
        macro_idx += 1
        return seq
    stop_playback()
    return keytab.KEYTAB_REFRESH

def is_playback():
    """ return true if we are in playback mode """
    global playback
    return playback

def keypending( scr ):
    """ return true if getch is going to return a real key """
    ch = scr.getch()
    if ch >= 0:
        curses.ungetch(ch)
    return (ch >= 0)

def getch( scr ):
    """ wrapper to fetch keys from a curses screen or window """
    global playback
    if playback:
        return 0
    else:
        time.sleep(0.01)
        ch = scr.getch()
        return ch

def get_keyseq( scr, ch ):
    """ get the full key sequence to be mapped, parameter is the first key of the sequence """
    global playback, recording

    if playback:
        return playback_seq()

    if 0<ch<256 and curses.ascii.isprint(ch):
        seq = chr(ch)
    else:
        map = keydef_map
        while True:
            if ch in map:
                map = map[ch]
                if not isinstance(map,dict):
                    seq = map
                    break
            else:
                seq = keytab.KEYTAB_NOKEY
                break
            if ch < 0:
                while ch < 0:
                    ch = scr.getch()
            else:
                ch = scr.getch()

    if recording:
        record_seq( seq )

    return seq

def mapkey( scr, keymap_xlate, ch ):
    """ complete fetching the key sequence and get the command and return character as a tuple (cmd_id, retkey) """
    seq = get_keyseq( scr, ch )
    return mapseq( keymap_xlate, seq )

def mapseq( keymap_xlate, seq ):
    """ map a key sequence from the KEYMAP_ constants to a command using the supplied keymap_xlate hash  return (cmd,seq) tuple"""
    ret = (cmd_names.CMD_RETURNKEY,seq)
    if len(seq) == 1 and curses.ascii.isprint(ord(seq[0])):
        return (cmd_names.CMD_INSERT,ord(seq[0]))
    elif seq in keymap_xlate:
        ret = keymap_xlate[seq]
    return ret

def loadkeymap():
    """ look for a file ~/.pedkeymap and load alternate key bindings from it """
    # lines either are blank, are a comment starting with #
    #  or are KEYMAP={EDITOR,DIALOG,MANAGER} which selects a keymap to apply subsequent binding to also clears that keymap
    #  or MAP=key,cmd,ret which maps key to cmd and specifies the return key that should result after the cmd executes
    global keymap_editor, keymap_dialog,keymap_manager

    kmf = os.path.expanduser("~/.pedkeymap")
    mapname = None
    if os.path.exists(kmf):
        for l in open(kmf,"r"):
            l = l.strip()
            if l and not l.startswith("#"):
                if l.startswith("KEYMAP"):
                    keyword,mapname = l.split("=",1)
                    mapname = mapname.strip().upper()
                    if mapname == "EDITOR":
                        keymap_editor = {}
                    elif mapname == "DIALOG":
                        keymap_dialog = {}
                    elif mapname == "MANAGER":
                        keymap_manager = {}
                elif l.startswith("MAP"):
                    keyword,mapping = l.split("=",1)
                    mapping = mapping.strip().upper()
                    key,cmd,ret = mapping.split(",",2)
                    if mapname == "EDITOR":
                        keymap_editor[keytab.name_to_key[key]] = ( cmd_names.name_to_cmd[cmd], keytab.name_to_key[ret] )
                    elif mapname == "DIALOG":
                        keymap_dialog[keytab.name_to_key[key]] = ( cmd_names.name_to_cmd[cmd], keytab.name_to_key[ret] )
                    elif mapname == "MANAGER":
                        keymap_manager[keytab.name_to_key[key]] = ( cmd_names.name_to_cmd[cmd], keytab.name_to_key[ret] )

def dumpkeymap():
    """ create a default ~/.pedkeymap keybinding file """
    kmf = os.path.expanduser("~/.pedkeymap")
    f = open(kmf,"w")
    keymaps = [ ("EDITOR",keymap_editor), ("DIALOG",keymap_dialog), ("MANAGER",keymap_manager) ]
    for name,km in keymaps:
        print("KEYMAP=%s"%name, file=f)
        for key, mapping in list(km.items()):
            print("MAP=%s,%s,%s"%(keytab.key_to_name[key],cmd_names.cmd_to_name[mapping[0]],keytab.key_to_name[mapping[1]]), file=f)

def loadkeydef():
    """ look for a file ~/.pedkeydef and load alternate KEYTAB definitions and mappings from raw curses key codes to KEYTAB definitions """
    # lines either are blank, are a comment starting with #
    # or are KEYTAB_KEY="literal"
    # or are KEYDEF=ord,[ord1...ordn],KEYTAB_KEY
    #
    kdf = os.path.expanduser("~/.pedkeydef")
    if os.path.exists(kdf):
        keytab.keydef = []
        for l in open(kdf,"r"):
            l = l.strip()
            if l and not l.startswith("#"):
                key,value = l.split("=",1)
                key = key.strip()
                value = value.strip()
                if key == "KEYDEF":
                    parms = [f.strip() for f in value.split(",")]
                    ords = tuple([int(f) for f in parms[:-1]])
                    key = keytab.name_to_key[parms[-1]]
                    keytab.keydef.append((ords,key))
                elif key.startswith("KEYTAB_"):
                    setattr(keytab,key,eval(value))
                    keytab.name_to_key[key] = eval(value)
                    keytab.key_to_name[eval(value)] = key
        compile_keydef()

def dumpkeydef():
    """ create a default ~/.pedkeydef keydef file """
    kdf = os.path.expanduser("~/.pedkeydef")
    fkdf = open(kdf,"w")
    for attr_name in dir(keytab):
        if attr_name.startswith("KEYTAB_"):
            print("%s=%s"%(attr_name,repr(getattr(keytab,attr_name))), file=fkdf)
    for k in keytab.keydef:
        print("KEYDEF=%s,%s"%(",".join([str(f) for f in k[0]]),keytab.key_to_name[k[1]]), file=fkdf)


# force the keydef_map to be built on load of module
if not keydef_map:
    compile_keydef()

def main(stdscr):
    stdscr.nodelay(1)
    stdscr.notimeout(0)
    stdscr.timeout(0)
    curses.raw()
    line = 0
    col = 0
    seq = get_keyseq(stdscr, getch(stdscr))
    k = mapseq(keymap_editor,seq)
    while True:
        if k[1] == 32:
            break
        if seq != '\x00':
            stdscr.addstr(line,col,"%s == %s               "%(seq,str(k)), curses.A_REVERSE)
            line += 1
            line = line % 10
        seq = get_keyseq(stdscr, getch(stdscr))
        k = mapseq(keymap_editor,seq)

    stdscr.nodelay(0)
#        altch = stdscr.getch()
#        stdscr.nodelay(1)
#        rest = ""
#        while altch > 0:
#            stdscr.addstr(0,0, "curses[%d][%s]"%(altch,curses.keyname(altch)), curses.A_REVERSE)
#            altch = stdscr.getch()
#
#        stdscr.nodelay(0)

if __name__ == '__main__':
    os.environ.setdefault('ESCDELAY','25')
    curses.wrapper(main)
