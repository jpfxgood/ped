# Copyright 2009 James P Goodwin ped tiny python editor
""" module to implement a python mode for the ped editor does colorizing of c/cpp code """
import editor_common
from message_dialog import message
import re
from pygments.lexers import CLexer,CppLexer
from pygments.token import Token
from mode import Tokens,render
import copy

lexer = None

def get_tabs(editor):
    """ return the tab stops for this type of file """
    return [2,4]

def detect_mode(editor):
    """ hook called to detect if this mode should be used for a file, returns True if it should be used, False otherwise """
    global lexer
    workfile = editor.getWorkfile()
    if re.search(r"(\.c$)|(\.c\:\(r.*\)$)",workfile.getFilename()):
        lexer = CLexer()
        return True
    elif re.search(r"(\.cpp$)|(\.cpp\:\(r.*\)$)",workfile.getFilename()):
        lexer = CppLexer()
        return True
    elif re.search(r"(\.h$)|(\.h\:\(r.*\)$)",workfile.getFilename()):
        lexer = CLexer()
        return True
    elif re.search(r"(\.hpp$)|(\.hpp\:\(r.*\)$)",workfile.getFilename()):
        lexer = CppLexer()
        return True
    else:
        return False

def handle(editor,ch):
    """ hook called for each keystroke, can be used for auto-indent or auto-complete """
    return ch

def finish(editor):     
    """ this editor is going away do anything required to clean up """
    pass

def redraw(editor):
    """ redraw the colorization based on the current token set, regenerate it if needed """
    workfile = editor.getWorkfile()

    if hasattr(workfile,"cpp_mode_tokens"):
        tokens = workfile.cpp_mode_tokens
    else:
        tokens = Tokens()
        setattr(workfile,"cpp_mode_tokens",tokens)

    if not tokens:
        return False

    if not tokens.getTokens() or tokens.getModref() != workfile.getModref():
        tokens.refresh(workfile,copy.copy(lexer))
        return False
        
    render(editor,tokens,
            [Token.Name.Decorator,Token.Keyword.Declaration,Token.Operator.Word,Token.Name.Builtin.Pseudo,Token.Keyword,Token.Keyword.Namespace],
            [Token.Text,Token.String,Token.Literal.String,Token.Literal.String.Doc],
            [Token.Comment,Token.Comment.Single])
            
    return True

def name():
    """ hook to return this mode's human readable name """
    if lexer:
        return lexer.name
    else:
        return ""
