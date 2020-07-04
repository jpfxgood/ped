# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a python mode for the ped editor does colorizing  by guessing the lexer of code """
from ped_core import editor_common
from ped_dialog.message_dialog import message
import re
from pygments.lexers import get_lexer_for_filename
from pygments.token import Token
from ped_core.mode import Tokens, render

lexer = None

def get_tabs(editor):
    """ return the tab stops for this type of file """
    return [4,8]

def detect_mode(editor):
    """ hook called to detect if this mode should be used for a file, returns True if it should be used, False otherwise """
    workfile = editor.getWorkfile()
    global lexer
    try:
        filename = workfile.getFilename()
        if filename:
            lexer = get_lexer_for_filename(filename,{})
        else:
            lexer = get_lexer_for_filename("unknown.txt",{})
        return True
    except Exception as e:
        lexer = get_lexer_for_filename("unknown.txt",{})
        return True

def handle(editor,ch):
    """ hook called for each keystroke, can be used for auto-indent or auto-complete """
    return ch


def finish(editor):
    """ this editor is going away do anything required to clean up """
    wf = editor.getWorkfile()
    if wf:
        if hasattr(wf,"guess_mode_tokens"):
            del wf.guess_mode_tokens
            wf.guess_mode_tokens = None
            delattr(wf,"guess_mode_tokens")

def redraw(editor):
    """ redraw the colorization based on the current token set, regenerate it if needed """
    workfile = editor.getWorkfile()

    if hasattr(workfile,"guess_mode_tokens"):
        tokens = workfile.guess_mode_tokens
    else:
        tokens = Tokens()
        setattr(workfile,"guess_mode_tokens",tokens)

    if not tokens:
        return False

    if not tokens.getTokens() or tokens.getModref() != workfile.getModref():
        detect_mode(editor)
        tokens.refresh(editor,lexer)
        return False

    render(editor,tokens,
            [Token.Name.Tag,Token.Name.Decorator,Token.Keyword.Declaration,Token.Operator.Word,Token.Name.Builtin.Pseudo,Token.Keyword,Token.Keyword.Namespace],
            [Token.Text,Token.String,Token.Literal.String,Token.Literal.String.Single,Token.Literal.String.Double,Token.Literal.String.Doc],
            [Token.Comment,Token.Comment.Hashbang,Token.Comment.Multiline,Token.Comment.Single])

    return True

def name():
    """ hook to return this mode's human readable name """
    if lexer:
        return lexer.name
    else:
        return ""
