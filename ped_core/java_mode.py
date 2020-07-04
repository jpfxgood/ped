# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a python mode for the ped editor does colorizing of java code """
from ped_core import editor_common
from ped_dialog.message_dialog import message
import re
from pygments.lexers import JavaLexer
from pygments.token import Token
from ped_core.mode import Tokens, render

def get_tabs(editor):
    """ return the tab stops for this type of file """
    return [4,8]

def detect_mode(editor):
    """ hook called to detect if this mode should be used for a file, returns True if it should be used, False otherwise """
    workfile = editor.getWorkfile()
    if re.search(r"(\.java$)|(\.java\:\(r.*\)$)",workfile.getFilename()):
        return True
    else:
        return False

def handle(editor,ch):
    """ hook called for each keystroke, can be used for auto-indent or auto-complete """
    if ch == 10:
        old_left = editor.left
        old_line = editor.line
        editor.cr()
        wf = editor.getWorkfile()
        line = editor.line + editor.vpos
        above = wf.getLine(line-1)
        match = re.match(r"^\s*(.*)(\{)\s*$",above)
        if match:
            if match.start(1) == match.start(2):
                editor.insert(match.start(1)*' ')
            else:
                editor.insert(wf.get_tab_stop(match.start(1))*' ')
        else:
            match = re.match(r"^\s*(.*)(\})\s*$",above)
            if not match:
                match = re.match(r"^\s*(\S+)",above)
                if match:
                    editor.insert(match.start(1)*' ')
            else:
                line -= 1
                while (line > 0):
                    above = wf.getLine(line-1)
                    match = re.match(r"^\s*(.*)(\{)\s*$",above)
                    if match:
                        editor.insert(match.start(1)*' ')
                        break
                    line -= 1

        if editor.left != old_left or editor.line != old_line:
            editor.invalidate_screen()
        return 0

    return ch

def finish(editor):
    """ this editor is going away do anything required to clean up """
    wf = editor.getWorkfile()
    if wf:
        if hasattr(wf,"java_mode_tokens"):
            del wf.java_mode_tokens
            wf.java_mode_tokens = None
            delattr(wf,"java_mode_tokens")

def redraw(editor):
    """ redraw the colorization based on the current token set, regenerate it if needed """
    workfile = editor.getWorkfile()

    if hasattr(workfile,"java_mode_tokens"):
        tokens = workfile.java_mode_tokens
    else:
        tokens = Tokens()
        setattr(workfile,"java_mode_tokens",tokens)

    if not tokens:
        return False

    if not tokens.getTokens() or tokens.getModref() != workfile.getModref():
        tokens.refresh(editor,JavaLexer())
        return False

    render( editor, tokens,
            [Token.Name.Decorator,Token.Keyword,Token.Operator.Word,Token.Name.Builtin.Pseudo],
            [Token.Text,Token.String,Token.Literal],
            [Token.Comment])
    return True

def name():
    """ hook to return this mode's human readable name """
    return "java_mode"
