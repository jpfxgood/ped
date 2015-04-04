# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a python mode for the ped editor does colorizing of java code """
import editor_common
from message_dialog import message
import re
from pygments.lexers import JavaLexer
from pygments.token import Token
from mode import Tokens, render

def get_tabs(editor):
    """ return the tab stops for this type of file """
    return [4,8]

def detect_mode(editor):
    """ hook called to detect if this mode should be used for a file, returns True if it should be used, False otherwise """
    workfile = editor.getWorkfile()
    if re.search("(\.java$)|(\.java\:\(r.*\)$)",workfile.getFilename()):
        return True
    else:
        return False

def handle(editor,ch):
    """ hook called for each keystroke, can be used for auto-indent or auto-complete """
    if ch == 10:
        editor.cr()
        wf = editor.getWorkfile()
        line = editor.line + editor.vpos
        above = wf.getLine(line-1)
        match = re.match("^\s*(if|for|while|else|try|catch|public|private|protected|do|class)\W",above)
        if match:
            stop = wf.get_tab_stop(match.start(1))
            editor.insert(stop*' ')
        else:
            match = re.match("^\s*(\S+)",above)
            if match:
                editor.insert(match.start(1)*' ')
        return 0
        
    return ch

def finish(editor):     
    """ this editor is going away do anything required to clean up """
    pass

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
        tokens.refresh(workfile,JavaLexer())
        return False

    render( editor, tokens,
            [Token.Name.Decorator,Token.Keyword.Declaration,Token.Operator.Word,Token.Name.Builtin.Pseudo,Token.Keyword,Token.Keyword.Namespace],
            [Token.Text,Token.String,Token.Literal.String,Token.Literal.String.Doc],
            [Token.Comment,Token.Comment.Single])
    return True

def name():
    """ hook to return this mode's human readable name """
    return "java_mode"
